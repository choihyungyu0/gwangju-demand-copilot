from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
AREA_FEATURES_PATH = ROOT_DIR / "data" / "processed" / "area_features_scored.csv"
METRICS_PATH = ROOT_DIR / "data" / "processed" / "model_metrics.json"
IMPORTANCE_PATH = ROOT_DIR / "data" / "processed" / "feature_importance.csv"


def read_metrics() -> dict[str, object]:
    if not METRICS_PATH.exists():
        print("model_metrics.json not found. Using empty model metric fallback.")
        return {"mae": "", "rmse": "", "r2": ""}

    with METRICS_PATH.open("r", encoding="utf-8") as file:
        metrics = json.load(file)
    return {
        "mae": metrics.get("mae", ""),
        "rmse": metrics.get("rmse", ""),
        "r2": metrics.get("r2", ""),
    }


def read_top_features() -> str:
    if not IMPORTANCE_PATH.exists():
        print("feature_importance.csv not found. Using empty model feature fallback.")
        return ""

    importance = pd.read_csv(IMPORTANCE_PATH, encoding="utf-8-sig")
    if importance.empty or "feature" not in importance.columns:
        return ""

    return ", ".join(importance.head(5)["feature"].astype(str).tolist())


def main() -> None:
    print("Applying model insight fields to area_features_scored.csv.")
    if not AREA_FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing scored area features: {AREA_FEATURES_PATH}")

    rows = pd.read_csv(AREA_FEATURES_PATH, encoding="utf-8-sig")
    metrics = read_metrics()
    top_features = read_top_features()

    rows["model_mae"] = metrics["mae"]
    rows["model_rmse"] = metrics["rmse"]
    rows["model_r2"] = metrics["r2"]
    rows["top_model_features"] = top_features

    save_csv_safe(rows, AREA_FEATURES_PATH)
    if top_features:
        print(f"Applied model metrics and top features: {top_features}")
    else:
        print("Model metrics are not available yet. The UI will show the safe fallback message.")


if __name__ == "__main__":
    main()
