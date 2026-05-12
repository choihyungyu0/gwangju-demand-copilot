from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "weather_area_features.csv"

OUTPUT_COLUMNS = [
    "area_id",
    "area_name",
    "district",
    "temp",
    "rain_mm",
    "rain_flag",
    "weather_score",
    "weather_risk_level",
    "weather_summary",
]

DEFAULT_AREAS = [
    {"area_id": "A001", "area_name": "충장로 / 금남로", "district": "동구"},
    {"area_id": "A002", "area_name": "양림동 역사문화마을", "district": "남구"},
    {"area_id": "A003", "area_name": "국립아시아문화전당 주변", "district": "동구"},
    {"area_id": "A004", "area_name": "1913 송정역시장 / 광주송정역", "district": "광산구"},
    {"area_id": "A005", "area_name": "상무지구", "district": "서구"},
]

MOCK_WEATHER_BY_AREA_ID = {
    "A001": {
        "temp": 24.0,
        "rain_mm": 12.5,
        "rain_flag": 1,
        "weather_score": 58,
        "weather_risk_level": "중간",
        "weather_summary": "보행 쇼핑 수요가 비에 민감해 우산 동선과 실내 유입 안내가 필요",
    },
    "A002": {
        "temp": 23.0,
        "rain_mm": 18.0,
        "rain_flag": 1,
        "weather_score": 52,
        "weather_risk_level": "높음",
        "weather_summary": "골목 관광과 도보 이동 비중이 높아 강수 시 체류 전환이 필요",
    },
    "A003": {
        "temp": 25.0,
        "rain_mm": 4.0,
        "rain_flag": 1,
        "weather_score": 72,
        "weather_risk_level": "중간",
        "weather_summary": "소나기 가능성은 있으나 실내 문화시설 유입으로 일부 완충 가능",
    },
    "A004": {
        "temp": 22.0,
        "rain_mm": 0.0,
        "rain_flag": 0,
        "weather_score": 88,
        "weather_risk_level": "낮음",
        "weather_summary": "맑은 날씨와 역세권 이동 수요가 안정적으로 유지",
    },
    "A005": {
        "temp": 26.0,
        "rain_mm": 9.0,
        "rain_flag": 1,
        "weather_score": 70,
        "weather_risk_level": "중간",
        "weather_summary": "업무·야간 수요가 있어 강수 영향은 비교적 완만",
    },
}

EMPTY_WEATHER_FEATURES = {
    "temp": 22.0,
    "rain_mm": 0.0,
    "rain_flag": 0,
    "weather_score": 75,
    "weather_risk_level": "낮음",
    "weather_summary": "날씨 mock 데이터 없음",
}


def read_area_rows() -> list[dict[str, object]]:
    if not AREAS_PATH.exists():
        print("areas.csv not found. Using built-in weather area fallback.")
        return DEFAULT_AREAS

    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    required_columns = {"area_id", "area_name", "district"}
    missing_columns = required_columns - set(areas.columns)
    if missing_columns:
        print(
            f"areas.csv is missing {sorted(missing_columns)}. "
            "Using built-in weather area fallback."
        )
        return DEFAULT_AREAS

    return areas[["area_id", "area_name", "district"]].to_dict("records")


def build_feature_rows(area_rows: list[dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for area in area_rows:
        area_id = str(area["area_id"])
        weather_features = MOCK_WEATHER_BY_AREA_ID.get(area_id, EMPTY_WEATHER_FEATURES)
        rows.append(
            {
                "area_id": area_id,
                "area_name": str(area["area_name"]),
                "district": str(area["district"]),
                **weather_features,
            }
        )

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def main() -> None:
    print("Generating mock weather demand-risk features.")
    features = build_feature_rows(read_area_rows())
    save_csv_safe(features, OUTPUT_PATH)

    print("Weather feature summary:")
    for _, row in features.iterrows():
        print(
            f"- {row['area_id']} {row['area_name']}: "
            f"temp={row['temp']}, "
            f"rain_mm={row['rain_mm']}, "
            f"rain_flag={row['rain_flag']}, "
            f"weather_score={row['weather_score']}, "
            f"weather_risk_level={row['weather_risk_level']}"
        )


if __name__ == "__main__":
    main()
