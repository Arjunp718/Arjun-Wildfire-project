import streamlit as st
from geopy.geocoders import Nominatim
import requests

st.title("🔥 Canada Wildfire Risk Checker")

town = st.text_input(
    "Enter a Canadian town or city",
    "New Westminster"
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

    data = requests.get(url).json()

    current = data["current"]

    return (
        current["temperature_2m"],
        current["relative_humidity_2m"],
        current["wind_speed_10m"]
    )

def calculate_risk(temp, humidity, wind):

    score = 0

    score += min(temp, 40) / 40 * 50

    score += (100 - humidity) / 100 * 30

    score += min(wind, 50) / 50 * 20

    return round(min(score, 100), 1)

if st.button("Check Risk"):

    try:

        geolocator = Nominatim(
            user_agent="wildfire_checker",
            timeout=10
        )

        location = geolocator.geocode(
            f"{town}, Canada"
        )

        if location is None:

            st.error("Location not found.")
            st.stop()

        lat = location.latitude
        lon = location.longitude

        temp, humidity, wind = get_weather(
            lat,
            lon
        )

        risk = calculate_risk(
            temp,
            humidity,
            wind
        )

        if risk >= 75:
            level = "EXTREME"
        elif risk >= 50:
            level = "HIGH"
        elif risk >= 25:
            level = "MODERATE"
        else:
            level = "LOW"

        st.success(
            f"📍 {town}"
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

        st.error(
            f"Error: {e}"
        )
