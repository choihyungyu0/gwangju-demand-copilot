from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_demand_training.csv"
METRICS_PATH = ROOT_DIR / "data" / "processed" / "model_metrics.json"
IMPORTANCE_PATH = ROOT_DIR / "data" / "processed" / "feature_importance.csv"
PREDICTIONS_PATH = ROOT_DIR / "data" / "processed" / "daily_model_predictions.csv"

FEATURE_COLUMNS = [
    "is_weekend",
    "matched_store_count",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
    "tourism_score",
    "tourist_spot_count",
    "event_count",
    "culture_count",
    "visitor_count_gu",
    "visitor_growth",
    "visitor_score",
    "temp",
    "rain_mm",
    "rain_flag",
    "weather_score",
]
TARGET_COLUMN = "demand_score"


def load_sklearn():
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        return RandomForestRegressor, mean_absolute_error, mean_squared_error, r2_score
    except ImportError:
        print("scikit-learn is not available in this environment.")
        print("Install scikit-learn locally or run this script in CI to train the MVP model.")
        return None


def date_split(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_dates = sorted(rows["date"].unique())
    split_index = max(1, int(len(unique_dates) * 0.8))
    train_dates = set(unique_dates[:split_index])
    test_dates = set(unique_dates[split_index:])
    return rows[rows["date"].isin(train_dates)].copy(), rows[rows["date"].isin(test_dates)].copy()


def main() -> None:
    print("Training explainable demand prediction model.")
    sklearn_tools = load_sklearn()
    if sklearn_tools is None:
        return

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing training dataset: {INPUT_PATH}")

    RandomForestRegressor, mean_absolute_error, mean_squared_error, r2_score = sklearn_tools
    rows = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    missing_columns = [column for column in [*FEATURE_COLUMNS, TARGET_COLUMN, "date"] if column not in rows.columns]
    if missing_columns:
        raise ValueError(f"Training dataset is missing columns: {missing_columns}")

    for column in [*FEATURE_COLUMNS, TARGET_COLUMN]:
        rows[column] = pd.to_numeric(rows[column], errors="coerce").fillna(0)

    train_rows, test_rows = date_split(rows)
    if test_rows.empty:
        raise ValueError("Test split is empty. Need more unique dates in the training dataset.")

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        min_samples_leaf=2,
    )
    model.fit(train_rows[FEATURE_COLUMNS], train_rows[TARGET_COLUMN])
    test_predictions = model.predict(test_rows[FEATURE_COLUMNS])

    mae = mean_absolute_error(test_rows[TARGET_COLUMN], test_predictions)
    rmse = sqrt(mean_squared_error(test_rows[TARGET_COLUMN], test_predictions))
    r2 = r2_score(test_rows[TARGET_COLUMN], test_predictions)

    metrics = {
        "model_type": "RandomForestRegressor",
        "train_rows": int(len(train_rows)),
        "test_rows": int(len(test_rows)),
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "r2": round(float(r2), 3),
    }
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)
        file.write("\n")

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    importance["importance"] = importance["importance"].round(6)
    save_csv_safe(importance, IMPORTANCE_PATH)

    output_predictions = test_rows[
        ["date", "area_id", "area_name", "district", TARGET_COLUMN]
    ].copy()
    output_predictions["predicted_demand_score"] = test_predictions.round(2)
    output_predictions["prediction_error"] = (
        output_predictions["predicted_demand_score"] - output_predictions[TARGET_COLUMN]
    ).round(2)
    save_csv_safe(output_predictions, PREDICTIONS_PATH)

    print("Model training complete.")
    print(f"MAE={metrics['mae']}, RMSE={metrics['rmse']}, R2={metrics['r2']}")
    print("Top feature importances:")
    print(importance.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
