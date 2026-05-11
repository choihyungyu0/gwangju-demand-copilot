from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
STORE_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "store_features_radius.csv"
TOURISM_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "tourism_area_features.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "area_features_full.csv"


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Missing input CSV: {path}")
        return pd.DataFrame()
    print(f"Reading CSV: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def main() -> None:
    print("Merging radius store features with tourism/event features.")
    store_features = read_csv_or_empty(STORE_FEATURES_PATH)
    tourism_features = read_csv_or_empty(TOURISM_FEATURES_PATH)

    if store_features.empty and tourism_features.empty:
        raise FileNotFoundError(
            "No store or tourism feature CSVs were available to merge."
        )
    if store_features.empty:
        print("Store radius features are unavailable. Output will contain tourism fields only.")
        merged = tourism_features.copy()
    elif tourism_features.empty:
        print("Tourism features are unavailable. Output will contain store fields only.")
        merged = store_features.copy()
    else:
        merged = store_features.merge(
            tourism_features,
            on=["area_id", "area_name"],
            how="left",
        )

    numeric_defaults = {
        "matched_store_count": 0,
        "food_count": 0,
        "cafe_count": 0,
        "retail_count": 0,
        "accommodation_count": 0,
        "tourist_spot_count": 0,
        "event_count": 0,
        "culture_count": 0,
        "tourism_score": 0,
    }
    for column, default_value in numeric_defaults.items():
        if column not in merged.columns:
            merged[column] = default_value
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(default_value)
        merged[column] = merged[column].round().astype(int)

    output_columns = [
        column
        for column in [
            "area_id",
            "area_name",
            "district",
            "matched_store_count",
            "food_count",
            "cafe_count",
            "retail_count",
            "accommodation_count",
            "tourist_spot_count",
            "event_count",
            "culture_count",
            "tourism_score",
        ]
        if column in merged.columns
    ]

    merged = merged[output_columns]
    save_csv_safe(merged, OUTPUT_PATH)

    print("Merged feature summary:")
    print(merged.to_string(index=False))


if __name__ == "__main__":
    main()
