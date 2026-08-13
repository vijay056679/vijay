"""
SANDBOX-EXECUTABLE VERSION.

This environment has no network access, so `xgboost` cannot be pip-installed
here. This script is IDENTICAL in structure/logic to train_model.py but uses
sklearn's GradientBoostingClassifier (same gradient-boosted-trees family) so
we can actually execute training and validate the full pipeline end-to-end,
producing a real, working .pkl and honest accuracy numbers.

To get the real XGBoost model: run train_model.py on your own machine after
`pip install xgboost` — same features, same data, same split logic, same
hyperparameter philosophy (translated to XGBoost's parameter names in that file).
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)

RANDOM_STATE = 42

df = pd.read_csv("air_quality_dataset_50000.csv")

FEATURES = ["pm2_5", "pm10", "no2", "so2", "co", "o3", "temperature_c"]
TARGET = "air_quality"

X = df[FEATURES].copy()
y_raw = df[TARGET].copy()

le = LabelEncoder()
y = le.fit_transform(y_raw)
print("Classes:", list(le.classes_))

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
)
print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

model = GradientBoostingClassifier(
    n_estimators=250,
    max_depth=4,
    learning_rate=0.06,
    subsample=0.8,
    min_samples_leaf=8,
    max_features=0.8,
    random_state=RANDOM_STATE,
    validation_fraction=0.15,
    n_iter_no_change=15,
    tol=1e-4,
)

model.fit(X_train_scaled, y_train)
print(f"\nActual n_estimators used (early stopping): {model.n_estimators_}")

train_pred = model.predict(X_train_scaled)
val_pred = model.predict(X_val_scaled)
test_pred = model.predict(X_test_scaled)

train_acc = accuracy_score(y_train, train_pred)
val_acc = accuracy_score(y_val, val_pred)
test_acc = accuracy_score(y_test, test_pred)

print(f"\nTrain accuracy:      {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy:       {test_acc:.4f}")
print(f"Train-Test gap:      {train_acc - test_acc:.4f}  (small gap = good generalization)")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_scores = cross_val_score(
    GradientBoostingClassifier(
        n_estimators=model.n_estimators_, max_depth=4, learning_rate=0.06,
        subsample=0.8, min_samples_leaf=8, max_features=0.8,
        random_state=RANDOM_STATE,
    ),
    X_train_scaled, y_train, cv=cv, scoring="accuracy"
)
print(f"\n5-Fold CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

print("\nClassification Report (Test Set):")
print(classification_report(y_test, test_pred, target_names=le.classes_))

print("Confusion Matrix (Test Set):")
print(confusion_matrix(y_test, test_pred))

print(f"\nWeighted F1 (Test): {f1_score(y_test, test_pred, average='weighted'):.4f}")

importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nFeature Importances:")
print(importances)

joblib.dump(model, "aqi_xgboost_model.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(FEATURES, "feature_names.pkl")

print("\nSaved: aqi_xgboost_model.pkl, label_encoder.pkl, scaler.pkl, feature_names.pkl")

sanity_rows = pd.DataFrame([
    {"pm2_5": 8, "pm10": 25, "no2": 12, "so2": 5, "co": 0.5, "o3": 20, "temperature_c": 22.0},
    {"pm2_5": 280, "pm10": 430, "no2": 145, "so2": 95, "co": 9.8, "o3": 145, "temperature_c": 40.0},
    {"pm2_5": 60, "pm10": 220, "no2": 65, "so2": 40, "co": 5.0, "o3": 95, "temperature_c": 30.0},
])
sanity_scaled = scaler.transform(sanity_rows[FEATURES])
sanity_pred = le.inverse_transform(model.predict(sanity_scaled))
print("\nSanity check on unseen extreme inputs:")
for i, pred in enumerate(sanity_pred):
    print(f"  Row {i}: predicted -> {pred}")
