import streamlit as st
import pandas as pd
import requests
import folium
import math
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="HND - Radar Policial",
    page_icon="🚓",
    layout="wide"
)

# --- INYECCIÓN DE MAGIA CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Stardos+Stencil:wght@400;700&family=VT323&display=swap');

    .stApp {
        background-color: #050505;
        color: #e0e0e0;
    }

    [data-testid="stSidebar"] {
        background-color: #101010;
        border-right: 2px solid #003366;
    }

    h1, h2, h3, .stencil-text {
        font-family: 'Stardos Stencil', cursive !important;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px #0044ff;
    }

    p, span, label, .stNumberInput, .terminal-text, .stSlider {
        font-family: 'VT323', monospace !important;
        font-size: 1.2rem !important;
        color: #c0c0c0 !important;
    }

    .stNumberInput div div input {
        background-color: #1a1a1a !important;
        color: #00ff00 !important;
        border: 1px solid #333 !important;
    }

    .stButton>button {
        font-family: 'Stardos Stencil', cursive !important;
        background-color: #cc9900 !important;
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

    .result-card {
        background-color: #0a0a0a;
        border: 1px solid #0044ff;
        padding: 15px;
        margin-bottom: 15px;
        position: relative;
        overflow: hidden;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #00ffff, transparent);
        animation: radar-beam 2s linear infinite;
    }

    .card-id { font-family: 'VT323', monospace; color: #00ffff; font-size: 1.1rem; font-weight: bold; }
    .card-title { font-family: 'Stardos Stencil', cursive; color: #ffffff; font-size: 1.4rem; margin-top: 5px; }
    .card-data { font-family: 'VT323', monospace; color: #ffcc00; font-size: 1.1rem; }

    @keyframes radar-beam {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
</style>
""", unsafe_allow_html=True)

# --- CABECERA PRINCIPAL ---
st.markdown('<h1 style="text-align:center;">📡 SISTEMA DE RADAR HND</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#888 !important;">Despacho Central - Localización de Unidades Metropolitanas (UMEP) y Postas</p>', unsafe_allow_html=True)
st.write("---")

# --- 1. LECTURA DE API KEY ---
try:
    api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
except KeyError:
    st.error("⚠️ CRITICAL ERROR: API Key de Google Maps no encontrada en los Secretos de Streamlit.")
    st.stop()

# --- 2. FUNCIONES MATEMÁTICAS Y DE BÚSQUEDA ---
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine"""
    R = 6371.0 # Radio de la Tierra en km
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return []

# --- 3. PANEL DE CONTROL LATERAL (Sidebar) ---
st.sidebar.markdown('<h2>🛠️ PANEL DE CONTROL</h2>', unsafe_allow_html=True)

# Sección GPS
st.sidebar.markdown('<p class="terminal-text">1. ENLACE SATELITAL (GPS):</p>', unsafe_allow_html=True)
st.sidebar.info("👆 Haz clic en 'Get Location' y permite el acceso.")
gps_data = streamlit_geolocation()

# Coordenadas por defecto (Respaldo Táctico)
lat_inicial = 14.5966
lon_inicial = -87.8340

# Captura de datos GPS si el usuario dio permisos
if gps_data and gps_data.get('latitude') is not None and gps_data.get('longitude') is not None:
    lat_inicial = gps_data['latitude']
    lon_inicial = gps_data['longitude']
    st.sidebar.success("📡 Señal GPS fijada con éxito.")

# Sección Manual y Configuración
st.sidebar.markdown('<p class="terminal-text">2. COORDENADAS ACTUALES:</p>', unsafe_allow_html=True)
user_lat = st.sidebar.number_input("LATITUD", value=lat_inicial, format="%.6f")
user_lon = st.sidebar.number_input("LONGITUD", value=lon_inicial, format="%.6f")

st.sidebar.markdown('<p class="terminal-text">3. FILTRO DE BÚSQUEDA:</p>', unsafe_allow_html=True)
# Selector de cantidad de resultados
num_resultados = st.sidebar.slider("CANTIDAD DE OBJETIVOS A MOSTRAR", min_value=1, max_value=10, value=3)

# --- 4. ÁREA DE TRABAJO (Resultados y Mapa) ---
col1, col2 = st.columns([1, 2])

with col1:
    buscar_btn = st.sidebar.button("📡 INICIAR RASTREO")

    if buscar_btn:
        with st.spinner('🚨 Sintonizando frecuencias... Rastreando señal...'):
            resultados = buscar_estaciones_google(user_lat, user_lon, api_key)
        
        if not resultados:
            st.warning("⚠️ No se detectan unidades o postas en el rango de frecuencia actual.")
        else:
            st.markdown(f'<h3>📍 TOP {num_resultados} UNIDADES MÁS CERCANAS</h3>', unsafe_allow_html=True)
            
            # Recortar la lista al número seleccionado por el usuario
            top_resultados = resultados[:num_resultados]
            estaciones_para_mapa = []

            for i, lugar in enumerate(top_resultados):
                nombre = lugar.get("name", "Desconocido").upper()
                direccion = lugar.get("vicinity", "N/A")
                lat_est = lugar["geometry"]["location"]["lat"]
                lon_est = lugar["geometry"]["location"]["lng"]
                
                # Calcular distancia en kilómetros
                distancia_km = calcular_distancia(user_lat, user_lon, lat_est, lon_est)
                
                estaciones_para_mapa.append({
                    "nombre": nombre,
                    "lat": lat_est,
                    "lon": lon_est,
                    "direccion": direccion,
                    "distancia": distancia_km
                })

                # Inyectar la tarjeta con la nueva línea de distancia
                st.markdown(f"""
                <div class="result-card">
                    <div class="card-id">OBJETIVO #{i+1}</div>
                    <div class="card-title">{nombre}</div>
                    <div class="card-data">📏 DISTANCIA: {distancia_km:.2f} km</div>
                    <div class="card-data">📍 UBICACIÓN: {direccion}</div>
                    <div class="card-data" style="color: #555;">🌐 COORDS: {lat_est:.3f}, {lon_est:.3f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.session_state['map_data'] = estaciones_para_mapa
    else:
        st.info("👈 Fije sus coordenadas y presione INICIAR RASTREO.")

# --- 5. RENDERIZADO DEL MAPA TÁCTICO (Folium) ---
with col2:
    if 'map_data' in st.session_state and buscar_btn:
        st.markdown('<h3>🗺️ VISUALIZACIÓN TÁCTICA</h3>', unsafe_allow_html=True)
        
        m = folium.Map(location=[user_lat, user_lon], zoom_start=14, tiles="CartoDB dark_matter")

        # Marcador del Usuario
        folium.Marker(
            [user_lat, user_lon],
            popup="<b>TU UBICACIÓN</b>",
            tooltip="Punto de Origen",
            icon=folium.Icon(color="blue", icon="crosshairs", prefix='fa') 
        ).add_to(m)

        # Marcadores de Postas Policiales
        for est in st.session_state['map_data']:
            html_popup = folium.Html(f"""
                <div style="font-family: sans-serif; color: black;">
                    <h4 style="margin-bottom:5px;color:#003366;">🚨 {est['nombre']}</h4>
                    <p style="margin:0;font-size:0.9rem;"><b>Dir:</b> {est['direccion']}</p>
                    <p style="margin:0;font-size:0.9rem;color:#d9534f;"><b>Distancia:</b> {est['distancia']:.2f} km</p>
                    <p style="margin:0;font-size:0.8rem;color:gray;">{est['lat']:.4f}, {est['lon']:.4f}</p>
                </div>
            """, script=True)
            
            popup = folium.Popup(html_popup, max_width=265)

            folium.Marker(
                [est['lat'], est['lon']],
                popup=popup,
                tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
                icon=folium.Icon(color="red", icon="car", prefix='fa')
            ).add_to(m)

        st_folium(m, width=None, height=650, returned_objects=[])
