from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
MATCH_PATH = ROOT_DIR / "data" / "processed" / "store_area_matches.csv"


def main() -> None:
    if not MATCH_PATH.exists():
        raise FileNotFoundError(
            f"{MATCH_PATH} does not exist. Run scripts/match_area_by_radius.py first."
        )

    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    matches = pd.read_csv(MATCH_PATH, encoding="utf-8-sig")

    print("Debugging sample radius matches.")
    for _, area in areas.iterrows():
        area_matches = matches[matches["area_id"] == area["area_id"]].copy()
        area_matches = area_matches.sort_values("distance_m").head(5)

        print(
            f"\n{area['area_id']} {area['area_name']} "
            f"center=({area['center_lat']}, {area['center_lng']}) "
            f"radius={int(area['radius_m'])}m"
        )

        if area_matches.empty:
            print("No matched stores found.")
            continue

        for _, store in area_matches.iterrows():
            print(
                f"- {store['store_name']} | {store['store_category']} | "
                f"lat={store['latitude']} | lng={store['longitude']} | "
                f"distance={store['distance_m']}m"
            )


if __name__ == "__main__":
    main()
