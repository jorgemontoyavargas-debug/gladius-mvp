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
        
        ### 2. SUPUESTOS ESTRUCTURALES
        * **Remodelación:** [Valor asumido]
        * **Deuda:** [Tasa asumida]
        * **Salida:** [Precio venta proyectado]
        
        ### 3. MODELO FINANCIERO (PYTHON)
        | Concepto | Valor |
        | :--- | :--- |
        | Inversión Total | ... |
        | Utilidad Neta | ... |
        | ROI | ... |
        
        ### 4. COMENTARIOS DEL CIO
        [Cierre]
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=msg)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "failed":
                st.error("Error en el análisis de IA.")
                st.stop()
        
        status.update(label="Análisis Finalizado", state="complete", expanded=False)

    # RECUPERACIÓN DE RESPUESTA (FIX DEL LOOP)
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    
    full_text = ""
    # Lógica para capturar todos los mensajes de respuesta en orden
    for m in reversed(mensajes.data):
        if m.role == "assistant":
            for c in m.content:
                if c.type == "text":
                    full_text += c.text.value + "\n\n"
    
    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.rerun()

# --- 6. VISUALIZACIÓN DE RESULTADOS ---
if st.session_state.messages:
    # 6.1 DASHBOARD DE INDICADORES (KPIs)
    # Calculamos algunos KPIs básicos en vivo para "adornar" el reporte
    px_m2 = precio / area
    
    st.divider()
    st.subheader("📊 Tablero de Control")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Precio Entrada / m²", f"${px_m2/1000000:,.1f}M", help="Calculado sobre precio base")
    k2.metric("Estado Físico", "Hueso" if "Remodelar" in estado else "Estándar", delta="Oportunidad CAPEX" if "Remodelar" in estado else "Listo para usar")
    k3.metric("Estrategia", estrategia.split(" ")[0], delta_color="off")
    
    st.divider()

    # 6.2 EL MEMORANDO (CHAT)
    last_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(last_msg)

    # 6.3 EVIDENCIA
    with st.expander("🔎 Ver Inteligencia de Mercado (Fuente de Datos)"):
        st.info(st.session_state.market_data)

# --- 7. CHAT PARA REFINAR ---
if prompt := st.chat_input("Dile al CIO: 'Ajusta la obra a 200M' o 'Calcula salida a 5 años'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
    
    with st.spinner("Recalculando modelo..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
    # RECUPERACIÓN (MISMO FIX)
    mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    full_resp = ""
    for m in reversed(mensajes.data):
         # Truco simple: Tomar solo los últimos mensajes después del user
         # (Simplificado para este MVP: tomamos el último bloque del asistente)
         pass 
    
    # Tomamos el mensaje más reciente del asistente
    final_ans = mensajes.data[0].content[0].text.value
    
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(final_ans)
    st.session_state.messages.append({"role": "assistant", "content": final_ans})
