import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="HND - Radar Policial",
    page_icon="🚓",
    layout="wide" # Usamos ancho completo para mejor visualización del mapa
)

# Importamos Google Fonts temáticas y aplicamos estilos globales
st.markdown("""
<style>
    /* Importar Fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Stardos+Stencil:wght@400;700&family=VT323&display=swap');

    /* Estilos Globales del Fondo y Texto Base */
    .stApp {
        background-color: #050505; /* Negro casi total */
        color: #e0e0e0;
    }

    /* Estilo del Menú Lateral */
    [data-testid="stSidebar"] {
        background-color: #101010;
        border-right: 2px solid #003366; /* Borde Azul Patrulla */
    }

    /* Títulos Principales (Stencil) */
    h1, h2, h3, .stencil-text {
        font-family: 'Stardos Stencil', cursive !important;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px #0044ff; /* Brillo neón azul sutil */
    }

    /* Textos de Datos y UI (Monospace/Terminal) */
    p, span, label, .stNumberInput, .terminal-text {
        font-family: 'VT323', monospace !important;
        font-size: 1.2rem !important;
        color: #c0c0c0 !important;
    }

    /* Estilo para los inputs numéricos del sidebar */
    .stNumberInput div div input {
        background-color: #1a1a1a !important;
        color: #00ff00 !important; /* Texto verde terminal */
        border: 1px solid #333 !important;
    }

    /* Botón Buscar Estilo Militar */
    .stButton>button {
        font-family: 'Stardos Stencil', cursive !important;
        background-color: #cc9900 !important; /* Amarillo Precaución */
        color: #000000 !important;
        border: none !important;
        border-radius: 0px !important;
        font-size: 1.3rem !important;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #ffcc00 !important;
        box-shadow: 0 0 15px #ffcc00;
        transform: scale(1.02);
    }

    /* --- ESTILO DE TARJETAS DE RESULTADOS (Magia de Radar) --- */
    .result-card {
        background-color: #0a0a0a;
        border: 1px solid #0044ff; /* Borde Azul */
        padding: 15px;
        margin-bottom: 15px;
        position: relative;
        overflow: hidden;
    }
    /* El borde neón de la tarjeta */
    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #00ffff, transparent);
        animation: radar-beam 2s linear infinite;
    }

    .card-id {
        font-family: 'VT323', monospace;
        color: #00ffff; /* Cian */
        font-size: 1.1rem;
        font-weight: bold;
    }
    .card-title {
        font-family: 'Stardos Stencil', cursive;
        color: #ffffff;
        font-size: 1.4rem;
        margin-top: 5px;
    }
    .card-data {
        font-family: 'VT323', monospace;
        color: #ffcc00; /* Amarillo */
        font-size: 1.1rem;
    }

    /* Animación del haz del radar */
    @keyframes radar-beam {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE LA APP (Mantenemos la seguridad y la API) ---

# Título con estilo inyectado
st.markdown('<h1 style="text-align:center;">📡 SISTEMA DE RADAR HND</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888 !important;">Despacho Central - Localización de Unidades Metropolitanas (UMEP) y Postas</p>', unsafe_allow_html=True)
st.write("---")

# 1. Leer la API Key de los Secretos
try:
    api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
except KeyError:
    st.error("⚠️ CRITICAL ERROR: Auth Key missing in secrets.")
    st.stop()

# 2. Sidebar Temático
st.sidebar.markdown('<h2>🛠️ PANEL DE CONTROL</h2>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="terminal-text">Ingrese coordenadas de referencia (WGS84):</p>', unsafe_allow_html=True)

# Coordenadas por defecto (Siguatepeque como centro)
user_lat = st.sidebar.number_input("LATITUD", value=14.5966, format="%.4f")
user_lon = st.sidebar.number_input("LONGITUD", value=-87.8340, format="%.4f")

# 3. Función de búsqueda (sin cambios)
def buscar_estaciones_google(lat, lon, key):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    parametros = {
        "location": f"{lat},{lon}",
        "rankby": "distance",
        "type": "police",
        "keyword": "policia",
        "language": "es",
        "key": key
    }
    try:
        respuesta = requests.get(url, params=parametros)
        if respuesta.status_code == 200:
            return respuesta.json().get("results", [])
    except:
        pass
    return []

# Layout de dos columnas para resultados y mapa
col1, col2 = st.columns([1, 2]) # El mapa (col2) será más ancho

# Ejecución al presionar el botón
with col1:
    buscar_btn = st.sidebar.button("📡 INICIAR RASTREO")

    if buscar_btn:
        # Spinner temático
        with st.spinner('🚨 Sintonizando frecuencias... Rastreando señal GPS...'):
            resultados = buscar_estaciones_google(user_lat, user_lon, api_key)
        
        if not resultados:
            st.warning("⚠️ No se detectan unidades o postas en el rango de frecuencia actual.")
        else:
            st.markdown('<h3>📍 UNIDADES MÁS CERCANAS</h3>', unsafe_allow_html=True)
            top_3 = resultados[:3]
            
            estaciones_para_mapa = []

            # Mostrar resultados usando HTML personalizado para las tarjetas
            for i, lugar in enumerate(top_3):
                nombre = lugar.get("name").upper()
                direccion = lugar.get("vicinity", "N/A")
                lat_est = lugar["geometry"]["location"]["lat"]
                lon_est = lugar["geometry"]["location"]["lng"]
                
                # Guardar datos para el mapa
                estaciones_para_mapa.append({
                    "nombre": nombre,
                    "lat": lat_est,
                    "lon": lon_est,
                    "direccion": direccion
                })

                # Inyección de la tarjeta HTML
                st.markdown(f"""
                <div class="result-card">
                    <div class="card-id">OBJETIVO #{i+1}</div>
                    <div class="card-title">{nombre}</div>
                    <div class="card-data">📍 {direccion}</div>
                    <div class="card-data">🌐 COORDS: {lat_est:.3f}, {lon_est:.3f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Pasamos los datos a la columna del mapa
            st.session_state['map_data'] = estaciones_para_mapa
    else:
        st.info("👈 Configure coordenadas y presione INICIAR RASTREO en el panel de control.")

# 4. Mapa Avanzado con Folium (Columna 2)
with col2:
    if 'map_data' in st.session_state and buscar_btn:
        st.markdown('<h3>🗺️ VISUALIZACIÓN TÁCTICA</h3>', unsafe_allow_html=True)
        
        # Crear el mapa base centrado en el usuario (usando Tiles oscuros temáticos)
        m = folium.Map(location=[user_lat, user_lon], zoom_start=13, tiles="CartoDB dark_matter")

        # --- MARCADOR DEL USUARIO (Pin especial) ---
        folium.Marker(
            [user_lat, user_lon],
            popup="<b>TU UBICACIÓN</b>",
            tooltip="Punto de Origen",
            icon=folium.Icon(color="blue", icon="user", prefix='fa') # Icono de usuario FontAwesome
        ).add_to(m)

        # --- MARCADORES DE POLICÍA (Iconos de Patrulla) ---
        for est in st.session_state['map_data']:
            # Crear popup HTML bonito para el mapa
            html_popup = folium.Html(f"""
                <div style="font-family: sans-serif; color: black;">
                    <h4 style="margin-bottom:5px;color:#003366;">🚨 {est['nombre']}</h4>
                    <p style="margin:0;font-size:0.9rem;"><b>Dir:</b> {est['direccion']}</p>
                    <p style="margin:0;font-size:0.8rem;color:gray;">{est['lat']:.4f}, {est['lon']:.4f}</p>
                </div>
            """, script=True)
            
            popup = folium.Popup(html_popup, max_width=265)

            folium.Marker(
                [est['lat'], est['lon']],
                popup=popup,
                tooltip=est['nombre'],
                # Icono de patrulla (coche) de FontAwesome, color rojo
                icon=folium.Icon(color="red", icon="car", prefix='fa')
            ).add_to(m)

        # Renderizar el mapa de Folium en Streamlit
        st_folium(m, width=None, height=500, returned_objects=[])
