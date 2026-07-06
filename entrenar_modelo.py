import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib


def entrenar_agente_smart_money():
    print("🧠 Iniciando el entrenamiento del Agente Deportivo (Modo Smart Money)...")

    # 1. Cargar la base de datos de alta calidad
    ruta_datos = "dataset_febrero_masivo.parquet"
    print(f"📂 Cargando datos filtrados desde {ruta_datos}...")
    try:
        df = pd.read_parquet(ruta_datos, engine='pyarrow')
    except Exception as e:
        print(f"❌ Error al cargar los datos: {e}")
        return

    print(f"✅ Total de anomalías financieras detectadas para entrenar: {len(df)} filas.")

    # 2. Limpieza final de seguridad
    # Nos aseguramos de que no haya nulos en las columnas que vamos a usar
    df = df.dropna(
        subset=['cote', 'porcentaje_impacto', 'volumen_relativo_tick', 'odd_diff', 'time', 'target_victoria'])

    # 3. Definir Variables Independientes (X) y el Target (y)
    # Estas son las pistas que el algoritmo usará para deducir si el equipo ganará
    features = [
        'cote',  # ¿A qué cuota entró el dinero?
        'porcentaje_impacto',  # ¿Qué porcentaje del mercado representó el golpe? (Tu métrica estrella)
        'volumen_relativo_tick',  # ¿Cuántos euros exactos fueron?
        'odd_diff',  # ¿La cuota estaba subiendo o bajando en ese instante?
        'time'  # ¿En qué minuto del partido ocurrió?
    ]

    X = df[features]
    y = df['target_victoria']

    # Vemos cómo de desbalanceado está el mercado
    victorias = len(df[df['target_victoria'] == 1])
    derrotas = len(df[df['target_victoria'] == 0])
    print(
        f"📊 Distribución de inyecciones: {victorias} acabaron en Victoria (1) | {derrotas} acabaron en No Victoria (0)")

    # 4. Dividir los datos (80% para estudiar, 20% para hacerle un examen al final)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 5. Entrenar el modelo (Random Forest)
    print("🌲 Entrenando el Bosque Aleatorio (Random Forest)...")
    # Usamos class_weight='balanced' para que el algoritmo preste más atención a la clase minoritaria si la hay
    modelo = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1, class_weight='balanced')
    modelo.fit(X_train, y_train)

    # 6. Evaluar el rendimiento
    print("\n📈 EVALUACIÓN DEL MODELO EN EL EXAMEN (Datos no vistos):")
    predicciones = modelo.predict(X_test)

    print("\nReporte de Clasificación:")
    print(classification_report(y_test, predicciones))

    print("\nMatriz de Confusión:")
    matriz = confusion_matrix(y_test, predicciones)
    print(f"Falsos Positivos (Dinero perdido): {matriz[0][1]}")
    print(f"Verdaderos Positivos (Smart Money acertado): {matriz[1][1]}")

    # 7. Guardar el cerebro para usarlo en el Agente en Vivo
    ruta_modelo = "modelo_agente_clasificador.pkl"
    joblib.dump(modelo, ruta_modelo)
    print(f"\n💾 ¡Cerebro de Smart Money optimizado y guardado en {ruta_modelo}!")


if __name__ == '__main__':
    entrenar_agente_smart_money()