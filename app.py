import streamlit as st
from openai import OpenAI
import time

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Gladius AI Chat", page_icon="⚔️", layout="wide")

st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO ---
col1, col2 = st.columns([1, 5])
with col1:
    st.title("⚔️")
with col2:
    st.title("GLADIUS PRO: TU SOCIO ACTIVO")
    st.caption("Auditoría en Tiempo Real | Conversación Habilitada")

st.markdown("---")

# --- INICIALIZAR ESTADO (MEMORIA) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "audit_started" not in st.session_state:
    st.session_state.audit_started = False

# --- SIDEBAR: CONTEXTO INICIAL ---
with st.sidebar:
    st.header("📋 Ficha Técnica Inicial")
    st.info("Ingresa los datos base para arrancar la conversación.")
    
    ubicacion = st.text_input("📍 Ubicación", value="La Cabrera, Bogota")
    tipologia = st.selectbox("🏗️ Tipo", ["Apartamento Familiar", "Apartaestudio", "Local", "Lote"])
    estado = st.selectbox("🛠️ Estado", ["Para Remodelar (Hueso)", "Buen Estado", "Nuevo"])
    precio = st.number_input("💰 Precio Compra (COP)", value=1070000000, step=10000000, format="%d")
    area = st.number_input("📐 Área (m²)", value=200)
    estrategia = st.selectbox("🎯 Estrategia", ["Vivir (Patrimonio)", "Flipping (Remodelar y Vender)", "Renta Tradicional", "Airbnb"])
    
    start_btn = st.button("🚀 INICIAR AUDITORÍA", type="primary")

    if st.session_state.audit_started:
        if st.button("🔄 Reiniciar Conversación"):
            st.session_state.messages = []
            st.session_state.thread_id = None
            st.session_state.audit_started = False
            st.rerun()

# --- LÓGICA DEL CLIENTE OPENAI ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- FUNCIÓN: ARRANCAR EL HILO ---
if start_btn and not st.session_state.audit_started:
    # 1. Crear Hilo
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.audit_started = True

    # 2. Enviar Prompt Inicial (Invisible al usuario)
    primer_mensaje = f"""
    Hola Gladius. Quiero auditar este negocio. 
    Actúa como mi socio senior. Si ves que falta información vital (ej: costo de remodelación en flipping), PREGÚNTAME antes de juzgar.
    
    DATOS:
    - Activo: {tipologia} en {ubicacion} ({estado})
    - Estrategia: {estrategia}
    - Precio Compra: ${precio:,.0f}
    - Área: {area} m2
    """
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=primer_mensaje
    )

    # 3. Ejecutar primera respuesta
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    with st.spinner('Gladius está leyendo la ficha técnica...'):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    
    # 4. Guardar respuesta en historial
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    respuesta_inicial = mensajes.data[0].content[0].text.value
    st.session_state.messages.append({"role": "assistant", "content": respuesta_inicial})

# --- MOSTRAR CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT DEL USUARIO (EL CHAT) ---
if prompt := st.chat_input("Escribe aquí... (Ej: 'La remodelación me cuesta 200 millones')"):
    if not st.session_state.audit_started:
        st.warning("⚠️ Primero llena los datos de la izquierda y dale a 'INICIAR AUDITORÍA'.")
    else:
        # 1. Mostrar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Enviar a OpenAI
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # 3. Ejecutar Asistente
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id
        )

        with st.chat_message("assistant"):
            with st.status("🧠 Pensando...", expanded=True) as status:
                while run.status != "completed":
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
                status.update(label="Respuesta lista", state="complete", expanded=False)
            
            # 4. Obtener y mostrar respuesta
            mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            respuesta_nueva = mensajes.data[0].content[0].text.value
            st.markdown(respuesta_nueva)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_nueva})
