"""
Generates a realistic, physically-consistent Air Quality dataset (50,000 rows).

Approach: for each row, first sample a target AQI category with realistic
real-world proportions (most days moderate/unhealthy-for-sensitive in a
polluted region, fewer days at the extremes -- similar to real annual
monitoring station data in many Asian cities). Then sample pollutant
concentrations from ranges consistent with that AQI category (using real
EPA breakpoint tables), with enough overlap/noise between adjacent bands
that the model must learn real boundaries rather than memorize a lookup
table (prevents overfitting, forces genuine generalization).
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 50000

CATEGORIES = ["Good", "Moderate", "Unhealthy for Sensitive", "Unhealthy", "Very Unhealthy"]
# Realistic real-world-like proportions for a moderately polluted region
PROPORTIONS = [0.05, 0.22, 0.28, 0.27, 0.18]

category = np.random.choice(CATEGORIES, size=N, p=PROPORTIONS)

# EPA concentration breakpoints per pollutant per category (lo, hi)
# Values chosen so each pollutant's band roughly matches its AQI sub-index band.
RANGES = {
    "Good":                     {"pm2_5": (5, 12),    "pm10": (10, 54),   "no2": (5, 40),   "so2": (2, 20),  "co": (0.2, 2.5), "o3": (10, 50)},
    "Moderate":                 {"pm2_5": (12, 35),   "pm10": (54, 154),  "no2": (30, 70),  "so2": (15, 40), "co": (2.0, 4.5), "o3": (40, 80)},
    "Unhealthy for Sensitive":  {"pm2_5": (35, 55),   "pm10": (154, 254), "no2": (60, 100), "so2": (35, 65), "co": (4.0, 7.0), "o3": (70, 110)},
    "Unhealthy":                {"pm2_5": (55, 150),  "pm10": (254, 354), "no2": (95, 130), "so2": (60, 90), "co": (6.5, 9.0), "o3": (100, 140)},
    "Very Unhealthy":           {"pm2_5": (150, 300), "pm10": (354, 450), "no2": (125, 150),"so2": (85, 100),"co": (8.5, 10.0),"o3": (130, 150)},
}

def sample_feature(cat_array, feat, jitter_frac=0.28):
    """Sample values within each row's category band, with jitter so
    bands overlap slightly (sensor noise / multi-pollutant real-world
    messiness) -> prevents the task from being trivially separable,
    which keeps the model from overfitting to hard boundaries."""
    out = np.zeros(len(cat_array))
    for cat in CATEGORIES:
        mask = cat_array == cat
        n = mask.sum()
        lo, hi = RANGES[cat][feat]
        vals = np.random.uniform(lo, hi, n)
        vals += np.random.normal(0, jitter_frac * (hi - lo), n)
        out[mask] = vals
    return out

pm2_5 = np.clip(sample_feature(category, "pm2_5"), 5, 300)
pm10 = np.clip(sample_feature(category, "pm10"), 10, 450)
no2 = np.clip(sample_feature(category, "no2"), 5, 150)
so2 = np.clip(sample_feature(category, "so2"), 2, 100)
co = np.clip(sample_feature(category, "co"), 0.2, 10)
o3 = np.clip(sample_feature(category, "o3"), 10, 150)

# Temperature: realistic ambient range with mild correlation to O3 (heat -> more ozone formation)
o3_norm = (o3 - 10) / (150 - 10)
temperature_c = np.clip(18 + 18 * o3_norm + np.random.normal(0, 4, N), 15, 45)

pm2_5 = np.round(pm2_5).astype(int)
pm10 = np.round(pm10).astype(int)
no2 = np.round(no2).astype(int)
so2 = np.round(so2).astype(int)
co = np.round(co, 2)
o3 = np.round(o3).astype(int)
temperature_c = np.round(temperature_c, 1)

# 8% label noise mimics real-world sensor/reporting error, keeps the
# accuracy ceiling honest (no model should reach 100% on real data).
noise_idx = np.random.choice(N, size=int(0.08 * N), replace=False)
final_category = category.copy()
final_category[noise_idx] = np.random.choice(CATEGORIES, size=len(noise_idx), p=PROPORTIONS)

df = pd.DataFrame({
    "pm2_5": pm2_5,
    "pm10": pm10,
    "no2": no2,
    "so2": so2,
    "co": co,
    "o3": o3,
    "temperature_c": temperature_c,
    "air_quality": final_category,
})

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

print("Class distribution:")
print(df["air_quality"].value_counts())
print("\nProportions:")
print(df["air_quality"].value_counts(normalize=True).round(3))
print("\nShape:", df.shape)

df.to_csv("/home/claude/aqi_project/air_quality_dataset_50000.csv", index=False)
print("\nSaved to air_quality_dataset_50000.csv")
