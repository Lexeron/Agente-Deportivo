import os
import json
import pandas as pd
import numpy as np


class MotorDatosBetwatch:
    """
    Motor ETL para procesar datos históricos de Betwatch.
    Combina la lectura de JSON y Parquet, extrayendo métricas de volumen y cuotas.
    """

    def __init__(self, ruta_base):
        self.ruta_base = ruta_base

    def cargar_mapeo_runners(self, match_id):
        """
        Lee el archivo JSON del partido para mapear runner_identifier a nombres reales.
        """
        ruta_json = os.path.join(self.ruta_base, str(match_id), f"{match_id}.json")

        with open(ruta_json, 'r', encoding='utf-8') as f:
            match_info = json.load(f)

        runners_map = {}
        # Iteramos sobre los mercados para guardar los identificadores
        for market in match_info.get('markets', []):
            market_id = market['market_id']
            runners_map[market_id] = {}
            for runner in market['runners']:
                runners_map[market_id][runner['runner_identifier']] = runner['name']

        return runners_map

    def cargar_y_limpiar_mercado(self, match_id, market_id):
        """
        Carga el Parquet, desanida el marcador y prepara la serie temporal.
        """
        ruta_parquet = os.path.join(self.ruta_base, str(match_id), f"{market_id}.parquet")

        # Usamos pandas con pyarrow como recomienda la documentación
        df = pd.read_parquet(ruta_parquet, engine='pyarrow')

        # La columna 'score' es un diccionario, vamos a desanidarla en columnas separadas
        # Extraemos: tiempo, goles, tarjetas, etc.
        if 'score' in df.columns:
            score_df = df['score'].apply(pd.Series)
            df = pd.concat([df.drop(['score'], axis=1), score_df], axis=1)

        # Ordenamos cronológicamente por la fecha del tick
        df = df.sort_values(by=['runner_identifier', 'date']).reset_index(drop=True)

        return df

    def compilar_mes_completo(self, nombre_mercado_objetivo="Match Odds"):
        """
        Recorre todos los días y partidos de la ruta base para crear el dataset global.
        """
        datos_globales = pd.DataFrame()
        partidos_procesados = 0

        # self.ruta_base ahora debería apuntar al mes: .../betwatch_football_2026_02/2026/02/

        # 1. Recorrer las carpetas de los días (01, 02, 03...)
        for dia in os.listdir(self.ruta_base):
            ruta_dia = os.path.join(self.ruta_base, dia)
            if not os.path.isdir(ruta_dia):
                continue

            # 2. Recorrer las carpetas de los partidos dentro de cada día
            for match_id_str in os.listdir(ruta_dia):
                ruta_partido = os.path.join(ruta_dia, match_id_str)
                if not os.path.isdir(ruta_partido):
                    continue

                match_id = int(match_id_str)
                ruta_json = os.path.join(ruta_partido, f"{match_id}.json")

                # Si no hay JSON, saltamos este partido
                if not os.path.exists(ruta_json):
                    continue

                # 3. Leer el JSON para buscar el ID del mercado objetivo (ej: "Match Odds")
                with open(ruta_json, 'r', encoding='utf-8') as f:
                    match_info = json.load(f)

                market_id_objetivo = None
                runners_nombres = {}

                for market in match_info.get('markets', []):
                    if market['name'] == nombre_mercado_objetivo:
                        market_id_objetivo = market['market_id']
                        for runner in market['runners']:
                            runners_nombres[runner['runner_identifier']] = runner['name']
                        break  # Ya encontramos el mercado

                if market_id_objetivo is None:
                    continue  # Este partido no tiene el mercado que buscamos

                # 4. Cargar el Parquet y procesarlo
                try:
                    # Ajustamos temporalmente la ruta_base del motor para que la función
                    # cargar_y_limpiar_mercado funcione mirando dentro del día correcto
                    ruta_original = self.ruta_base
                    self.ruta_base = ruta_dia

                    df_crudo = self.cargar_y_limpiar_mercado(match_id, market_id_objetivo)
                    df_procesado = self.ingenieria_de_caracteristicas(df_crudo)

                    # Añadir metadatos útiles
                    df_procesado['match_id'] = match_id
                    df_procesado['nombre_equipo'] = df_procesado['runner_identifier'].map(runners_nombres)

                    # Concatenar al dataset global
                    datos_globales = pd.concat([datos_globales, df_procesado], ignore_index=True)
                    partidos_procesados += 1

                    # Restauramos la ruta
                    self.ruta_base = ruta_original

                except Exception as e:
                    print(f"⚠️ Error procesando partido {match_id}: {e}")
                    self.ruta_base = ruta_original

        print(f"✅ Proceso finalizado. {partidos_procesados} partidos procesados.")
        return datos_globales

    def ingenieria_de_caracteristicas(self, df, umbral_desajuste=0.15, ventanas_futuro=5):
        """
        Calcula las métricas solicitadas: Derivadas de cuota, volumen relativo y define el Target.
        """
        # Agrupamos por runner para que los cálculos de cuotas no se mezclen entre equipos
        df_procesado = pd.DataFrame()

        for runner_id, grupo in df.groupby('runner_identifier'):
            grupo = grupo.copy()

            # 1. MÉTRICAS DE CUOTAS (Derivada / Velocidad de cambio)
            # Calculamos la diferencia de la cuota respecto al tick anterior
            grupo['odd_diff'] = grupo['cote'].diff().fillna(0)
            grupo['odd_velocidad_media_3m'] = grupo['odd_diff'].rolling(window=3).mean().fillna(0)

            # 2. MÉTRICAS DE VOLUMEN
            # Volumen inyectado en este tick exacto (derivada del volumen)
            grupo['volumen_relativo_tick'] = grupo['volume'].diff().fillna(0)
            grupo['volumen_relativo_tick'] = grupo['volumen_relativo_tick'].apply(
                lambda x: max(x, 0))  # Evitar negativos raros

            # 3. DEFINICIÓN DEL ÉXITO (TARGET - LABELING)
            # Queremos saber si en 'N' ticks hacia el futuro la cuota va a subir o bajar drásticamente.
            # Shift mueve la columna hacia arriba para "mirar al futuro"
            grupo['cote_futura'] = grupo['cote'].shift(-ventanas_futuro)

            # Calculamos el % de cambio hacia el futuro
            grupo['cambio_porcentual_futuro'] = ((grupo['cote_futura'] - grupo['cote']) / grupo['cote'])

            # Etiquetamos:
            #  1 = Sube drásticamente (oportunidad de Lay)
            # -1 = Baja drásticamente (oportunidad de Back)
            #  0 = Estable
            condiciones = [
                (grupo['cambio_porcentual_futuro'] >= umbral_desajuste),
                (grupo['cambio_porcentual_futuro'] <= -umbral_desajuste)
            ]
            opciones = [1, -1]
            grupo['target_desajuste'] = np.select(condiciones, opciones, default=0)

            df_procesado = pd.concat([df_procesado, grupo])

        # Limpiamos los nulos que generó el shift() al final del archivo
        df_procesado = df_procesado.dropna(subset=['cote_futura'])

        return df_procesado.sort_values(by='date')


