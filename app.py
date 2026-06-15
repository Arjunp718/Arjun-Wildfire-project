import streamlit as st
import requests

st.set_page_config(
    page_title="Canada Wildfire Risk Checker",
    page_icon="🔥"
)

st.title("🔥 Canada Wildfire Risk Checker")

st.write(
    "Enter any Canadian town or city to estimate wildfire risk using real weather data."
)

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

def get_weather(lat, lon):

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

def calculate_risk(temp, humidity, wind):

    score = 0

    # Temperature (35 points)
    score += min(temp, 40) / 40 * 35

    # Humidity (45 points)
    score += (100 - humidity) / 100 * 45

    # Wind (20 points)
    score += min(wind, 50) / 50 * 20

    return round(min(score, 100), 1)

if st.button("Check Wildfire Risk"):

    try:

        result = get_coordinates(town)

        if result is None:
            st.error("Canadian location not found.")
            st.stop()

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

        if risk >= 85:
            level = "EXTREME"

        elif risk >= 65:
            level = "HIGH"

        elif risk >= 35:
            level = "MODERATE"

        else:
            level = "LOW"

        st.success(f"📍 Location: {location_name}")

        st.write(f"Latitude: {lat:.4f}")
        st.write(f"Longitude: {lon:.4f}")

        st.subheader("🌤 Current Weather")

        st.write(f"🌡 Temperature: {temp} °C")
        st.write(f"💧 Humidity: {humidity}%")
        st.write(f"💨 Wind Speed: {wind} km/h")

        st.subheader("🔥 Wildfire Risk Assessment")

        st.metric(
            "Wildfire Risk Score",
            f"{risk}/100"
        )

        st.metric(
            "Risk Level",
            level
        )

        if level == "LOW":

            st.success(
                "🟢 Low wildfire danger. Conditions are generally safe."
            )

        elif level == "MODERATE":

            st.warning(
                "🟡 Moderate wildfire danger. Dry conditions may allow fires to spread."
            )

        elif level == "HIGH":

            st.warning(
                "🟠 High wildfire danger. Fires could start and spread quickly."
            )

        else:

            st.error(
                "🔴 Extreme wildfire danger. Very favorable conditions for wildfire growth."
            )

    except Exception as e:

        st.error(f"Error: {e}")
