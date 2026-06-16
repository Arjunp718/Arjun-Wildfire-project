import streamlit as st
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

st.set_page_config(
    page_title="🔥 AI Wildfire Vision System",
    page_icon="🔥"
)

st.title("🔥 AI Wildfire Vision System (CLIP Image AI)")

st.write("Upload an image and the AI will analyze wildfire risk from visual patterns.")

# -------------------------
# LOAD AI MODEL
# -------------------------

@st.cache_resource
def load_model():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

model, processor = load_model()

# -------------------------
# AI FUNCTION
# -------------------------

def clip_fire_score(image):

    labels = [
        "a forest fire burning",
        "a dry forest with wildfire risk",
        "a healthy green forest",
        "a wet forest with water",
        "a drought damaged landscape"
    ]

    inputs = processor(
        text=labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)[0]

    fire_risk = probs[0] + probs[1] + probs[4]
    safe = probs[2] + probs[3]

    score = float(fire_risk / (fire_risk + safe)) * 100

    return round(score, 2), probs

# -------------------------
# UI
# -------------------------

uploaded_file = st.file_uploader(
    "📸 Upload Image (Satellite / Forest / Fire Area)",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    image = Image.open(uploaded_file)

    # Show image clearly
    st.image(image, caption="🖼️ Input Image (Used by AI Model)", use_container_width=True)

    st.info("🤖 AI is analyzing image using CLIP vision model...")

    score, probs = clip_fire_score(image)

    # -------------------------
    # DISPLAY AI UNDERSTANDING
    # -------------------------

    st.subheader("🧠 AI Vision Understanding")

    st.write("The AI compares your image with these concepts:")

    st.write("🔥 Fire / Dry Risk Concepts")
    st.write("- Forest fire burning")
    st.write("- Dry forest / drought landscape")

    st.write("🌿 Safe Concepts")
    st.write("- Green healthy forest")
    st.write("- Wet forest with water")

    # show probabilities
    st.subheader("📊 Model Confidence")

    st.write(f"🔥 Fire Detection Confidence: {probs[0]*100:.1f}%")
    st.write(f"🌾 Dry Risk Confidence: {probs[1]*100:.1f}%")
    st.write(f"🌵 Drought Confidence: {probs[4]*100:.1f}%")
    st.write(f"🌿 Green Forest Confidence: {probs[2]*100:.1f}%")
    st.write(f"💧 Wet Area Confidence: {probs[3]*100:.1f}%")

    # final score
    st.subheader("🔥 Final AI Wildfire Risk Score")

    st.metric("Risk Score", f"{score}/100")

    if score > 75:
        st.error("🔥 HIGH WILDFIRE RISK DETECTED (AI Prediction)")
    elif score > 50:
        st.warning("⚠️ MODERATE WILDFIRE RISK")
    else:
        st.success("✅ LOW WILDFIRE RISK")

    # proof AI is using image
    st.caption("✔ This prediction is generated directly from image pixel analysis using a CLIP vision-language AI model.")
