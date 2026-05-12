from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "tourism_area_features.csv"

OUTPUT_COLUMNS = [
    "area_id",
    "area_name",
    "tourist_spot_count",
    "event_count",
    "culture_count",
    "tourism_score",
]

DEFAULT_AREAS = [
    {"area_id": "A001", "area_name": "충장로 / 금남로"},
    {"area_id": "A002", "area_name": "양림동 역사문화마을"},
    {"area_id": "A003", "area_name": "국립아시아문화전당 주변"},
    {"area_id": "A004", "area_name": "1913 송정역시장 / 광주송정역"},
    {"area_id": "A005", "area_name": "상무지구"},
]

MOCK_TOURISM_BY_AREA_ID = {
    "A001": {
        "tourist_spot_count": 8,
        "event_count": 5,
        "culture_count": 4,
        "tourism_score": 74,
    },
    "A002": {
        "tourist_spot_count": 16,
        "event_count": 3,
        "culture_count": 9,
        "tourism_score": 86,
    },
    "A003": {
        "tourist_spot_count": 13,
        "event_count": 11,
        "culture_count": 12,
        "tourism_score": 93,
    },
    "A004": {
        "tourist_spot_count": 10,
        "event_count": 4,
        "culture_count": 5,
        "tourism_score": 78,
    },
    "A005": {
        "tourist_spot_count": 4,
        "event_count": 2,
        "culture_count": 2,
        "tourism_score": 45,
    },
}

EMPTY_TOURISM_FEATURES = {
    "tourist_spot_count": 0,
    "event_count": 0,
    "culture_count": 0,
    "tourism_score": 0,
}


def read_area_rows() -> list[dict[str, object]]:
    if not AREAS_PATH.exists():
        print("areas.csv not found. Using built-in mock area fallback.")
        return DEFAULT_AREAS

    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    required_columns = {"area_id", "area_name"}
    missing_columns = required_columns - set(areas.columns)
    if missing_columns:
        print(
            f"areas.csv is missing {sorted(missing_columns)}. "
            "Using built-in mock area fallback."
        )
        return DEFAULT_AREAS

    return areas[["area_id", "area_name"]].to_dict("records")


def build_feature_rows(area_rows: list[dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for area in area_rows:
        area_id = str(area["area_id"])
        mock_features = MOCK_TOURISM_BY_AREA_ID.get(area_id, EMPTY_TOURISM_FEATURES)
        rows.append(
            {
                "area_id": area_id,
                "area_name": str(area["area_name"]),
                **mock_features,
            }
        )

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main() -> None:
    print("Generating mock tourism and event features.")
    features = build_feature_rows(read_area_rows())
    save_csv_safe(features, OUTPUT_PATH)

    print("Tourism feature summary:")
    for _, row in features.iterrows():
        print(
            f"- {row['area_id']} {row['area_name']}: "
            f"tourism_score={row['tourism_score']}, "
            f"tourist_spot_count={row['tourist_spot_count']}, "
            f"event_count={row['event_count']}, "
            f"culture_count={row['culture_count']}"
        )


if __name__ == "__main__":
    main()
