import streamlit as st
import numpy as np
import requests
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="🔥 Wildfire AI Model", page_icon="🔥")

st.title("🔥 Wildfire Risk AI System (ML + Satellite Style)")

st.write("AI model using weather + vegetation index to estimate wildfire probability.")

# -------------------------
# WEATHER
# -------------------------

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )

    data = requests.get(url).json()["current"]

    return (
        data["temperature_2m"],
        data["relative_humidity_2m"],
        data["wind_speed_10m"]
    )

# -------------------------
# IMAGE → VEGETATION INDEX (NDVI-STYLE)
# -------------------------

def vegetation_index(image):

    img = np.array(image.convert("RGB")).astype(float)

    red = img[:, :, 0]
    green = img[:, :, 1]

    # NDVI-like approximation (no NIR available)
    vi = (green - red) / (green + red + 1e-6)

    return np.mean(vi)

# -------------------------
# TRAIN SYNTHETIC MODEL (SCALABLE BASELINE)
# -------------------------

@st.cache_resource
def train_model():

    np.random.seed(42)

    # synthetic dataset (replace later with NASA FIRMS + NDVI)
    n = 3000

    temp = np.random.uniform(5, 40, n)
    humidity = np.random.uniform(10, 100, n)
    wind = np.random.uniform(0, 50, n)
    vi = np.random.uniform(-0.5, 0.8, n)

    # fire probability logic (training ground truth)
    prob = (
        (temp / 40) * 0.3 +
        ((100 - humidity) / 100) * 0.3 +
        (wind / 50) * 0.2 +
        ((1 - vi)) * 0.2
    )

    y = (prob > 0.55).astype(int)

    X = np.column_stack([temp, humidity, wind, vi])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    return model

model = train_model()

# -------------------------
# INPUT
# -------------------------

uploaded_file = st.file_uploader("📸 Upload Image", type=["jpg", "jpeg", "png"])

lat = st.number_input("Latitude", value=49.2)
lon = st.number_input("Longitude", value=-122.9)

if uploaded_file:

    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    # -------------------------
    # FEATURES
    # -------------------------

    temp, humidity, wind = get_weather(lat, lon)
    vi = vegetation_index(image)

    features = np.array([[temp, humidity, wind, vi]])

    # -------------------------
    # PREDICTION (REAL ML PROBABILITY)
    # -------------------------

    prob = model.predict_proba(features)[0][1] * 100

    pred = model.predict(features)[0]

    # -------------------------
    # EXPLANATION (IMPORTANCE STYLE)
    # -------------------------

    st.subheader("📊 Inputs")

    st.write(f"🌡 Temperature: {temp:.1f}°C")
    st.write(f"💧 Humidity: {humidity:.1f}%")
    st.write(f"💨 Wind: {wind:.1f} km/h")
    st.write(f"🌿 Vegetation Index: {vi:.3f}")

    st.markdown("---")

    st.subheader("🤖 AI Prediction")

    st.metric("🔥 Fire Probability", f"{prob:.1f}%")

    if prob > 70:
        st.error("🔥 HIGH FIRE RISK")
    elif prob > 40:
        st.warning("⚠️ MODERATE RISK")
    else:
        st.success("✅ LOW RISK")

    # -------------------------
    # FEATURE CONTRIBUTION (EXPLAINABILITY)
    # -------------------------

    st.subheader("🧠 What the model is using")

    st.write("🌡 Higher temperature → increases risk")
    st.write("💧 Lower humidity → increases dryness risk")
    st.write("💨 Higher wind → spreads fire faster")
    st.write("🌿 Lower vegetation index → drier land")

    st.markdown("---")

    st.write("⚙️ Model Type: Random Forest Classifier")
    st.write("📈 Output: probability via predict_proba()")
