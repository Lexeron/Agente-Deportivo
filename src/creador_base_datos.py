import os
import json
import time
import pandas as pd
import numpy as np


def construir_base_masiva():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_febrero = os.path.join(directorio_actual, "../betwatch_football_2026_02", "2026", "02")

    print(f"🚀 Iniciando el rastreo PROPORCIONAL en: {ruta_febrero}")

    if not os.path.exists(ruta_febrero):
        print("❌ ERROR CRÍTICO: No encuentro la carpeta.")
        return

    inicio_tiempo = time.time()
    lista_dataframes = []
    partidos_procesados = 0
    partidos_omitidos = 0

    dias = sorted([d for d in os.listdir(ruta_febrero) if os.path.isdir(os.path.join(ruta_febrero, d))])

    for dia in dias:
        ruta_dia = os.path.join(ruta_febrero, dia)
        print(f"📅 Procesando día {dia}/02/2026...")

        partidos = [p for p in os.listdir(ruta_dia) if os.path.isdir(os.path.join(ruta_dia, p))]

        for match_id_str in partidos:
            ruta_partido = os.path.join(ruta_dia, match_id_str)
            ruta_json = os.path.join(ruta_partido, f"{match_id_str}.json")

            if not os.path.exists(ruta_json):
                partidos_omitidos += 1
                continue

            try:
                with open(ruta_json, 'r', encoding='utf-8') as f:
                    match_info = json.load(f)

                market_id_objetivo = None
                runners_map = {}

                for market in match_info.get('markets', []):
                    if market.get('name') == 'Match Odds':
                        market_id_objetivo = market['market_id']
                        for runner in market.get('runners', []):
                            runners_map[runner['runner_identifier']] = runner['name']
                        break

                if market_id_objetivo is None:
                    partidos_omitidos += 1
                    continue

                ruta_parquet = os.path.join(ruta_partido, f"{market_id_objetivo}.parquet")
                if not os.path.exists(ruta_parquet):
                    partidos_omitidos += 1
                    continue

                df = pd.read_parquet(ruta_parquet, engine='pyarrow')

                if df.empty or 'runner_identifier' not in df.columns:
                    partidos_omitidos += 1
                    continue

                if 'score' in df.columns:
                    score_df = df['score'].apply(pd.Series)
                    df = pd.concat([df.drop(['score'], axis=1), score_df], axis=1)

                df = df.sort_values(by=['runner_identifier', 'date']).reset_index(drop=True)
                df_limpio = pd.DataFrame()

                for runner_id, grupo in df.groupby('runner_identifier'):
                    grupo = grupo.copy()

                    if 'time' in grupo.columns:
                        grupo['time'] = pd.to_numeric(grupo['time'], errors='coerce')
                        grupo = grupo.dropna(subset=['time'])

                    if grupo.empty:
                        continue

                    grupo['odd_diff'] = grupo['cote'].diff().fillna(0)
                    grupo['volumen_relativo_tick'] = grupo['volume'].diff().fillna(0)
                    grupo['volumen_relativo_tick'] = grupo['volumen_relativo_tick'].clip(lower=0)

                    # --- TU NUEVA LÓGICA DE IMPACTO RELATIVO ---
                    # Calculamos qué % representa este tick sobre el volumen total acumulado hasta ese momento
                    # Evitamos dividir por cero usando np.where
                    grupo['porcentaje_impacto'] = np.where(
                        grupo['volume'] > 0,
                        (grupo['volumen_relativo_tick'] / grupo['volume']) * 100,
                        0
                    )

                    cuota_final_del_partido = grupo['cote'].iloc[-1]
                    if cuota_final_del_partido <= 1.05:
                        etiqueta_ganador = 1
                    else:
                        etiqueta_ganador = 0

                    grupo['target_victoria'] = etiqueta_ganador

                    grupo['match_id'] = match_id_str
                    grupo['nombre_equipo'] = runners_map.get(runner_id, "Desconocido")

                    for col in ['goal_v1', 'goal_v2', 'red_v1', 'red_v2']:
                        if col in grupo.columns:
                            grupo[col] = grupo[col].fillna(0)
                        else:
                            grupo[col] = 0

                    df_limpio = pd.concat([df_limpio, grupo])

                # --- EL NUEVO ESCUDO INTELIGENTE ---
                if not df_limpio.empty:
                    # Condición 1: Que entren al menos 300€ (Suelo mínimo para evitar ruido de céntimos)
                    # Condición 2: Que el golpe represente más del 4% de todo el dinero de ese equipo
                    filtro_inteligente = (df_limpio['volumen_relativo_tick'] >= 300) & (
                                df_limpio['porcentaje_impacto'] >= 4.0)
                    df_limpio = df_limpio[filtro_inteligente]

                if not df_limpio.empty:
                    lista_dataframes.append(df_limpio)
                    partidos_procesados += 1
                else:
                    partidos_omitidos += 1

            except Exception as e:
                partidos_omitidos += 1

    if lista_dataframes:
        print("\n🔨 Consolidando datos de alta calidad en un archivo masivo...")
        base_datos_final = pd.concat(lista_dataframes, ignore_index=True)

        if 'date' in base_datos_final.columns:
            base_datos_final = base_datos_final.sort_values(by=['date']).reset_index(drop=True)

        ruta_guardado = os.path.join(directorio_actual, "../data/dataset_febrero_masivo.parquet")
        base_datos_final.to_parquet(ruta_guardado, engine='pyarrow', index=False)

        tiempo_total = (time.time() - inicio_tiempo) / 60
        print(f"\n✅ ¡ÉXITO! Base de datos de 'Smart Money Relativo' creada con {len(base_datos_final)} filas.")
        print(f"💾 Guardada en: {ruta_guardado}")
        print(f"📈 Partidos procesados con inyecciones relevantes: {partidos_procesados}")
        print(f"⏱️ Tiempo: {tiempo_total:.2f} minutos.")
    else:
        print("\n❌ No se extrajeron inyecciones grandes. Prueba bajando los filtros.")


if __name__ == '__main__':
    construir_base_masiva()