import sys
import re
import joblib
import asyncio
import numpy as np
import pandas as pd
import time
import threading
from sklearn.ensemble import RandomForestRegressor
from streamlit.runtime.scriptrunner import add_script_run_ctx

navegador_lock = threading.Lock()  # EL SEMÁFORO PARA EL PUERTO 9222

# --- PARCHE DE WINDOWS OBLIGATORIO ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent

# --- 1. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Agente Betwatch Live", page_icon="📈", layout="wide")

st.title("🤖 Analista Betwatch Live (Nivel 4: Memoria + Navegación + ML Dual)")
st.markdown("Analizando tu navegador Chrome real en el puerto **9222** y aplicando **Random Forest**.")




# --- 2. CARGA DEL MODELO DE MACHINE LEARNING REAL ---
@st.cache_resource
def cargar_cerebro_ia():
    """Carga el modelo RandomForest pre-entrenado con los 3.2M de datos históricos."""
    try:
        print("🧠 Cargando modelo de clasificación deportivo...")
        modelo = joblib.load("models/modelo_agente_clasificador.pkl")
        print("✅ Modelo cargado correctamente.")
        return modelo
    except Exception as e:
        print(f"❌ Error cargando el modelo: {e}")
        st.error("No se encontró 'modelo_agente_clasificador.pkl'. ¡Entrena el modelo primero!")
        return None

modelo_ia = cargar_cerebro_ia()

# --- 3. HERRAMIENTAS DEL AGENTE ---
@tool
def evaluar_smart_money_en_vivo(cuota: float, volumen_total: float, inyeccion_actual: float, odd_diff: float, minuto: int) -> str:
    """
    PREDICCIÓN ML AVANZADA: Evalúa si una inyección de dinero en un partido en vivo es "Smart Money" real.
    Necesita la cuota actual, el volumen total acumulado, cuánto dinero acaba de entrar, la variación de cuota y el minuto.
    """
    if not modelo_ia:
        return "Error: El cerebro (modelo ML) no está cargado."

    try:
        # 1. Filtro matemático de emergencia (Evitar ruido)
        if inyeccion_actual < 300:
            return "⚖️ **RUIDO DE MERCADO:** La inyección es menor a 300€. No es relevante para el análisis."

        # 2. Calcular la métrica estrella: Porcentaje de Impacto
        porcentaje_impacto = 0
        if volumen_total > 0:
            porcentaje_impacto = (inyeccion_actual / volumen_total) * 100

        if porcentaje_impacto < 4.0:
            return f"🟢 **MERCADO NORMAL:** La inyección representa solo un {porcentaje_impacto:.1f}% del volumen total. No hay anomalías graves."

        # 3. Predicción con nuestro Modelo Random Forest Entrenado
        variables_ml = [[cuota, porcentaje_impacto, inyeccion_actual, odd_diff, minuto]]
        prediccion = modelo_ia.predict(variables_ml)[0]
        prob_victoria = modelo_ia.predict_proba(variables_ml)[0][1] * 100

        if prediccion == 1:
            return f"🔥 **SMART MONEY DETECTADO (ALERTA ROJA):** El modelo predice VICTORIA. \nEl impacto es masivo ({porcentaje_impacto:.1f}% del mercado). Probabilidad de éxito estadístico: {prob_victoria:.1f}%."
        else:
            return f"⚠️ **TRAMPA DE MERCADO (DUMB MONEY):** Entró mucho dinero ({inyeccion_actual}€), pero la IA ha visto este patrón antes y predice que NO GANARÁN. Evitar esta apuesta."

    except Exception as e:
        return f"Error en la evaluación del Smart Money: {e}"
