from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "daily_area_dataset_scored.csv"
SCORED_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "area_features_scored.csv"
AREA_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "area_features_full.csv"
TOURISM_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "tourism_area_features.csv"
OUTPUT_PATH = ROOT_DIR / "public" / "predictions.json"


def read_rows() -> list[dict[str, str]]:
    with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_area_features() -> dict[str, dict[str, str]]:
    for feature_path in [SCORED_FEATURES_PATH, AREA_FEATURES_PATH, TOURISM_FEATURES_PATH]:
        if feature_path.exists():
            print(f"Reading area feature enrichment: {feature_path}")
            with feature_path.open("r", encoding="utf-8-sig", newline="") as file:
                return {row["area_id"]: row for row in csv.DictReader(file)}

    print("No area feature enrichment CSV found. Using scored daily data fallback.")
    return {}


def row_float(row: dict[str, str], column: str, fallback: float = 0) -> float:
    value = row.get(column)
    if value in (None, ""):
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def feature_float(
    feature_row: dict[str, str],
    column: str,
    fallback: float,
) -> float:
    value = feature_row.get(column)
    if value in (None, ""):
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def feature_text(feature_row: dict[str, str], column: str, fallback: str) -> str:
    value = feature_row.get(column)
    if value in (None, ""):
        return fallback
    return value


def pct_change(current: float, baseline: float) -> str:
    if baseline == 0:
        return "+0%"
    value = round(((current - baseline) / baseline) * 100)
    sign = "+" if value >= 0 else ""
    return f"{sign}{value}%"


def weighted_demand_score(
    commercial_score: float,
    tourism_component_score: float,
    visitor_component_score: float,
    event_component_score: float,
    weather_component_score: float,
) -> float:
    return (
        commercial_score * 0.25
        + tourism_component_score * 0.20
        + visitor_component_score * 0.25
        + event_component_score * 0.10
        + weather_component_score * 0.20
    )


def score_level_from_score(score: int) -> str:
    if score >= 85:
        return "매우 높음"
    if score >= 70:
        return "높음"
    if score >= 55:
        return "보통"
    return "낮음"


def weather_risk_from_score(weather_score: float, rain_flag: int, rain_mm: float) -> str:
    if rain_mm >= 15 or weather_score < 55:
        return "높음"
    if rain_flag == 1 or rain_mm >= 5 or weather_score < 75:
        return "중간"
    return "낮음"


def risk_level(
    latest_rows: list[dict[str, str]],
    predicted_score: int,
    weather_risk_level: str,
    rain_flag: int,
) -> str:
    rain_days = sum(round(row_float(row, "rain_flag")) for row in latest_rows)
    scores = [row_float(row, "demand_score") for row in latest_rows]
    volatility = pstdev(scores) if len(scores) > 1 else 0

    if weather_risk_level == "높음" or predicted_score < 55 or rain_days >= 2 or volatility >= 18:
        return "높음"
    if weather_risk_level == "중간" or rain_flag == 1 or predicted_score < 72 or rain_days == 1 or volatility >= 10:
        return "중간"
    return "낮음"


def classify_area(
    area_name: str,
    tourism_score: int,
    tourist_spot_count: int,
    event_count: int,
    matched_store_count: int,
    food_count: int,
) -> str:
    if event_count >= 8:
        return "문화·행사 영향이 큰 상권"
    if "양림" in area_name or (tourist_spot_count >= 12 and tourism_score >= 80):
        return "관광형 카페 상권"
    if "송정역시장" in area_name or ("시장" in area_name and food_count >= 250):
        return "전통시장 기반 관광 상권"
    if tourism_score < 55 and matched_store_count >= 2500:
        return "직장인 중심 야간 상권"
    return "상업·관광 혼합 상권"


def default_score_reason(
    commercial_score: int,
    tourism_component_score: int,
    visitor_component_score: int,
    event_component_score: int,
    weather_component_score: int,
    visitor_growth: float,
    rain_flag: int,
    weather_risk_level: str,
) -> list[str]:
    reasons: list[str] = []
    if commercial_score >= 70:
        reasons.append("상권 밀집도가 높아 기본 수요가 높습니다.")
    elif commercial_score <= 30:
        reasons.append("상권 밀집도는 낮지만 목적 방문 수요를 함께 확인해야 합니다.")
    else:
        reasons.append("상권 밀집도는 안정적인 기본 수요를 만듭니다.")

    if tourism_component_score >= 70 or event_component_score >= 60:
        reasons.append("관광/행사 영향으로 주말 방문 가능성이 높습니다.")
    else:
        reasons.append("관광/행사 영향은 제한적이어서 생활권 수요 비중이 큽니다.")

    if visitor_component_score >= 80 or visitor_growth > 0:
        reasons.append("방문자 증가 추세가 있어 수요 상승 가능성이 있습니다.")
    elif visitor_growth < 0:
        reasons.append("방문자 감소 가능성이 있어 보수적인 운영이 필요합니다.")
    else:
        reasons.append("방문 수요는 안정적인 흐름을 보입니다.")

    if weather_risk_level == "높음" or rain_flag == 1:
        reasons.append("강수 리스크가 있어 야외 유입은 줄어들 수 있습니다.")
    elif weather_component_score >= 80:
        reasons.append("날씨 조건이 양호해 외부 유입에 유리합니다.")

    return reasons[:3]


