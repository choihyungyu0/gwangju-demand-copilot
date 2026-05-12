from __future__ import annotations

from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "processed" / "area_features_full.csv"
OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "area_features_scored.csv"

SAFE_DEFAULTS = {
    "visitor_score": 70,
    "weather_score": 85,
    "tourism_score": 60,
    "event_count": 0,
    "matched_store_count": 0,
    "visitor_growth": 0,
    "rain_flag": 0,
    "rain_mm": 0,
}


def numeric_column(rows: pd.DataFrame, column: str, fallback: float) -> pd.Series:
    if column not in rows.columns:
        print(f"Missing {column}. Using safe fallback: {fallback}")
        return pd.Series(fallback, index=rows.index)
    return pd.to_numeric(rows[column], errors="coerce").fillna(fallback)


def normalize_series(series: pd.Series) -> pd.Series:
    low = series.min()
    high = series.max()
    if high == low:
        if high == 0:
            return pd.Series(0, index=series.index)
        return pd.Series(50, index=series.index)
    return ((series - low) / (high - low) * 100).clip(lower=0, upper=100)


def score_level(score: int) -> str:
    if score >= 85:
        return "매우 높음"
    if score >= 70:
        return "높음"
    if score >= 55:
        return "보통"
    return "낮음"


def score_summary(area_name: str, score: int, level: str) -> str:
    return (
        f"{area_name}의 최종 수요예측 점수는 {score}점이며 {level} 수준입니다. "
        "상권 밀도, 관광/행사 매력, 방문 흐름, 날씨 리스크를 함께 반영한 MVP 점수입니다."
    )


def build_reasons(row: pd.Series) -> list[str]:
    reasons: list[str] = []
    if row["commercial_score"] >= 70:
        reasons.append("상권 밀집도가 높아 기본 수요가 높습니다.")
    elif row["commercial_score"] <= 30:
        reasons.append("상권 밀집도는 낮지만 목적 방문 수요를 함께 확인해야 합니다.")
    else:
        reasons.append("상권 밀집도는 안정적인 기본 수요를 만듭니다.")

    if row["tourism_component_score"] >= 70 or row["event_component_score"] >= 60:
        reasons.append("관광/행사 영향으로 주말 방문 가능성이 높습니다.")
    else:
        reasons.append("관광/행사 영향은 제한적이어서 생활권 수요 비중이 큽니다.")

    if row["visitor_component_score"] >= 80 or row["visitor_growth"] > 0:
        reasons.append("방문자 증가 추세가 있어 수요 상승 가능성이 있습니다.")
    elif row["visitor_growth"] < 0:
        reasons.append("방문자 감소 가능성이 있어 보수적인 운영이 필요합니다.")
    else:
        reasons.append("방문 수요는 안정적인 흐름을 보입니다.")

    if row["weather_risk_level"] == "높음" or row["rain_flag"] == 1:
        reasons.append("강수 리스크가 있어 야외 유입은 줄어들 수 있습니다.")
    elif row["weather_component_score"] >= 80:
        reasons.append("날씨 조건이 양호해 외부 유입에 유리합니다.")

    return reasons[:3]


def build_risk_summary(row: pd.Series) -> str:
    if row["weather_risk_level"] == "높음" or row["rain_mm"] >= 15:
        return "강수 리스크가 높아 야외 홍보와 보행 유입은 보수적으로 보는 것이 좋습니다."
    if row["rain_flag"] == 1:
        return "비 예보가 있어 실내 유입 동선과 우천 안내를 준비해야 합니다."
    if row["predicted_score"] < 55:
        return "수요 점수가 낮아 재고와 인력 운영을 보수적으로 잡는 것이 좋습니다."
    return "큰 날씨 리스크는 낮은 편이며 기본 수요 흐름을 중심으로 운영할 수 있습니다."


