from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from save_csv_safe import CSV_ENCODING, save_csv_safe


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT_DIR / "data" / "raw" / "store_data.csv"
GWANGJU_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "gwangju_store_data.csv"
FEATURE_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "store_features.csv"
GWANGJU_TEMP_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "gwangju_store_data.tmp.csv"
FEATURE_TEMP_OUTPUT_PATH = ROOT_DIR / "data" / "processed" / "store_features.tmp.csv"
ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
CHUNK_SIZE = 100_000
PREVIEW_ROWS = 20

EXPECTED_KOREAN_TOKENS = [
    "상호명",
    "시도명",
    "시군구명",
    "상권업종대분류명",
    "상권업종중분류명",
    "위도",
    "경도",
    "광주",
]

BROKEN_TEXT_MARKERS = [
    "\ufffd",
    "�",
    "占",
    "Ã",
    "Â",
    "ì",
    "í",
    "ë",
    "ê",
    "¼",
    "½",
    "¾",
]

FIELD_CANDIDATES = {
    "sido_name": ["시도명", "시도"],
    "district": ["시군구명", "시군구"],
    "category_large": ["상권업종대분류명", "상권업종대분류", "대분류명"],
    "category_middle": ["상권업종중분류명", "상권업종중분류", "중분류명"],
    "store_name": ["상호명", "상호"],
    "latitude": ["위도", "lat", "latitude"],
    "longitude": ["경도", "lng", "lon", "longitude"],
}

AREA_ROWS = [
    {"area_id": "A001", "area_name": "충장로 / 금남로", "district": "동구"},
    {"area_id": "A002", "area_name": "양림동 역사문화마을", "district": "남구"},
    {"area_id": "A003", "area_name": "국립아시아문화전당 주변", "district": "동구"},
    {"area_id": "A004", "area_name": "1913 송정역시장 / 광주송정역", "district": "광산구"},
    {"area_id": "A005", "area_name": "상무지구", "district": "서구"},
]

DISTRICT_TO_AREAS = {
    "동구": [
        {"area_id": "A001", "area_name": "충장로 / 금남로"},
        {"area_id": "A003", "area_name": "국립아시아문화전당 주변"},
    ],
    "남구": [{"area_id": "A002", "area_name": "양림동 역사문화마을"}],
    "광산구": [{"area_id": "A004", "area_name": "1913 송정역시장 / 광주송정역"}],
    "서구": [{"area_id": "A005", "area_name": "상무지구"}],
}

CATEGORY_KEYWORDS = {
    "food": ["음식", "식당", "한식", "중식", "양식", "일식"],
    "cafe": ["카페", "커피", "디저트"],
    "retail": ["편의점", "쇼핑", "소매"],
    "accommodation": ["호텔", "모텔", "게스트하우스", "숙박"],
}


def text_for_validation(frame: pd.DataFrame) -> str:
    column_text = " ".join(str(column) for column in frame.columns)
    value_text = " ".join(
        frame.fillna("").astype(str).head(PREVIEW_ROWS).to_numpy().ravel().tolist()
    )
    return f"{column_text} {value_text}"


def korean_validation_report(frame: pd.DataFrame) -> tuple[bool, str]:
    sample_text = text_for_validation(frame)
    hangul_count = len(re.findall(r"[가-힣]", sample_text))
    broken_count = sum(sample_text.count(marker) for marker in BROKEN_TEXT_MARKERS)
    token_hits = [token for token in EXPECTED_KOREAN_TOKENS if token in sample_text]

    if broken_count > 0:
        return False, f"broken text markers found: {broken_count}"
    if hangul_count < 20:
        return False, f"too few Korean characters found: {hangul_count}"
    if len(token_hits) < 4:
        return False, f"not enough expected Korean tokens found: {token_hits}"

    return True, f"Korean validation passed; token hits: {token_hits}"


def read_preview_with_encoding(encoding: str) -> pd.DataFrame:
    return pd.read_csv(
        RAW_PATH,
        encoding=encoding,
        encoding_errors="strict",
        dtype=str,
        nrows=PREVIEW_ROWS,
        on_bad_lines="skip",
    )


def detect_encoding() -> tuple[str, list[str]]:
    for encoding in ENCODINGS_TO_TRY:
        try:
            preview = read_preview_with_encoding(encoding)
        except UnicodeDecodeError as error:
            print(f"Rejected encoding {encoding}: decode error: {error}")
            continue

        is_valid, reason = korean_validation_report(preview)
        if is_valid:
            print(f"Accepted encoding {encoding}: {reason}")
            return encoding, list(preview.columns)

        print(f"Rejected encoding {encoding}: {reason}")

    raise ValueError(
        "Could not find an encoding that preserves Korean text. "
        f"Tried: {', '.join(ENCODINGS_TO_TRY)}"
    )