@tool
def escanear_betwatch_en_vivo() -> str:
    """Extrae el contenido de la portada de Betwatch manteniendo los nombres de los equipos."""
    with navegador_lock:
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                pagina = browser.contexts[0].pages[0]
                pagina.goto("https://betwatch.fr/")
                pagina.wait_for_timeout(5000)

                # --- SCROLL Y CLIC MÚLTIPLE EN CARGAR MÁS ---
                print("⏬ Iniciando escaneo de portada...")
                limite_paginas = 3

                for i in range(limite_paginas):
                    pagina.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    pagina.wait_for_timeout(1500)
                    try:
                        boton_mas = pagina.locator("button").filter(
                            has_text=re.compile(r"more|plus|load|cargar", re.IGNORECASE)).filter(visible=True).first

                        if boton_mas.is_visible():
                            boton_mas.click(force=True)
                            pagina.wait_for_timeout(2000)
                        else:
                            break
                    except Exception:
                        break

                # --- NUEVA EXTRACCIÓN CORREGIDA ---
                # Obtenemos el texto de la página tal cual lo ve el usuario
                cuerpo_texto = pagina.locator("body").inner_text()

                # Limpiamos saltos de línea excesivos usando expresiones regulares (re),
                # pero MANTENEMOS las palabras (nombres de equipos) intactas.
                texto_limpio = re.sub(r'\n+', '\n', cuerpo_texto.strip())

                # Cortamos a 8000 caracteres para no pasar el límite de la IA,
                # lo que nos da margen para leer los primeros 15-20 partidos perfectamente.
                texto_comprimido = texto_limpio[:8000]

                if not texto_comprimido or len(texto_comprimido) < 10:
                    return "Error: La página está en blanco o no extrajo datos."

                return f"INSTRUCCIÓN: Detecta los nombres de los equipos, cuotas y volumen de euros (€). Haz una TABLA MARKDOWN clara.\n\nDATOS EXTRAÍDOS:\n{texto_comprimido}"
        except Exception as e:
            return f"ERROR de navegador: {e}"

@tool
def analizar_partido_a_fondo(nombre_equipo: str) -> str:
    """Hace clic en un partido específico y extrae su texto."""
    with navegador_lock:
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                pagina = browser.contexts[0].pages[0]
                pagina.goto("https://betwatch.fr/money")
                pagina.wait_for_timeout(5000)

                enlace_equipo = pagina.locator(f"a:has-text('{nombre_equipo}')").filter(visible=True).first
                if enlace_equipo.is_visible():
                    enlace_equipo.scroll_into_view_if_needed()
                    enlace_equipo.click(force=True)
                    pagina.wait_for_timeout(4000)
                else:
                    return f"No encontré enlace para {nombre_equipo}."

                cuerpo_texto = pagina.locator("body").inner_text()
                return f"DATOS DE {nombre_equipo}:\n\n{cuerpo_texto[:15000]}"
        except Exception as e:
            return f"Error de navegación: {e}"


