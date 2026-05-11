from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset.csv"
START_DATE = date(2026, 5, 1)
DAYS = 30


AREA_PROFILES = {
    "A001": {
        "visitor_base": 51000,
        "visitor_step": 430,
        "store_total": 1380,
        "food_count": 520,
        "cafe_count": 210,
        "retail_count": 420,
        "tourist_spot_count": 8,
        "event_base": 2,
    },
    "A002": {
        "visitor_base": 27500,
        "visitor_step": 260,
        "store_total": 430,
        "food_count": 150,
        "cafe_count": 170,
        "retail_count": 60,
        "tourist_spot_count": 14,
        "event_base": 1,
    },
    "A003": {
        "visitor_base": 42000,
        "visitor_step": 390,
        "store_total": 720,
        "food_count": 270,
        "cafe_count": 150,
        "retail_count": 115,
        "tourist_spot_count": 16,
        "event_base": 4,
    },
    "A004": {
        "visitor_base": 36500,
        "visitor_step": 340,
        "store_total": 610,
        "food_count": 250,
        "cafe_count": 85,
        "retail_count": 180,
        "tourist_spot_count": 9,
        "event_base": 2,
    },
    "A005": {
        "visitor_base": 45500,
        "visitor_step": 310,
        "store_total": 980,
        "food_count": 470,
        "cafe_count": 160,
        "retail_count": 145,
        "tourist_spot_count": 4,
        "event_base": 1,
    },
}


FIELDNAMES = [
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
]


def read_areas() -> list[dict[str, str]]:
    with AREAS_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def make_row(area: dict[str, str], day_index: int) -> dict[str, object]:
    current_date = START_DATE + timedelta(days=day_index)
    is_weekend = 1 if current_date.weekday() >= 5 else 0
    profile = AREA_PROFILES[area["area_id"]]

    weekly_wave = (day_index % 7) * profile["visitor_step"]
    weekend_boost = 7600 if is_weekend else 0
    rain_flag = 1 if (day_index + int(area["area_id"][-1])) % 9 == 0 else 0
    rain_penalty = 2600 if rain_flag else 0

    event_count = profile["event_base"]
    if is_weekend:
        event_count += 2
    if area["area_id"] == "A003" and day_index % 5 in (1, 2):
        event_count += 2
    if area["area_id"] == "A004" and is_weekend:
        event_count += 1
    if area["area_id"] == "A005" and current_date.weekday() in (3, 4):
        event_count += 1

    temp = 18 + (day_index % 10) + (1 if is_weekend else 0)
    visitor_count = (
        profile["visitor_base"] + weekly_wave + weekend_boost + (event_count * 850) - rain_penalty
    )

    return {
        "date": current_date.isoformat(),
        "area_id": area["area_id"],
        "area_name": area["area_name"],
        "district": area["district"],
        "is_weekend": is_weekend,
        "visitor_count_gu": visitor_count,
        "store_total": profile["store_total"],
        "food_count": profile["food_count"],
        "cafe_count": profile["cafe_count"],
        "retail_count": profile["retail_count"],
        "tourist_spot_count": profile["tourist_spot_count"],
        "event_count": event_count,
        "temp": temp,
        "rain_flag": rain_flag,
    }


def main() -> None:
    areas = read_areas()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = [make_row(area, day_index) for area in areas for day_index in range(DAYS)]

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
