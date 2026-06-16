import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load NASA FIRMS data
data = pd.read_csv("fires_data.csv")
# Remove rows with missing values
data = data.dropna(subset=["brightness", "confidence", "frp"])

# Features
X = data[["brightness", "confidence", "frp"]]

# Target wildfire intensity score
y = (
    data["brightness"] * 0.5 +
    data["confidence"] * 0.2 +
    data["frp"] * 0.3
)

# Train model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

# Save model
joblib.dump(model, "fire_model.pkl")

print("Model trained and saved!")