@tool
def extraer_datos_details_partido(nombre_equipo: str) -> str:
    """Extrae la tabla de 'Details', contexto del partido y predice tendencia con ML."""
    with navegador_lock:
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                pagina = browser.contexts[0].pages[0]
                pagina.goto("https://betwatch.fr/money")
                pagina.wait_for_timeout(8000)

                # 1. CLIC EN EL EQUIPO
                enlace_equipo = pagina.locator(f"a:has-text('{nombre_equipo}')").filter(visible=True).first
                if enlace_equipo.is_visible():
                    enlace_equipo.click(force=True)
                    try:
                        pagina.wait_for_selector('tr', timeout=8000)
                        pagina.wait_for_timeout(4000)
                    except:
                        pagina.wait_for_timeout(4000)
                else:
                    return f"No encontré enlace para {nombre_equipo}."

                # 2. CLIC EN DETAILS
                boton_detalles = pagina.locator("button").filter(
                    has_text=re.compile(r"details|détails", re.IGNORECASE)).filter(visible=True).first
                if boton_detalles.is_visible():
                    boton_detalles.click(force=True)
                    pagina.wait_for_timeout(4000)

                # 3. EXTRACCIÓN DE TABLA
                datos_tabla = pagina.evaluate('''() => {
                    const tablas = Array.from(document.querySelectorAll('table'));
                    for (const tabla of tablas) {
                        const texto = tabla.innerText.toLowerCase();
                        if (texto.includes('volume') || texto.includes('vol.')) {
                            const rows = Array.from(tabla.querySelectorAll('tr'));
                            const cleanData = [];
                            for (const row of rows) {
                                const cells = Array.from(row.querySelectorAll('th, td')).map(c => c.innerText.trim());
                                if (cells.length >= 3) cleanData.push(cells);
                            }
                            if (cleanData.length > 1) return cleanData;
                        }
                    }
                    return [];
                }''')

                # 4. EXTRACCIÓN DE CONTEXTO (🎯 QUIRÚRGICO BASADO EN TU HTML)
                datos_contexto = pagina.evaluate('''() => {
                    // Buscamos exactamente el div grande central donde Betwatch pone el marcador o la hora
                    const elementoPrincipal = document.querySelector('.text-3xl');
                    let texto_central = elementoPrincipal ? elementoPrincipal.innerText.trim() : "Sin datos";

                    let difGoles = 0;
                    // Solo calcula diferencia si el texto central tiene formato exacto de goles (Ej: "2 - 1")
                    const matchMarcador = texto_central.match(/^(\d+)\s*-\s*(\d+)$/);
                    if (matchMarcador) {
                        difGoles = parseInt(matchMarcador[1]) - parseInt(matchMarcador[2]);
                    }

                    const matchMinuto = document.body.innerText.match(/(\d{1,2})'/);
                    let minuto = matchMinuto ? parseInt(matchMinuto[1]) : 0;

                    return { difGoles, minuto, texto_central };
                }''')

                if not datos_tabla or len(datos_tabla) <= 1:
                    return f"Tabla no encontrada. Contexto: {datos_contexto['texto_central']} (Minuto {datos_contexto['minuto']})"

                # 5. CREAR TABLA MARKDOWN VISIBLE
                md_table = "| " + " | ".join(datos_tabla[0]) + " |\n"
                md_table += "|" + "|".join(["---"] * len(datos_tabla[0])) + "|\n"
                for index, fila in enumerate(datos_tabla[1:]):
                    if index > 25: break
                    md_table += "| " + " | ".join(fila) + " |\n"

                # 6. PREDICCIÓN ML (Actualizada al Smart Money)
                alerta_visual = "🟢 **MERCADO ESTABLE**"
                try:
                    if len(datos_tabla) >= 3:
                        fila_actual = datos_tabla[1]
                        fila_anterior = datos_tabla[2]

                        c_act = float(re.sub(r'[^\d\.]', '', fila_actual[1].replace(',', '.')))
                        v_act = float(re.sub(r'[^\d\.]', '', fila_actual[2].replace(',', '.')))
                        c_ant = float(re.sub(r'[^\d\.]', '', fila_anterior[1].replace(',', '.')))
                        v_ant = float(re.sub(r'[^\d\.]', '', fila_anterior[2].replace(',', '.')))

                        odd_diff = c_act - c_ant
                        vol_relativo = max(0, v_act - v_ant)

                        # -- Nuevas Variables --
                        minuto = datos_contexto['minuto']
                        porcentaje_impacto = (vol_relativo / v_act) * 100 if v_act > 0 else 0

                        # Solo consultamos a la IA si es una inyección fuerte
                        if vol_relativo >= 300 and porcentaje_impacto >= 4.0:
                            variables_ml = [[c_act, porcentaje_impacto, vol_relativo, odd_diff, minuto]]
                            pred = modelo_ia.predict(variables_ml)[0]
                            prob_victoria = modelo_ia.predict_proba(variables_ml)[0][1] * 100

                            if pred == 1:
                                alerta_visual = f"🔥 **ALERTA SMART MONEY:** ¡Modelo predice VICTORIA ({prob_victoria:.1f}%)!"
                            elif pred == 0:
                                alerta_visual = "⚠️ **TRAMPA DETECTADA:** Fuerte inyección de dinero, pero la IA predice derrota."
                except Exception as e:
                    print(f"Error interno en predicción ML: {e}")

                # EL RESULTADO FINAL CON LA TABLA
                return f"{alerta_visual}\n**Marcador/Estado:** {datos_contexto['texto_central']} (Minuto {datos_contexto['minuto']})\n**Diferencia Goles:** {datos_contexto['difGoles']}\n\n**HISTORIAL DE TRANSACCIONES:**\n{md_table}"

        except Exception as e:
            return f"Error en Details: {e}"

# --- 4. CONFIGURACIÓN DEL CEREBRO ---
@st.cache_resource
def configurar_agente():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key="AIzaSyBYa3b3061BwLNpwh9eXHHrF9WvS-cowOQ",
        temperature=0
    )

    herramientas = [
        escanear_betwatch_en_vivo,
        analizar_partido_a_fondo,
        extraer_datos_details_partido,
        evaluar_smart_money_en_vivo  # <--- Nuevo nombre
    ]

    return create_react_agent(llm, tools=herramientas)

agente = configurar_agente()

