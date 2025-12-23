import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gladius Pro", page_icon="🏛️", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ GLADIUS PRO")
    st.caption("Fix: Recuperación de Respuesta Completa")
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
        st.rerun()

# --- ESTADO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if not st.secrets.get("OPENAI_API_KEY") or not st.secrets.get("OPENAI_ASSISTANT_ID"):
    st.error("⚠️ Faltan Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- FUNCIÓN BÚSQUEDA ---
def get_market_intel():
    try:
        with DDGS() as ddgs:
            q_rates = "tasas interes credito hipotecario vivienda colombia bancos actual 2025"
            r_rates = list(ddgs.text(q_rates, max_results=2))
            q_price = f"precio metro cuadrado venta {ubicacion} finca raiz 2024 2025"
            r_price = list(ddgs.text(q_price, max_results=2))
            return f"MARKET INTELLIGENCE (WEB):\nTASAS: {str(r_rates)}\nPRECIOS ZONA: {str(r_price)}"
    except:
        return "MARKET INTELLIGENCE: No disponible. Usa defaults."

# --- BIENVENIDA ---
if not st.session_state.messages:
    col_main, _ = st.columns([3,1])
    with col_main:
        st.title("Socio de Inversión IA")
        st.write("Configura el caso a la izquierda y dale a GENERAR.")

# --- LÓGICA PRINCIPAL ---
if audit_btn and not st.session_state.thread_id:
    with st.status("🧠 Gladius está analizando...", expanded=True) as status:
        st.write("📡 Investigando mercado...")
        intel = get_market_intel()
        st.write("🏗️ Modelando escenario...")
        
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        msg = f"""
        NUEVO DEAL:
        - Activo: {tipologia} en {ubicacion} ({estado}).
        - Precio: ${precio:,.0f} ({area} m2).
        - Estrategia: {estrategia}.
        
        DATA REAL-TIME:
        {intel}
        
        INSTRUCCIÓN:
        1. Asume los costos/tasas faltantes (Defaults Expertos).
        2. Calcula en Python.
        3. Escribe el REPORTE COMPLETO (Summary -> Supuestos -> Modelo -> Remarks).
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=msg)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "failed":
                st.error("Fallo en OpenAI.")
                st.stop()
        
        status.update(label="Listo", state="complete", expanded=False)

    # --- FIX DE RECUPERACIÓN (AQUÍ ESTÁ LA MAGIA) ---
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Recogemos TODO lo que dijo el asistente en este turno (puede ser 1 o más mensajes)
    full_response = ""
    for msg in mensajes.data:
        if msg.role == "user":
            break # Paramos al llegar a tu pregunta
        if msg.role == "assistant":
            for content in msg.content:
                if content.type == "text":
                    # Concatenamos al principio porque la lista viene invertida (más nuevo primero)
                    full_response = content.text.value + "\n\n" + full_response
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()

# --- CHAT ---
for msg in st.session_state.messages:
    avatar = "🏛️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Corrige supuestos..."):
    if st.session_state.thread_id:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
        run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
        
        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("Pensando..."):
                while run.status != "completed":
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
            # --- MISMO FIX PARA EL CHAT ---
            mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            full_response = ""
            for msg in mensajes.data:
                if msg.role == "user":
                    break
                if msg.role == "assistant":
                    for content in msg.content:
                        if content.type == "text":
                            full_response = content.text.value + "\n\n" + full_response
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
