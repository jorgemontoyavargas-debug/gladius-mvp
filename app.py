import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- 1. CONFIGURACIÓN "INSTITUTIONAL GRADE" ---
st.set_page_config(page_title="Gladius Terminal", page_icon="🏛️", layout="wide")

# CSS: Estilo Limpio, Profesional y de Alto Contraste
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
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
    .stButton>button:hover { background-color: #333333; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🏛️ GLADIUS")
    st.caption("Private Equity Partner | AI-Powered")
    st.markdown("---")
    
    st.subheader("Configuración del Deal")
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

if not st.secrets.get("OPENAI_API_KEY"):
    st.error("Faltan las API Keys.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- 4. INTELIGENCIA DE MERCADO (CON FAILOVER) ---
def get_intel():
    """Intenta buscar en web. Si falla (vacío), devuelve instrucción de fallback."""
    try:
        with DDGS() as ddgs:
            q1 = f"precio metro cuadrado venta {ubicacion} finca raiz bogota 2024 2025"
            q2 = "tasas interes credito hipotecario vivienda colombia bancos hoy 2025"
            r1 = list(ddgs.text(q1, max_results=3))
            r2 = list(ddgs.text(q2, max_results=3))
            
            # Si DuckDuckGo devuelve listas vacías (bloqueo), forzamos el error
            if not r1 and not r2:
                raise Exception("Bloqueo de búsqueda")
                
            return f"MARKET DATA (REAL): PRECIOS: {str(r1)} | TASAS: {str(r2)}"
    except:
        # PLAN B: Si la búsqueda falla, le decimos a la IA que use su "Conocimiento Latente"
        return "ADVERTENCIA DEL SISTEMA: La API de búsqueda externa no respondió. USA TU CONOCIMIENTO INTERNO DE EXPERTO SOBRE EL MERCADO DE BOGOTÁ 2024-2025. NO MENCIONES QUE LA BÚSQUEDA FALLÓ. Actúa con total seguridad sobre los datos."

# --- 5. LOGICA PRINCIPAL ---
if audit_btn:
    with st.status("🦅 Gladius está estructurando el deal...", expanded=True) as status:
        st.write("📡 Escaneando asimetrías de mercado...")
        intel = get_intel()
        st.session_state.market_data = intel
        
        st.write("🧮 Corriendo modelo de valuación...")
        
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        # --- EL PROMPT "LOBO DE WALL STREET" ---
        msg = f"""
        ACTÚA COMO UN CIO (CHIEF INVESTMENT OFFICER) DE UN FONDO DE PRIVATE EQUITY.
        Tu tono es: **Sofisticado, Persuasivo, Financiero y Seguro.**
        PROHIBIDO sonar como un asistente virtual ("Hola, aquí tienes...").
        Debes sonar como si estuvieras vendiendo el negocio del siglo a la junta directiva.
        
        USA TÉRMINOS FINANCIEROS DE ÉLITE:
        "Upside Potential", "Cap Rate", "Ineficiencia de Mercado", "Arbitraje de Valor", "Margen de Seguridad", "Equity Multiple".
        
        DEAL A EVALUAR: {tipo} en {ubicacion} ({estado}).
        PRECIO ENTRADA: ${precio:,.0f} ({area}m2).
        ESTRATEGIA: {estrategia}.
        
        CONTEXTO: {intel}
        
        TU MISIÓN:
        1. ASUME los vacíos (Obra, Deuda, Salida) con criterio agresivo pero realista.
        2. CALCULA en Python (Code Interpreter).
        3. REDACTA EL MEMORANDO (Markdown).
        
        FORMATO ESTRICTO (NO REPITAS TÍTULOS):
        
        ### 1. VEREDICTO EJECUTIVO
        **DECISIÓN:** [🟢 APROBADO / 🔴 RECHAZADO]
        **LA TESIS:** [Párrafo de 3-4 líneas. Véndeme la historia. ¿Dónde está el dinero escondido? ¿Por qué esto es una oportunidad única?]
        
        ### 2. ESTRUCTURACIÓN DEL DEAL (SUPUESTOS)
        * **CAPEX (Remodelación):** [Monto Asumido] (Explica por qué: "Para lograr un producto AAA...")
        * **Apalancamiento:** [Tasa] (Explica el impacto en el flujo).
        * **Exit Strategy:** [Precio Venta] (Justifica el upside).
        
        ### 3. MODELO FINANCIERO
        (SOLO MUESTRA LA TABLA AQUÍ. NO REPITAS EL TÍTULO "MODELO FINANCIERO" DOS VECES).
        | Concepto | Valor |
        | :--- | :--- |
        | Inversión Total (All-in) | ... |
        | Equity Requerido | ... |
        | Utilidad Neta Proyectada | ... |
        | **ROI (Retorno s/ Capital)** | **...** |
        
        ### 4. CIO CLOSING REMARKS
        [Tu conclusión final. Habla de riesgo vs recompensa. Sé contundente.]
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=msg)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status == "failed":
                st.error("Error en la IA.")
                st.stop()
        
        status.update(label="Análisis Finalizado", state="complete", expanded=False)

    # RECUPERACIÓN LIMPIA
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    full_text = ""
    # Capturamos respuesta completa
    for m in reversed(mensajes.data):
        if m.role == "assistant":
            for c in m.content:
                if c.type == "text":
                    full_text += c.text.value + "\n\n"
    
    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.rerun()

# --- 6. VISUALIZACIÓN ---
if not st.session_state.messages:
    st.markdown("## 🦅 Terminal de Inversión")
    st.markdown("Configura el activo a la izquierda para iniciar la auditoría de capital.")

if st.session_state.messages:
    # KPI BOARD
    px_m2 = precio / area
    st.divider()
    k1, k2, k3 = st.columns(3)
    k1.metric("Precio Entrada / m²", f"${px_m2/1000000:,.1f}M", "vs Mercado (Est)")
    k2.metric("Condición Actual", "Hueso" if "Remodelar" in estado else "Estándar", "Oportunidad de Valor")
    k3.metric("Tesis", estrategia.split(" ")[0])
    st.divider()

    # CHAT
    last_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(last_msg)

    # EVIDENCIA OCULTA (SOLO PARA TI)
    with st.expander("🛠️ Debug: Inteligencia de Mercado"):
        st.text(st.session_state.market_data)

# --- 7. INPUT CHAT ---
if prompt := st.chat_input("Refina la tesis..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
    
    with st.spinner("Re-evaluando estrategia..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
    mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    final_ans = messages = mensajes.data[0].content[0].text.value
    
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(final_ans)
    st.session_state.messages.append({"role": "assistant", "content": final_ans})
