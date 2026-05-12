from __future__ import annotations

from pathlib import Path

import make_prediction_json
import make_mock_tourism_features
import merge_visitor_features
from merge_tourism_features import (
    OUTPUT_PATH,
    STORE_FEATURES_PATH,
    merge_feature_files,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
REAL_TOURISM_FEATURES_PATH = (
    ROOT_DIR / "data" / "processed" / "tourism_area_features_real.csv"
)
MOCK_TOURISM_FEATURES_PATH = (
    ROOT_DIR / "data" / "processed" / "tourism_area_features.csv"
)


def select_tourism_features_path() -> Path:
    if REAL_TOURISM_FEATURES_PATH.exists():
        print(f"Using real TourAPI tourism features: {REAL_TOURISM_FEATURES_PATH}")
        return REAL_TOURISM_FEATURES_PATH

    print(
        "Real TourAPI tourism features were not found. "
        "Using mock tourism fallback instead."
    )
    if not MOCK_TOURISM_FEATURES_PATH.exists():
        print("Mock tourism features are missing, so they will be regenerated now.")
        make_mock_tourism_features.main()

    if not MOCK_TOURISM_FEATURES_PATH.exists():
        raise FileNotFoundError(
            "No real or mock tourism feature CSV is available to apply."
        )

    print(f"Using mock tourism features: {MOCK_TOURISM_FEATURES_PATH}")
    return MOCK_TOURISM_FEATURES_PATH


def main() -> None:
    print("Applying tourism features to the full area feature table.")
    tourism_features_path = select_tourism_features_path()
    merge_feature_files(
        store_features_path=STORE_FEATURES_PATH,
        tourism_features_path=tourism_features_path,
        output_path=OUTPUT_PATH,
    )

    print("Reapplying visitor demand features after tourism merge.")
    merge_visitor_features.main()

    print("Regenerating public/predictions.json from merged area features.")
    make_prediction_json.main()


if __name__ == "__main__":
    main()