def default_risk_summary(
    predicted_score: int,
    rain_flag: int,
    rain_mm: float,
    weather_risk_level: str,
) -> str:
    if weather_risk_level == "높음" or rain_mm >= 15:
        return "강수 리스크가 높아 야외 홍보와 보행 유입은 보수적으로 보는 것이 좋습니다."
    if rain_flag == 1:
        return "비 예보가 있어 실내 유입 동선과 우천 안내를 준비해야 합니다."
    if predicted_score < 55:
        return "수요 점수가 낮아 재고와 인력 운영을 보수적으로 잡는 것이 좋습니다."
    return "큰 날씨 리스크는 낮은 편이며 기본 수요 흐름을 중심으로 운영할 수 있습니다."


def default_actions(
    predicted_score: int,
    event_component_score: int,
    visitor_growth: float,
    rain_flag: int,
    weather_risk_level: str,
) -> list[str]:
    actions: list[str] = []
    if predicted_score >= 80:
        actions.append("피크 시간대 판매·응대 인력을 미리 보강하세요.")
    elif predicted_score >= 60:
        actions.append("기본 인력은 유지하고 점심·저녁 피크에 탄력 배치하세요.")
    else:
        actions.append("고정비를 줄이고 소량 재고 중심으로 운영하세요.")

    if rain_flag == 1 or weather_risk_level == "높음":
        actions.append("우천 안내, 실내 체류 상품, 배달 노출을 강화하세요.")
    else:
        actions.append("매장 앞 안내와 현장 쿠폰으로 보행 유입을 높이세요.")

    if event_component_score >= 60:
        actions.append("행사 전후 2시간 프로모션과 빠른 결제 동선을 준비하세요.")
    elif visitor_growth > 0:
        actions.append("방문자 증가에 맞춰 인기 품목 재고를 선제적으로 확보하세요.")
    else:
        actions.append("단골·생활권 고객 대상 재방문 혜택을 운영하세요.")
    return actions[:3]


