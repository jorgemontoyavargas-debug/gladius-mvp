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
    }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title("⚔️ GLADIUS")
st.caption("COMITÉ DE INVERSIÓN AUTOMATIZADO | V4.0 (HYBRID KNOWLEDGE)")
st.markdown("---")

# --- SIDEBAR (INPUTS) ---
st.sidebar.header("1. El Activo")
ubicacion = st.sidebar.text_input("📍 Ubicación Exacta", value="La Cabrera, Bogota")
tipologia = st.sidebar.selectbox("🏗️ Tipo de Inmueble", ["Apartamento Familiar", "Apartaestudio", "Casa", "Local", "Lote"])
estado = st.sidebar.selectbox("🛠️ Estado Físico", ["Para Remodelar (Hueso)", "Buen Estado", "Nuevo / Sobre Planos"])

st.sidebar.header("2. Los Números")
precio = st.sidebar.number_input("💰 Precio de Compra (COP)", min_value=0, value=1070000000, step=10000000, format="%d")
area = st.sidebar.number_input("📐 Área Total (m²)", min_value=10, value=200, step=1)
admin = st.sidebar.number_input("🏢 Administración (COP)", min_value=0, value=2500000, step=50000, format="%d")

st.sidebar.header("3. La Estrategia")
estrategia = st.sidebar.selectbox("🎯 Objetivo Principal", 
                                  ["Vivir (Patrimonio)", 
                                   "Flipping (Remodelar y Vender)", 
                                   "Renta Tradicional", 
                                   "Airbnb"])

ingreso_est = st.sidebar.number_input("💸 Ingreso Mensual Estimado (COP)", min_value=0, value=0, step=100000, format="%d", help="Pon 0 si es para vivir")

# --- LÓGICA DE BÚSQUEDA + CONOCIMIENTO ---
def obtener_contexto_mercado(zona, tipo):
    info_web = ""
    try:
        with DDGS() as ddgs:
            q = f"precio metro cuadrado venta {tipo} {zona} 2024 2025 bogota finca raiz"
            r = list(ddgs.text(q, max_results=3))
            if r:
                info_web = f"DATOS WEB RECIENTES: {str(r)}"
    except:
        info_web = "ADVERTENCIA: Búsqueda web falló."

    # BASE DE DATOS DE RESPALDO (HARDCODED)
    # Esto asegura que Gladius sepa de zonas clave aunque falle internet
    referencias = """
    REFERENCIA DE PRECIOS BOGOTÁ (SI NO HAY DATOS WEB, USA ESTO):
    - La Cabrera / Rosales / Nogal: $10.000.000 - $16.000.000 / m2
    - Chicó / Virrey: $9.000.000 - $14.000.000 / m2
    - Santa Bárbara / Usaquén: $7.000.000 - $11.000.000 / m2
    - Cedritos / Colina: $5.500.000 - $8.000.000 / m2
    - Chapinero Alto: $7.000.000 - $10.000.000 / m2
    """
    
    return info_web + "\n" + referencias

# --- PROMPT MAESTRO (EL CEREBRO DESBLOQUEADO) ---
SYSTEM_PROMPT = """
ERES GLADIUS. TU TRABAJO ES DETECTAR VALOR, NO SOLO FLUJO DE CAJA.

### REGLA DE ORO (LA LÓGICA DE 'HUESO'):
Si la Estrategia es "Vivir" o "Flipping" o "Remodelar":
1.  **IGNORA EL FLUJO DE CAJA NEGATIVO.** Es normal que no genere renta si voy a vivir ahí. No castigues el negocio por tener Ingreso $0.
2.  **TU ÚNICA METRICA ES EL PRECIO/M² DE COMPRA vs. MERCADO.**
    * Calcula: Precio Total / Área.
    * Compara contra los "DATOS DE REFERENCIA".
    * **SI COMPRA A MITAD DE PRECIO: ¡ES UN VERDE ROTUNDO (GO)!** No importa si el edificio es viejo. El descuento ES la ganancia.

### INSTRUCCIONES DE CONTEXTO:
Tienes acceso a una lista de "REFERENCIA DE PRECIOS BOGOTÁ".
Si la búsqueda web falla, **USA TU CONOCIMIENTO INTERNO Y ESA LISTA**.
Tú sabes que comprar a $5M/m² en La Cabrera es un regalo del cielo. DÍSELO.

### ESTRUCTURA DE RESPUESTA (MARKDOWN):

# 🏛️ EL DECRETO GLADIUS
> **SENTENCIA:** [🟢 EJECUTAR / 🟡 RENEGOCIAR / 🔴 DESCARTAR]
> **LA VERDAD:** [Veredicto directo. Ej: "Es el negocio del año. Compras a precio de costo en la zona más cara."]

## 🔍 AUDITORÍA DE VALOR (EL TESORO)
* **Tu Precio de Entrada:** $[Calculado]/m²
* **Precio Real de Zona:** [Rango estimado]
* **⚡ EQUITY INMEDIATO (GANANCIA):** [Diferencia en Millones]. 
*(Explica que esta ganancia ya es suya al firmar).*

## 📉 ANÁLISIS FINANCIERO
*(Nota: Al ser estrategia de Patrimonio/Vivir, el flujo de caja mensual es irrelevante, nos enfocamos en la valorización).*

## 🔥 RECOMENDACIÓN
[Cierre fuerte]
"""

# --- EJECUCIÓN ---
if st.sidebar.button("💀 EJECUTAR AUDITORÍA", type="primary"):
    if precio == 0 or area == 0:
        st.error("⚠️ Faltan datos numéricos.")
    else:
        # Cálculos Python
        pxm2 = precio / area
        
        # Progreso
        my_bar = st.progress(0, text="Interrogando al mercado...")
        
        # Contexto Híbrido
        contexto = obtener_contexto_mercado(ubicacion, tipologia)
        my_bar.progress(60, text="Analizando descuento por m²...")
        
        # Llamada OpenAI
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        user_input = f"""
        CASO: {tipologia} en {ubicacion} ({estado}).
        ESTRATEGIA: {estrategia}.
        PRECIO: ${precio:,.0f}.
        ÁREA: {area} m2.
        PRECIO x M2 REAL: ${pxm2:,.0f}/m2.
        INGRESO MENSUAL: ${ingreso_est:,.0f} (Si es 0, es porque vive ahí).
        
        CONTEXTO MERCADO:
        {contexto}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5
            )
            my_bar.progress(100, text="Listo.")
            st.markdown(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Error: {e}")