instrucciones_sistema = (
    "Eres un experto en Trading Deportivo y Machine Learning.\n"
    "REGLAS:\n"
    "1. Usa 'escanear_betwatch_en_vivo' para leer la portada.\n"
    "2. Para hacer clic, usa SOLO EL NOMBRE DE UN EQUIPO.\n"
    "3. Usa 'extraer_datos_details_partido' si piden HISTORIAL o DETAILS.\n"
    "4. Tienes un modelo de ML real conectado. Puedes usar 'predecir_tendencia_mercado' si tienes la cuota, el volumen y sus variaciones recientes."
)
# --- 4.5 LÓGICA DE RADAR INTELIGENTE ---
def bucle_radar_inteligente():
    print("🚀 Radar Inteligente iniciado (Versión Completa)...")
    if "memoria_volumenes" not in st.session_state:
        st.session_state.memoria_volumenes = {}

    errores_consecutivos = 0
    try:
        with sync_playwright() as p:
            with navegador_lock:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                pagina_radar = browser.contexts[0].new_page()
                pagina_radar.goto("https://betwatch.fr/money")
                pagina_radar.wait_for_timeout(5000)

                # Mantener funcionalidad: Despliegue de cartelera
                print("⏬ Desplegando cartelera completa...")
                for _ in range(5):
                    pagina_radar.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    pagina_radar.wait_for_timeout(1500)
                    try:
                        boton_mas = pagina_radar.locator("button").filter(
                            has_text=re.compile(r"more|plus|load|cargar", re.IGNORECASE)).filter(visible=True).first
                        if boton_mas.is_visible():
                            boton_mas.click(force=True)
                            pagina_radar.wait_for_timeout(2000)
                        else:
                            break
                    except:
                        break

            while st.session_state.vigilando:
                try:
                    with navegador_lock:
                        # Extraemos los datos estructurados (La parte que fallaba)
                        partidos_detectados = pagina_radar.evaluate('''() => {
                            return Array.from(document.querySelectorAll('.match-container')).slice(0, 10).map(c => {
                                const texto = c.innerText;
                                const euros = texto.match(/(\\d+[\\s\\.]?\\d*)\\s*€/g);
                                let vol = 0;
                                if(euros) vol = euros.reduce((acc, curr) => acc + parseInt(curr.replace(/[^\\d]/g, '')), 0);
                                const nombre = texto.split('\\n')[0].replace('Match Odds', '').trim();
                                return { nombre, vol };
                            }).filter(p => p.vol > 0);
                        }''')

                    # Procesamiento y memoria (Lógica original mantenida)
                    datos_tabla_ciclo = []
                    nombres_grafico = []
                    riesgos_grafico = []
                    analisis_realizados = 0

                    for p in partidos_detectados:
                        nombre, vol = p['nombre'], p['vol']
                        vol_previo = st.session_state.memoria_volumenes.get(nombre, 0)
                        diferencia = vol - vol_previo if vol_previo > 0 else 0
                        st.session_state.memoria_volumenes[nombre] = vol

                        riesgo = min((diferencia / 3000) * 100, 100) if diferencia > 0 else 5

                        datos_tabla_ciclo.append({
                            "Partido": nombre[:20],
                            "Vol. Actual (€)": vol,
                            "Inyección (€)": diferencia,
                            "Riesgo (%)": round(riesgo, 1)
                        })
                        nombres_grafico.append(nombre[:15])
                        riesgos_grafico.append(riesgo)

                        # ALERTA DE IA (Lógica mantenida)
                        if diferencia > 2000 and analisis_realizados < 2:
                            analisis_realizados += 1
                            try:
                                res = extraer_datos_details_partido.invoke({"nombre_equipo": nombre})
                                if any(s in str(res) for s in ["🔴", "🟡", "🔥"]):
                                    st.session_state.historial.append({"rol": "assistant",
                                                                       "contenido": f"⚡ **ALERTA {nombre}: +{diferencia}€**\n{res}"})
                            except:
                                pass

                    # Actualización estado UI
                    st.session_state.datos_tabla_radar = datos_tabla_ciclo
                    st.session_state.datos_grafico = {"Partido": nombres_grafico, "Riesgo (%)": riesgos_grafico}

                    errores_consecutivos = 0
                    time.sleep(45)

                except Exception as e:
                    errores_consecutivos += 1
                    print(f"⚠️ Error menor: {e}")
                    if errores_consecutivos >= 3:
                        st.session_state.vigilando = False
                        break
                    time.sleep(10)

            with navegador_lock:
                pagina_radar.close()
    except Exception as e:
        print(f"❌ Error crítico: {e}")

# --- 4.6 MENÚ LATERAL Y UI GRÁFICO ---
if "vigilando" not in st.session_state:
    st.session_state.vigilando = False
if "datos_grafico" not in st.session_state:
    st.session_state.datos_grafico = {"Partido": [], "Riesgo (%)": []}
