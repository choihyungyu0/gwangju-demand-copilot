from __future__ import annotations

from pathlib import Path

import pandas as pd


CSV_ENCODING = "utf-8-sig"


def save_csv_safe(df: pd.DataFrame, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving CSV: {output_path}")
    print(f"CSV encoding: {CSV_ENCODING}")
    df.to_csv(output_path, index=False, encoding=CSV_ENCODING)
