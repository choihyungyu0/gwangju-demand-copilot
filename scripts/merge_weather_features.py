from __future__ import annotations

from pathlib import Path

import pandas as pd

import make_mock_weather_features
from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREA_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "area_features_full.csv"
WEATHER_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "weather_area_features.csv"
OUTPUT_PATH = AREA_FEATURES_PATH

WEATHER_COLUMNS = [
    "area_id",
    "temp",
    "rain_mm",
    "rain_flag",
    "weather_score",
    "weather_risk_level",
    "weather_summary",
]

NUMERIC_WEATHER_DEFAULTS = {
    "temp": 22.0,
    "rain_mm": 0.0,
    "rain_flag": 0,
    "weather_score": 75,
}

TEXT_WEATHER_DEFAULTS = {
    "weather_risk_level": "낮음",
    "weather_summary": "날씨 feature 정보 없음",
}


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Missing input CSV: {path}")
        return pd.DataFrame()
    print(f"Reading CSV: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def ensure_weather_features() -> pd.DataFrame:
    weather_features = read_csv_or_empty(WEATHER_FEATURES_PATH)
    if not weather_features.empty:
        return weather_features

    print("Weather feature CSV is missing. Regenerating mock weather fallback.")
    make_mock_weather_features.main()
    return read_csv_or_empty(WEATHER_FEATURES_PATH)


def main() -> None:
    print("Merging weather demand-risk features into full area features.")
    area_features = read_csv_or_empty(AREA_FEATURES_PATH)
    weather_features = ensure_weather_features()

    if area_features.empty:
        raise FileNotFoundError(
            "area_features_full.csv is required before weather features can be merged."
        )
    if weather_features.empty:
        raise FileNotFoundError("No weather feature CSV was available to merge.")

    weather_feature_columns = [column for column in WEATHER_COLUMNS if column != "area_id"]
    existing_weather_columns = [
        column for column in weather_feature_columns if column in area_features.columns
    ]
    if existing_weather_columns:
        area_features = area_features.drop(columns=existing_weather_columns)

    available_weather_columns = [
        column for column in WEATHER_COLUMNS if column in weather_features.columns
    ]
    merged = area_features.merge(
        weather_features[available_weather_columns],
        on="area_id",
        how="left",
    )

    for column, default_value in NUMERIC_WEATHER_DEFAULTS.items():
        if column not in merged.columns:
            merged[column] = default_value
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(default_value)
        if column in {"temp", "rain_mm"}:
            merged[column] = merged[column].round(1)
        else:
            merged[column] = merged[column].round().astype(int)

    for column, default_value in TEXT_WEATHER_DEFAULTS.items():
        if column not in merged.columns:
            merged[column] = default_value
        merged[column] = merged[column].fillna(default_value)

    save_csv_safe(merged, OUTPUT_PATH)

    print("Merged weather feature summary:")
    summary_columns = [
        "area_id",
        "area_name",
        "temp",
        "rain_mm",
        "rain_flag",
        "weather_score",
        "weather_risk_level",
    ]
    print(merged[[column for column in summary_columns if column in merged.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
