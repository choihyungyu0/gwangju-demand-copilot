from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset_scored.csv"
OUTPUT_PATH = ROOT_DIR / "public" / "predictions.json"


def read_rows() -> list[dict[str, str]]:
    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def as_float(row: dict[str, str], column: str) -> float:
    return float(row[column])


def pct_change(current: float, baseline: float) -> str:
    if baseline == 0:
        return "+0%"
    value = round(((current - baseline) / baseline) * 100)
    sign = "+" if value >= 0 else ""
    return f"{sign}{value}%"


def risk_level(latest_rows: list[dict[str, str]], predicted_score: int) -> str:
    rain_days = sum(int(row["rain_flag"]) for row in latest_rows)
    scores = [as_float(row, "demand_score") for row in latest_rows]
    volatility = pstdev(scores) if len(scores) > 1 else 0

    if predicted_score < 55 or rain_days >= 2 or volatility >= 18:
        return "높음"
    if predicted_score < 72 or rain_days == 1 or volatility >= 10:
        return "중간"
    return "낮음"


def build_top_factors(latest_rows: list[dict[str, str]]) -> list[str]:
    avg_visitor = mean(as_float(row, "visitor_score") for row in latest_rows)
    avg_event = mean(as_float(row, "event_score") for row in latest_rows)
    avg_tourism = mean(as_float(row, "tourism_score") for row in latest_rows)
    avg_store = mean(as_float(row, "store_score") for row in latest_rows)
    avg_weather = mean(as_float(row, "weather_score") for row in latest_rows)

    candidates = [
        (avg_visitor, "방문자 흐름이 수요 점수에 가장 크게 기여"),
        (avg_event, "행사·이벤트 일정이 단기 수요를 끌어올림"),
        (avg_tourism, "관광 자원 밀도가 방문 목적성을 강화"),
        (avg_store, "상가·음식·소매 밀도가 소비 전환 가능성을 높임"),
        (avg_weather, "날씨 조건이 보행과 체류 수요에 영향"),
    ]
    candidates.sort(reverse=True, key=lambda item: item[0])
    return [label for _, label in candidates[:3]]


def build_recommendations(
    area_name: str, latest_rows: list[dict[str, str]], predicted_score: int, risk: str
) -> list[str]:
    avg_food = mean(as_float(row, "food_count") for row in latest_rows)
    avg_cafe = mean(as_float(row, "cafe_count") for row in latest_rows)
    avg_event = mean(as_float(row, "event_count") for row in latest_rows)
    rain_days = sum(int(row["rain_flag"]) for row in latest_rows)

    recommendations: list[str] = []
    if predicted_score >= 80:
        recommendations.append("피크 시간대 판매·응대 인력을 보강")
    else:
        recommendations.append("고정 인력은 유지하고 시간대별 탄력 배치를 준비")

    if avg_food >= 300:
        recommendations.append("식음 인기 품목 재고를 선제적으로 확대")
    elif avg_cafe >= 140:
        recommendations.append("카페·디저트 체류형 상품을 전면 배치")
    else:
        recommendations.append("소량 재고와 빠른 회전 상품 중심으로 운영")

    if avg_event >= 4:
        recommendations.append("행사 전후 2시간 프로모션과 안내 문구를 준비")
    elif rain_days > 0:
        recommendations.append("우천 가능일에는 배달·실내 체류 상품 노출을 강화")
    else:
        recommendations.append(f"{area_name} 방문객 대상 현장 쿠폰을 운영")

    if risk == "높음":
        recommendations.append("예약 취소와 우천 변수에 대비해 당일 발주를 보수적으로 조정")

    return recommendations[:4]


def build_summary(area_name: str, predicted_score: int, change_text: str, risk: str) -> str:
    return (
        f"{area_name}의 최근 7일 예측 수요는 {predicted_score}점이며 "
        f"이전 기간 평균 대비 {change_text}입니다. 운영 리스크는 {risk} 수준으로 "
        "인력, 재고, 프로모션을 함께 조정하는 것이 좋습니다."
    )


def make_prediction(area_rows: list[dict[str, str]]) -> dict[str, object]:
    area_rows.sort(key=lambda row: row["date"])
    latest_rows = area_rows[-7:]
    history_rows = area_rows[:-7] or area_rows

    latest_avg = mean(as_float(row, "demand_score") for row in latest_rows)
    history_avg = mean(as_float(row, "demand_score") for row in history_rows)
    predicted_score = round(latest_avg)
    change_text = pct_change(latest_avg, history_avg)
    risk = risk_level(latest_rows, predicted_score)
    first = latest_rows[0]

    return {
        "area_id": first["area_id"],
        "area_name": first["area_name"],
        "district": first["district"],
        "predicted_score": predicted_score,
        "change_vs_avg": change_text,
        "risk_level": risk,
        "summary": build_summary(first["area_name"], predicted_score, change_text, risk),
        "top_factors": build_top_factors(latest_rows),
        "recommendations": build_recommendations(
            first["area_name"], latest_rows, predicted_score, risk
        ),
        "forecast": [
            {"date": row["date"], "score": round(as_float(row, "demand_score"))}
            for row in latest_rows
        ],
    }


def main() -> None:
    rows = read_rows()
    rows_by_area: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_area[row["area_id"]].append(row)

    predictions = [
        make_prediction(rows_by_area[area_id]) for area_id in sorted(rows_by_area.keys())
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"Wrote {len(predictions)} area predictions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
