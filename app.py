import streamlit as st
import requests
import numpy as np
from PIL import Image

import torch
from transformers import CLIPProcessor, CLIPModel

st.set_page_config(
    page_title="🔥 AI Wildfire Predictor (CLIP)",
    page_icon="🔥"
)

st.title("🔥 AI Wildfire Risk Predictor (CLIP + Weather + Satellite)")

# -------------------------
# LOAD CLIP MODEL (AI)
# -------------------------

@st.cache_resource
def load_model():

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    return model, processor


model, processor = load_model()

# -------------------------
# WEATHER
# -------------------------

def get_weather(lat, lon):

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )

    data = requests.get(url, timeout=15).json()
    c = data["current"]

    return c["temperature_2m"], c["relative_humidity_2m"], c["wind_speed_10m"]

# -------------------------
# CLIP FIRE SCORE
# -------------------------

def clip_fire_score(image):

    labels = [
        "a forest fire burning",
        "a high wildfire risk dry forest",
        "a green safe forest",
        "a wet area with water and vegetation",
        "a dry drought landscape"
    ]

    inputs = processor(
        text=labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

        logits = outputs.logits_per_image
        probs = logits.softmax(dim=1)[0]

    risk_keywords = probs[0] + probs[1] + probs[4]  # fire + dry + drought
    safe_keywords = probs[2] + probs[3]

    score = float(risk_keywords / (risk_keywords + safe_keywords)) * 100

    return round(score, 2)

# -------------------------
# FINAL RISK MODEL
# -------------------------

def final_risk(clip_score, temp, humidity, wind):

    score = clip_score * 0.6
    score += min(temp, 40) * 0.4
    score += (100 - humidity) * 0.5
    score += min(wind, 50) * 0.3

    score = score / 2.0

    return min(round(score, 1), 100)

def level(score):

    if score >= 80:
        return "EXTREME"
    elif score >= 60:
        return "HIGH"
    elif score >= 35:
        return "MODERATE"
    else:
        return "LOW"

# -------------------------
# UI
# -------------------------

uploaded_file = st.file_uploader(
    "Upload Satellite / Forest Image",
    type=["jpg", "jpeg", "png"]
)

lat = st.number_input("Latitude", value=49.0)
lon = st.number_input("Longitude", value=-122.0)

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    st.info("Running AI (CLIP model)...")

    clip_score = clip_fire_score(image)

    temp, humidity, wind = get_weather(lat, lon)

    risk = final_risk(clip_score, temp, humidity, wind)
    risk_level = level(risk)

    st.subheader("🔥 AI Results")

    st.write(f"🤖 CLIP Fire Score: {clip_score}/100")
    st.write(f"🌡 Temp: {temp}°C")
    st.write(f"💧 Humidity: {humidity}%")
    st.write(f"💨 Wind: {wind} km/h")

    st.metric("🔥 Final Wildfire Risk", f"{risk}/100")
    st.metric("Risk Level", risk_level)
