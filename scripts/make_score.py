from __future__ import annotations

import csv
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset_scored.csv"

NUMERIC_COLUMNS = [
    "visitor_count_gu",
    "event_count",
    "tourist_spot_count",
    "store_total",
    "food_count",
    "cafe_count",
    "retail_count",
]

OUTPUT_FIELDS = [
    "date",
    "area_id",
    "area_name",
    "district",
    "is_weekend",
    "visitor_count_gu",
    "store_total",
    "food_count",
    "cafe_count",
    "retail_count",
    "tourist_spot_count",
    "event_count",
    "temp",
    "rain_flag",
    "visitor_score",
    "event_score",
    "tourism_score",
    "store_score",
    "weather_score",
    "demand_score",
]


def read_rows() -> list[dict[str, str]]:
    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def min_max(values: list[float]) -> tuple[float, float]:
    return min(values), max(values)


def normalize(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    return ((value - low) / (high - low)) * 100


def to_float(row: dict[str, str], column: str) -> float:
    return float(row[column])


def main() -> None:
    rows = read_rows()
    bounds = {
        column: min_max([to_float(row, column) for row in rows]) for column in NUMERIC_COLUMNS
    }

    scored_rows: list[dict[str, object]] = []
    for row in rows:
        visitor_score = normalize(
            to_float(row, "visitor_count_gu"), *bounds["visitor_count_gu"]
        )
        event_score = normalize(to_float(row, "event_count"), *bounds["event_count"])
        tourism_score = normalize(
            to_float(row, "tourist_spot_count"), *bounds["tourist_spot_count"]
        )

        store_parts = [
            normalize(to_float(row, "store_total"), *bounds["store_total"]),
            normalize(to_float(row, "food_count"), *bounds["food_count"]),
            normalize(to_float(row, "cafe_count"), *bounds["cafe_count"]),
            normalize(to_float(row, "retail_count"), *bounds["retail_count"]),
        ]
        store_score = sum(store_parts) / len(store_parts)

        temp = to_float(row, "temp")
        rain_flag = int(row["rain_flag"])
        weather_score = 82 - abs(temp - 22) * 2
        if rain_flag == 1:
            weather_score -= 32
        weather_score = max(0, min(100, weather_score))

        demand_score = (
            visitor_score * 0.4
            + event_score * 0.2
            + tourism_score * 0.15
            + store_score * 0.15
            + weather_score * 0.1
        )

        scored_row = dict(row)
        scored_row.update(
            {
                "visitor_score": round(visitor_score, 2),
                "event_score": round(event_score, 2),
                "tourism_score": round(tourism_score, 2),
                "store_score": round(store_score, 2),
                "weather_score": round(weather_score, 2),
                "demand_score": round(demand_score, 2),
            }
        )
        scored_rows.append(scored_row)

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(scored_rows)

    print(f"Wrote {len(scored_rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
