from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from geo_utils import haversine_distance
from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
STORE_PATH = ROOT_DIR / "data" / "processed" / "gwangju_store_data.csv"
MATCH_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "store_area_matches.csv"
FEATURE_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "store_features_radius.csv"

MATCH_COLUMNS = [
    "area_id",
    "area_name",
    "district",
    "radius_m",
    "store_name",
    "store_category",
    "latitude",
    "longitude",
    "distance_m",
]

FEATURE_COLUMNS = [
    "area_id",
    "area_name",
    "district",
    "matched_store_count",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
]


def read_areas() -> pd.DataFrame:
    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    required_columns = {
        "area_id",
        "area_name",
        "district",
        "center_lat",
        "center_lng",
        "radius_m",
    }
    missing = required_columns - set(areas.columns)
    if missing:
        raise ValueError(f"areas.csv is missing required columns: {sorted(missing)}")

    for column in ["center_lat", "center_lng", "radius_m"]:
        areas[column] = pd.to_numeric(areas[column], errors="coerce")

    areas = areas.dropna(subset=["center_lat", "center_lng", "radius_m"]).copy()
    print(f"Loaded {len(areas)} areas from {AREAS_PATH}")
    return areas


def read_stores() -> pd.DataFrame:
    stores = pd.read_csv(STORE_PATH, encoding="utf-8-sig")
    required_columns = {"store_name", "store_category", "latitude", "longitude"}
    missing = required_columns - set(stores.columns)
    if missing:
        raise ValueError(f"gwangju_store_data.csv is missing columns: {sorted(missing)}")

    stores["latitude"] = pd.to_numeric(stores["latitude"], errors="coerce")
    stores["longitude"] = pd.to_numeric(stores["longitude"], errors="coerce")
    before = len(stores)
    stores = stores.dropna(subset=["latitude", "longitude"]).copy()
    print(f"Loaded {before} stores from {STORE_PATH}")
    print(f"Stores with valid coordinates: {len(stores)}")
    return stores


def match_one_area(area: pd.Series, stores: pd.DataFrame) -> pd.DataFrame:
    distances = haversine_distance(
        area["center_lat"],
        area["center_lng"],
        stores["latitude"].to_numpy(),
        stores["longitude"].to_numpy(),
    )
    mask = distances <= area["radius_m"]
    matched = stores.loc[mask, ["store_name", "store_category", "latitude", "longitude"]].copy()
    matched["distance_m"] = np.round(distances[mask], 1)
    matched["area_id"] = area["area_id"]
    matched["area_name"] = area["area_name"]
    matched["district"] = area["district"]
    matched["radius_m"] = int(area["radius_m"])
    return matched[MATCH_COLUMNS]


def build_feature_rows(areas: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, area in areas.iterrows():
        area_matches = matches[matches["area_id"] == area["area_id"]]
        rows.append(
            {
                "area_id": area["area_id"],
                "area_name": area["area_name"],
                "district": area["district"],
                "matched_store_count": len(area_matches),
                "food_count": int((area_matches["store_category"] == "food").sum()),
                "cafe_count": int((area_matches["store_category"] == "cafe").sum()),
                "retail_count": int((area_matches["store_category"] == "retail").sum()),
                "accommodation_count": int(
                    (area_matches["store_category"] == "accommodation").sum()
                ),
            }
        )

    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)


def print_area_logs(areas: pd.DataFrame, matches: pd.DataFrame) -> None:
    for _, area in areas.iterrows():
        area_matches = matches[matches["area_id"] == area["area_id"]]
        average_distance = (
            round(area_matches["distance_m"].mean(), 1) if not area_matches.empty else 0
        )
        print(
            f"{area['area_id']} {area['area_name']} radius {int(area['radius_m'])}m: "
            f"matched {len(area_matches)} stores, average distance {average_distance}m"
        )

        if area_matches.empty:
            print("  No matched stores.")
            continue

        print("  Sample matched stores:")
        sample = area_matches.sort_values("distance_m").head(5)
        for _, store in sample.iterrows():
            print(
                f"  - {store['store_name']} | {store['store_category']} | "
                f"{store['distance_m']}m"
            )


def main() -> None:
    print("Starting radius-based area matching.")
    areas = read_areas()
    stores = read_stores()

    match_frames = [match_one_area(area, stores) for _, area in areas.iterrows()]
    matches = (
        pd.concat(match_frames, ignore_index=True)
        if match_frames
        else pd.DataFrame(columns=MATCH_COLUMNS)
    )
    features = build_feature_rows(areas, matches)

    print_area_logs(areas, matches)
    save_csv_safe(matches, MATCH_OUTPUT_PATH)
    save_csv_safe(features, FEATURE_OUTPUT_PATH)
    print(f"Saved area-store matches: {MATCH_OUTPUT_PATH}")
    print(f"Saved radius store features: {FEATURE_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
