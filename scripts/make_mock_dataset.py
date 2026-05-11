from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
RADIUS_STORE_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "store_features_radius.csv"
STORE_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "store_features.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset.csv"
START_DATE = date(2026, 5, 1)
DAYS = 30


AREA_PROFILES = {
    "A001": {
        "visitor_base": 51000,
        "visitor_step": 430,
        "store_total": 1380,
        "food_count": 520,
        "cafe_count": 210,
        "retail_count": 420,
        "accommodation_count": 22,
        "tourist_spot_count": 8,
        "event_base": 2,
    },
    "A002": {
        "visitor_base": 27500,
        "visitor_step": 260,
        "store_total": 430,
        "food_count": 150,
        "cafe_count": 170,
        "retail_count": 60,
        "accommodation_count": 18,
        "tourist_spot_count": 14,
        "event_base": 1,
    },
    "A003": {
        "visitor_base": 42000,
        "visitor_step": 390,
        "store_total": 720,
        "food_count": 270,
        "cafe_count": 150,
        "retail_count": 115,
        "accommodation_count": 20,
        "tourist_spot_count": 16,
        "event_base": 4,
    },
    "A004": {
        "visitor_base": 36500,
        "visitor_step": 340,
        "store_total": 610,
        "food_count": 250,
        "cafe_count": 85,
        "retail_count": 180,
        "accommodation_count": 35,
        "tourist_spot_count": 9,
        "event_base": 2,
    },
    "A005": {
        "visitor_base": 45500,
        "visitor_step": 310,
        "store_total": 980,
        "food_count": 470,
        "cafe_count": 160,
        "retail_count": 145,
        "accommodation_count": 28,
        "tourist_spot_count": 4,
        "event_base": 1,
    },
}


FIELDNAMES = [
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
]

STORE_FEATURE_COLUMNS = [
    "store_total",
    "matched_store_count",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
]


def read_areas() -> list[dict[str, object]]:
    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    return areas.to_dict("records")


def to_int(value: object) -> int:
    numeric_value = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric_value):
        return 0
    return int(numeric_value)


def load_store_features() -> dict[str, dict[str, int]]:
    if RADIUS_STORE_FEATURES_PATH.exists():
        feature_path = RADIUS_STORE_FEATURES_PATH
        print("Using radius-based store features.")
    elif STORE_FEATURES_PATH.exists():
        feature_path = STORE_FEATURES_PATH
        print("Radius features not found. Using district-level store features.")
    else:
        print("No store feature CSV found. Using mock store fallback values.")
        return {}

    features = pd.read_csv(feature_path, encoding="utf-8-sig")
    if "matched_store_count" in features.columns and "store_total" not in features.columns:
        features["store_total"] = features["matched_store_count"]
    elif "store_total" in features.columns and "matched_store_count" not in features.columns:
        features["matched_store_count"] = features["store_total"]

    missing_columns = [
        column
        for column in ["area_id", *STORE_FEATURE_COLUMNS]
        if column not in features.columns
    ]
    if missing_columns:
        print(
            f"{feature_path.name} is missing columns "
            f"{missing_columns}. Using mock store fallback values."
        )
        return {}

    feature_map: dict[str, dict[str, int]] = {}
    for _, row in features.iterrows():
        area_id = str(row["area_id"])
        feature_map[area_id] = {
            column: to_int(row[column])
            for column in STORE_FEATURE_COLUMNS
        }

    print(f"Loaded store features from {feature_path} for {len(feature_map)} areas.")
    return feature_map


def make_row(
    area: dict[str, object],
    day_index: int,
    store_features: dict[str, dict[str, int]],
) -> dict[str, object]:
    current_date = START_DATE + timedelta(days=day_index)
    area_id = str(area["area_id"])
    is_weekend = 1 if current_date.weekday() >= 5 else 0
    profile = dict(AREA_PROFILES[area_id])

    if area_id in store_features:
        profile.update(store_features[area_id])

    weekly_wave = (day_index % 7) * profile["visitor_step"]
    weekend_boost = 7600 if is_weekend else 0
    rain_flag = 1 if (day_index + int(area_id[-1])) % 9 == 0 else 0
    rain_penalty = 2600 if rain_flag else 0

    event_count = profile["event_base"]
    if is_weekend:
        event_count += 2
    if area_id == "A003" and day_index % 5 in (1, 2):
        event_count += 2
    if area_id == "A004" and is_weekend:
        event_count += 1
    if area_id == "A005" and current_date.weekday() in (3, 4):
        event_count += 1

    temp = 18 + (day_index % 10) + (1 if is_weekend else 0)
    visitor_count = (
        profile["visitor_base"]
        + weekly_wave
        + weekend_boost
        + (event_count * 850)
        - rain_penalty
    )

    return {
        "date": current_date.isoformat(),
        "area_id": area_id,
        "area_name": area["area_name"],
        "district": area["district"],
        "area_radius_m": to_int(area.get("radius_m", 0)),
        "is_weekend": is_weekend,
        "visitor_count_gu": visitor_count,
        "matched_store_count": profile.get("matched_store_count", profile["store_total"]),
        "store_total": profile["store_total"],
        "food_count": profile["food_count"],
        "cafe_count": profile["cafe_count"],
        "retail_count": profile["retail_count"],
        "accommodation_count": profile["accommodation_count"],
        "tourist_spot_count": profile["tourist_spot_count"],
        "event_count": event_count,
        "temp": temp,
        "rain_flag": rain_flag,
    }


def main() -> None:
    areas = read_areas()
    store_features = load_store_features()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        make_row(area, day_index, store_features)
        for area in areas
        for day_index in range(DAYS)
    ]

    save_csv_safe(pd.DataFrame(rows, columns=FIELDNAMES), OUTPUT_PATH)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
