import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gladius Terminal", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #111; }
    .stButton>button { width: 100%; background-color: #000; color: #fff; font-weight: bold; border-radius: 6px; padding: 0.8rem; border: none; }
    .stButton>button:hover { background-color: #333; }
    .stChatMessage { background-color: #f4f4f4; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🏛️ GLADIUS")
    st.caption("Private Equity Partner")
    st.markdown("---")
    
    st.subheader("El Activo")
    ubicacion = st.text_input("📍 Ubicación", value="La Cabrera, Bogota")
    estrategia = st.selectbox("🎯 Estrategia", ["Vivir (Patrimonio)", "Flipping", "Renta", "Airbnb"])
    precio = st.number_input("💰 Precio (COP)", value=1070000000, step=10000000, format="%d")
    area = st.number_input("📐 Área (m²)", value=200)
    estado = st.selectbox("🛠️ Condición", ["Para Remodelar (Hueso)", "Buen Estado"])

    st.markdown("---")
    audit_btn = st.button("💀 EJECUTAR STRESS TEST")
    
    if st.button("🔄 Nueva Operación"):
        st.session_state.clear()
        st.rerun()

# --- 3. ESTADO ---
if "messages" not in st.session_state: st.session_state.messages = []
if "thread_id" not in st.session_state: st.session_state.thread_id = None
if "market_data" not in st.session_state: st.session_state.market_data = None

if not st.secrets.get("OPENAI_API_KEY"): st.stop()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
assistant_id = st.secrets["OPENAI_ASSISTANT_ID"]

# --- 4. BÚSQUEDA HONESTA ---
def get_intel():
    """Intenta buscar. Si falla, reporta el fallo honestamente."""
    try:
        with DDGS() as ddgs:
            # Intentamos traer tasas reales
            q = "tasas credito hipotecario vivienda colombia bancos hoy 2025"
            r = list(ddgs.text(q, max_results=2))
            if not r: return "ERROR: No se pudo conectar a la fuente de tasas. (Se usará escenario base 14% E.A.)"
            return f"TASAS MERCADO (REF): {str(r)}"
    except:
        return "ERROR DE CONEXIÓN: Asumiendo escenario conservador de tasas altas para el Stress Test."

# --- 5. LOGICA PRINCIPAL ---
if audit_btn:
    with st.status("🦅 Ejecutando Auditoría de Riesgo...", expanded=True) as status:
        st.write("📡 Verificando costo del dinero (Tasas)...")
        intel = get_intel()
        st.session_state.market_data = intel
        
        st.write("🩸 Calculando liquidez y flujo de caja...")
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
        # --- PROMPT V5.3: THE REALITY CHECK ---
        msg = f"""
        ACTÚA COMO UN SOCIO DE INVERSIÓN (RISK MANAGER).
        Tu trabajo no es solo evaluar el edificio, es evaluar MI CAPACIDAD de pagarlo.
        
        DEAL: {ubicacion} | Precio: ${precio:,.0f} | Estado: {estado} | Estrategia: {estrategia}.
        CONTEXTO TASAS: {intel}
        
        TU MISIÓN (ESTRICTA):
        1.  **ASUME EL PEOR ESCENARIO:** Si es "Hueso", asume remodelación cara ($3M/m²).
        2.  **MODELA LA DEUDA:** Usa tasa de mercado (o 14% E.A. si falló la búsqueda) a 20 Años. LTV 70%.
        3.  **EJECUTA EL "STRESS TEST" (PRUEBA DE ÁCIDO):**
            * Calcula cuánto EFECTIVO necesito el Día 1 (Cuota Inicial 30% + Costo Remodelación TOTAL).
            * Calcula mi "Monthly Burn" (Cuota Hipoteca + Admin + Impuestos).
        
        FORMATO DE RESPUESTA (MARKDOWN):
        
        ### 1. 🩸 EL "STRESS TEST" DE LIQUIDEZ (LO CRÍTICO)
        > **CASH REQUIRED (Día 1):** **$[Monto]**
        > *(Desglose: Cuota inicial $[X] + Remodelación $[Y])*
        >
        > **¿TIENES ESTE CAPITAL?** Si no lo tienes líquido, estamos en riesgo de iliquidez antes de empezar.
        
        ### 2. 📉 IMPACTO EN TU FLUJO DE CAJA MENSUAL
        > **Tu "Sangrado" Mensual Estimado:** **$[Monto]/mes**
        > *(Cuota Banco al [Tasa]% + Admin + Predial)*.
        >
        > **ANÁLISIS DE RIESGO:** [Dime si este flujo es peligroso. Ej: "Necesitas ganar 30M libres al mes solo para sostener esto"].

        ### 3. 🏛️ VEREDICTO DEL ACTIVO (LA TESIS)
        * **Valor Entrada Real (All-in):** $[Monto] ($/m2)
        * **Upside Potencial:** [Si remodelo, ¿cuánto gano?]
        * **Sentencia:** [APROBADO / RIESGO ALTO DE ILIQUIDEZ / RECHAZADO]
        
        ### 4. PREGUNTA DE CIERRE
        "He modelado esto con un LTV del 70% a 20 años. **¿Esta estructura de deuda se ajusta a tu realidad o prefieres que recalcule con otro capital propio?**"
        """
        
        client.beta.threads.messages.create(thread_id=thread.id, role="user", content=msg)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        status.update(label="Stress Test Finalizado", state="complete", expanded=False)

    # RECUPERACIÓN DE RESPUESTA
    mensajes = client.beta.threads.messages.list(thread_id=thread.id)
    full_text = ""
    for m in reversed(mensajes.data):
        if m.role == "assistant":
            for c in m.content:
                if c.type == "text": full_text += c.text.value + "\n\n"
    
    st.session_state.messages.append({"role": "assistant", "content": full_text})
    st.rerun()

# --- 6. VISUALIZACIÓN ---
if st.session_state.messages:
    # EXTRAER KPI DE RIESGO
    st.divider()
    st.markdown("### 🔥 ZONA DE RIESGO")
    k1, k2, k3 = st.columns(3)
    
    # Calculos simples de referencia visual (El GPT dará los exactos)
    equity_necesario = precio * 0.3
    remodelacion_est = area * 2500000 if "Remodelar" in estado else 0
    cash_day_1 = equity_necesario + remodelacion_est
    
    k1.metric("Caja Mínima Requerida (Est)", f"${cash_day_1/1000000:,.0f}M", "Equity + Obra", delta_color="inverse")
    k2.metric("Endeudamiento Base", "70%", "LTV Asumido")
    k3.metric("Riesgo Iliquidez", "ALTO" if cash_day_1 > 500000000 else "MEDIO", help="Basado en monto inicial")
    
    st.divider()

    # CHAT
    last_msg = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(last_msg)

    with st.expander("🔎 Verificación de Fuentes (Sin Alucinaciones)"):
        st.text(st.session_state.market_data)

# --- 7. INPUT CHAT ---
if prompt := st.chat_input("Ej: 'Solo tengo 400M de caja' o 'Calcula a 15 años'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
    
    with st.spinner("Recalculando riesgo de liquidez..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            
    mensajes = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    final_ans = mensajes.data[0].content[0].text.value
    
    with st.chat_message("assistant", avatar="🦅"):
        st.markdown(final_ans)
    st.session_state.messages.append({"role": "assistant", "content": final_ans})
