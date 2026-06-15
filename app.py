import streamlit as st
import requests
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS

st.set_page_config(
    page_title="Canada Wildfire Risk System",
    page_icon="🔥"
)

st.title("🔥 Canada Wildfire Risk System")

tab1, tab2 = st.tabs([
    "📍 Town Risk Checker",
    "📸 Photo Analyzer"
])

# --------------------------
# COMMON FUNCTIONS
# --------------------------

def calculate_risk(temp, humidity, wind):

    score = 0
    score += min(temp, 40) / 40 * 35
    score += (100 - humidity) / 100 * 45
    score += min(wind, 50) / 50 * 20

    return round(min(score, 100), 1)


def risk_level(score):

    if score >= 85:
        return "EXTREME"
    elif score >= 65:
        return "HIGH"
    elif score >= 35:
        return "MODERATE"
    else:
        return "LOW"


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

    current = data["current"]

    return (
        current["temperature_2m"],
        current["relative_humidity_2m"],
        current["wind_speed_10m"]
    )

# --------------------------
# TAB 1 - TOWN CHECKER
# --------------------------

with tab1:

    st.header("📍 Town Risk Checker")

    town = st.text_input("Enter a Canadian town", "New Westminster")

    def get_coordinates(city):

        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}"
            "&count=1"
            "&language=en"
            "&format=json"
            "&countryCode=CA"
        )

        data = requests.get(url, timeout=15).json()

        if "results" not in data:
            return None

        r = data["results"][0]

        return r["latitude"], r["longitude"], r["name"]

    if st.button("Check Town Risk"):

        result = get_coordinates(town)

        if result is None:
            st.error("Location not found")
        else:

            lat, lon, name = result
            temp, humidity, wind = get_weather(lat, lon)

            risk = calculate_risk(temp, humidity, wind)
            level = risk_level(risk)

            st.success(f"📍 {name}")

            st.write(f"🌡 Temp: {temp}°C")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"💨 Wind: {wind} km/h")

            st.metric("Risk Score", f"{risk}/100")
            st.metric("Risk Level", level)

# --------------------------
# TAB 2 - PHOTO ANALYZER
# --------------------------

with tab2:

    st.header("📸 Photo Analyzer")

    uploaded_file = st.file_uploader(
        "Upload photo with GPS data",
        type=["jpg", "jpeg", "png"]
    )

    def get_exif(image):

        exif = {}
        info = image._getexif()

        if info:
            for tag, value in info.items():
                exif[TAGS.get(tag, tag)] = value

        return exif


    def dms_to_decimal(dms, ref):

        deg = float(dms[0])
        minutes = float(dms[1])
        sec = float(dms[2])

        dec = deg + minutes / 60 + sec / 3600

        if ref in ["S", "W"]:
            dec *= -1

        return dec


    def analyze_vegetation(image):

        img = np.array(image.convert("RGB"))

        red = img[:, :, 0]
        green = img[:, :, 1]
        blue = img[:, :, 2]

        green_pixels = np.sum((green > red) & (green > blue))
        brown_pixels = np.sum((red > green) & (green > blue))

        total = img.shape[0] * img.shape[1]

        return (
            (green_pixels / total) * 100,
            (brown_pixels / total) * 100
        )


    def vegetation_density(green):

        if green > 60:
            return "Dense"
        elif green > 30:
            return "Moderate"
        else:
            return "Sparse"


    if uploaded_file:

        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

        exif = get_exif(image)

        if "GPSInfo" not in exif:
            st.error("No GPS data found in image")
        else:

            gps = exif["GPSInfo"]

            lat = dms_to_decimal(gps[2], gps[1])
            lon = dms_to_decimal(gps[4], gps[3])

            st.success("📍 GPS Location Extracted")

            st.write(f"Latitude: {lat:.6f}")
            st.write(f"Longitude: {lon:.6f}")

            temp, humidity, wind = get_weather(lat, lon)

            green, brown = analyze_vegetation(image)
            density = vegetation_density(green)

            risk = calculate_risk(temp, humidity, wind)

            if brown > 20:
                risk += 10
            elif brown > 10:
                risk += 5

            risk = min(risk, 100)
            level = risk_level(risk)

            st.write(f"🌿 Green: {green:.1f}%")
            st.write(f"🍂 Dry: {brown:.1f}%")
            st.write(f"🌳 Density: {density}")

            st.write(f"🌡 Temp: {temp}°C")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"💨 Wind: {wind} km/h")

            st.metric("Risk Score", f"{risk}/100")
            st.metric("Risk Level", level)
