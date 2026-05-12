from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset_scored.csv"

NUMERIC_COLUMNS = [
    "visitor_count_gu",
    "event_count",
    "tourist_spot_count",
    "store_total",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
]

OUTPUT_FIELDS = [
    "date",
    "area_id",
    "area_name",
    "district",
    "area_radius_m",
    "is_weekend",
    "visitor_count_gu",
    "matched_store_count",
    "store_total",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
    "tourist_spot_count",
    "event_count",
    "temp",
    "rain_flag",
    "visitor_score",
    "event_score",
    "tourism_score",
    "store_score",
    "weather_score",
    "demand_score",
]


def normalize_series(series: pd.Series) -> pd.Series:
    low = series.min()
    high = series.max()
    if high == low:
        return pd.Series(50.0, index=series.index)
    return ((series - low) / (high - low)) * 100


def main() -> None:
    rows = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

    if "accommodation_count" not in rows.columns:
        rows["accommodation_count"] = 0
    if "matched_store_count" not in rows.columns:
        rows["matched_store_count"] = rows["store_total"]
    if "area_radius_m" not in rows.columns:
        rows["area_radius_m"] = 0

    for column in [*NUMERIC_COLUMNS, "matched_store_count", "area_radius_m", "temp", "rain_flag"]:
        rows[column] = pd.to_numeric(rows[column], errors="coerce").fillna(0)

    rows["visitor_score"] = normalize_series(rows["visitor_count_gu"])
    rows["event_score"] = normalize_series(rows["event_count"])
    rows["tourism_score"] = normalize_series(rows["tourist_spot_count"])

    store_score_parts = [
        normalize_series(rows["store_total"]),
        normalize_series(rows["food_count"]),
        normalize_series(rows["cafe_count"]),
        normalize_series(rows["retail_count"]),
        normalize_series(rows["accommodation_count"]),
    ]
    rows["store_score"] = sum(store_score_parts) / len(store_score_parts)

    rows["weather_score"] = 82 - (rows["temp"] - 22).abs() * 2
    rows.loc[rows["rain_flag"] == 1, "weather_score"] -= 32
    rows["weather_score"] = rows["weather_score"].clip(lower=0, upper=100)

    rows["demand_score"] = (
        rows["store_score"] * 0.25
        + rows["tourism_score"] * 0.2
        + rows["visitor_score"] * 0.25
        + rows["event_score"] * 0.1
        + rows["weather_score"] * 0.2
    )

    score_columns = [
        "visitor_score",
        "event_score",
        "tourism_score",
        "store_score",
        "weather_score",
        "demand_score",
    ]
    rows[score_columns] = rows[score_columns].round(2)

    save_csv_safe(rows[OUTPUT_FIELDS], OUTPUT_PATH)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
