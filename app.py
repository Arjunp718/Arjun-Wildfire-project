import streamlit as st
import requests
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim

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

```
score = 0

score += min(temp, 40) / 40 * 35
score += (100 - humidity) / 100 * 45
score += min(wind, 50) / 50 * 20

return round(min(score, 100), 1)
```

def risk_level(score):

```
if score >= 85:
    return "EXTREME"

elif score >= 65:
    return "HIGH"

elif score >= 35:
    return "MODERATE"

else:
    return "LOW"
```

def get_weather(lat, lon):

```
url = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}"
    f"&longitude={lon}"
    f"&current=temperature_2m,"
    f"relative_humidity_2m,"
    f"wind_speed_10m"
)

response = requests.get(url, timeout=15)

data = response.json()

current = data["current"]

return (
    current["temperature_2m"],
    current["relative_humidity_2m"],
    current["wind_speed_10m"]
)
```

# --------------------------

# TAB 1

# --------------------------

with tab1:

```
st.header("📍 Town Risk Checker")

town = st.text_input(
    "Enter a Canadian town or city",
    "New Westminster"
)

def get_coordinates(city):

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}"
        "&count=1"
        "&language=en"
        "&format=json"
        "&countryCode=CA"
    )

    response = requests.get(url, timeout=15)

    data = response.json()

    if "results" not in data:
        return None

    result = data["results"][0]

    return (
        result["latitude"],
        result["longitude"],
        result["name"]
    )

if st.button("Check Town Risk"):

    try:

        result = get_coordinates(town)

        if result is None:

            st.error("Canadian location not found.")

        else:

            lat, lon, location_name = result

            temp, humidity, wind = get_weather(
                lat,
                lon
            )

            risk = calculate_risk(
                temp,
                humidity,
                wind
            )

            level = risk_level(risk)

            st.success(
                f"📍 Location: {location_name}"
            )

            st.write(f"🌡 Temperature: {temp}°C")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"💨 Wind Speed: {wind} km/h")

            st.metric(
                "Wildfire Risk Score",
                f"{risk}/100"
            )

            st.metric(
                "Risk Level",
                level
            )

    except Exception as e:

        st.error(f"Error: {e}")
```

# --------------------------

# TAB 2

# --------------------------

with tab2:

```
st.header("📸 Photo Analyzer")

uploaded_file = st.file_uploader(
    "Upload a GPS-tagged photo",
    type=["jpg", "jpeg", "png"]
)

def get_exif_data(image):

    exif = {}

    info = image._getexif()

    if info:

        for tag, value in info.items():

            decoded = TAGS.get(tag, tag)

            exif[decoded] = value

    return exif

def dms_to_decimal(dms, ref):

    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])

    decimal = degrees + minutes / 60 + seconds / 3600

    if ref in ["S", "W"]:
        decimal *= -1

    return decimal

def analyze_vegetation(image):

    img = np.array(
        image.convert("RGB")
    )

    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]

    green_pixels = np.sum(
        (green > red) &
        (green > blue)
    )

    brown_pixels = np.sum(
        (red > green) &
        (green > blue)
    )

    total_pixels = (
        img.shape[0] * img.shape[1]
    )

    green_percent = (
        green_pixels / total_pixels
    ) * 100

    brown_percent = (
        brown_pixels / total_pixels
    ) * 100

    return green_percent, brown_percent

def vegetation_density(green_percent):

    if green_percent > 60:
        return "Dense"

    elif green_percent > 30:
        return "Moderate"

    else:
        return "Sparse"

if uploaded_file:

    try:

        image = Image.open(
            uploaded_file
        )

        st.image(
            image,
            caption="Uploaded Photo",
            use_container_width=True
        )

        exif = get_exif_data(image)

        if "GPSInfo" not in exif:

            st.error(
                "No GPS location found in this image."
            )

        else:

            gps = exif["GPSInfo"]

            lat = dms_to_decimal(
                gps[2],
                gps[1]
            )

            lon = dms_to_decimal(
                gps[4],
                gps[3]
            )

            geolocator = Nominatim(
                user_agent="wildfire_detector",
                timeout=10
            )

            location = geolocator.reverse(
                f"{lat}, {lon}"
            )

            town_name = "Unknown"

            if location:

                address = location.raw["address"]

                town_name = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or "Unknown"
                )

            green_percent, brown_percent = (
                analyze_vegetation(image)
            )

            density = vegetation_density(
                green_percent
            )

            temp, humidity, wind = get_weather(
                lat,
                lon
            )

            risk = calculate_risk(
                temp,
                humidity,
                wind
            )

            if brown_percent > 20:
                risk += 10

            elif brown_percent > 10:
                risk += 5

            risk = min(risk, 100)

            level = risk_level(risk)

            st.success(
                f"📍 Photo taken near: {town_name}"
            )

            st.write(
                f"🌿 Green Vegetation: {green_percent:.1f}%"
            )

            st.write(
                f"🍂 Dry Vegetation: {brown_percent:.1f}%"
            )

            st.write(
                f"🌳 Vegetation Density: {density}"
            )

            st.write(
                f"🌡 Temperature: {temp}°C"
            )

            st.write(
                f"💧 Humidity: {humidity}%"
            )

            st.write(
                f"💨 Wind Speed: {wind} km/h"
            )

            st.metric(
                "Wildfire Risk Score",
                f"{risk:.1f}/100"
            )

            st.metric(
                "Risk Level",
                level
            )

    except Exception as e:

        st.error(f"Error: {e}")
```

```
```
