# ⚽ Chatbot IA para Análisis Predictivo de Datos Deportivos

Este repositorio contiene la arquitectura completa y el código fuente del proyecto "Desarrollo de un chat bot con IA para datos deportivos". El sistema integra ingeniería de datos en tiempo real, modelos predictivos y una interfaz conversacional inteligente.

## 🧠 Arquitectura y Metodología

1. **Motor de Extracción y Minería de Datos:** Scraping en vivo mediante Playwright. Datos históricos gestionados en formato `.parquet` para eficiencia analítica.
2. **Modelo de Machine Learning:** Clasificador basado en Random Forest (`scikit-learn`) que aplica la métrica de "Porcentaje de Impacto" para detectar anomalías de mercado.
3. **Agente Conversacional y UI:** Interfaz web interactiva con Streamlit, conectada a LLMs mediante LangChain.

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python 3.10+
* **Machine Learning:** Scikit-Learn, Pandas, Numpy
* **Agente IA:** LangChain / Google Gemini API
* **Scraping:** Playwright
* **Interfaz Gráfica:** Streamlit

## 🚀 Guía Completa de Ejecución (Paso a Paso)

### Paso 1: Clonar el repositorio
```bash
git clone [https://github.com/Lexeron/Agente-Deportivo.git](https://github.com/Lexeron/Agente-Deportivo.git)
cd Agente-Deportivo
```
### Paso 2: Crear el entorno virtual e instalar dependencias
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
### Paso 3: Configurar variables de entorno
Crea un archivo .env en la raíz y añade tu clave:
```bash
GOOGLE_API_KEY=tu_clave_aqui
```
### Paso 4: Preparar el navegador (Navegador persistente)
Abre una terminal (CMD o PowerShell) y ejecuta este comando para iniciar el puerto de depuración:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\perfil_bot"
```
Nota: Debes dejar esta ventana de Chrome abierta mientras el bot esté funcionando.

### Paso 5: Lanzar el Agente
En una nueva terminal, activa el entorno virtual y ejecuta:
```bash
venv\Scripts\activate
streamlit run main.py
```
📊 Roadmap de Desarrollo

[ ] Optimización de la base de datos local para histórico de alertas.

[ ] Refinamiento de prompts para análisis predictivo avanzado.

[ ] Implementación de lógica de pagos para servicios premium.
