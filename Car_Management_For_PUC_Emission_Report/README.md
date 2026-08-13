# 🚗 PUC Emission Fault Classifier
### XGBoost · Flask · Real-time Diagnosis

---

## Project Structure

```
Car_Management_For_PUC_Emission_Report/
├── train_model.py          ← XGBoost training script (run this first)
├── app.py                  ← Flask web application
├── emission_model.pkl      ← Saved model (auto-generated)
├── requirements.txt        ← Python dependencies
├── templates/
│   └── index.html          ← Web UI with injected CSS
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the XGBoost model
```bash
python train_model.py
```
Expected output:
```
Train Accuracy : 91.xx%
Test  Accuracy : 91.xx%
Gap (overfit?) : <2%   ← healthy
CV (5-fold)    : 91.xx% ± 0.xx%
✅  Model saved → emission_model.pkl
```

### 3. Run the Flask app
```bash
python app.py
```
Open → **http://localhost:5000**

---

## Model Architecture

| Parameter | Value |
|---|---|
| Algorithm | `XGBoost` (multi:softmax) |
| n_estimators | ~300–600 (early stopping) |
| Learning rate | 0.05 |
| Max depth | 8 |
| Subsample | 0.85 (anti-overfit) |
| colsample_bytree | 0.80 (anti-overfit) |
| reg_alpha (L1) | 0.2 |
| reg_lambda (L2) | 1.5 |
| min_child_weight | 10 |
| gamma | 0.05 |

---

## Feature Engineering (30 features)

Raw PUC readings → 30 engineered features:
- **Raw**: CO, HC, NOx, PM, O2, Lambda + Fuel/Standard encodings
- **Ratios**: CO/O2, HC/NOx, NOx/PM, CO/HC, PM/HC (combustion efficiency)
- **Products**: CO×Lambda, HC×O2, NOx×Lambda, PM×CO (fault interaction)
- **Squares**: HC², CO², Lambda² (non-linear patterns)
- **Bins**: HC zone, NOx zone, PM zone, Lambda zone (threshold detection)

---

## Target Classes (10)

| Issue | Severity | Primary Signal |
|---|---|---|
| Normal | ✅ OK | HC<200, NOx<0.05 |
| Air Filter Clogged | ⚠️ Medium | HC≈350, elevated CO |
| DPF Clogging | 🚨 High | High PM (diesel) |
| EGR Valve Problem | 🚨 High | High NOx |
| Engine Misfire | 🚨 High | HC≈550, high O2 |
| Fuel Injector Issue | ⚠️ Medium | Rich mix, λ<1 |
| Injector Problem | ⚠️ Medium | HC≈376, NOx≈0.17 |
| Rich Fuel Mixture | ⚠️ Medium | High CO, λ<0.9 |
| Spark Plug Issue | ⚠️ Medium | HC≈550, high O2 |
| Turbocharger Issue | 🚨 High | HC≈376, NOx≈0.17 |

---

## Anti-Overfitting Measures

1. **Early stopping** (40 rounds no improvement on validation set)
2. **Row subsampling** — 85% of rows per tree
3. **Feature subsampling** — 80% of features per tree/level
4. **L1 + L2 regularisation** — penalises complex trees
5. **min_child_weight=10** — prevents tiny leaf nodes
6. **gamma=0.05** — minimum gain threshold for splits
7. **5-fold cross-validation** — verifies generalisation

Expected train/test gap: **< 3%** (no overfitting).