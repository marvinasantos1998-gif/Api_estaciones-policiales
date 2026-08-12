import streamlit as st
import pandas as pd
import requests

# Título de la App
st.title("🚓 Localizador Dinámico de Policía")
st.write("Conectado a Google Maps para encontrar las estaciones reales más cercanas en Honduras.")

# 1. Leer la API Key de los Secretos de Streamlit
try:
    api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
except KeyError:
    st.error("⚠️ Error: No se encontró la API Key en los secretos de Streamlit.")
    st.stop()
st.sidebar.header("Tus Coordenadas")
st.sidebar.write("*(Ej. Siguatepeque: Lat 14.5966, Lon -87.8340)*")
user_lat = st.sidebar.number_input("Latitud", value=14.5966, format="%.4f")
user_lon = st.sidebar.number_input("Longitud", value=-87.8340, format="%.4f")

# 2. Función para buscar en Google Maps
def buscar_estaciones_google(lat, lon, key):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    parametros = {
        "location": f"{lat},{lon}",
        "rankby": "distance",   # Ordena automáticamente por cercanía
        "type": "police",       # Filtra solo estaciones de policía
        "keyword": "policia",   # Refuerza la búsqueda en español
        "language": "es",
        "key": key
    }
    
    respuesta = requests.get(url, params=parametros)
    if respuesta.status_code == 200:
        return respuesta.json().get("results", [])
    else:
        return []

# Botón Buscar
if st.sidebar.button("🔍 Buscar Estaciones", type="primary"):
    
    if not api_key:
        st.error("⚠️ Necesitas ingresar una API Key de Google Maps para realizar la búsqueda dinámica.")
    else:
        with st.spinner('Buscando en Google Maps...'):
            resultados = buscar_estaciones_google(user_lat, user_lon, api_key)
        
        if len(resultados) == 0:
            st.warning("No se encontraron estaciones de policía cercanas o la API Key es inválida.")
        else:
            # Tomamos solo los 3 primeros resultados (los más cercanos)
            top_3 = resultados[:3]
            
            st.subheader("📍 Las 3 estaciones más cercanas:")
            
            datos_mapa = [{"lat": user_lat, "lon": user_lon, "color": "#0000FF"}] # Azul = Usuario
            
            # Mostrar las tarjetas
            for i, lugar in enumerate(top_3):
                nombre = lugar.get("name")
                direccion = lugar.get("vicinity", "Dirección no disponible")
                lat_estacion = lugar["geometry"]["location"]["lat"]
                lon_estacion = lugar["geometry"]["location"]["lng"]
                
                st.info(f"**{i+1}. {nombre}**  \n📍 Dirección: {direccion}")
                
                # Agregamos al mapa (Rojo = Policía)
                datos_mapa.append({"lat": lat_estacion, "lon": lon_estacion, "color": "#FF0000"})
            
            # 3. Dibujar el Mapa
            st.write("---")
            st.subheader("🗺️ Mapa de Ubicaciones (Azul = Tú, Rojo = Policía)")
            df_mapa = pd.DataFrame(datos_mapa)
            st.map(df_mapa, color="color", size=200)
else:
    st.info("👈 Ingresa la API Key, tus coordenadas y presiona 'Buscar Estaciones'.")
