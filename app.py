import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time
import json

# --- 1. CONFIGURACIÓN "INSTITUTIONAL GRADE" ---
st.set_page_config(page_title="Gladius Terminal", page_icon="🏛️", layout="wide")

# CSS: Estilo Limpio, Profesional y de Alto Contraste (Tipo Reporte Bancario)
st.markdown("""
    <style>
    /* Fondo limpio y tipografía ejecutiva */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    /* Botones de Acción (Estilo Call-to-Action) */
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: #ffffff;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.6rem;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #333333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* Tarjetas de Chat más limpias */
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
    }
    /* Métricas destacadas */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (PANEL DE CONTROL) ---
with st.sidebar:
    st.title("🏛️ GLADIUS")
    st.caption("Private Equity Partner | AI-Powered")
    st.markdown("---")
    
    st.subheader("1. Configuración del Deal")
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
    
    if st.button("🔄 Nueva Operación"):
        st.session_state.clear()
        st.rerun()

# --- 3. ESTADO & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = None
if "market_data" not in st.session_state: st.session_state.market_data = None

# VALIDACIÓN DE SECRETOS
if not st.secrets.get("OPENAI_API_KEY") or not st.secrets.get("OPENAI_ASSISTANT_ID"):
    st.warning("⚠️ Faltan las llaves de API en Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- 4. INTELIGENCIA DE MERCADO ---
def get_intel():
    try:
        with DDGS() as ddgs:
            q1 = f"precio metro cuadrado venta {ubicacion} finca raiz 2024 2025"
            q2 = "tasas interes credito hipotecario vivienda colombia bancos hoy 2025"
            # Traemos un poco más de contexto
            r1 = list(ddgs.text(q1, max_results=2))
            r2 = list(ddgs.text(q2, max_results=2))
            return f"DATAZO REAL (PRECIOS): {str(r1)} | DATAZO REAL (TASAS): {str(r2)}"
    except:
        return "DATA WEB NO DISPONIBLE. (Usa defaults)"

# --- 5. DASHBOARD PRINCIPAL ---
if not st.session_state.messages:
    # Landing limpia
    st.markdown("## 🦅 Panel de Decisión de Inversión")
    st.markdown("""
    Bienvenido al terminal de **Gladius**. 
    Este sistema utiliza **Inteligencia de Mercado en Tiempo Real** + **Modelado Financiero** para auditar oportunidades.
    
    **Instrucciones:**
    1. Define los parámetros del activo a la izquierda.
    2. Ejecuta el análisis.
    3. Recibe un Memorando de Inversión profesional.
    """)

if audit_btn:
    with st.status("🦅 Gladius está auditando el activo...", expanded=True) as status:
        st.write("📡 Conectando con fuentes de mercado (Tasas/Precios)...")
        intel = get_intel()
        st.session_state.market_data = intel
        
        st.write("🧮 Corriendo modelo financiero en Python...")
        
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        # PROMPT DE EJECUCIÓN (MODO SOCIO SENIOR)
        msg = f"""
        ACTÚA COMO UN CIO DE PRIVATE EQUITY.
        
        DEAL: {tipo} en {ubicacion} ({estado}).
        PRECIO: ${precio:,.0f} ({area}m2).
        ESTRATEGIA: {estrategia}.
        
        CONTEXTO DE MERCADO (REAL): {intel}
        
        TU MISIÓN:
        1. ASUME los costos faltantes (Obra, Deuda) usando criterio de experto y el contexto web.
        2. CALCULA: Inversión Total, Equity, ROI y Utilidad.
        3. REDACTA EL MEMORANDO.
        
        FORMATO OBLIGATORIO DE SALIDA (MARKDOWN):
        
        # 🦅 MEMORANDO DE INVERSIÓN
        
        ### 1. VEREDICTO EJECUTIVO
        **DECISIÓN:** [APROBADO / RECHAZADO]
        **TESIS:** [Resumen estratégico]
        
        ### 2. SUPUESTOS
