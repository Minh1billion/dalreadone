import json
from pprint import pprint


CORR_HIGH = 0.5
CORR_MODERATE = 0.3
TOP_VALUES_N = 5
SAMPLE_VALUES_N = 10


def _imbalance_ratio(top_values: list[dict]) -> float | None:
    pcts = [v["pct"] for v in top_values if v["pct"] > 0]
    if len(pcts) < 2:
        return None
    return round(max(pcts) / min(pcts), 2)


def _build_column(name: str, schema_col: dict, numeric: dict, categorical: dict, dist: dict, n_rows: int) -> dict:
    col: dict = {
        "name": name,
        "dtype": schema_col["dtype"],
        "inferred_type": schema_col["inferred_type"],
        "n_unique": schema_col["n_unique"],
        "null_pct": round(schema_col["n_nulls"] / n_rows * 100, 2),
        "sample_values": schema_col.get("first_10_unique_values", [])[:SAMPLE_VALUES_N],
    }

    if name in numeric:
        s = numeric[name]
        col.update({
            "min": s["min"],
            "max": s["max"],
            "mean": round(s["mean"], 4),
            "median": s["median"],
            "p25": s["p25"],
            "p75": s["p75"],
            "skewness": round(s["skewness"], 4),
            "has_negatives": s["min"] < 0,
            "zeros_pct": s["zeros_pct"],
            "outlier_pct": s["outlier_pct"],
        })

    if name in categorical:
        c = categorical[name]
        top = c["top_values"][:TOP_VALUES_N]
        col.update({
            "cardinality": c["cardinality"],
            "rare_pct": c["rare_pct"],
            "top_values": [{"value": v["value"], "pct": v["pct"]} for v in top],
            "imbalance_ratio": _imbalance_ratio(top),
        })

    if name in dist:
        d = dist[name]
        col["dist_hint"] = d["dist_type_hint"]
        if name not in numeric:
            col["outlier_pct"] = round(d["outlier_summary"]["count"] / n_rows * 100, 2)

    return col


def _build_correlations(corr: dict) -> dict:
    high, moderate = [], []
    seen = set()

    for p in corr.get("top_corr_pairs", []):
        key = (p["col_a"], p["col_b"])
        seen.add(key)
        entry = {"col_a": p["col_a"], "col_b": p["col_b"], "method": p["method"], "value": p["value"]}
        if abs(p["value"]) >= CORR_HIGH:
            high.append(entry)
        elif abs(p["value"]) >= CORR_MODERATE:
            moderate.append(entry)

    for source_key in ("pearson", "cramers_v"):
        for key, value in corr.get(source_key, {}).items():
            if abs(value) < CORR_MODERATE:
                continue
            a, b = key.split("__", 1)
            if (a, b) in seen or (b, a) in seen:
                continue
            seen.add((a, b))
            entry = {"col_a": a, "col_b": b, "method": source_key, "value": value}
            if abs(value) >= CORR_HIGH:
                high.append(entry)
            else:
                moderate.append(entry)

    return {"high": high, "moderate": moderate}


def build_context(report: dict) -> dict:
    r = report["eda_report"]
    schema = r["schema"]
    missing = r["missing_and_duplicates"]
    univariate = r["univariate"]
    numeric = univariate.get("numeric", {})
    categorical = univariate.get("categorical", {})
    dist = r.get("distributions", {})
    dt = r.get("datetime", {})
    corr = r.get("correlations", {})
    quality = r.get("data_quality_score", {})
    n_rows = schema["n_rows"]

    columns = [
        _build_column(col["name"], col, numeric, categorical, dist, n_rows)
        for col in schema["columns"]
    ]

    datetime_cols = [
        {
            "name": name,
            "min": info["min_date"],
            "max": info["max_date"],
            "range_days": info["date_range_days"],
        }
        for name, info in dt.items()
    ]

    return {
        "meta": {
            "source_file": r["meta"]["source_file"],
            "n_rows": n_rows,
            "n_cols": schema["n_cols"],
            "duplicate_rows": missing["duplicate_rows"],
            "duplicate_pct": missing["duplicate_pct"],
        },
        "columns": columns,
        "datetime_cols": datetime_cols,
        "correlations": _build_correlations(corr),
        "quality": {
            "overall_score": quality.get("overall_score"),
            "flags": quality.get("flags", []),
        },
    }


if __name__ == "__main__":
    for path in [
        "eda_online_retail.csv.json",
        "eda_Future of Jobs AI Dataset.csv.json",
    ]:
        try:
            with open(path) as f:
                report = json.load(f)
        except FileNotFoundError:
            print(f"[skip] {path} not found")
            continue

        compact = build_context(report)

        original_tokens = len(json.dumps(report))
        compact_tokens = len(json.dumps(compact))
        reduction = (1 - compact_tokens / original_tokens) * 100

        print(f"\n{'='*60}")
        print(f"File : {path}")
        print(f"Before: {original_tokens:,} chars")
        print(f"After : {compact_tokens:,} chars")
        print(f"Saved : {reduction:.1f}%")
        print(f"{'='*60}")
        pprint(compact)