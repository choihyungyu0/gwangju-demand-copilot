from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data" / "raw" / "store_data.csv"
ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
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
        INPUT_PATH,
        encoding=encoding,
        encoding_errors="strict",
        dtype=str,
        nrows=PREVIEW_ROWS,
        on_bad_lines="skip",
    )


def detect_encoding() -> tuple[str, pd.DataFrame]:
    for encoding in ENCODINGS_TO_TRY:
        try:
            preview = read_preview_with_encoding(encoding)
        except UnicodeDecodeError as error:
            print(f"Rejected encoding {encoding}: decode error: {error}")
            continue

        is_valid, reason = korean_validation_report(preview)
        if is_valid:
            print(f"Accepted encoding {encoding}: {reason}")
            return encoding, preview

        print(f"Rejected encoding {encoding}: {reason}")

    raise ValueError(
        "Could not find an encoding that preserves Korean text. "
        f"Tried: {', '.join(ENCODINGS_TO_TRY)}"
    )


def main() -> None:
    print(f"Inspecting raw store data only: {INPUT_PATH}")
    encoding, preview = detect_encoding()

    print(f"Chosen encoding: {encoding}")
    print("Column names:")
    for column in preview.columns:
        print(f"- {column}")

    print("First 3 rows:")
    print(preview.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
