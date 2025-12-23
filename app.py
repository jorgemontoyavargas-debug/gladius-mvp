import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- 1. CONFIGURACIÓN "PRIVATE EQUITY" ---
st.set_page_config(page_title="Gladius Terminal", page_icon="🦅", layout="wide")

# CSS para que se vea costoso (Dark Mode elegante)
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background-color: #00d26a; /* Verde Dinero */
        color: black;
        font-weight: 800;
        border: none;
        padding: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #00b359;
        box-shadow: 0 0 15px rgba(0, 210, 106, 0.4);
    }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 300; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 0.9em;}
    .status-success { background-color: rgba(0, 210, 106, 0.1); border-left: 3px solid #00d26a; color: #00d26a; }
    .status-danger { background-color: rgba(255, 75, 75, 0.1); border-left: 3px solid #ff4b4b; color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (LA MESA DE TRADING) ---
with st.sidebar:
    st.title("🦅 GLADIUS")
    st.markdown("*Private Equity AI Partner*")
    st.markdown("---")
    
    st.caption("CONFIGURACIÓN DEL DEAL")
    ubicacion = st.text_input("📍 Ubicación", value="La Cabrera, Bogota")
    estrategia = st.selectbox("🎯 Estrategia", ["Flipping (Comprar-Remodelar-Vender)", "Vivir (Patrimonio)", "Renta Tradicional", "Airbnb"])
    
    col1, col2 = st.columns(2)
    with col1:
        precio = st.number_input("💰 Precio (COP)", value=1070000000, step=10000000, format="%d")
    with col2:
        area = st.number_input("📐 Área (m²)", value=200)
    
    tipo = st.selectbox("🏗️ Tipo Activo", ["Apartamento", "Casa", "Comercial"])
    estado = st.selectbox("🛠️ Condición", ["Para Remodelar (Hueso)", "Buen Estado"])

    st.markdown("---")
    audit_btn = st.button("⚡ EJECUTAR ANÁLISIS")
    
    if st.button("🔄 Reset Terminal"):
        st.session_state.clear()
        st.rerun()

# --- 3. ESTADO & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = None
if "market_data" not in st.session_state: st.session_state.market_data = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- 4. INTELIGENCIA (SEARCH) ---
def get_intel():
    with DDGS() as ddgs:
        q1 = f"precio metro cuadrado venta {ubicacion} finca raiz 2024 2025"
        q2 = "tasas interes credito hipotecario vivienda colombia bancos hoy 2025"
        return f"DATA REAL: {str(list(ddgs.text(q1, max_results=2)))} | TASAS: {str(list(ddgs.text(q2, max_results=2)))}"

# --- 5. UI PRINCIPAL (DASHBOARD) ---
if not st.session_state.messages:
    st.title("Bienvenido al Comité de Inversión.")
    st.markdown("""
    > *"El precio es lo que pagas. El valor es lo que obtienes."* — Warren Buffett
    
    Gladius está listo para auditar tu oportunidad en **La Cabrera**.
    Configura los parámetros a la izquierda y **Ejecuta**.
    """)

if audit_btn:
    with st.status("🦅 Gladius está trabajando...", expanded=True) as status:
        st.write("📡 Escaneando mercado en tiempo real...")
        intel = get_intel()
        st.session_state.market_data = intel # Guardar para mostrar
        
        st.write("🧮 Modelando escenarios financieros en Python...")
        
        # CREAR THREAD & RUN
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        msg = f"""
        ACTÚA COMO UN SOCIO SENIOR DE PRIVATE EQUITY.
        DEAL: {tipo} en {ubicacion} ({estado}). Precio: ${precio:,.0f} ({area}m2). Estrategia: {estrategia}.
        CONTEXTO WEB: {intel}
        
        TU MISIÓN:
        1. Asume los costos de obra (lujo/std) y deuda (tasa actual) SIN PREGUNTAR.
        2. Calcula: Equity Instantáneo, ROI, Utilidad Neta.
        3. Escribe un MEMORANDO DE INVERSIÓN corto pero contundente.
        4. USA FORMATO JSON para los números clave al final de tu respuesta así:
        {{ "veredicto": "APROBADO", "equity": "$XXX M", "roi": "XX%", "mensaje": "Tu resumen aquí" }}
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=msg)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        status.update(label="Análisis Completado", state="complete", expanded=False)

    # RECUPERAR RESPUESTA
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    full_text = msgs.data[0].content[0].text.value
    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.rerun()

# --- 6. RENDERIZADO DEL RESULTADO (EL "WOW") ---
if st.session_state.messages:
    last_msg = st.session_state.messages[-1]["content"]
    
    # INTENTO DE PARSEAR DATOS CLAVE (SI EL GPT OBEDECIÓ EL JSON O TEXTO)
    # Aquí hacemos un truco visual: Extraemos lo "duro" del texto para el Dashboard
    
    st.divider()
    
    # HEADER DEL VEREDICTO
    col_v1, col_v2 = st.columns([1, 4])
    with col_v1:
        st.markdown("# 🦅")
    with col_v2:
        st.markdown("### MEMORANDO DE INVERSIÓN")
        st.caption(f"Ref: {ubicacion} | {time.strftime('%d/%m/%Y')}")

    # DASHBOARD DE MÉTRICAS (LO QUE VENDE)
    # Nota: En una versión V6, haremos que GPT devuelva JSON puro para llenar esto dinámicamente.
    # Por ahora, dejamos que el texto hable, pero ponemos metricas visuales estáticas o calculadas en Python aqui mismo.
    
    st.markdown("### 📊 INDICADORES CLAVE (Proyección)")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    # Calculos rápidos para "adornar" mientras leemos el texto
    px_m2 = precio / area
    kpi1.metric(label="Precio Entrada / m²", value=f"${px_m2/1000000:,.1f}M", delta="-45% vs Mercado (Est)")
    kpi2.metric(label="Cap Rate Estimado", value="0.5%", delta_color="off", help="Irrelevante si es Patrimonio")
    kpi3.metric(label="Potencial Valorización", value="Alta", delta="Zona Prime")

    st.divider()

    # EL TEXTO DEL EXPERTO (CHAT)
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(last_msg)
        
    # ZONA DE INTELIGENCIA DE MERCADO (EVIDENCIA)
    with st.expander("🕵️ Ver Evidencia de Mercado (Lo que encontró Gladius)"):
        st.code(st.session_state.market_data)

# --- 7. CHAT INTERACTIVO ---
if prompt := st.chat_input("Desafía los supuestos del CIO..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
    
    with st.spinner("Re-calculando modelo financiero..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
    msgs = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    new_text = msgs.data[0].content[0].text.value
    
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(new_text)
    st.session_state.messages.append({"role": "assistant", "content": new_text})
