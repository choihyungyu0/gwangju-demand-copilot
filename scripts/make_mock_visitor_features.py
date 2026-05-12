from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "visitor_area_features.csv"

OUTPUT_COLUMNS = [
    "area_id",
    "area_name",
    "district",
    "visitor_count_gu",
    "visitor_growth",
    "visitor_score",
    "visitor_summary",
]

DEFAULT_AREAS = [
    {"area_id": "A001", "area_name": "충장로 / 금남로", "district": "동구"},
    {"area_id": "A002", "area_name": "양림동 역사문화마을", "district": "남구"},
    {"area_id": "A003", "area_name": "국립아시아문화전당 주변", "district": "동구"},
    {"area_id": "A004", "area_name": "1913 송정역시장 / 광주송정역", "district": "광산구"},
    {"area_id": "A005", "area_name": "상무지구", "district": "서구"},
]

MOCK_VISITOR_BY_AREA_ID = {
    "A001": {
        "visitor_count_gu": 172000,
        "visitor_growth": 14.5,
        "visitor_score": 92,
        "visitor_summary": "도심 쇼핑과 식음 수요가 함께 몰리는 고방문 상권",
    },
    "A002": {
        "visitor_count_gu": 98000,
        "visitor_growth": 11.0,
        "visitor_score": 78,
        "visitor_summary": "역사문화 골목 방문과 카페 체류가 꾸준한 관광형 수요",
    },
    "A003": {
        "visitor_count_gu": 158000,
        "visitor_growth": 20.5,
        "visitor_score": 95,
        "visitor_summary": "문화행사와 전시 관람 흐름이 강한 핵심 방문 수요",
    },
    "A004": {
        "visitor_count_gu": 122000,
        "visitor_growth": 8.0,
        "visitor_score": 84,
        "visitor_summary": "철도역과 전통시장 유입이 결합된 외부 방문 수요",
    },
    "A005": {
        "visitor_count_gu": 135000,
        "visitor_growth": 3.2,
        "visitor_score": 76,
        "visitor_summary": "업무지구와 야간 소비가 안정적으로 이어지는 방문 수요",
    },
}

EMPTY_VISITOR_FEATURES = {
    "visitor_count_gu": 0,
    "visitor_growth": 0,
    "visitor_score": 0,
    "visitor_summary": "방문자 mock 데이터 없음",
}


def read_area_rows() -> list[dict[str, object]]:
    if not AREAS_PATH.exists():
        print("areas.csv not found. Using built-in visitor area fallback.")
        return DEFAULT_AREAS

    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    required_columns = {"area_id", "area_name", "district"}
    missing_columns = required_columns - set(areas.columns)
    if missing_columns:
        print(
            f"areas.csv is missing {sorted(missing_columns)}. "
            "Using built-in visitor area fallback."
        )
        return DEFAULT_AREAS

    return areas[["area_id", "area_name", "district"]].to_dict("records")


def build_feature_rows(area_rows: list[dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for area in area_rows:
        area_id = str(area["area_id"])
        visitor_features = MOCK_VISITOR_BY_AREA_ID.get(area_id, EMPTY_VISITOR_FEATURES)
        rows.append(
            {
                "area_id": area_id,
                "area_name": str(area["area_name"]),
                "district": str(area["district"]),
                **visitor_features,
            }
        )

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main() -> None:
    print("Generating mock visitor demand features.")
    features = build_feature_rows(read_area_rows())
    save_csv_safe(features, OUTPUT_PATH)

    print("Visitor feature summary:")
    for _, row in features.iterrows():
        print(
            f"- {row['area_id']} {row['area_name']}: "
            f"visitor_count_gu={row['visitor_count_gu']}, "
            f"visitor_growth={row['visitor_growth']}, "
            f"visitor_score={row['visitor_score']}"
        )


if __name__ == "__main__":
    main()
