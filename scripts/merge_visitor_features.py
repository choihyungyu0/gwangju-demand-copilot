from __future__ import annotations

from pathlib import Path

import pandas as pd

import make_mock_visitor_features
from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREA_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "area_features_full.csv"
VISITOR_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "visitor_area_features.csv"
OUTPUT_PATH = AREA_FEATURES_PATH

VISITOR_COLUMNS = [
    "area_id",
    "visitor_count_gu",
    "visitor_growth",
    "visitor_score",
    "visitor_summary",
]

NUMERIC_VISITOR_DEFAULTS = {
    "visitor_count_gu": 0,
    "visitor_growth": 0,
    "visitor_score": 0,
}


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"Missing input CSV: {path}")
        return pd.DataFrame()
    print(f"Reading CSV: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def ensure_visitor_features() -> pd.DataFrame:
    visitor_features = read_csv_or_empty(VISITOR_FEATURES_PATH)
    if not visitor_features.empty:
        return visitor_features

    print("Visitor feature CSV is missing. Regenerating mock visitor fallback.")
    make_mock_visitor_features.main()
    return read_csv_or_empty(VISITOR_FEATURES_PATH)


def main() -> None:
    print("Merging visitor demand features into full area features.")
    area_features = read_csv_or_empty(AREA_FEATURES_PATH)
    visitor_features = ensure_visitor_features()

    if area_features.empty:
        raise FileNotFoundError(
            "area_features_full.csv is required before visitor features can be merged."
        )
    if visitor_features.empty:
        raise FileNotFoundError("No visitor feature CSV was available to merge.")

    available_visitor_columns = [
        column for column in VISITOR_COLUMNS if column in visitor_features.columns
    ]
    merged = area_features.merge(
        visitor_features[available_visitor_columns],
        on="area_id",
        how="left",
        suffixes=("", "_visitor"),
    )

    for column in ["area_name_visitor", "district_visitor"]:
        if column in merged.columns:
            merged = merged.drop(columns=[column])

    for column, default_value in NUMERIC_VISITOR_DEFAULTS.items():
        if column not in merged.columns:
            merged[column] = default_value
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(default_value)
        if column == "visitor_growth":
            merged[column] = merged[column].round(1)
        else:
            merged[column] = merged[column].round().astype(int)

    if "visitor_summary" not in merged.columns:
        merged["visitor_summary"] = "방문자 feature 정보 없음"
    merged["visitor_summary"] = merged["visitor_summary"].fillna("방문자 feature 정보 없음")

    save_csv_safe(merged, OUTPUT_PATH)

    print("Merged visitor feature summary:")
    summary_columns = [
        "area_id",
        "area_name",
        "visitor_count_gu",
        "visitor_growth",
        "visitor_score",
        "visitor_summary",
    ]
    print(merged[[column for column in summary_columns if column in merged.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
