import streamlit as st
from openai import OpenAI
import time

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Gladius AI", page_icon="⚔️", layout="centered")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: white;
        font-weight: bold;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #333;
    }
    .stButton>button:hover {
        background-color: #333;
        border-color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("⚔️ GLADIUS PRO")
st.caption("COMITÉ DE INVERSIÓN | POWERED BY GPT-4o + CODE INTERPRETER")
st.markdown("---")

# --- INPUTS (DATOS) ---
st.sidebar.header("1. El Activo")
ubicacion = st.sidebar.text_input("📍 Ubicación", value="La Cabrera, Bogota")
tipologia = st.sidebar.selectbox("🏗️ Tipo", ["Apartamento Familiar", "Apartaestudio", "Local", "Lote"])
estado = st.sidebar.selectbox("🛠️ Estado", ["Para Remodelar (Hueso)", "Buen Estado", "Nuevo"])

st.sidebar.header("2. Los Números")
precio = st.sidebar.number_input("💰 Precio (COP)", value=1070000000, step=10000000, format="%d")
area = st.sidebar.number_input("📐 Área (m²)", value=200)
admin = st.sidebar.number_input("🏢 Admin (COP)", value=2500000, step=50000, format="%d")

st.sidebar.header("3. Estrategia")
estrategia = st.sidebar.selectbox("🎯 Objetivo", ["Vivir (Patrimonio)", "Flipping (Venta Rápida)", "Renta Tradicional", "Airbnb"])
ingreso = st.sidebar.number_input("💸 Ingreso Mensual Est.", value=0, help="Pon 0 si es para vivir")

# --- LÓGICA DEL CEREBRO (ASSISTANTS API) ---
if st.sidebar.button("💀 EJECUTAR AUDITORÍA", type="primary"):
    
    # Validar que existan las llaves
    if not st.secrets.get("OPENAI_API_KEY") or not st.secrets.get("OPENAI_ASSISTANT_ID"):
        st.error("⚠️ Error de Configuración: Faltan las API Keys en Secrets.")
        st.stop()

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

    try:
        # 1. Crear un Hilo de conversación (Thread)
        thread = client.beta.threads.create()

        # 2. Enviar los datos del usuario al hilo
        mensaje_usuario = f"""
        AUDITA ESTE NEGOCIO INMOBILIARIO:
        
        - Activo: {tipologia} en {ubicacion} ({estado})
        - Estrategia: {estrategia}
        - Precio Compra: ${precio:,.0f}
        - Área: {area} m2
        - Administración: ${admin:,.0f}
        - Ingreso Mensual Estimado: ${ingreso:,.0f}
        
        Usa tu Code Interpreter para verificar el precio por m2.
        Sé brutalmente honesto con la recomendación.
        """

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=mensaje_usuario
        )

        # 3. Ejecutar al Asistente (Run)
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # 4. Esperar a que piense (Polling)
        with st.status("🧠 Gladius está analizando el caso...", expanded=True) as status:
            while run.status != "completed":
                time.sleep(1) # Esperar 1 segundo
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                
                if run.status == "failed":
                    st.error("❌ El análisis falló. Intenta de nuevo.")
                    st.stop()
            
            status.update(label="✅ Análisis Completado", state="complete", expanded=False)

        # 5. Obtener y Mostrar Respuesta
        mensajes = client.beta.threads.messages.list(thread_id=thread.id)
        
        # La respuesta más reciente es la primera en la lista
        respuesta_final = mensajes.data[0].content[0].text.value
        
        st.markdown(respuesta_final)

    except Exception as e:
        st.error(f"Ocurrió un error de conexión: {e}")
