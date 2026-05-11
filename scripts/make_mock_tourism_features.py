from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "tourism_area_features.csv"


TOURISM_FEATURES = [
    {
        "area_id": "A001",
        "area_name": "충장로 / 금남로",
        "tourist_spot_count": 8,
        "event_count": 5,
        "culture_count": 4,
        "tourism_score": 74,
    },
    {
        "area_id": "A002",
        "area_name": "양림동 역사문화마을",
        "tourist_spot_count": 16,
        "event_count": 3,
        "culture_count": 9,
        "tourism_score": 86,
    },
    {
        "area_id": "A003",
        "area_name": "국립아시아문화전당 주변",
        "tourist_spot_count": 13,
        "event_count": 11,
        "culture_count": 12,
        "tourism_score": 93,
    },
    {
        "area_id": "A004",
        "area_name": "1913 송정역시장 / 광주송정역",
        "tourist_spot_count": 10,
        "event_count": 4,
        "culture_count": 5,
        "tourism_score": 78,
    },
    {
        "area_id": "A005",
        "area_name": "상무지구",
        "tourist_spot_count": 4,
        "event_count": 2,
        "culture_count": 2,
        "tourism_score": 45,
    },
]


def main() -> None:
    print("Generating mock tourism and event features.")
    features = pd.DataFrame(TOURISM_FEATURES)
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
