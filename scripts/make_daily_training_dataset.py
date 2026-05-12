from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from random import Random

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "area_features_scored.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_demand_training.csv"
START_DATE = date(2026, 5, 1)
END_DATE = date(2026, 6, 29)
RANDOM_SEED = 42

OUTPUT_COLUMNS = [
    "date",
    "area_id",
    "area_name",
    "district",
    "day_of_week",
    "is_weekend",
    "matched_store_count",
    "food_count",
    "cafe_count",
    "retail_count",
    "accommodation_count",
    "tourism_score",
    "tourist_spot_count",
    "event_count",
    "culture_count",
    "visitor_count_gu",
    "visitor_growth",
    "visitor_score",
    "temp",
    "rain_mm",
    "rain_flag",
    "weather_score",
    "commercial_score",
    "tourism_component_score",
    "visitor_component_score",
    "event_component_score",
    "weather_component_score",
    "demand_score",
]


def as_number(row: pd.Series, column: str, fallback: float = 0) -> float:
    value = row.get(column, fallback)
    if pd.isna(value):
        return fallback
    return float(value)


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def daterange(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=offset) for offset in range(days)]


def weekend_visitor_boost(area_id: str) -> float:
    return {
        "A001": 8,
        "A002": 5,
        "A003": 9,
        "A004": 7,
        "A005": 1,
    }.get(area_id, 3)


def rain_sensitivity(area_id: str) -> float:
    return {
        "A001": 9,
        "A002": 10,
        "A003": 6,
        "A004": 5,
        "A005": 3,
    }.get(area_id, 5)


def daily_weather(base_temp: float, base_rain_mm: float, area_index: int, day_index: int) -> tuple[float, float, int]:
    seasonal_wave = ((day_index % 14) - 7) * 0.35
    temp = round(base_temp + seasonal_wave + area_index * 0.2, 1)
    rain_day = (day_index + area_index * 3) % 11 in {2, 7}
    if rain_day:
        rain_mm = round(max(2.0, base_rain_mm * 0.55 + ((day_index % 5) + 1) * 1.8), 1)
    else:
        rain_mm = 0.0
    return temp, rain_mm, int(rain_mm > 0)


def build_daily_row(area: pd.Series, target_date: date, day_index: int, area_index: int, rng: Random) -> dict[str, object]:
    area_id = str(area["area_id"])
    day_of_week = target_date.weekday()
    is_weekend = int(day_of_week >= 5)

    temp, rain_mm, rain_flag = daily_weather(
        as_number(area, "temp", 22),
        as_number(area, "rain_mm", 0),
        area_index,
        day_index,
    )

    event_count = as_number(area, "event_count", 0)
    if is_weekend and area_id in {"A001", "A003"}:
        event_count += 2
    elif is_weekend and area_id in {"A002", "A004"}:
        event_count += 1

    visitor_score = as_number(area, "visitor_score", 70)
    visitor_score += weekend_visitor_boost(area_id) if is_weekend else 0
    if area_id == "A005" and day_of_week < 5:
        visitor_score += 3
    if area_id == "A004" and is_weekend:
        visitor_score += 3
    if rain_flag:
        visitor_score -= rain_sensitivity(area_id) * 0.4
    visitor_score += rng.uniform(-2.0, 2.0)
    visitor_score = round(clamp(visitor_score), 1)

    visitor_count = as_number(area, "visitor_count_gu", 90000)
    visitor_multiplier = 1 + ((visitor_score - as_number(area, "visitor_score", 70)) / 100)
    visitor_count = round(visitor_count * visitor_multiplier)

    weather_score = 88 - abs(temp - 23) * 1.5
    if rain_flag:
        weather_score -= 18 + rain_mm * 0.9
    weather_score = round(clamp(weather_score), 1)

    commercial_score = as_number(area, "commercial_score", 50)
    tourism_component_score = as_number(area, "tourism_component_score", as_number(area, "tourism_score", 60))
    visitor_component_score = visitor_score
    event_component_score = clamp(event_count * 9)
    weather_component_score = weather_score

    demand_score = (
        commercial_score * 0.25
        + tourism_component_score * 0.20
        + visitor_component_score * 0.25
        + event_component_score * 0.10
        + weather_component_score * 0.20
    )
    demand_score = round(clamp(demand_score), 1)

    return {
        "date": target_date.isoformat(),
        "area_id": area_id,
        "area_name": area["area_name"],
        "district": area["district"],
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "matched_store_count": round(as_number(area, "matched_store_count")),
        "food_count": round(as_number(area, "food_count")),
        "cafe_count": round(as_number(area, "cafe_count")),
        "retail_count": round(as_number(area, "retail_count")),
        "accommodation_count": round(as_number(area, "accommodation_count")),
        "tourism_score": round(as_number(area, "tourism_score", 60)),
        "tourist_spot_count": round(as_number(area, "tourist_spot_count")),
        "event_count": round(event_count),
        "culture_count": round(as_number(area, "culture_count")),
        "visitor_count_gu": visitor_count,
        "visitor_growth": round(as_number(area, "visitor_growth", 0), 1),
        "visitor_score": visitor_score,
        "temp": temp,
        "rain_mm": rain_mm,
        "rain_flag": rain_flag,
        "weather_score": weather_score,
        "commercial_score": round(commercial_score, 1),
        "tourism_component_score": round(tourism_component_score, 1),
        "visitor_component_score": round(visitor_component_score, 1),
        "event_component_score": round(event_component_score, 1),
        "weather_component_score": round(weather_component_score, 1),
        "demand_score": demand_score,
    }


def main() -> None:
    print("Generating 60-day daily demand training dataset.")
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_PATH}")

    area_rows = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    rng = Random(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    dates = daterange(START_DATE, END_DATE)
    for area_index, (_, area) in enumerate(area_rows.iterrows()):
        for day_index, target_date in enumerate(dates):
            rows.append(build_daily_row(area, target_date, day_index, area_index, rng))

    output = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    save_csv_safe(output, OUTPUT_PATH)
    print(f"Wrote {len(output)} rows to {OUTPUT_PATH}")
    print(f"Date range: {START_DATE.isoformat()} to {END_DATE.isoformat()}")


if __name__ == "__main__":
    main()