def normalize_column_name(column: str) -> str:
    return str(column).replace(" ", "").replace("\ufeff", "").strip().lower()


def resolve_columns(columns: list[str]) -> dict[str, str]:
    normalized_columns = {normalize_column_name(column): column for column in columns}
    resolved: dict[str, str] = {}

    for output_name, candidates in FIELD_CANDIDATES.items():
        for candidate in candidates:
            actual_column = normalized_columns.get(normalize_column_name(candidate))
            if actual_column:
                resolved[output_name] = actual_column
                break

    missing = [field for field in FIELD_CANDIDATES if field not in resolved]
    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
            + "\nDetected columns: "
            + ", ".join(columns)
        )

    return resolved


def keyword_pattern(keywords: list[str]) -> str:
    return "|".join(re.escape(keyword) for keyword in keywords)


def categorize_stores(frame: pd.DataFrame) -> pd.Series:
    search_text = (
        frame[["category_large", "category_middle", "store_name"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
    )

    category = pd.Series("other", index=frame.index)
    category[
        search_text.str.contains(keyword_pattern(CATEGORY_KEYWORDS["retail"]), na=False)
    ] = "retail"
    category[
        search_text.str.contains(keyword_pattern(CATEGORY_KEYWORDS["food"]), na=False)
    ] = "food"
    category[
        search_text.str.contains(keyword_pattern(CATEGORY_KEYWORDS["cafe"]), na=False)
    ] = "cafe"
    category[
        search_text.str.contains(
            keyword_pattern(CATEGORY_KEYWORDS["accommodation"]), na=False
        )
    ] = "accommodation"
    return category


def normalize_chunk(chunk: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    normalized = pd.DataFrame(
        {
            "sido_name": chunk[column_map["sido_name"]],
            "district": chunk[column_map["district"]],
            "category_large": chunk[column_map["category_large"]],
            "category_middle": chunk[column_map["category_middle"]],
            "store_name": chunk[column_map["store_name"]],
            "latitude": chunk[column_map["latitude"]],
            "longitude": chunk[column_map["longitude"]],
        }
    )

    text_columns = [
        "sido_name",
        "district",
        "category_large",
        "category_middle",
        "store_name",
    ]
    for column in text_columns:
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()

    normalized["latitude"] = pd.to_numeric(normalized["latitude"], errors="coerce")
    normalized["longitude"] = pd.to_numeric(normalized["longitude"], errors="coerce")
    normalized["store_category"] = categorize_stores(normalized)
    return normalized


def map_to_areas(gwangju_stores: pd.DataFrame) -> pd.DataFrame:
    mapped_frames: list[pd.DataFrame] = []

    for district, area_targets in DISTRICT_TO_AREAS.items():
        district_stores = gwangju_stores[gwangju_stores["district"] == district]
        if district_stores.empty:
            continue

        for area in area_targets:
            mapped = district_stores.copy()
            mapped["area_id"] = area["area_id"]
            mapped["area_name"] = area["area_name"]
            mapped_frames.append(mapped)

    if not mapped_frames:
        return pd.DataFrame()

    return pd.concat(mapped_frames, ignore_index=True)


def aggregate_features(mapped_stores: pd.DataFrame) -> pd.DataFrame:
    if mapped_stores.empty:
        return pd.DataFrame()

    grouped = mapped_stores.groupby(
        ["area_id", "area_name", "district"], as_index=False
    ).agg(
        store_total=("store_name", "size"),
        food_count=("store_category", lambda values: int((values == "food").sum())),
        cafe_count=("store_category", lambda values: int((values == "cafe").sum())),
        retail_count=("store_category", lambda values: int((values == "retail").sum())),
        accommodation_count=(
            "store_category",
            lambda values: int((values == "accommodation").sum()),
        ),
    )
    return grouped


def merge_feature_parts(feature_parts: list[pd.DataFrame]) -> pd.DataFrame:
    base = pd.DataFrame(AREA_ROWS)
    count_columns = [
        "store_total",
        "food_count",
        "cafe_count",
        "retail_count",
        "accommodation_count",
    ]

    if feature_parts:
        combined = pd.concat(feature_parts, ignore_index=True)
        combined = combined.groupby(
            ["area_id", "area_name", "district"], as_index=False
        )[count_columns].sum()
        features = base.merge(combined, on=["area_id", "area_name", "district"], how="left")
    else:
        features = base.copy()
        for column in count_columns:
            features[column] = 0

    for column in count_columns:
        features[column] = features[column].fillna(0).astype(int)

    return features[
        [
            "area_id",
            "area_name",
            "district",
            "store_total",
            "food_count",
            "cafe_count",
            "retail_count",
            "accommodation_count",
        ]
    ]


def print_sample_logs(gwangju_sample: pd.DataFrame, features: pd.DataFrame) -> None:
    print("Sample Korean values:")
    sample_columns = ["sido_name", "district", "category_large", "category_middle", "store_name"]
    print(gwangju_sample[sample_columns].head(5).to_string(index=False))

    print("Detected district names:")
    district_names = sorted(name for name in gwangju_sample["district"].dropna().unique())
    print(", ".join(district_names))

    print("Detected category names:")
    category_names = sorted(
        name for name in gwangju_sample["category_middle"].dropna().unique()
    )
    print(", ".join(category_names[:40]))
    if len(category_names) > 40:
        print(f"... and {len(category_names) - 40} more")

    print("Generated feature counts:")
    print(features.to_string(index=False))


def replace_output_file(temp_path: Path, output_path: Path) -> None:
    try:
        temp_path.replace(output_path)
    except PermissionError as error:
        if output_path.exists() and temp_path.read_bytes() == output_path.read_bytes():
            print(
                f"Target CSV is locked but already matches regenerated output: {output_path}"
            )
            print(f"Removing duplicate temporary CSV: {temp_path}")
            temp_path.unlink()
            return

        raise PermissionError(
            f"Could not replace {output_path}. Close any spreadsheet/editor "
            f"that has this CSV open, then rerun this script. Temporary output "
            f"was written to {temp_path}."
        ) from error


def main() -> None:
    print(f"Reading raw store data only: {RAW_PATH}")
    encoding, columns = detect_encoding()
    column_map = resolve_columns(columns)
    source_columns = list(dict.fromkeys(column_map.values()))

    print(f"Chosen encoding: {encoding}")
    print("Resolved source columns:")
    for output_name, source_name in column_map.items():
        print(f"- {output_name}: {source_name}")

    GWANGJU_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    for temp_path in [GWANGJU_TEMP_OUTPUT_PATH, FEATURE_TEMP_OUTPUT_PATH]:
        if temp_path.exists():
            temp_path.unlink()

    rows_loaded = 0
    rows_filtered = 0
    rows_mapped = 0
    first_output_chunk = True
    feature_parts: list[pd.DataFrame] = []
    sample_frames: list[pd.DataFrame] = []

    print(f"Saving CSV: {GWANGJU_TEMP_OUTPUT_PATH}")
    print(f"CSV encoding: {CSV_ENCODING}")
    with GWANGJU_TEMP_OUTPUT_PATH.open("w", encoding=CSV_ENCODING, newline="") as file:
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                RAW_PATH,
                encoding=encoding,
                encoding_errors="strict",
                dtype=str,
                usecols=source_columns,
                chunksize=CHUNK_SIZE,
                on_bad_lines="skip",
            ),
            start=1,
        ):
            rows_loaded += len(chunk)
            normalized = normalize_chunk(chunk, column_map)
            gwangju_stores = normalized[
                normalized["sido_name"].str.contains("광주", na=False)
            ].copy()
            rows_filtered += len(gwangju_stores)

            if not gwangju_stores.empty and len(sample_frames) < 3:
                sample_frames.append(gwangju_stores.head(20))

            if gwangju_stores.empty:
                print(f"Chunk {chunk_number}: loaded {len(chunk)} rows, Gwangju rows 0")
                continue

            gwangju_stores.to_csv(
                file,
                header=first_output_chunk,
                index=False,
            )
            first_output_chunk = False

            mapped_stores = map_to_areas(gwangju_stores)
            rows_mapped += len(mapped_stores)
            feature_part = aggregate_features(mapped_stores)
            if not feature_part.empty:
                feature_parts.append(feature_part)

            print(
                f"Chunk {chunk_number}: loaded {len(chunk)} rows, "
                f"Gwangju rows {len(gwangju_stores)}, mapped rows {len(mapped_stores)}"
            )

    features = merge_feature_parts(feature_parts)
    save_csv_safe(features, FEATURE_TEMP_OUTPUT_PATH)

    replace_output_file(FEATURE_TEMP_OUTPUT_PATH, FEATURE_OUTPUT_PATH)
    replace_output_file(GWANGJU_TEMP_OUTPUT_PATH, GWANGJU_OUTPUT_PATH)

    sample = pd.concat(sample_frames, ignore_index=True) if sample_frames else pd.DataFrame()
    print(f"Rows loaded: {rows_loaded}")
    print(f"Rows filtered to Gwangju: {rows_filtered}")
    print(f"Rows mapped to MVP areas: {rows_mapped}")
    if not sample.empty:
        print_sample_logs(sample, features)
    else:
        print("No Gwangju rows were available for sample Korean values.")

    print(f"Saved normalized Gwangju store data: {GWANGJU_OUTPUT_PATH}")
    print(f"Saved area store features: {FEATURE_OUTPUT_PATH}")
    print(
        "Assumption: district-level mapping duplicates 동구 stores into both "
        "충장로 / 금남로 and 국립아시아문화전당 주변 because this MVP does not yet "
        "use precise area boundary polygons."
    )


if __name__ == "__main__":
    main()
