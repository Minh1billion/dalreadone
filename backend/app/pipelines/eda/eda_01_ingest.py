import json
import io
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Union


def _get_extension(path: Union[str, Path]) -> str:
    return "".join(Path(path).suffixes).lower()


def _load_json(buf: io.BytesIO) -> pd.DataFrame:
    raw = json.load(buf)
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        records = next((v for v in raw.values() if isinstance(v, list)), [raw])
    else:
        raise ValueError("JSON root must be an array or object")
    df = pd.json_normalize(records)
    return _stringify_list_cols(df)


def _load_jsonl(buf: io.BytesIO) -> pd.DataFrame:
    records = [json.loads(line) for line in buf.read().decode().splitlines() if line.strip()]
    df = pd.json_normalize(records)
    df = df.dropna(axis=1, how="all")
    return _stringify_list_cols(df)


def _stringify_list_cols(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x
            )
    return df


def read_data(path: Union[str, Path], **kwargs) -> tuple[pd.DataFrame, dict]:
    ext = _get_extension(path)
    path = str(path)

    meta = {
        "source": path.replace("\\", "/").split("/")[-1],
        "file_format": ext,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        buf = io.BytesIO(open(path, "rb").read())
        if ext.endswith(".csv"):
            kwargs.setdefault("encoding", "utf-8")
            kwargs.setdefault("low_memory", False)
            return pd.read_csv(buf, **kwargs), meta
        elif ext.endswith((".xlsx", ".xls")):
            return pd.read_excel(buf, **kwargs), meta
        elif ext.endswith(".json"):
            return _load_json(buf), meta
        elif ext.endswith(".jsonl"):
            return _load_jsonl(buf), meta
        elif ext.endswith(".parquet"):
            return pd.read_parquet(buf, **kwargs), meta
        else:
            raise ValueError(f"Unsupported file format: {path}")
    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Error reading {path}: {e}")