# --- CÓMO USAR ESTA HERRAMIENTA EN TU ENTORNO LOCAL ---
if __name__ == '__main__':
    import os

    # 1. Obtenemos la ruta absoluta de donde está tu script Agente.py
    DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))

    # 2. Construimos la ruta dinámica hacia el día 1 de febrero
    # Fíjate en la jerarquía /año/mes/día que exige Betwatch
    RUTA_DATOS = os.path.join(DIRECTORIO_BASE, "betwatch_football_2026_02", "2026", "02", "01")

    MATCH_ID = 35108566

    # ¡OJO! Según el JSON de muestra, el mercado "Match Odds" tiene el ID 252278031
    # Asegúrate de usar el correcto para el partido que estás probando
    MARKET_ID = 252278031

    print(f"Buscando datos en: {RUTA_DATOS}")

    # Iniciamos el motor
    motor = MotorDatosBetwatch(RUTA_DATOS)

    try:
        # 1. Cargamos nombres reales
        nombres_runners = motor.cargar_mapeo_runners(MATCH_ID)
        print("Equipos detectados:", nombres_runners[MARKET_ID])

        # 2. Cargamos el Parquet
        df_crudo = motor.cargar_y_limpiar_mercado(MATCH_ID, MARKET_ID)

        # 3. Calculamos derivadas y Target
        df_listo_para_ml = motor.ingenieria_de_caracteristicas(df_crudo, umbral_desajuste=0.10, ventanas_futuro=10)
        df_listo_para_ml['nombre_equipo'] = df_listo_para_ml['runner_identifier'].map(nombres_runners[MARKET_ID])

        print("\n✅ ÉXITO. Muestra de datos listos:")
        columnas_clave = ['time', 'nombre_equipo', 'cote', 'odd_diff', 'volume', 'volumen_relativo_tick',
                          'target_desajuste']
        print(df_listo_para_ml[columnas_clave].head(10))

    except FileNotFoundError as e:
        print(f"\n❌ ERROR DE RUTA: {e}")
        print("Revisa que la carpeta 'betwatch_football_2026_02' esté bien escrita y contenga '2026/02/01/35108566'.")