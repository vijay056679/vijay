"""
Train an XGBoost classifier on the Air Quality dataset.

Run this locally after: pip install xgboost scikit-learn pandas joblib

Outputs:
  - aqi_xgboost_model.pkl   (trained model, ready for inference)
  - label_encoder.pkl        (maps class names <-> integer labels)
  - scaler.pkl                (feature scaler used at inference time)
  - feature_names.pkl         (column order expected by the model)
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)

# XGBoost import (the real thing — use this locally)
from xgboost import XGBClassifier

RANDOM_STATE = 42

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------
df = pd.read_csv("air_quality_dataset_50000.csv")

FEATURES = ["pm2_5", "pm10", "no2", "so2", "co", "o3", "temperature_c"]
TARGET = "air_quality"

X = df[FEATURES].copy()
y_raw = df[TARGET].copy()

# ------------------------------------------------------------------
# 2. Encode labels
# ------------------------------------------------------------------
le = LabelEncoder()
y = le.fit_transform(y_raw)
print("Classes:", list(le.classes_))

# ------------------------------------------------------------------
# 3. Train / validation / test split (stratified to preserve class ratios)
#    70% train, 15% validation, 15% test — validation is used for early
#    stopping / hyperparameter checks, test is only touched once at the end.
# ------------------------------------------------------------------
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
)

print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")

# ------------------------------------------------------------------
# 4. Feature scaling (tree models don't strictly need it, but keeping it
#    makes the pipeline consistent if you later swap in other model types,
#    and the Flask app expects scaled input for consistency)
# ------------------------------------------------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# ------------------------------------------------------------------
# 5. Train XGBoost with regularization to prevent overfitting:
#    - max_depth kept moderate (not too deep -> less memorization)
#    - subsample / colsample_bytree < 1.0 -> each tree sees a random
#      subset of rows/columns, reduces variance
#    - reg_alpha / reg_lambda -> L1/L2 regularization on leaf weights
#    - early_stopping_rounds -> stop training once validation score
#      stops improving, prevents the model from overfitting the
#      training set as more boosting rounds are added
# ------------------------------------------------------------------
model = XGBClassifier(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,
    reg_lambda=1.5,
    min_child_weight=3,
    gamma=0.1,
    objective="multi:softprob",
    num_class=len(le.classes_),
    eval_metric="mlogloss",
    random_state=RANDOM_STATE,
    early_stopping_rounds=30,
    n_jobs=-1,
)

model.fit(
    X_train_scaled, y_train,
    eval_set=[(X_val_scaled, y_val)],
    verbose=False,
)

print(f"\nBest iteration: {model.best_iteration}")

# ------------------------------------------------------------------
# 6. Evaluate — check train vs test gap to confirm no overfitting
# ------------------------------------------------------------------
train_pred = model.predict(X_train_scaled)
val_pred = model.predict(X_val_scaled)
test_pred = model.predict(X_test_scaled)

train_acc = accuracy_score(y_train, train_pred)
val_acc = accuracy_score(y_val, val_pred)
test_acc = accuracy_score(y_test, test_pred)

print(f"\nTrain accuracy:      {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy:       {test_acc:.4f}")
print(f"Train-Test gap:      {train_acc - test_acc:.4f}  (small gap = good generalization, not overfit)")

# 5-fold cross-validation on the full training data for a robust estimate
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_scores = cross_val_score(
    XGBClassifier(
        n_estimators=model.best_iteration or 200,
        max_depth=5, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=1.5,
        min_child_weight=3, gamma=0.1,
        objective="multi:softprob", num_class=len(le.classes_),
        random_state=RANDOM_STATE, n_jobs=-1,
    ),
    X_train_scaled, y_train, cv=cv, scoring="accuracy"
)
print(f"\n5-Fold CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

print("\nClassification Report (Test Set):")
print(classification_report(y_test, test_pred, target_names=le.classes_))

print("Confusion Matrix (Test Set):")
print(confusion_matrix(y_test, test_pred))

print(f"\nWeighted F1 (Test): {f1_score(y_test, test_pred, average='weighted'):.4f}")

# ------------------------------------------------------------------
# 7. Feature importance
# ------------------------------------------------------------------
importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nFeature Importances:")
print(importances)

# ------------------------------------------------------------------
# 8. Save artifacts
# ------------------------------------------------------------------
joblib.dump(model, "aqi_xgboost_model.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(FEATURES, "feature_names.pkl")

print("\nSaved: aqi_xgboost_model.pkl, label_encoder.pkl, scaler.pkl, feature_names.pkl")

# ------------------------------------------------------------------
# 9. Quick sanity check on unseen, hand-crafted extreme inputs
#    (values the model has never seen combined this way)
# ------------------------------------------------------------------
sanity_rows = pd.DataFrame([
    {"pm2_5": 8, "pm10": 25, "no2": 12, "so2": 5, "co": 0.5, "o3": 20, "temperature_c": 22.0},   # expect Good
    {"pm2_5": 280, "pm10": 430, "no2": 145, "so2": 95, "co": 9.8, "o3": 145, "temperature_c": 40.0}, # expect Very Unhealthy
    {"pm2_5": 60, "pm10": 220, "no2": 65, "so2": 40, "co": 5.0, "o3": 95, "temperature_c": 30.0}, # expect Unhealthy for Sensitive-ish
])
sanity_scaled = scaler.transform(sanity_rows[FEATURES])
sanity_pred = le.inverse_transform(model.predict(sanity_scaled))
print("\nSanity check on unseen extreme inputs:")
for i, pred in enumerate(sanity_pred):
    print(f"  Row {i}: predicted -> {pred}")
