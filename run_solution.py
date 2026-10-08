import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("1. Loading datasets...")
train_df = pd.read_csv("data/train-test.csv")
val_df = pd.read_csv("data/validation.csv")
dec_df = pd.read_csv("data/december-chart-inputs.csv")

# Ensure proper datetime parsing
train_df["date"] = pd.to_datetime(train_df["date"])
val_df["date"] = pd.to_datetime(val_df["date"])
# Handle format in december-chart-inputs (DD-MM-YYYY)
dec_df["date"] = pd.to_datetime(dec_df["date"], format="%d-%m-%Y")

print("2. Imputing missing values...")
# Impute weight by equipment median
weight_medians = train_df.groupby("equipment")["weight"].median()
train_df["weight"] = train_df["weight"].fillna(train_df["equipment"].map(weight_medians))
val_df["weight"] = val_df["weight"].fillna(val_df["equipment"].map(weight_medians))

# Impute market_index by daily mean, fallback to global median
daily_market = train_df.groupby("date")["market_index"].mean()
train_df["market_index"] = train_df["market_index"].fillna(train_df["date"].map(daily_market)).fillna(train_df["market_index"].median())

val_daily_market = val_df.groupby("date")["market_index"].mean()
val_df["market_index"] = val_df["market_index"].fillna(val_df["date"].map(val_daily_market)).fillna(train_df["market_index"].median())

print("3. Preparing features...")
def engineer_features(df):
    df = df.copy()
    df["dayofweek"] = df["date"].dt.dayofweek
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    
    # Geographic distance features
    df["lat_diff"] = df["delivery_lat"] - df["pickup_lat"]
    df["lon_diff"] = df["delivery_lon"] - df["pickup_lon"]
    df["euclidean_dist"] = np.sqrt(df["lat_diff"]**2 + df["lon_diff"]**2)
    
    # Interactions
    df["dist_quote_inter"] = df["distance"] * df["quote_signal"]
    df["dist_market_inter"] = df["distance"] * df["market_index"]
    df["weight_per_mile"] = df["weight"] / (df["distance"] + 1e-5)
    return df

# Lexington to Fort Wayne coordinates for December inputs
dec_df["pickup_lat"] = 36.99152
dec_df["pickup_lon"] = -84.99876
dec_df["delivery_lat"] = 41.31561
dec_df["delivery_lon"] = -85.36206

# Map December daily average market_index & quote_signal from validation.csv
dec_signals = val_df.groupby(val_df["date"].dt.date).agg({
    "market_index": "mean",
    "quote_signal": "mean"
}).reset_index()
dec_signals["date"] = pd.to_datetime(dec_signals["date"])
dec_df = dec_df.merge(dec_signals, on="date", how="left")

train_feat = engineer_features(train_df)
val_feat = engineer_features(val_df)
dec_feat = engineer_features(dec_df)

feature_cols = [
    "distance", "weight", "pickup_lat", "pickup_lon", "delivery_lat", "delivery_lon",
    "market_index", "quote_signal", "dayofweek", "is_weekend", "day", "month",
    "lat_diff", "lon_diff", "euclidean_dist", "dist_quote_inter", "dist_market_inter", "weight_per_mile",
    "equipment"
]

for c in ["equipment"]:
    train_feat[c] = train_feat[c].astype("category")
    val_feat[c] = val_feat[c].astype("category")
    dec_feat[c] = dec_feat[c].astype("category")

print("4. Validating with Temporal Split (Jan-Aug Train -> Sep-Oct Test)...")
split_date = pd.to_datetime("2025-09-01")
tr_split = train_feat[train_feat["date"] < split_date]
va_split = train_feat[train_feat["date"] >= split_date]

val_eval_model = LGBMRegressor(n_estimators=1000, learning_rate=0.03, random_state=42, verbose=-1)
val_eval_model.fit(tr_split[feature_cols], tr_split["posted_rate"])
split_preds = val_eval_model.predict(va_split[feature_cols])

mae = mean_absolute_error(va_split["posted_rate"], split_preds)
rmse = np.sqrt(mean_squared_error(va_split["posted_rate"], split_preds))
r2 = r2_score(va_split["posted_rate"], split_preds)
print(f"--> Local Validation Results: MAE = ${mae:.2f} | RMSE = ${rmse:.2f} | R2 = {r2:.4f}")

print("5. Training final model on all development data...")
final_model = LGBMRegressor(n_estimators=1200, learning_rate=0.03, random_state=42, verbose=-1)
final_model.fit(train_feat[feature_cols], train_feat["posted_rate"])

print("6. Predicting on validation.csv & december-chart-inputs.csv...")
val_preds = final_model.predict(val_feat[feature_cols])
dec_preds = final_model.predict(dec_feat[feature_cols])

# Ensure all rates are strictly positive
val_preds = np.clip(val_preds, a_min=1.0, a_max=None)
dec_preds = np.clip(dec_preds, a_min=1.0, a_max=None)

# 7. Save validation_predictions.csv
val_submission = pd.DataFrame({
    "load_id": val_df["load_id"],
    "predicted_rate": val_preds
})
val_submission.to_csv("validation_predictions.csv", index=False)
print("--> Saved validation_predictions.csv (12,000 rows)")

# 8. Save updated december_chart_inputs.csv preserving exact required format
dec_output = dec_df[["pickup", "delivery", "distance", "equipment", "weight", "date"]].copy()
dec_output["predicted_rate"] = dec_preds
# Reformat date back to YYYY-MM-DD as expected by score.py
dec_output["date"] = dec_output["date"].dt.strftime("%Y-%m-%d")
dec_output.to_csv("data/december-chart-inputs.csv", index=False)
print("--> Saved december-chart-inputs.csv (31 rows)")