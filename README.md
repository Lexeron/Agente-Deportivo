# ⚽ Chatbot IA para Análisis Predictivo de Datos Deportivos

Este repositorio contiene el código fuente y la arquitectura completa del proyecto **"Desarrollo de un chat bot con IA para datos deportivos"**. 

El sistema integra ingeniería de datos en tiempo real, un modelo predictivo entrenado para la detección de *Smart Money* y una interfaz conversacional inteligente impulsada por Modelos de Lenguaje Grande (LLMs).

## 🧠 Arquitectura y Metodología

El núcleo del proyecto se divide en tres subsistemas principales:

1. **Motor de Extracción y Minería de Datos:** Utiliza técnicas de *Web Scraping* para capturar métricas en vivo (cuotas, volúmenes transaccionados, minuto del partido). Los datos históricos se procesan mediante estructuras columnares eficientes (`.parquet`).
2. **Modelo de Machine Learning:** Se ha desarrollado un clasificador basado en **Random Forest** utilizando `scikit-learn`. El algoritmo aplica una métrica matemática propia denominada *Porcentaje de Impacto* para normalizar los volúmenes de inyección de capital, logrando una **precisión del 81%** en la detección de oportunidades de mercado.
3. **Agente Conversacional y UI:** Interfaz web interactiva construida con **Streamlit** que permite al usuario consultar partidos en directo, visualizar el radar de alertas y recibir análisis en lenguaje natural.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Machine Learning:** Scikit-Learn[cite: 1], Pandas, Numpy
* **Agente IA:** LangChain / OpenAI API (o el proveedor LLM configurado)
* **Scraping en vivo:** Playwright
* **Interfaz Gráfica:** Streamlit

## 🚀 Guía de Instalación y Despliegue

Sigue estos pasos para levantar el entorno de forma local:

### 1. Clonar el repositorio y preparar el entorno
Se recomienda aislar las dependencias utilizando un entorno virtual.

```bash
git clone [https://github.com/tu-usuario/chatbot-deportivo-ia.git](https://github.com/tu-usuario/chatbot-deportivo-ia.git)
cd chatbot-deportivo-ia
python -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate
