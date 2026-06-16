import streamlit as st
import requests
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

st.set_page_config(
    page_title="🔥 Canada Wildfire Risk System",
    page_icon="🔥"
)

st.title("🔥 Canada Wildfire Risk System (Explainable AI)")

st.write("Upload a GPS-enabled photo. The system analyzes weather + image data to estimate wildfire risk.")

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
# IMAGE GPS EXTRACTION
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
# IMAGE ANALYSIS
# -------------------------

def analyze_image(image):

    img = np.array(image.convert("RGB"))

    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]

    total = img.shape[0] * img.shape[1]

    green_percent = np.sum((green > red) & (green > blue)) / total * 100
    brown_percent = np.sum((red > green) & (green > blue)) / total * 100

    return green_percent, brown_percent

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
        st.error("❌ No GPS data found in image.")
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
    # IMAGE FEATURES
    # -------------------------

    green, brown = analyze_image(image)

    # -------------------------
    # FACTOR MODEL
    # -------------------------

    factors = {}

    # 🌡 Temperature
    factors["Temperature"] = min(temp, 40) / 40 * 30

    # 💧 Dryness
    factors["Dryness"] = (100 - humidity) / 100 * 35

    # 💨 Wind
    factors["Wind"] = min(wind, 50) / 50 * 20

    # 🌿 Green reduces risk
    factors["Green Cover"] = -(green / 100) * 20

    # 🍂 Dry vegetation increases risk
    factors["Dry Vegetation"] = (brown / 100) * 25

    # 🌳 density adjustment
    if green > 60:
        factors["Density"] = -10
    elif green < 30:
        factors["Density"] = 10
    else:
        factors["Density"] = 0

    # -------------------------
    # FINAL RISK
    # -------------------------

    risk = sum(factors.values())
    risk = max(0, min(risk, 100))

    # -------------------------
    # OUTPUT
    # -------------------------

    st.subheader("📊 Wildfire Risk Breakdown (Explainable AI)")

    st.write("### 🌿 Image + Weather Inputs")
    st.write(f"🌡 Temperature: {temp}°C")
    st.write(f"💧 Humidity: {humidity}%")
    st.write(f"💨 Wind: {wind} km/h")
    st.write(f"🌿 Green Vegetation: {green:.1f}%")
    st.write(f"🍂 Dry Vegetation: {brown:.1f}%")

    st.markdown("---")

    st.write("### 🧠 Factor Contributions")

    for k, v in factors.items():
        if v >= 0:
            st.write(f"{k}: +{v:.1f}")
        else:
            st.write(f"{k}: {v:.1f}")

    st.markdown("---")

    st.metric("🔥 Final Wildfire Risk Score", f"{risk:.1f}/100")

    if risk >= 75:
        st.error("🔥 EXTREME FIRE RISK")
    elif risk >= 50:
        st.warning("⚠️ HIGH FIRE RISK")
    elif risk >= 25:
        st.info("🟡 MODERATE RISK")
    else:
        st.success("✅ LOW RISK")