if "datos_tabla_radar" not in st.session_state:
    st.session_state.datos_tabla_radar = []

with st.sidebar:
    st.header("🌍 Panel de Control")
    # Usamos una variable de estado para saber si el hilo está vivo
    if st.button("▶️ Activar Radar", disabled=st.session_state.get("vigilando", False)):
        st.session_state.vigilando = True
        hilo_vigilante = threading.Thread(target=bucle_radar_inteligente, daemon=True)
        add_script_run_ctx(hilo_vigilante)
        hilo_vigilante.start()
        st.rerun() # Fuerza recarga inmediata

    if st.button("⏹️ Detener Radar", disabled=not st.session_state.get("vigilando", False)):
        st.session_state.vigilando = False
        st.warning("Radar solicitando parada...")
        st.rerun()

# Contenedores dinámicos en la pantalla principal
col_grafico, col_tabla = st.columns([1, 2])

with col_grafico:
    st.subheader("📊 Riesgo (%)")
    contenedor_grafico = st.empty()

with col_tabla:
    st.subheader("📋 Registro de Mercado en Vivo")
    contenedor_tabla = st.empty()


def dibujar_interfaz_vivo():
    # Renderizamos el gráfico
    if len(st.session_state.datos_grafico["Partido"]) > 0:
        df_grafico = pd.DataFrame(st.session_state.datos_grafico)
        df_grafico.set_index("Partido", inplace=True)
        contenedor_grafico.bar_chart(df_grafico, color="#ff4b4b")
    else:
        if st.session_state.vigilando:
            contenedor_grafico.info("Radar activo: Escaneando gráfico...")
        else:
            contenedor_grafico.write("El radar está apagado.")

    # Renderizamos la tabla ordenada por las mayores inyecciones
    if len(st.session_state.datos_tabla_radar) > 0:
        df_tabla = pd.DataFrame(st.session_state.datos_tabla_radar)
        # Ordenamos para que los que más dinero han recibido de golpe salgan arriba del todo
        df_tabla = df_tabla.sort_values(by="Inyección (€)", ascending=False).reset_index(drop=True)

        # Le damos formato a la tabla para que se vea bonita en Streamlit
        contenedor_tabla.dataframe(
            df_tabla,
            use_container_width=True,
            column_config={
                "Vol. Previo (€)": st.column_config.NumberColumn(format="€ %d"),
                "Vol. Actual (€)": st.column_config.NumberColumn(format="€ %d"),
                "Inyección (€)": st.column_config.NumberColumn(format="€ %d"),
                "Riesgo (%)": st.column_config.ProgressColumn(format="%f %%", min_value=0, max_value=100)
            },
            hide_index=True
        )
    else:
        if st.session_state.vigilando:
            contenedor_tabla.info("Radar activo: Recopilando datos de mercado...")
        else:
            contenedor_tabla.write("El radar está apagado.")


dibujar_interfaz_vivo()

# --- 5. LÓGICA DE ACTUALIZACIÓN AUTOMÁTICA ---
if st.session_state.get("vigilando", False):
    # Esto le dice a Streamlit: "Refresca la página cada 45 segundos"
    # Sin necesidad de hacer st.rerun() dentro del hilo del radar
    time.sleep(45)
    st.rerun()

if "historial" not in st.session_state:
    st.session_state.historial = []