def make_prediction(
    area_rows: list[dict[str, str]],
    area_feature_map: dict[str, dict[str, str]],
) -> dict[str, object]:
    area_rows.sort(key=lambda row: row["date"])
    latest_rows = area_rows[-7:]
    history_rows = area_rows[:-7] or area_rows

    first = latest_rows[0]
    area_features = area_feature_map.get(first["area_id"], {})

    matched_store_count = round(
        feature_float(area_features, "matched_store_count", row_float(first, "matched_store_count"))
    )
    food_count = round(feature_float(area_features, "food_count", row_float(first, "food_count")))
    tourism_score = round(
        feature_float(
            area_features,
            "tourism_score",
            mean(row_float(row, "tourism_score") for row in latest_rows),
        )
    )
    tourist_spot_count = round(
        feature_float(area_features, "tourist_spot_count", row_float(first, "tourist_spot_count"))
    )
    event_count = round(
        feature_float(
            area_features,
            "event_count",
            mean(row_float(row, "event_count") for row in latest_rows),
        )
    )
    culture_count = round(feature_float(area_features, "culture_count", row_float(first, "culture_count")))

    visitor_count_gu = round(
        feature_float(area_features, "visitor_count_gu", row_float(first, "visitor_count_gu"))
    )
    visitor_growth = feature_float(area_features, "visitor_growth", 0)
    visitor_score = round(
        feature_float(
            area_features,
            "visitor_score",
            mean(row_float(row, "visitor_score") for row in latest_rows),
        )
    )
    visitor_summary = feature_text(area_features, "visitor_summary", "방문자 feature 정보 없음")

    temp = round(
        feature_float(area_features, "temp", mean(row_float(row, "temp") for row in latest_rows)),
        1,
    )
    rain_mm = round(feature_float(area_features, "rain_mm", 0), 1)
    rain_flag = round(
        feature_float(area_features, "rain_flag", max(row_float(row, "rain_flag") for row in latest_rows))
    )
    weather_score = round(
        feature_float(
            area_features,
            "weather_score",
            mean(row_float(row, "weather_score") for row in latest_rows),
        )
    )
    weather_risk_level = feature_text(
        area_features,
        "weather_risk_level",
        weather_risk_from_score(weather_score, rain_flag, rain_mm),
    )
    weather_summary = feature_text(area_features, "weather_summary", "날씨 feature 정보 없음")

    commercial_score = round(
        feature_float(
            area_features,
            "commercial_score",
            mean(row_float(row, "store_score") for row in latest_rows),
        )
    )
    tourism_component_score = round(
        feature_float(area_features, "tourism_component_score", tourism_score)
    )
    visitor_component_score = round(
        feature_float(area_features, "visitor_component_score", visitor_score)
    )
    event_component_score = round(
        feature_float(
            area_features,
            "event_component_score",
            mean(row_float(row, "event_score") for row in latest_rows),
        )
    )
    weather_component_score = round(
        feature_float(area_features, "weather_component_score", weather_score)
    )

    latest_scores = [
        weighted_demand_score(
            commercial_score,
            tourism_component_score,
            visitor_component_score,
            event_component_score,
            weather_component_score,
        )
        for _ in latest_rows
    ]
    history_scores = [
        weighted_demand_score(
            commercial_score,
            tourism_component_score,
            visitor_component_score,
            event_component_score,
            weather_component_score,
        )
        for _ in history_rows
    ]
    latest_avg = mean(latest_scores)
    history_avg = mean(history_scores)
    predicted_score = round(feature_float(area_features, "predicted_score", latest_avg))
    change_text = pct_change(latest_avg, history_avg)
    risk = risk_level(latest_rows, predicted_score, weather_risk_level, rain_flag)

    score_level = feature_text(
        area_features, "score_level", score_level_from_score(predicted_score)
    )
    area_type = classify_area(
        first["area_name"],
        tourism_score,
        tourist_spot_count,
        event_count,
        matched_store_count,
        food_count,
    )

    fallback_reasons = default_score_reason(
        commercial_score,
        tourism_component_score,
        visitor_component_score,
        event_component_score,
        weather_component_score,
        visitor_growth,
        rain_flag,
        weather_risk_level,
    )
    score_reason_1 = feature_text(area_features, "score_reason_1", fallback_reasons[0])
    score_reason_2 = feature_text(area_features, "score_reason_2", fallback_reasons[1])
    score_reason_3 = feature_text(area_features, "score_reason_3", fallback_reasons[2])
    score_reasons = [score_reason_1, score_reason_2, score_reason_3]

    risk_summary = feature_text(
        area_features,
        "risk_summary",
        default_risk_summary(predicted_score, rain_flag, rain_mm, weather_risk_level),
    )
    fallback_actions = default_actions(
        predicted_score,
        event_component_score,
        visitor_growth,
        rain_flag,
        weather_risk_level,
    )
    recommended_action_1 = feature_text(
        area_features, "recommended_action_1", fallback_actions[0]
    )
    recommended_action_2 = feature_text(
        area_features, "recommended_action_2", fallback_actions[1]
    )
    recommended_action_3 = feature_text(
        area_features, "recommended_action_3", fallback_actions[2]
    )
    recommended_actions = [
        recommended_action_1,
        recommended_action_2,
        recommended_action_3,
    ]
    model_mae = feature_text(area_features, "model_mae", "")
    model_rmse = feature_text(area_features, "model_rmse", "")
    model_r2 = feature_text(area_features, "model_r2", "")
    top_model_features = feature_text(area_features, "top_model_features", "")

    score_summary = feature_text(
        area_features,
        "score_summary",
        (
            f"{first['area_name']}의 최종 수요예측 점수는 {predicted_score}점이며 "
            f"{score_level} 수준입니다. 상권, 관광/행사, 방문 흐름, 날씨를 함께 반영했습니다."
        ),
    )

    return {
        "area_id": first["area_id"],
        "area_name": first["area_name"],
        "district": first["district"],
        "matched_store_count": matched_store_count,
        "area_radius_m": round(row_float(first, "area_radius_m")),
        "tourism_score": tourism_score,
        "tourist_spot_count": tourist_spot_count,
        "event_count": event_count,
        "culture_count": culture_count,
        "visitor_count_gu": visitor_count_gu,
        "visitor_growth": round(visitor_growth, 1),
        "visitor_score": visitor_score,
        "visitor_summary": visitor_summary,
        "temp": temp,
        "rain_mm": rain_mm,
        "rain_flag": rain_flag,
        "weather_score": weather_score,
        "weather_risk_level": weather_risk_level,
        "weather_summary": weather_summary,
        "area_type_summary": area_type,
        "predicted_score": predicted_score,
        "commercial_score": commercial_score,
        "tourism_component_score": tourism_component_score,
        "visitor_component_score": visitor_component_score,
        "event_component_score": event_component_score,
        "weather_component_score": weather_component_score,
        "score_level": score_level,
        "score_summary": score_summary,
        "score_reason_1": score_reason_1,
        "score_reason_2": score_reason_2,
        "score_reason_3": score_reason_3,
        "risk_summary": risk_summary,
        "recommended_action_1": recommended_action_1,
        "recommended_action_2": recommended_action_2,
        "recommended_action_3": recommended_action_3,
        "model_mae": model_mae,
        "model_rmse": model_rmse,
        "model_r2": model_r2,
        "top_model_features": top_model_features,
        "change_vs_avg": change_text,
        "risk_level": risk,
        "summary": f"{score_summary} {risk_summary}",
        "top_factors": score_reasons,
        "recommendations": recommended_actions,
        "forecast": [
            {"date": row["date"], "score": round(score)}
            for row, score in zip(latest_rows, latest_scores)
        ],
    }


def main() -> None:
    rows = read_rows()
    area_feature_map = read_area_features()
    rows_by_area: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_area[row["area_id"]].append(row)

    predictions = [
        make_prediction(rows_by_area[area_id], area_feature_map)
        for area_id in sorted(rows_by_area.keys())
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print(f"Wrote {len(predictions)} area predictions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
