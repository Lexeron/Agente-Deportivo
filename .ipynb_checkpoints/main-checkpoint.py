import sys
import asyncio

# --- PARCHE DE WINDOWS OBLIGATORIO ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  # <-- AIMessage añadido para la memoria
from langgraph.prebuilt import create_react_agent

# --- 1. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Agente Betwatch Live", page_icon="📈", layout="wide")

st.title("🤖 Analista Betwatch Live (Nivel 3: Memoria + Navegación)")
st.markdown("Analizando tu navegador Chrome real en el puerto **9222**.")


# --- 2. HERRAMIENTAS DEL AGENTE ---

@tool
def escanear_betwatch_en_vivo() -> str:
    """Extrae el contenido de la pestaña de Betwatch para ver TODOS los partidos que hay en juego."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            contexto = browser.contexts[0]

            pagina = None
            for p_actual in contexto.pages:
                if "betwatch.fr" in p_actual.url:
                    pagina = p_actual
                    break

            if not pagina:
                pagina = contexto.new_page()

            # --- ARREGLO NAVEGACIÓN: Forzamos la vuelta a la portada ---
            if pagina.url != "https://betwatch.fr/" and pagina.url != "https://betwatch.fr":
                print("🔄 Volviendo a la portada...")
                pagina.goto("https://betwatch.fr/")
                pagina.wait_for_timeout(3000)
            elif not pagina.url.startswith("http"):
                pagina.goto("https://betwatch.fr/")
                pagina.wait_for_timeout(3000)

            pagina.wait_for_timeout(2000)
            cuerpo_texto = pagina.locator("body").inner_text()

            print("🔥 PORTADA ESCANEADA")
            return f"DATOS DE LA PORTADA ACTUALES:\n\n{cuerpo_texto[:10000]}"
    except Exception as e:
        print(f"❌ ERROR EN ESCANEO: {e}")
        return f"ERROR: Asegúrate de que Chrome esté abierto en el puerto 9222. {e}"


@tool
def analizar_partido_a_fondo(nombre_equipo: str) -> str:
    """Usa esta herramienta obligatoriamente para hacer clic en un partido específico y ver el volumen de dinero (Match Odds)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            contexto = browser.contexts[0]

            pagina = None
            for p_actual in contexto.pages:
                if "betwatch.fr" in p_actual.url:
                    pagina = p_actual
                    break

            if not pagina:
                return "ERROR: No encuentro la pestaña de Betwatch."

            # --- ARREGLO NAVEGACIÓN: Aseguramos que estamos en la lista de partidos ---
            if pagina.url != "https://betwatch.fr/" and pagina.url != "https://betwatch.fr":
                print("🔄 Volviendo a la portada para buscar el equipo...")
                pagina.goto("https://betwatch.fr/")
                pagina.wait_for_timeout(3000)

            print(f"🖱️ Buscando y haciendo clic en: {nombre_equipo}...")

            elementos = pagina.get_by_text(nombre_equipo, exact=False)

            # Buscamos cuál de todos los textos repetidos es el que se ve en pantalla
            for i in range(elementos.count()):
                if elementos.nth(i).is_visible():
                    elementos.nth(i).click(force=True)
                    break
            else:
                elementos.first.click(force=True)

            # Esperamos a que baje el menú de estadísticas/dinero
            pagina.wait_for_timeout(2000)

            cuerpo_texto = pagina.locator("body").inner_text()

            # Volvemos a hacer clic para cerrarlo y dejar todo limpio
            for i in range(elementos.count()):
                if elementos.nth(i).is_visible():
                    elementos.nth(i).click(force=True)
                    break
            else:
                elementos.first.click(force=True)

            print(f"✅ DATOS DE {nombre_equipo} EXTRAÍDOS CON ÉXITO")
            return f"DATOS DETALLADOS DE {nombre_equipo} (Incluye volúmenes de dinero):\n\n{cuerpo_texto[:15000]}"
    except Exception as e:
        print(f"❌ Error al hacer clic: {e}")
        return f"No se pudo hacer clic en {nombre_equipo}. Error: {e}"


# --- 3. CONFIGURACIÓN DEL CEREBRO ---
@st.cache_resource
def configurar_agente():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key="AIzaSyBYa3b3061BwLNpwh9eXHHrF9WvS-cowOQ",
        temperature=0
    )

    herramientas = [escanear_betwatch_en_vivo, analizar_partido_a_fondo]
    return create_react_agent(llm, tools=herramientas)


agente = configurar_agente()

instrucciones_sistema = (
    "Eres un experto en Trading Deportivo. REGLAS:\n"
    "1. Usa 'escanear_betwatch_en_vivo' para ver la lista general de partidos.\n"
    "2. Si te preguntan por DINERO, VOLUMEN o ESTADÍSTICAS de un partido, usa OBLIGATORIAMENTE 'analizar_partido_a_fondo'.\n"
    "3. Reporta siempre los euros (€) invertidos si los ves.\n"
    "4. Crea tablas Markdown claras.\n"
    "5. Sé directo."
)

# --- 4. LÓGICA DEL CHATBOT CON MEMORIA ---
if "historial" not in st.session_state:
    st.session_state.historial = []

# Dibujamos los mensajes anteriores
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

# Cuando el usuario escribe algo nuevo
if prompt := st.chat_input("Ej: ¿Qué partidos hay ahora?"):
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- ARREGLO DE MEMORIA: Le pasamos toda la charla a la IA ---
    mensajes_para_ia = [SystemMessage(content=instrucciones_sistema)]

    # Añadimos todo el historial previo
    for msg in st.session_state.historial:
        if msg["rol"] == "user":
            mensajes_para_ia.append(HumanMessage(content=msg["contenido"]))
        elif msg["rol"] == "assistant":
            mensajes_para_ia.append(AIMessage(content=msg["contenido"]))

    # Añadimos la pregunta actual
    mensajes_para_ia.append(HumanMessage(content=prompt))

    # Guardamos la pregunta del usuario en el historial visual
    st.session_state.historial.append({"rol": "user", "contenido": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🕵️‍♂️ Analizando e interactuando con Chrome..."):
            try:
                # Invocamos al agente pasándole TODOS los mensajes
                resultado = agente.invoke({"messages": mensajes_para_ia})

                # Limpieza de la respuesta multimodal
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
                # Guardamos la respuesta de la IA en el historial visual
                st.session_state.historial.append({"rol": "assistant", "contenido": respuesta_final})

            except Exception as e:
                st.error(f"Error de ejecución: {e}")