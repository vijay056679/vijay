from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import os

app = Flask(__name__)

# ── Load model ─────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "emission_model.pkl")

with open(MODEL_PATH, "rb") as f:
    payload = pickle.load(f)

model      = payload["model"]
le_issue   = payload["label_enc"]
FEATURES   = payload["features"]
CLASSES    = payload["classes"]
TRAIN_ACC  = payload.get("train_acc", "N/A")
TEST_ACC   = payload.get("test_acc",  "N/A")
CV_MEAN    = payload.get("cv_mean",   "N/A")


# ── Feature builder (must match train_model.py exactly) ────────────────────
def build_features(fuel_type: str, emission_standard: str,
                   CO: float, HC: float, NOx: float,
                   PM: float, O2: float, Lambda: float) -> np.ndarray:
    import pandas as pd

    Fuel_enc     = 1 if fuel_type == "Petrol" else 0
    Std_enc      = 1 if emission_standard == "BS6" else 0
    Fuel_Std_enc = Fuel_enc * 2 + Std_enc

    Lambda_dev   = abs(Lambda - 1.0)
    Lambda_sign  = np.sign(Lambda - 1.0)
    CO_O2_ratio  = CO  / (O2  + 1e-3)
    HC_NOx_ratio = HC  / (NOx + 1e-3)
    NOx_PM_ratio = NOx / (PM  + 1e-5)
    CO_HC_ratio  = CO  / (HC  + 1e-3)
    PM_HC_ratio  = PM  / (HC  + 1e-3)
    CO_x_Lambda  = CO  * Lambda
    HC_x_O2      = HC  * O2
    NOx_x_Lambda = NOx * Lambda
    PM_x_CO      = PM  * CO
    HC_x_NOx     = HC  * NOx
    O2_x_Lambda  = O2  * Lambda
    HC_sq        = HC  ** 2
    CO_sq        = CO  ** 2
    Lambda_sq    = Lambda ** 2

    # binned zones
    HC_zone = (0 if HC <= 200 else 1 if HC <= 400 else 2 if HC <= 500 else 3 if HC <= 600 else 4)
    NOx_zone = (0 if NOx <= 0.05 else 1 if NOx <= 0.12 else 2 if NOx <= 0.16 else 3)
    PM_zone  = (0 if PM <= 0.003 else 1 if PM <= 0.01 else 2 if PM <= 0.015 else 3)
    Lambda_zone = (0 if Lambda <= 0.90 else 1 if Lambda <= 0.99 else 2 if Lambda <= 1.01 else 3 if Lambda <= 1.10 else 4)

    row = [
        Fuel_enc, Std_enc, Fuel_Std_enc,
        CO, HC, NOx, PM, O2, Lambda,
        Lambda_dev, Lambda_sign, CO_O2_ratio, HC_NOx_ratio,
        NOx_PM_ratio, CO_HC_ratio, PM_HC_ratio,
        CO_x_Lambda, HC_x_O2, NOx_x_Lambda, PM_x_CO, HC_x_NOx, O2_x_Lambda,
        HC_sq, CO_sq, Lambda_sq,
        HC_zone, NOx_zone, PM_zone, Lambda_zone,
    ]
    return np.array(row, dtype=float).reshape(1, -1)


# ── Issue metadata ──────────────────────────────────────────────────────────
ISSUE_INFO = {
    "Normal": {
        "icon": "✅", "severity": "ok",
        "desc": "All emission parameters are within acceptable PUC limits.",
        "action": "No action required. Schedule next PUC check as per regulations."
    },
    "Air Filter Clogged": {
        "icon": "🌬️", "severity": "medium",
        "desc": "Restricted airflow causing elevated HC and CO due to rich mixture.",
        "action": "Replace air filter. Check intake manifold for blockages."
    },
    "DPF Clogging": {
        "icon": "🏭", "severity": "high",
        "desc": "Diesel Particulate Filter is clogged, raising PM emissions significantly.",
        "action": "Perform DPF regeneration or replace DPF. Use diesel with ULSD specification."
    },
    "EGR Valve Problem": {
        "icon": "🔄", "severity": "high",
        "desc": "Exhaust Gas Recirculation valve malfunction causing elevated NOx.",
        "action": "Clean or replace EGR valve. Inspect EGR cooler and vacuum lines."
    },
    "Engine Misfire": {
        "icon": "⚡", "severity": "high",
        "desc": "Incomplete combustion causing high HC spike and O2 presence in exhaust.",
        "action": "Check spark plugs, ignition coils, and fuel injectors. Run diagnostic scan."
    },
    "Fuel Injector Issue": {
        "icon": "💧", "severity": "medium",
        "desc": "Injector delivering incorrect fuel quantity — rich mixture pattern detected.",
        "action": "Clean or replace fuel injectors. Check fuel pressure and fuel pump."
    },
    "Injector Problem": {
        "icon": "⚙️", "severity": "medium",
        "desc": "Injector timing/flow issue affecting combustion efficiency.",
        "action": "Perform injector calibration test. Replace faulty injector(s)."
    },
    "Rich Fuel Mixture": {
        "icon": "🔥", "severity": "medium",
        "desc": "Excess fuel in air-fuel mixture causing high CO and HC emissions.",
        "action": "Check O2 sensor, MAF sensor, and fuel pressure regulator."
    },
    "Spark Plug Issue": {
        "icon": "🔌", "severity": "medium",
        "desc": "Worn or fouled spark plugs causing misfires and elevated HC.",
        "action": "Replace spark plugs. Inspect ignition leads and distributor cap."
    },
    "Turbocharger Issue": {
        "icon": "🌀", "severity": "high",
        "desc": "Turbocharger fault affecting air delivery and combustion pressure.",
        "action": "Inspect turbo for oil leaks, blade wear. Check boost pressure and intercooler."
    },
}

