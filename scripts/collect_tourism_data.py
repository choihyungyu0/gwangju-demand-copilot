from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from save_csv_safe import save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
AREAS_PATH = ROOT_DIR / "data" / "processed" / "areas.csv"
RAW_OUTPUT_PATH = ROOT_DIR / "data" / "raw" / "tourism_api_results.json"
FEATURE_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "tourism_area_features_real.csv"

TOUR_API_ENDPOINT = "http://apis.data.go.kr/B551011/KorService2/locationBasedList2"
TOUR_API_APP_NAME = "GwangjuDemandCopilot"
TOUR_API_TIMEOUT_SECONDS = 20
TOUR_API_NUM_ROWS = 100
TOUR_API_MAX_PAGES = 3
TOUR_API_MAX_RADIUS_M = 20000

CONTENT_TYPES = {
    "tourist_spots": {
        "label": "tourist spots",
        "content_type_id": "12",
        "feature_column": "tourist_spot_count",
    },
    "culture": {
        "label": "cultural facilities",
        "content_type_id": "14",
        "feature_column": "culture_count",
    },
    "events": {
        "label": "events/festivals",
        "content_type_id": "15",
        "feature_column": "event_count",
    },
}

OUTPUT_COLUMNS = [
    "area_id",
    "area_name",
    "tourist_spot_count",
    "event_count",
    "culture_count",
    "tourism_score",
]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    print(f"Loading environment values from {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_service_key() -> str | None:
    load_env_file(ENV_PATH)
    service_key = os.environ.get("TOUR_API_SERVICE_KEY", "").strip()
    if not service_key or service_key == "your_tour_api_key_here":
        return None
    return service_key


def read_areas() -> pd.DataFrame:
    if not AREAS_PATH.exists():
        print(f"Could not find {AREAS_PATH}. Run the area/store pipeline first.")
        return pd.DataFrame()

    areas = pd.read_csv(AREAS_PATH, encoding="utf-8-sig")
    required_columns = {
        "area_id",
        "area_name",
        "center_lat",
        "center_lng",
        "radius_m",
    }
    missing_columns = required_columns - set(areas.columns)
    if missing_columns:
        print(
            f"{AREAS_PATH} is missing columns: {sorted(missing_columns)}. "
            "Cannot call location-based TourAPI without area centers."
        )
        return pd.DataFrame()

    return areas.sort_values("area_id").reset_index(drop=True)


def bounded_radius(value: Any) -> int:
    try:
        radius = int(round(float(value)))
    except (TypeError, ValueError):
        radius = 1000
    return max(1, min(radius, TOUR_API_MAX_RADIUS_M))


def build_params(
    service_key: str,
    area: pd.Series,
    content_type_id: str,
    page_no: int,
) -> dict[str, str | int]:
    return {
        "serviceKey": service_key,
        "MobileOS": "ETC",
        "MobileApp": TOUR_API_APP_NAME,
        "_type": "json",
        "arrange": "E",
        "mapX": str(area["center_lng"]),
        "mapY": str(area["center_lat"]),
        "radius": bounded_radius(area["radius_m"]),
        "contentTypeId": content_type_id,
        "numOfRows": TOUR_API_NUM_ROWS,
        "pageNo": page_no,
    }


def build_url(params: dict[str, str | int]) -> str:
    # Keep already URL-encoded service keys usable while encoding plain keys safely.
    return f"{TOUR_API_ENDPOINT}?{urlencode(params, safe='%')}"


def redacted_params(params: dict[str, str | int]) -> dict[str, str | int]:
    safe_params = dict(params)
    safe_params["serviceKey"] = "<redacted>"
    return safe_params


def normalize_items(data: dict[str, Any]) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
    response = data.get("response") if isinstance(data, dict) else {}
    body = response.get("body", {}) if isinstance(response, dict) else {}
    header = response.get("header", {}) if isinstance(response, dict) else {}

    total_count_raw = body.get("totalCount", 0) if isinstance(body, dict) else 0
    try:
        total_count = int(total_count_raw)
    except (TypeError, ValueError):
        total_count = 0

    items_container = body.get("items", {}) if isinstance(body, dict) else {}
    if isinstance(items_container, dict):
        items_raw = items_container.get("item", [])
    else:
        items_raw = []

    if isinstance(items_raw, dict):
        items = [items_raw]
    elif isinstance(items_raw, list):
        items = [item for item in items_raw if isinstance(item, dict)]
    else:
        items = []

    if total_count == 0 and items:
        total_count = len(items)

    return total_count, items, header if isinstance(header, dict) else {}


def fetch_tourapi_page(params: dict[str, str | int]) -> dict[str, Any]:
    url = build_url(params)
    request = Request(url, headers={"User-Agent": TOUR_API_APP_NAME})
    with urlopen(request, timeout=TOUR_API_TIMEOUT_SECONDS) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def collect_category(
    service_key: str,
    area: pd.Series,
    category_key: str,
    category: dict[str, str],
) -> dict[str, Any]:
    print(
        f"Requesting {category['label']} for {area['area_id']} "
        f"{area['area_name']} within {bounded_radius(area['radius_m'])}m."
    )

    all_items: list[dict[str, Any]] = []
    first_total_count = 0
    last_header: dict[str, Any] = {}
    request_examples: list[dict[str, str | int]] = []

    for page_no in range(1, TOUR_API_MAX_PAGES + 1):
        params = build_params(service_key, area, category["content_type_id"], page_no)
        request_examples.append(redacted_params(params))
        try:
            data = fetch_tourapi_page(params)
        except HTTPError as error:
            print(f"TourAPI HTTP error for {area['area_id']} {category['label']}: {error}")
            return {
                "category": category_key,
                "content_type_id": category["content_type_id"],
                "total_count": 0,
                "items": all_items,
                "requests": request_examples,
                "error": f"HTTPError: {error}",
            }
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"TourAPI request failed for {area['area_id']} {category['label']}: {error}")
            return {
                "category": category_key,
                "content_type_id": category["content_type_id"],
                "total_count": 0,
                "items": all_items,
                "requests": request_examples,
                "error": error.__class__.__name__,
            }

        total_count, items, header = normalize_items(data)
        if page_no == 1:
            first_total_count = total_count
        last_header = header
        all_items.extend(items)

        result_code = str(header.get("resultCode", ""))
        result_message = str(header.get("resultMsg", ""))
        if result_code and result_code not in {"0000", "OK"}:
            print(f"TourAPI returned {result_code}: {result_message}")
            break

        if len(all_items) >= total_count or not items:
            break

    print(
        f"Collected {len(all_items)} sample rows, total_count={first_total_count} "
        f"for {area['area_id']} {category['label']}."
    )
    return {
        "category": category_key,
        "content_type_id": category["content_type_id"],
        "total_count": first_total_count,
        "items": all_items,
        "requests": request_examples,
        "header": last_header,
    }


