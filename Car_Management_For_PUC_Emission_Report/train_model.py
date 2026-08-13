import pandas as pd
import numpy as np
import pickle
import json
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
import xgboost as xgb


# 1.  LOAD DATA

CSV_PATH = "cars_emission_dataset_100000.csv"   # ← change path if needed
df = pd.read_csv(CSV_PATH)

print(f"Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
print("Class distribution:\n", df["Issue"].value_counts(), "\n")


# 2.  FEATURE ENGINEERING
#     Real-world PUC signal: emission ratios
#     capture fault-specific combustion patterns

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # ── categorical encodings ──────────────────────────────
    d["Fuel_enc"]     = (d["Fuel_Type"] == "Petrol").astype(int)        # 0=Diesel, 1=Petrol
    d["Std_enc"]      = (d["Emission_Standard"] == "BS6").astype(int)   # 0=BS4, 1=BS6
    d["Fuel_Std_enc"] = d["Fuel_enc"] * 2 + d["Std_enc"]               # 4-way interaction

    # ── combustion ratio features ──────────────────────────
    d["Lambda_dev"]   = (d["Lambda"] - 1.0).abs()       # stoichiometric deviation
    d["Lambda_sign"]  = np.sign(d["Lambda"] - 1.0)      # rich(-1) / lean(+1)
    d["CO_O2_ratio"]  = d["CO"] / (d["O2"] + 1e-3)      # rich combustion indicator
    d["HC_NOx_ratio"] = d["HC"] / (d["NOx"] + 1e-3)     # misfire vs EGR signal
    d["NOx_PM_ratio"] = d["NOx"] / (d["PM"] + 1e-5)     # DPF vs EGR signal
    d["CO_HC_ratio"]  = d["CO"] / (d["HC"] + 1e-3)      # injection quality
    d["PM_HC_ratio"]  = d["PM"] / (d["HC"] + 1e-3)      # particulate efficiency

    # ── interaction products ───────────────────────────────
    d["CO_x_Lambda"]  = d["CO"]  * d["Lambda"]
    d["HC_x_O2"]      = d["HC"]  * d["O2"]
    d["NOx_x_Lambda"] = d["NOx"] * d["Lambda"]
    d["PM_x_CO"]      = d["PM"]  * d["CO"]
    d["HC_x_NOx"]     = d["HC"]  * d["NOx"]
    d["O2_x_Lambda"]  = d["O2"]  * d["Lambda"]

    # ── squared terms (non-linear patterns) ───────────────
    d["HC_sq"]        = d["HC"]  ** 2
    d["CO_sq"]        = d["CO"]  ** 2
    d["Lambda_sq"]    = d["Lambda"] ** 2

    # ── binned combustion zones ────────────────────────────
    d["HC_zone"]      = pd.cut(d["HC"],  bins=[0, 200, 400, 500, 600, 701],
                                labels=[0, 1, 2, 3, 4]).astype(float)
    d["NOx_zone"]     = pd.cut(d["NOx"], bins=[0, 0.05, 0.12, 0.16, 0.30],
                                labels=[0, 1, 2, 3]).astype(float)
    d["PM_zone"]      = pd.cut(d["PM"],  bins=[0, 0.003, 0.01, 0.015, 0.030],
                                labels=[0, 1, 2, 3]).astype(float)
    d["Lambda_zone"]  = pd.cut(d["Lambda"], bins=[0.69, 0.90, 0.99, 1.01, 1.10, 1.31],
                                labels=[0, 1, 2, 3, 4]).astype(float)
    return d


df = add_features(df)

FEATURES = [
    # raw
    "Fuel_enc", "Std_enc", "Fuel_Std_enc",
    "CO", "HC", "NOx", "PM", "O2", "Lambda",
    # ratios
    "Lambda_dev", "Lambda_sign",
    "CO_O2_ratio", "HC_NOx_ratio", "NOx_PM_ratio", "CO_HC_ratio", "PM_HC_ratio",
    # products
    "CO_x_Lambda", "HC_x_O2", "NOx_x_Lambda", "PM_x_CO", "HC_x_NOx", "O2_x_Lambda",
    # squares
    "HC_sq", "CO_sq", "Lambda_sq",
    # bins
    "HC_zone", "NOx_zone", "PM_zone", "Lambda_zone",
]


# 3.  ENCODE TARGET

le_issue = LabelEncoder()
df["Issue_enc"] = le_issue.fit_transform(df["Issue"])

X = df[FEATURES].values
y = df["Issue_enc"].values


# 4.  TRAIN / TEST SPLIT (stratified)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"Train: {len(X_train):,}   Test: {len(X_test):,}\n")


# 5.  XGBOOST MODEL
#     Tuned to generalise — no overfitting:
#     • subsample / colsample_bytree < 1.0
#     • min_child_weight prevents tiny splits
#     • reg_alpha / reg_lambda penalise complexity
#     • early_stopping on eval set

dtrain = xgb.DMatrix(X_train, label=y_train)
dtest  = xgb.DMatrix(X_test,  label=y_test)

params = {
    "objective":        "multi:softmax",
    "num_class":        len(le_issue.classes_),
    "eval_metric":      "merror",          # 1 - accuracy
    "eta":              0.05,              # learning rate
    "max_depth":        8,
    "min_child_weight": 10,                # prevents over-splitting
    "subsample":        0.85,              # row sampling per tree
    "colsample_bytree": 0.80,             # feature sampling per tree
    "colsample_bylevel":0.80,
    "reg_alpha":        0.2,              # L1
    "reg_lambda":       1.5,              # L2
    "gamma":            0.05,             # min gain to split
    "seed":             42,
    "nthread":          -1,
    "tree_method":      "hist",           # fast histogram method
}

evals_result = {}
model = xgb.train(
    params,
    dtrain,
    num_boost_round     = 1000,
    evals               = [(dtrain, "train"), (dtest, "test")],
    early_stopping_rounds = 40,
    evals_result        = evals_result,
    verbose_eval        = 50,
)


# 6.  EVALUATE

y_pred_train = model.predict(dtrain).astype(int)
y_pred_test  = model.predict(dtest).astype(int)

train_acc = accuracy_score(y_train, y_pred_train)
test_acc  = accuracy_score(y_test,  y_pred_test)

print(f"\n{'='*50}")
print(f"  Train Accuracy : {train_acc*100:.2f}%")
print(f"  Test  Accuracy : {test_acc*100:.2f}%")
print(f"  Gap (overfit?) : {(train_acc - test_acc)*100:.2f}%  ← should be <5%")
print(f"{'='*50}\n")

print("Per-class report:")
print(classification_report(
    y_test, y_pred_test,
    target_names=le_issue.classes_
))


# 7.  CROSS-VALIDATION (5-fold, test generality)

print("Running 5-fold cross-validation ...")

clf_sklearn = xgb.XGBClassifier(
    n_estimators        = model.best_iteration,
    learning_rate       = 0.05,
    max_depth           = 8,
    min_child_weight    = 10,
    subsample           = 0.85,
    colsample_bytree    = 0.80,
    colsample_bylevel   = 0.80,
    reg_alpha           = 0.2,
    reg_lambda          = 1.5,
    gamma               = 0.05,
    use_label_encoder   = False,
    eval_metric         = "mlogloss",
    random_state        = 42,
    tree_method         = "hist",
)
cv_scores = cross_val_score(clf_sklearn, X, y, cv=5, scoring="accuracy", n_jobs=-1)
print(f"CV Accuracy: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%\n")


# 8.  SAVE MODEL  (.pkl)

# Re-fit sklearn wrapper on full training set for pickling
clf_sklearn.fit(X_train, y_train)

payload = {
    "model":      clf_sklearn,
    "label_enc":  le_issue,
    "features":   FEATURES,
    "classes":    list(le_issue.classes_),
    "fuel_types": ["Diesel", "Petrol"],
    "standards":  ["BS4", "BS6"],
    "train_acc":  round(train_acc * 100, 2),
    "test_acc":   round(test_acc  * 100, 2),
    "cv_mean":    round(cv_scores.mean() * 100, 2),
    "cv_std":     round(cv_scores.std()  * 100, 2),
}

with open("emission_model.pkl", "wb") as f:
    pickle.dump(payload, f)

print("✅  Model saved → emission_model.pkl")
print("    Bundled: XGBClassifier, LabelEncoder, feature list, metadata")
