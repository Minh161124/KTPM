import pandas as pd
import numpy as np
import os

os.makedirs("data", exist_ok=True)

rng = pd.date_range("2024-01-01","2025-11-01", freq="D")
np.random.seed(42)

df = pd.DataFrame({"date": rng})
df["num_customers"] = np.random.poisson(80, len(df))
df["sessions"] = (df["num_customers"] * (1 + np.random.normal(0,0.05,len(df)))).astype(int)
df["avg_session_minutes"] = np.clip(np.random.normal(90,10,len(df)), 30, 240)
df["promo_flag"] = (np.random.rand(len(df)) < 0.08).astype(int)
df["holiday_flag"] = (df["date"].dt.weekday >=5).astype(int)

df["revenue"] = (
    df["num_customers"]*15000 *
    (1 + 0.2*df["promo_flag"]) *
    (1 + np.random.normal(0,0.12,len(df)))
)

df.to_csv("data/revenue.csv", index=False)
print("Saved data/revenue.csv")