def build_actions(row: pd.Series) -> list[str]:
    actions: list[str] = []
    if row["predicted_score"] >= 80:
        actions.append("피크 시간대 판매·응대 인력을 미리 보강하세요.")
    elif row["predicted_score"] >= 60:
        actions.append("기본 인력은 유지하고 점심·저녁 피크에 탄력 배치하세요.")
    else:
        actions.append("고정비를 줄이고 소량 재고 중심으로 운영하세요.")

    if row["rain_flag"] == 1 or row["weather_risk_level"] == "높음":
        actions.append("우천 안내, 실내 체류 상품, 배달 노출을 강화하세요.")
    else:
        actions.append("매장 앞 안내와 현장 쿠폰으로 보행 유입을 높이세요.")

    if row["event_component_score"] >= 60:
        actions.append("행사 전후 2시간 프로모션과 빠른 결제 동선을 준비하세요.")
    elif row["visitor_growth"] > 0:
        actions.append("방문자 증가에 맞춰 인기 품목 재고를 선제적으로 확보하세요.")
    else:
        actions.append("단골·생활권 고객 대상 재방문 혜택을 운영하세요.")

    return actions[:3]


def main() -> None:
    print("Calculating explainable demand prediction scores.")
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_PATH}")

    rows = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    if rows.empty:
        raise ValueError("area_features_full.csv is empty.")

    matched_store_count = numeric_column(
        rows, "matched_store_count", SAFE_DEFAULTS["matched_store_count"]
    )
    event_count = numeric_column(rows, "event_count", SAFE_DEFAULTS["event_count"])

    rows["commercial_score"] = normalize_series(matched_store_count).round(1)
    rows["tourism_component_score"] = numeric_column(
        rows, "tourism_score", SAFE_DEFAULTS["tourism_score"]
    ).clip(lower=0, upper=100)
    rows["visitor_component_score"] = numeric_column(
        rows, "visitor_score", SAFE_DEFAULTS["visitor_score"]
    ).clip(lower=0, upper=100)
    rows["event_component_score"] = normalize_series(event_count).round(1)
    rows["weather_component_score"] = numeric_column(
        rows, "weather_score", SAFE_DEFAULTS["weather_score"]
    ).clip(lower=0, upper=100)

    rows["visitor_growth"] = numeric_column(
        rows, "visitor_growth", SAFE_DEFAULTS["visitor_growth"]
    )
    rows["rain_flag"] = numeric_column(rows, "rain_flag", SAFE_DEFAULTS["rain_flag"]).round().astype(int)
    rows["rain_mm"] = numeric_column(rows, "rain_mm", SAFE_DEFAULTS["rain_mm"])
    if "weather_risk_level" not in rows.columns:
        rows["weather_risk_level"] = "낮음"
    rows["weather_risk_level"] = rows["weather_risk_level"].fillna("낮음")

    rows["predicted_score"] = (
        rows["commercial_score"] * 0.25
        + rows["tourism_component_score"] * 0.20
        + rows["visitor_component_score"] * 0.25
        + rows["event_component_score"] * 0.10
        + rows["weather_component_score"] * 0.20
    ).round().clip(lower=0, upper=100).astype(int)

    rows["score_level"] = rows["predicted_score"].apply(score_level)
    rows["score_summary"] = rows.apply(
        lambda row: score_summary(str(row["area_name"]), int(row["predicted_score"]), str(row["score_level"])),
        axis=1,
    )

    reason_rows = rows.apply(build_reasons, axis=1)
    rows["score_reason_1"] = reason_rows.apply(lambda reasons: reasons[0])
    rows["score_reason_2"] = reason_rows.apply(lambda reasons: reasons[1])
    rows["score_reason_3"] = reason_rows.apply(lambda reasons: reasons[2])
    rows["risk_summary"] = rows.apply(build_risk_summary, axis=1)

    action_rows = rows.apply(build_actions, axis=1)
    rows["recommended_action_1"] = action_rows.apply(lambda actions: actions[0])
    rows["recommended_action_2"] = action_rows.apply(lambda actions: actions[1])
    rows["recommended_action_3"] = action_rows.apply(lambda actions: actions[2])

    save_csv_safe(rows, OUTPUT_PATH)

    print("Demand score summary:")
    print(
        rows[
            [
                "area_id",
                "area_name",
                "predicted_score",
                "score_level",
                "commercial_score",
                "tourism_component_score",
                "visitor_component_score",
                "event_component_score",
                "weather_component_score",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
