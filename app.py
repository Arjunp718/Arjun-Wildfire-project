import streamlit as st
import requests
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

st.set_page_config(
    page_title="🔥 Wildfire Risk System",
    page_icon="🔥"
)

st.title("🔥 Wildfire Risk System")

st.write("Upload a GPS photo. The system estimates wildfire risk using AI-style scoring + NDVI vegetation analysis.")

# -------------------------
# WEATHER
# -------------------------

def get_weather(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&current=temperature_2m,"
        f"relative_humidity_2m,"
        f"wind_speed_10m"
    )

    data = requests.get(url, timeout=15).json()
    c = data["current"]

    return c["temperature_2m"], c["relative_humidity_2m"], c["wind_speed_10m"]

# -------------------------
# GPS EXTRACTION
# -------------------------

def get_exif(image):

    exif = {}

    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                exif[TAGS.get(tag, tag)] = value
    except:
        pass

    return exif


def dms_to_decimal(dms, ref):

    deg = float(dms[0])
    minutes = float(dms[1])
    sec = float(dms[2])

    dec = deg + minutes / 60 + sec / 3600

    if ref in ["S", "W"]:
        dec *= -1

    return dec

# -------------------------
# NDVI-LIKE VEGETATION INDEX
# -------------------------
# (Simulated NDVI using RGB since true NIR not available)

def compute_ndvi(image):

    img = np.array(image.convert("RGB")).astype(float)

    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]

    # fake NIR approximation (common hack in basic CV projects)
    nir = (green + red) / 2

    ndvi = (nir - red) / (nir + red + 1e-6)

    return np.mean(ndvi)

# -------------------------
# IMAGE FEATURES
# -------------------------

def analyze_image(image):

    img = np.array(image.convert("RGB"))

    red = img[:, :, 0]
    green = img[:, :, 1]

    total = img.shape[0] * img.shape[1]

    green_percent = np.sum((green > red)) / total * 100
    brown_percent = np.sum((red > green)) / total * 100

    return green_percent, brown_percent

# -------------------------
# LOGISTIC STYLE AI MODEL
# -------------------------

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# -------------------------
# UPLOAD
# -------------------------

uploaded_file = st.file_uploader(
    "📸 Upload GPS Photo",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    exif = get_exif(image)

    if "GPSInfo" not in exif:
        st.error("No GPS data found in image.")
        st.stop()

    gps = exif["GPSInfo"]

    lat = dms_to_decimal(gps[2], gps[1])
    lon = dms_to_decimal(gps[4], gps[3])

    st.success("📍 GPS Extracted")

    st.write(f"Latitude: {lat:.6f}")
    st.write(f"Longitude: {lon:.6f}")

    # -------------------------
    # WEATHER
    # -------------------------

    temp, humidity, wind = get_weather(lat, lon)

    # -------------------------
    # IMAGE ANALYSIS
    # -------------------------

    green, brown = analyze_image(image)
    ndvi = compute_ndvi(image)

    # -------------------------
    # FEATURE SCORING (AI STYLE)
    # -------------------------

    # normalize inputs
    t = temp / 40
    h = (100 - humidity) / 100
    w = wind / 50
    g = green / 100
    b = brown / 100
    n = (1 - ndvi)

    # weighted model (learned-style weights)
    raw_score = (
        1.5 * t +
        2.0 * h +
        1.2 * w +
        1.8 * b +
        1.5 * n -
        1.2 * g
    )

    risk_prob = sigmoid(raw_score) * 100

    # -------------------------
    # BREAKDOWN
    # -------------------------

    breakdown = {
        "🌡 Temperature": t * 30,
        "💧 Dryness": h * 35,
        "💨 Wind": w * 20,
        "🍂 Dry Vegetation": b * 25,
        "🛰 NDVI Dryness": n * 30,
        "🌿 Green Reduction": -g * 20
    }

    # final clamp
    risk = max(0, min(risk_prob, 100))

    # -------------------------
    # OUTPUT
    # -------------------------

    st.subheader("🧠 AI Model Breakdown (Explainable ML-style)")

    st.write("### 🌿 Inputs")
    st.write(f"🌡 Temperature: {temp}°C")
    st.write(f"💧 Humidity: {humidity}%")
    st.write(f"💨 Wind: {wind} km/h")
    st.write(f"🌿 Green: {green:.1f}%")
    st.write(f"🍂 Dry: {brown:.1f}%")
    st.write(f"🛰 NDVI Index: {ndvi:.3f}")

    st.markdown("---")

    st.write("### 📊 Feature Contributions")

    for k, v in breakdown.items():
        st.write(f"{k}: {v:.2f}")

    st.markdown("---")

    st.metric("🔥 Fire Probability", f"{risk:.1f}%")

    if risk > 75:
        st.error("🔥 EXTREME FIRE RISK")
    elif risk > 50:
        st.warning("⚠️ HIGH FIRE RISK")
    elif risk > 25:
        st.info("🟡 MODERATE RISK")
    else:
        st.success("✅ LOW RISK")
