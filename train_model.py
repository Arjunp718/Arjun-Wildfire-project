import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

# -------------------------
# LOAD NASA FIRMS DATA (CSV YOU DOWNLOAD)
# -------------------------
# Download from:
# https://firms.modaps.eosdis.nasa.gov/

data = pd.read_csv("fires.csv")

# Expected columns (NASA FIRMS typical):
# latitude, longitude, brightness, acq_date

# -------------------------
# SYNTHETIC WEATHER + NDVI ENRICHMENT (SIMULATION STEP)
# -------------------------

np.random.seed(42)

n = len(data)

data["temp"] = np.random.uniform(10, 40, n)
data["humidity"] = np.random.uniform(10, 100, n)
data["wind"] = np.random.uniform(0, 50, n)
data["ndvi"] = np.random.uniform(-0.3, 0.8, n)

# -------------------------
# LABEL (FIRE = 1 from NASA FIRMS)
# -------------------------

data["fire"] = 1

# create negative samples (no fire)
neg = data.sample(n)

neg["fire"] = 0
neg["temp"] *= np.random.uniform(0.5, 0.9)
neg["humidity"] *= np.random.uniform(1.0, 1.2)
neg["wind"] *= np.random.uniform(0.5, 1.0)
neg["ndvi"] *= np.random.uniform(1.0, 1.2)

full = pd.concat([data, neg])

# -------------------------
# TRAIN MODEL
# -------------------------

X = full[["temp", "humidity", "wind", "ndvi"]]
y = full["fire"]

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

model.fit(X, y)

joblib.dump(model, "fire_model.pkl")

print("Model trained and saved!")
