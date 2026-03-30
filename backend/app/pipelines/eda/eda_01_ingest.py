import pandas as pd

from datetime import datetime, timezone

from pathlib import Path
from typing import Union

VALID_EXTENSIONS_MAP = {
    ".csv": pd.read_csv,
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
    ".json": pd.read_json,
    ".jsonl": lambda x, **kwargs: pd.read_json(x, lines=True, **kwargs),
    ".parquet": pd.read_parquet,
}


def _get_extension(path: Union[str, Path]) -> str:
    return "".join(Path(path).suffixes).lower()


def read_data(path: Union[str, Path], **kwargs) -> tuple[pd.DataFrame, dict]:
    ext = _get_extension(path)
    path = str(path)

    if ext.endswith(".csv"):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("low_memory", False)

    for extension, reader in VALID_EXTENSIONS_MAP.items():
        if ext.endswith(extension):
            try:
                meta = {
                    "source": path.split("\\")[-1],
                    "file_format": extension,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
                return reader(path, **kwargs), meta
            except Exception as e:
                raise RuntimeError(f"Error reading {path}: {e}")

    for reader in VALID_EXTENSIONS_MAP.values():
        try:
            return reader(path, **kwargs)
        except Exception:
            continue

    raise ValueError(f"Unsupported file format: {path}")

if __name__ == "__main__":
    df, meta = read_data("backend\\test\\data.csv")
    print(df)
    print(meta)