for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])
if prompt := st.chat_input("Ej: Predice el desajuste si la cuota es 4.5 y volumen 1100€"):
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- NUEVO: INYECCIÓN DE CONCIENCIA DE MODO ---
    modo_actual = "PREMIUM" if st.session_state.get("es_premium", False) else "GRATIS"

    instrucciones_dinamicas = (
        f"Eres un Agente de Trading Deportivo de Élite. ACCESO A INTERNET HABILITADO.\n"
        f"🚨 ESTADO DE LA CUENTA DEL USUARIO: MODO {modo_actual} 🚨\n\n"
        "REGLAS OBLIGATORIAS:\n"
        "1. Si te piden detalles de un equipo, EJECUTA 'extraer_datos_details_partido'. No des excusas.\n"
        "2. Si el MODO es PREMIUM, tienes prohibido usar la herramienta gratis. Pide al usuario el Volumen Agregado si no te lo ha dado, y usa SIEMPRE 'predecir_desajuste_premium'.\n"
        "3. Si el MODO es GRATIS, tienes prohibido usar la herramienta premium. Usa SOLO 'predecir_desajuste_mercado' y recuérdale sutilmente al usuario que sus datos serían más precisos en la versión Pro."
    )

    mensajes_para_ia = [SystemMessage(content=instrucciones_sistema)]

    # --- NUEVO: AMNESIA SELECTIVA (Ahorro masivo de tokens) ---
    # Cogemos solo los últimos 6 mensajes del historial (3 preguntas y 3 respuestas)
    mensajes_recientes = st.session_state.historial[-6:] if len(
        st.session_state.historial) > 6 else st.session_state.historial

    for msg in mensajes_recientes:
        if msg["rol"] == "user":
            mensajes_para_ia.append(HumanMessage(content=msg["contenido"]))
        elif msg["rol"] == "assistant":
            mensajes_para_ia.append(AIMessage(content=msg["contenido"]))

    mensajes_para_ia.append(HumanMessage(content=prompt))
    st.session_state.historial.append({"rol": "user", "contenido": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🕵️‍♂️ Analizando el mercado e invocando modelos..."):
            try:
                resultado = agente.invoke({"messages": mensajes_para_ia})
                respuesta_bruta = resultado["messages"][-1].content

                if isinstance(respuesta_bruta, list):
                    respuesta_final = ""
                    for item in respuesta_bruta:
                        if isinstance(item, dict) and "text" in item:
                            respuesta_final += item["text"]
                        elif isinstance(item, str):
                            respuesta_final += item
                else:
                    respuesta_final = str(respuesta_bruta)

                st.markdown(respuesta_final)
                st.session_state.historial.append({"rol": "assistant", "contenido": respuesta_final})


            except Exception as e:

                # 1. Convertimos el error a texto en minúsculas para analizarlo

                mensaje_error = str(e).lower()

                # --- ESCUDO 1: Límite de la API Gratuita ---

                if "429" in mensaje_error or "quota" in mensaje_error or "exhausted" in mensaje_error:

                    mensaje_amigable = (

                        "⚠️ **Límite de API Gratuita Alcanzado**\n\n"

                        "Google ha pausado temporalmente mis respuestas porque hemos superado el límite de consultas por minuto.\n"

                        "*El Radar sigue funcionando.* Espera un par de minutos."

                    )

                    st.warning(mensaje_amigable)

                    st.session_state.historial.append({"rol": "assistant",
                                                       "contenido": "⚠️ *Aviso: Límite de API alcanzado. Esperando enfriamiento.*"})


                # --- ESCUDO 2: Navegador Cerrado o Puerto Incorrecto ---

                elif "target closed" in mensaje_error or "connection refused" in mensaje_error or "connect_over_cdp" in mensaje_error:

                    mensaje_amigable = (

                        "🌐 **Navegador Desconectado**\n\n"

                        "No puedo comunicarme con tu Chrome. Asegúrate de que lo tienes abierto y que lo lanzaste desde la terminal con el puerto correcto:\n"

                        "`chrome.exe --remote-debugging-port=9222`"

                    )

                    st.error(mensaje_amigable)

                    st.session_state.historial.append(
                        {"rol": "assistant", "contenido": "🌐 *Error: Conexión con el navegador perdida.*"})


                # --- ESCUDO 3: Tiempo de espera agotado (Internet lento o web caída) ---

                elif "timeout" in mensaje_error or "exceeded" in mensaje_error:

                    mensaje_amigable = (

                        "⏳ **Tiempo de Espera Agotado**\n\n"

                        "La web de Betwatch está tardando demasiado en cargar o ha cambiado su diseño interno. He abortado la misión por seguridad. Vuelve a intentarlo en unos segundos."

                    )

                    st.warning(mensaje_amigable)

                    st.session_state.historial.append(
                        {"rol": "assistant", "contenido": "⏳ *Aviso: Timeout al intentar cargar la web.*"})


                # --- ESCUDO 4: El Agente se hace un lío respondiendo ---

                elif "parse" in mensaje_error or "could not parse" in mensaje_error:

                    mensaje_amigable = (

                        "🧠 **Cruce de cables en el procesamiento...**\n\n"

                        "He encontrado los datos, pero me he hecho un lío intentando formatearlos para mostrártelos. ¿Puedes reformular la pregunta de forma un poco más directa?"

                    )

                    st.info(mensaje_amigable)

                    st.session_state.historial.append(
                        {"rol": "assistant", "contenido": "🧠 *Aviso: Error de parseo en la respuesta del LLM.*"})


                # --- ESCUDO 5: Errores técnicos puros ---

                else:

                    st.error(f"🔧 **Error técnico del sistema:** {e}")