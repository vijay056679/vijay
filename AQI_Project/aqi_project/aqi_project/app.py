"""
Flask app: Air Quality Prediction using trained XGBoost model.

Run: python app.py
Visit: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "aqi_xgboost_model.pkl"))
label_encoder = joblib.load(os.path.join(BASE_DIR, "label_encoder.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
feature_names = joblib.load(os.path.join(BASE_DIR, "feature_names.pkl"))

# Category -> display metadata (used to drive the gauge / colors / advisory text)
CATEGORY_META = {
    "Good": {
        "band": "0–50", "color": "#5ec48b", "glow": "rgba(94,196,139,0.35)",
        "needle_deg": -72,
        "advisory": "Air quality is satisfactory. Conditions pose little or no risk.",
    },
    "Moderate": {
        "band": "51–100", "color": "#d9c24a", "glow": "rgba(217,194,74,0.35)",
        "needle_deg": -36,
        "advisory": "Acceptable air quality. Unusually sensitive individuals should consider limiting prolonged outdoor exertion.",
    },
    "Unhealthy for Sensitive": {
        "band": "101–150", "color": "#e08a3c", "glow": "rgba(224,138,60,0.35)",
        "needle_deg": 0,
        "advisory": "Sensitive groups (children, elderly, respiratory/heart conditions) should reduce prolonged outdoor exertion.",
    },
    "Unhealthy": {
        "band": "151–200", "color": "#d1543f", "glow": "rgba(209,84,63,0.35)",
        "needle_deg": 36,
        "advisory": "Everyone may begin to experience health effects. Sensitive groups should avoid outdoor exertion.",
    },
    "Very Unhealthy": {
        "band": "201+", "color": "#8b3a62", "glow": "rgba(139,58,98,0.4)",
        "needle_deg": 72,
        "advisory": "Health alert: everyone may experience more serious health effects. Avoid outdoor activity.",
    },
}

FIELD_SPECS = [
    {"key": "pm2_5", "label": "PM2.5", "unit": "\u00b5g/m\u00b3", "min": 0, "max": 300, "step": 1, "default": 45},
    {"key": "pm10", "label": "PM10", "unit": "\u00b5g/m\u00b3", "min": 0, "max": 450, "step": 1, "default": 90},
    {"key": "no2", "label": "NO\u2082", "unit": "ppb", "min": 0, "max": 150, "step": 1, "default": 35},
    {"key": "so2", "label": "SO\u2082", "unit": "ppb", "min": 0, "max": 100, "step": 1, "default": 20},
    {"key": "co", "label": "CO", "unit": "ppm", "min": 0, "max": 10, "step": 0.1, "default": 2.5},
    {"key": "o3", "label": "O\u2083", "unit": "ppb", "min": 0, "max": 150, "step": 1, "default": 55},
    {"key": "temperature_c", "label": "Temperature", "unit": "\u00b0C", "min": 15, "max": 45, "step": 0.1, "default": 26},
]


@app.route("/")
def index():
    return render_template("index.html", fields=FIELD_SPECS)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)
        row = {}
        for spec in FIELD_SPECS:
            key = spec["key"]
            val = data.get(key)
            if val is None:
                return jsonify({"error": f"Missing field: {key}"}), 400
            row[key] = float(val)

        X = pd.DataFrame([row])[feature_names]
        X_scaled = scaler.transform(X)

        pred_idx = model.predict(X_scaled)[0]
        proba = model.predict_proba(X_scaled)[0]
        pred_label = label_encoder.inverse_transform([pred_idx])[0]

        probs = {
            label_encoder.inverse_transform([i])[0]: round(float(p) * 100, 2)
            for i, p in enumerate(proba)
        }
        probs = dict(sorted(probs.items(), key=lambda kv: -kv[1]))

        meta = CATEGORY_META.get(pred_label, {})

        return jsonify({
            "prediction": pred_label,
            "confidence": round(float(np.max(proba)) * 100, 2),
            "probabilities": probs,
            "band": meta.get("band"),
            "color": meta.get("color"),
            "glow": meta.get("glow"),
            "needle_deg": meta.get("needle_deg"),
            "advisory": meta.get("advisory"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
