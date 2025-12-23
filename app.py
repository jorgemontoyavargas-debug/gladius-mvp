import streamlit as st
from openai import OpenAI
from duckduckgo_search import DDGS

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gladius Auditor", page_icon="⚔️", layout="centered")

# --- ESTILOS VISUALES ---
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
        background-color: #333333;
        color: white;
        border: 1px solid #fff;
    }
    h1 { color: #000; }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title("⚔️ GLADIUS")
st.caption("COMITÉ DE INVERSIÓN AUTOMATIZADO | V3.0 (SEARCH + REASONING)")
st.markdown("---")

# --- SIDEBAR (INPUTS) ---
st.sidebar.header("1. El Activo")
ubicacion = st.sidebar.text_input("📍 Ubicación Exacta", placeholder="Ej: La Cabrera, Calle 85, Bogotá")
tipologia = st.sidebar.selectbox("🏗️ Tipo de Inmueble", ["Apartamento Familiar", "Apartaestudio / Loft", "Casa", "Local Comercial", "Lote"])
estado = st.sidebar.selectbox("🛠️ Estado Físico", ["Nuevo / Sobre Planos", "Usado (Buen estado)", "Para Remodelar (Hueso)"])

st.sidebar.header("2. Los Números")
precio = st.sidebar.number_input("💰 Precio de Compra (COP)", min_value=0, step=10000000, format="%d")
area = st.sidebar.number_input("📐 Área Total (m²)", min_value=10, step=1)
admin = st.sidebar.number_input("🏢 Administración (COP)", min_value=0, step=50000, format="%d")

st.sidebar.header("3. La Estrategia")
estrategia = st.sidebar.selectbox("🎯 Objetivo Principal", 
                                  ["Vivir (Patrimonio)", 
                                   "Renta Tradicional (Flujo)", 
                                   "Airbnb / Rentas Cortas", 
                                   "Flipping (Comprar, Remodelar, Vender)"])

ingreso_est = st.sidebar.number_input("💸 Ingreso Mensual Estimado (COP)", min_value=0, step=100000, format="%d", help="Canon esperado o Promedio Airbnb")

# --- LÓGICA DE BÚSQUEDA (LOS OJOS) ---
def buscar_contexto(zona, tipo):
    try:
        with DDGS() as ddgs:
            # Buscamos precios de venta recientes
            q1 = f"precio metro cuadrado venta {tipo} {zona} 2024 2025 bogota finca raiz"
            r1 = list(ddgs.text(q1, max_results=3))
            contexto = f"DATAZO DE INTERNET (Venta): {str(r1)}\n"
            
            # Buscamos precios de arriendo
            q2 = f"precio arriendo {tipo} {zona} 2024 2025 metrocuadrado"
            r2 = list(ddgs.text(q2, max_results=2))
            contexto += f"DATAZO DE INTERNET (Renta): {str(r2)}"
            return contexto
    except:
        return "No se pudo conectar a internet. Usa tu base de conocimiento interna."

# --- PROMPT MAESTRO (EL CEREBRO SENIOR) ---
SYSTEM_PROMPT = """
ERES GLADIUS. No eres un chatbot. Eres un SOCIO SENIOR DE INVERSIÓN.
Tu trabajo no es ser amable. Es proteger el capital del usuario.

### TUS REGLAS INQUEBRANTABLES:
1.  **DECISION-AS-A-SERVICE:** Empieza SIEMPRE con un veredicto binario.
2.  **LÓGICA DE NEGOCIO (EL JUEZ):**
    * **SI LA ESTRATEGIA ES "VIVIR", "FLIPPING" O "REMODELAR":**
        * Tu Dios es el **PRECIO POR M² DE COMPRA** vs. **PRECIO DE MERCADO**.
        * Si el usuario compra con -20% de descuento (Equity Instantáneo), es un **🟢 GO DEAL**, aunque el flujo de caja sea neutro.
        * *Razón:* "Se gana en la compra, no en la venta".
    * **SI LA ESTRATEGIA ES "RENTA" O "AIRBNB":**
        * Tu Dios es el **CASHFLOW (Flujo de Caja)**.
        * Si el arriendo no paga la operación, es un **🔴 KILL DEAL**, a menos que el precio sea ridículamente bajo.

3.  **TONO DE VOZ:**
    * Directo, cínico, profesional, "Anti-Bullshit".
    * Si el usuario trae un mal negocio, humíllalo con elegancia (con números).
    * Si trae una joya, felicítalo por encontrar la falla en la Matrix.

4.  **ESTRUCTURA DE RESPUESTA (OBLIGATORIA EN MARKDOWN):**

    # 🏛️ EL DECRETO GLADIUS
    > **SENTENCIA:** [🟢 EJECUTAR / 🟡 RENEGOCIAR / 🔴 DESCARTAR]
    > **LA VERDAD CRUDA:** [Aquí explica por qué, en 3 líneas duras. Ataca la lógica del usuario si es necesario.]

    ## 🔍 AUDITORÍA DE VALOR (TU COMPRA vs. MERCADO)
    * **Tu Precio:** $[X]/m²
    * **Mercado Real (Detectado):** $[Y]/m²
    * **⚡ EQUITY DÍA 1:** [Calcula: (Mercado - Tu Precio) * Area]. (Si es positivo: "Te ganaste esto firmando". Si es negativo: "Perdiste esto firmando").

    ## 📊 LA REALIDAD FINANCIERA
    [Tabla simple con Ingresos, Gastos (Admin + Predial estimado), NOI Anual y Cap Rate]

    ## 🔥 RECOMENDACIÓN FINAL
    [Una frase matadora para cerrar]

"""

# --- BOTÓN DE EJECUCIÓN ---
if st.sidebar.button("💀 EJECUTAR AUDITORÍA", type="primary"):
    if precio == 0 or ubicacion == "":
        st.error("⚠️ Sin datos no hay paraíso. Dame Ubicación y Precio.")
    else:
        # 1. CÁLCULOS PREVIOS (Para ayudar a la IA)
        pxm2 = precio / area
        noi = (ingreso_est - admin) * 12
        cap_rate_est = (noi / precio) * 100 if precio > 0 else 0
        
        # 2. INDICADOR DE PROGRESO
        progress_text = "Gladius está interrogando al mercado..."
        my_bar = st.progress(0, text=progress_text)
        
        # 3. BÚSQUEDA WEB
        datos_mercado = buscar_contexto(ubicacion, tipologia)
        my_bar.progress(50, text="Analizando viabilidad financiera...")
        
        # 4. LLAMADA A OPENAI
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        user_prompt = f"""
        AUDITA ESTE CASO REAL:
        - Activo: {tipologia} en {ubicacion} ({estado}).
        - Estrategia: {estrategia}.
        - Precio: ${precio:,.0f} (equivale a ${pxm2:,.0f} / m²).
        - Ingreso Mensual: ${ingreso_est:,.0f}.
        - Admin: ${admin:,.0f}.
        
        DATOS DUROS (Contexto de Internet):
        {datos_mercado}
        
        CALCULADORA AUXILIAR (Para que no falles):
        - Cap Rate Bruto: {cap_rate_est:.2f}%
        - Costo por m2: ${pxm2:,.0f}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6 # Un poco más creativo para el "tono", pero controlado
            )
            my_bar.progress(100, text="Auditoría Completada.")
            st.markdown(response.choices[0].message.content)
            
            # Debug (Opcional: ver qué encontró en internet)
            with st.expander("🕵️ Ver qué encontró Gladius en internet"):
                st.write(datos_mercado)

        except Exception as e:
            st.error(f"Error cerebral: {e}")
