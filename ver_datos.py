import pandas as pd


def inspeccionar_archivo_masivo():
    ruta_datos = "dataset_febrero_masivo.parquet"
    print(f"🔍 Abriendo tu base de datos MASIVA: {ruta_datos}...\n")

    try:
        # 1. Cargamos el archivo grande
        df = pd.read_parquet(ruta_datos, engine='pyarrow')

        print("📊 1. TAMAÑO DEL DATASET:")
        print(f"Total de filas registradas: {len(df)}\n")

        # 2. Vemos exactamente qué columnas nos guardó tu creador de bases de datos
        print("🛠️ 2. TODAS LAS COLUMNAS DISPONIBLES EN EL ARCHIVO:")
        columnas = df.columns.tolist()
        print(columnas)

        # 3. Buscamos las columnas vitales para la nueva estrategia
        print("\n👀 3. BUSCANDO CONTEXTO DEL PARTIDO (Minutos y Goles):")
        cols_tiempo_goles = [c for c in columnas if
                             c.lower() in ['time', 'minute', 'score', 'home_score', 'away_score']]
        if cols_tiempo_goles:
            print(f"✅ ¡Perfecto! El dataset incluye estas columnas de contexto: {cols_tiempo_goles}")
        else:
            print(
                "⚠️ Cuidado: No detecto columnas con nombres obvios de minutos o goles. Tendremos que revisar la lista de arriba.")

        # 4. Filtramos para ver solo dónde está el Dinero Inteligente
        print("\n💰 4. MUESTRA PURA DE 'SMART MONEY' (Inyecciones de > 2000€ en un instante):")
        if 'volumen_relativo_tick' in df.columns:
            # Buscamos anomalías financieras reales
            inyecciones = df[df['volumen_relativo_tick'] > 2000].sort_values(by='volumen_relativo_tick',
                                                                             ascending=False)

            if not inyecciones.empty:
                print(f"Detectadas {len(inyecciones)} inyecciones masivas en el histórico.")

                # Preparamos las columnas a mostrar (las básicas + las de tiempo si existen)
                cols_mostrar = ['nombre_equipo', 'cote', 'volume', 'volumen_relativo_tick']
                cols_mostrar.extend(cols_tiempo_goles)

                # Mostramos el Top 10 de inyecciones de dinero más bestias de tu base de datos
                print(inyecciones[cols_mostrar].head(10).to_string(index=False))
            else:
                print("No hay inyecciones mayores a 2000€. (Quizás el filtro deba ser más bajo).")

    except Exception as e:
        print(f"❌ Error abriendo el archivo: {e}")


if __name__ == '__main__':
    inspeccionar_archivo_masivo()