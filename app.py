import streamlit as st
import numpy as np
import requests
from PIL import Image
import joblib

st.set_page_config(page_title="🔥 Wildfire AI (NASA Level 2)", page_icon="🔥")

st.title("🔥 Wildfire Risk AI (NASA Level 2 Model)")

# -------------------------
# LOAD MODEL
# -------------------------

model = joblib.load("fire_model.pkl")

# -------------------------
# WEATHER
# -------------------------

def get_weather(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )

    c = requests.get(url).json()["current"]

    return c["temperature_2m"], c["relative_humidity_2m"], c["wind_speed_10m"]

# -------------------------
# NDVI (image-based vegetation)
# -------------------------

def ndvi(image):

    img = np.array(image.convert("RGB")).astype(float)

    red = img[:, :, 0]
    green = img[:, :, 1]

    nir = (green + red) / 2

    return np.mean((nir - red) / (nir + red + 1e-6))

# -------------------------
# INPUT
# -------------------------

uploaded = st.file_uploader("📸 Upload image", type=["jpg", "png"])

lat = st.number_input("Latitude", value=49.2)
lon = st.number_input("Longitude", value=-122.9)

if uploaded:

    img = Image.open(uploaded)
    st.image(img, use_container_width=True)

    # -------------------------
    # FEATURES
    # -------------------------

    temp, humidity, wind = get_weather(lat, lon)
    vi = ndvi(img)

    X = np.array([[temp, humidity, wind, vi]])

    # -------------------------
    # REAL ML PREDICTION
    # -------------------------

    prob = model.predict_proba(X)[0][1] * 100

    st.subheader("🔥 Prediction")

    st.metric("Fire Probability", f"{prob:.1f}%")

    # -------------------------
    # EXPLANATION
    # -------------------------

    st.write("### Inputs")
    st.write(f"🌡 Temp: {temp}")
    st.write(f"💧 Humidity: {humidity}")
    st.write(f"💨 Wind: {wind}")
    st.write(f"🌿 NDVI: {vi:.3f}")

    if prob > 75:
        st.error("🔥 Extreme Risk")
    elif prob > 50:
        st.warning("⚠️ High Risk")
    else:
        st.success("✅ Low Risk")
