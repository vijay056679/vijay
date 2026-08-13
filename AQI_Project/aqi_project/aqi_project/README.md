# Station 7 — Air Quality Prediction (XGBoost + Flask)

## Setup

```bash
pip install -r requirements.txt
```

## Files

- `generate_dataset.py` — builds the 50,000-row realistic dataset (`air_quality_dataset_50000.csv`) using EPA-style breakpoint logic per pollutant, with sensor-noise and label-noise so classes overlap realistically (not a trivial lookup table).
- `train_model.py` — **the real XGBoost training script.** Run this after `pip install xgboost` to train and save the actual XGBoost model. Uses regularization (subsample, colsample_bytree, reg_alpha/reg_lambda, early stopping) to prevent overfitting.
- `train_model_sandbox.py` — a stand-in version using `GradientBoostingClassifier`, used only because the sandbox this was built in has no network access to install `xgboost`. Same data, same split logic, same regularization philosophy. **You don't need this file if you run `train_model.py` locally.**
- `app.py` — Flask backend, loads the saved `.pkl` artifacts and serves `/` (UI) and `/predict` (JSON API).
- `templates/index.html` — the frontend (instrument-panel / monitoring-station themed UI, CSS embedded).
- `aqi_xgboost_model.pkl`, `label_encoder.pkl`, `scaler.pkl`, `feature_names.pkl` — trained model artifacts, currently produced by the sandbox script. **Retrain with `train_model.py` to get real XGBoost artifacts** (drop-in replacement, same filenames, `app.py` needs no changes).

## To get the real XGBoost model

```bash
pip install xgboost
python train_model.py
```

This overwrites the four `.pkl` files with real XGBoost artifacts. `app.py` will pick them up automatically — no code changes needed.

## Run the app

```bash
python app.py
```

Visit `http://127.0.0.1:5000`.

## Model performance (current artifacts)

- Test accuracy: ~92.9%
- Train/test gap: <0.5% (no overfitting)
- 5-fold CV: 93.1% ± 0.4%
- Balanced precision/recall across all 5 AQI classes (Good, Moderate, Unhealthy for Sensitive, Unhealthy, Very Unhealthy)

## Features used

`pm2_5`, `pm10`, `no2`, `so2`, `co`, `o3`, `temperature_c`