def tourism_score(
    tourist_spot_count: int,
    event_count: int,
    culture_count: int,
) -> int:
    weighted_score = (
        tourist_spot_count * 4
        + event_count * 7
        + culture_count * 5
    )
    return max(0, min(100, round(weighted_score)))


def collect_area(service_key: str, area: pd.Series) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_categories: dict[str, Any] = {}
    feature_row: dict[str, Any] = {
        "area_id": area["area_id"],
        "area_name": area["area_name"],
        "tourist_spot_count": 0,
        "event_count": 0,
        "culture_count": 0,
    }

    for category_key, category in CONTENT_TYPES.items():
        result = collect_category(service_key, area, category_key, category)
        raw_categories[category_key] = result
        feature_row[category["feature_column"]] = int(result.get("total_count", 0) or 0)

    feature_row["tourism_score"] = tourism_score(
        int(feature_row["tourist_spot_count"]),
        int(feature_row["event_count"]),
        int(feature_row["culture_count"]),
    )
    raw_area = {
        "area_id": area["area_id"],
        "area_name": area["area_name"],
        "center_lat": float(area["center_lat"]),
        "center_lng": float(area["center_lng"]),
        "radius_m": bounded_radius(area["radius_m"]),
        "categories": raw_categories,
    }
    return raw_area, feature_row


def save_raw_results(raw_results: dict[str, Any]) -> None:
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving raw TourAPI-like JSON: {RAW_OUTPUT_PATH}")
    RAW_OUTPUT_PATH.write_text(
        json.dumps(raw_results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    print("Preparing real tourism data collection from Korea Tourism Organization TourAPI.")
    service_key = read_service_key()
    if service_key is None:
        print(
            "TOUR_API_SERVICE_KEY is missing. Skipping real TourAPI collection "
            "and keeping the existing mock tourism fallback."
        )
        print("Add TOUR_API_SERVICE_KEY to .env when you are ready to collect real data.")
        return

    areas = read_areas()
    if areas.empty:
        print("No area rows available. Nothing to collect.")
        return

    raw_results: dict[str, Any] = {
        "source": "Korea Tourism Organization KorService2/locationBasedList2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "serviceKey is intentionally redacted from saved request parameters.",
        "areas": [],
    }
    feature_rows: list[dict[str, Any]] = []

    for _, area in areas.iterrows():
        raw_area, feature_row = collect_area(service_key, area)
        raw_results["areas"].append(raw_area)
        feature_rows.append(feature_row)

    features = pd.DataFrame(feature_rows, columns=OUTPUT_COLUMNS)
    save_raw_results(raw_results)
    save_csv_safe(features, FEATURE_OUTPUT_PATH)

    print("Real tourism feature summary:")
    for _, row in features.iterrows():
        print(
            f"- {row['area_id']} {row['area_name']}: "
            f"tourism_score={row['tourism_score']}, "
            f"tourist_spot_count={row['tourist_spot_count']}, "
            f"event_count={row['event_count']}, "
            f"culture_count={row['culture_count']}"
        )


if __name__ == "__main__":
    main()
