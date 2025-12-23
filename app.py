import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gladius Pro", page_icon="🏛️", layout="wide")

# --- ESTILOS CSS (UI LIMPIA) ---
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button {
        width: 100%;
        background-color: #000;
        color: white;
        font-weight: bold;
        padding: 0.7rem;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #333;
        border-color: #000;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (INPUTS SIMPLES) ---
with st.sidebar:
    st.title("🏛️ GLADIUS PRO")
    st.caption("Powered by GPT-4o + Real Time Data")
    st.markdown("---")
    
    st.subheader("1. El Activo")
    ubicacion = st.text_input("📍 Ubicación", value="La Cabrera, Bogota")
    tipologia = st.selectbox("🏗️ Tipo", ["Apartamento", "Casa", "Local", "Lote"])
    estado = st.selectbox("🛠️ Estado", ["Para Remodelar (Hueso)", "Buen Estado", "Nuevo"])
    
    col1, col2 = st.columns(2)
    with col1:
        precio = st.number_input("💰 Precio (COP)", value=1070000000, step=10000000, format="%d")
    with col2:
        area = st.number_input("📐 Área (m²)", value=200)
    
    st.subheader("2. La Estrategia")
    estrategia = st.selectbox("🎯 Tesis", ["Vivir (Patrimonio)", "Flipping (Remodelar y Vender)", "Renta Tradicional", "Airbnb"])
    
    st.markdown("---")
    audit_btn = st.button("⚡ GENERAR TESIS DE INVERSIÓN", type="primary")
    
    if st.button("🔄 Nueva Auditoría"):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.run_started = False
        st.rerun()

# --- GESTIÓN DE ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Validar secretos
if not st.secrets.get("OPENAI_API_KEY") or not st.secrets.get("OPENAI_ASSISTANT_ID"):
    st.error("⚠️ Faltan las llaves de OpenAI en los 'Secrets'. Configúralas en el dashboard de Streamlit.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- FUNCIÓN DE BÚSQUEDA (MARKET INTEL) ---
def get_market_intel():
    """Busca tasas y precios en tiempo real para darle contexto al modelo"""
    try:
        with DDGS() as ddgs:
            # Busca tasas de crédito HOY
            q_rates = "tasas interes credito hipotecario vivienda colombia bancos actual 2025"
            r_rates = list(ddgs.text(q_rates, max_results=2))
            # Busca precios zona HOY
            q_price = f"precio metro cuadrado venta {ubicacion} finca raiz 2024 2025"
            r_price = list(ddgs.text(q_price, max_results=2))
            
            return f"MARKET INTELLIGENCE (WEB):\nTASAS: {str(r_rates)}\nPRECIOS ZONA: {str(r_price)}"
    except:
        return "MARKET INTELLIGENCE: No disponible (Error de conexión). Usa tus defaults internos."

# --- PANTALLA PRINCIPAL (BIENVENIDA) ---
if not st.session_state.messages:
    col_main, _ = st.columns([3,1])
    with col_main:
        st.title("Tu Socio de Inversión IA")
        st.markdown(f"""
        **Estás operando con Gladius Pro (GPT-4o).**
        
        Este sistema está diseñado para velocidad y criterio:
        1.  **Investiga:** Busca tasas y precios de mercado en tiempo real.
        2.  **Propone:** Si faltan datos (Obra, Deuda), asume "Defaults Expertos" y te los presenta.
        3.  **Calcula:** Usa Python para modelar el escenario financiero.
        
        *Configura los datos a la izquierda y presiona GENERAR TESIS.*
        """)

# --- LÓGICA DE EJECUCIÓN (EL CEREBRO) ---
if audit_btn and not st.session_state.thread_id:
    # 1. Feedback inmediato al usuario
    with st.status("🧠 Gladius está analizando el negocio...", expanded=True) as status:
        st.write("📡 Recolectando inteligencia de mercado (Tasas/Precios)...")
        intel = get_market_intel()
        
        st.write("🏗️ Estructurando Tesis de Inversión y Supuestos...")
        
        # 2. Crear Thread
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        # 3. Prompt de Usuario (ESTO ACTIVA EL MODO "SOCIO SENIOR")
        mensaje_inicial = f"""
        NUEVO DEAL PARA ANÁLISIS:
        - Activo: {tipologia} en {ubicacion} ({estado}).
        - Precio Entrada: ${precio:,.0f} ({area} m2).
        - Estrategia: {estrategia}.
        
        DATA DE MERCADO (REAL-TIME):
        {intel}
        
        INSTRUCCIÓN:
        Actúa como mi Socio Senior (CIO).
        NO ME HAGAS PREGUNTAS DE ENTRADA.
        Si falta información (Costos de obra, Condiciones de Deuda, Precio de Salida), LLENA LOS VACÍOS con tus "Defaults de Experto" (basados en la zona y el mercado).
        
        Calcula los números en Python y DAME LA TESIS DE INVERSIÓN YA.
        Avisa claramente qué supuestos usaste para que yo pueda corregirlos si es necesario.
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=mensaje_inicial)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        # 4. Esperar respuesta
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "failed":
                st.error("Error en el análisis del Asistente.")
                st.stop()
        
        status.update(label="Tesis Generada", state="complete", expanded=False)
        
    # 5. Mostrar respuesta inicial
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    rta = mensajes.data[0].content[0].text.value
    st.session_state.messages.append({"role": "assistant", "content": rta})
    st.rerun()

# --- INTERFAZ DE CHAT (PARA CORRECCIONES) ---
for msg in st.session_state.messages:
    avatar = "🏛️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- INPUT PARA CHAT ---
if prompt := st.chat_input("Corrige los supuestos o pide profundizar..."):
    if st.session_state.thread_id:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
        run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
        
        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("Recalculando modelo..."):
                while run.status != "completed":
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
            mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            rta = mensajes.data[0].content[0].text.value
            st.markdown(rta)
            st.session_state.messages.append({"role": "assistant", "content": rta})