SEVERITY_LABELS = {"ok": "PASS", "medium": "WARNING", "high": "FAIL"}


# ── Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
                           classes=CLASSES,
                           train_acc=TRAIN_ACC,
                           test_acc=TEST_ACC,
                           cv_mean=CV_MEAN)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        fuel_type  = data["fuel_type"]
        emission_std = data["emission_standard"]
        CO     = float(data["CO"])
        HC     = float(data["HC"])
        NOx    = float(data["NOx"])
        PM     = float(data["PM"])
        O2     = float(data["O2"])
        Lambda = float(data["Lambda"])

        X = build_features(fuel_type, emission_std, CO, HC, NOx, PM, O2, Lambda)

        # Prediction
        pred_enc  = model.predict(X)[0]
        pred_label = le_issue.inverse_transform([pred_enc])[0]

        # Probabilities
        proba = model.predict_proba(X)[0]
        top_n = sorted(enumerate(proba), key=lambda x: -x[1])[:5]
        top_issues = [
            {"label": le_issue.inverse_transform([i])[0], "prob": round(float(p)*100, 1)}
            for i, p in top_n
        ]

        info = ISSUE_INFO.get(pred_label, {
            "icon": "❓", "severity": "medium",
            "desc": "Issue detected.", "action": "Consult a mechanic."
        })

        return jsonify({
            "success": True,
            "issue": pred_label,
            "icon": info["icon"],
            "severity": info["severity"],
            "severity_label": SEVERITY_LABELS[info["severity"]],
            "description": info["desc"],
            "action": info["action"],
            "top_issues": top_issues,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/sample/<issue_type>")
def sample(issue_type):
    """Return realistic sample values for a given issue type."""
    samples = {
        "Normal":             {"CO":0.20,"HC":120,"NOx":0.025,"PM":0.0018,"O2":0.50,"Lambda":1.00},
        "Air Filter Clogged": {"CO":0.55,"HC":350,"NOx":0.140,"PM":0.0090,"O2":0.55,"Lambda":1.05},
        "DPF Clogging":       {"CO":0.55,"HC":355,"NOx":0.141,"PM":0.0091,"O2":0.55,"Lambda":1.05},
        "EGR Valve Problem":  {"CO":0.55,"HC":352,"NOx":0.142,"PM":0.0090,"O2":0.55,"Lambda":1.05},
        "Engine Misfire":     {"CO":0.55,"HC":550,"NOx":0.100,"PM":0.0060,"O2":0.70,"Lambda":1.15},
        "Spark Plug Issue":   {"CO":0.55,"HC":550,"NOx":0.100,"PM":0.0060,"O2":0.70,"Lambda":1.15},
        "Fuel Injector Issue":{"CO":0.70,"HC":450,"NOx":0.130,"PM":0.0125,"O2":0.35,"Lambda":0.83},
        "Rich Fuel Mixture":  {"CO":0.70,"HC":450,"NOx":0.130,"PM":0.0125,"O2":0.35,"Lambda":0.83},
        "Injector Problem":   {"CO":0.55,"HC":376,"NOx":0.175,"PM":0.0175,"O2":0.60,"Lambda":0.97},
        "Turbocharger Issue": {"CO":0.55,"HC":376,"NOx":0.175,"PM":0.0175,"O2":0.60,"Lambda":0.97},
    }
    vals = samples.get(issue_type, samples["Normal"])
    return jsonify(vals)


if __name__ == "__main__":
    print(f"\n🚗 Emission Fault Classifier ready")
    print(f"   Model test accuracy : {TEST_ACC}%")
    print(f"   Open → http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)