# DALreaDone - API Spec

Base URL: `http://localhost:8000` (dev) - set via `VITE_API_BASE_URL`.

All protected endpoints 🔒 require `Authorization: Bearer <access_token>` header.
Refresh token is stored in an `httpOnly` cookie, managed automatically by the browser.

---

## Error shape

All errors follow FastAPI's default:

```json
{ "detail": "Human-readable error message" }
```

| Code | Meaning |
|------|---------|
| 400 | Bad request (unsupported file type, project limit, validation error) |
| 401 | Missing or expired token |
| 403 | Not the resource owner |
| 404 | Resource not found |
| 500 | Internal / LLM error |

---

## Auth

### POST /api/auth/register

Register a new user.

**Request**
```json
{ "username": "alice", "password": "secret123" }
```

**Response 201**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Refresh token is set as an `httpOnly` cookie.

---

### POST /api/auth/login

**Request**
```json
{ "username": "alice", "password": "secret123" }
```

**Response 200**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### POST /api/auth/refresh

Get a new access token using the refresh cookie. No request body - cookie is sent automatically.

**Response 200**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

**Error 401** - cookie missing or expired.

---

### POST /api/auth/logout

**Response 200**
```json
{ "message": "Logged out" }
```

---

### GET /auth/google

Redirects the browser to the Google OAuth consent screen. Navigate directly - do not `fetch`.

---

### GET /auth/google/callback

OAuth callback handled by the backend. On success, redirects to:
```
{FRONTEND_URL}?access_token=<jwt>
```

Read `access_token` from the query string, store it in memory, then call `window.history.replaceState` to strip it from the URL.

---

### GET /auth/github
### GET /auth/github/callback

Same pattern as Google.

---

## Projects

### POST /api/projects 🔒

**Request**
```json
{ "name": "Q3 Sales Analysis" }
```

**Response 201**
```json
{
  "id": 1,
  "name": "Q3 Sales Analysis",
  "user_id": 42,
  "created_at": "2025-01-01T00:00:00"
}
```

---

### GET /api/projects 🔒

**Response 200** - array of project objects (same shape as above).

---

### GET /api/projects/{project_id} 🔒

**Response 200** - single project object.
**Error 404** / **Error 403**

---

### PATCH /api/projects/{project_id} 🔒

**Request**
```json
{ "name": "Q4 Sales Analysis" }
```

**Response 200** - updated project object.

---

### DELETE /api/projects/{project_id} 🔒

Deletes the project and all its files (S3 + DB).

**Response 204**

---

## Files

Supported formats: `.csv`, `.xlsx`, `.xls`, `.json`, `.jsonl`, `.parquet`
Max **5 files** per project. Uploading a file with the same name overwrites the existing one.

### POST /api/projects/{project_id}/files 🔒

**Request** - `multipart/form-data`, field `file`.

**Response 201**
```json
{
  "id": 7,
  "filename": "sales_q3.csv",
  "s3_key": "projects/1/sales_q3.csv",
  "project_id": 1,
  "uploaded_by_id": 42,
  "uploaded_at": "2025-01-01T00:00:00"
}
```

**Error 400** - unsupported format, or project at 5-file limit.

---

### GET /api/projects/{project_id}/files 🔒

**Response 200** - array of file objects (same shape as above).

---

### DELETE /api/projects/{project_id}/files/{file_id} 🔒

**Response 204**
**Error 404** - file not found in this project.

---

### GET /api/projects/{project_id}/files/{file_id}/preview 🔒

Returns the first rows of the file for display before running EDA.

**Response 200**
```json
{
  "columns": ["category", "revenue", "date"],
  "rows": [
    ["Electronics", 1200.5, "2024-01-15"],
    ["Clothing", 430.0, "2024-01-16"]
  ],
  "total_rows": 5420
}
```

---

## EDA

The EDA pipeline is a pure-Python statistical profiler that runs as a background task. The LLM is only called after profiling completes, via a separate review endpoint.

### POST /api/eda/files/{file_id} 🔒

Queue an EDA task.

**Response 202**
```json
{ "task_id": "eda_a1b2c3d4" }
```

---

### GET /api/eda/{task_id} 🔒

Poll EDA task status.

`status` values: `pending` → `running` → `done` | `error`

`step` values (in order): `schema`, `missing_and_duplicates`, `univariate`, `datetime`, `correlations`, `distributions`, `data_quality_score`

`progress` is an integer 0–100. When `status == "done"`, `result` contains the full EDA report. When `status == "error"`, `error` contains the message.

**Response 200 (running)**
```json
{
  "task_id": "eda_a1b2c3d4",
  "status": "running",
  "step": "correlations",
  "progress": 65,
  "result": null,
  "error": null
}
```

**Response 200 (done)** - `result` is the full EDA report object:

```json
{
  "task_id": "eda_a1b2c3d4",
  "status": "done",
  "step": "data_quality_score",
  "progress": 100,
  "error": null,
  "result": {
    "eda_report": {
      "meta": {
        "source_file": "sales_q3.csv",
        "generated_at": "2025-01-01T00:00:00Z"
      },
      "schema": {
        "n_rows": 5420,
        "n_cols": 8,
        "memory_mb": 1.24,
        "columns": [
          {
            "name": "revenue",
            "dtype": "float64",
            "inferred_type": "floating",
            "n_nulls": 12,
            "n_unique": 3841,
            "first_10_unique_values": [1200.5, 430.0, 89.9]
          }
        ]
      },
      "missing_and_duplicates": {
        "duplicate_rows": 3,
        "duplicate_pct": 0.06,
        "columns": {
          "revenue": { "null_count": 12, "null_pct": 0.22 }
        }
      },
      "univariate": {
        "numeric": {
          "revenue": {
            "mean": 842.3,
            "median": 610.0,
            "std": 540.1,
            "min": 0.5,
            "max": 9800.0,
            "p25": 320.0,
            "p75": 1100.0,
            "skewness": 1.42,
            "kurtosis": 3.11,
            "zeros_pct": 0.0,
            "outlier_count": 48,
            "outlier_pct": 0.89
          }
        },
        "categorical": {
          "category": {
            "cardinality": 5,
            "top_values": [
              { "value": "Electronics", "count": 1820, "pct": 33.58 }
            ],
            "entropy": 2.18,
            "mode": "Electronics",
            "rare_pct": 0.0
          }
        }
      },
      "datetime": {
        "date": {
          "min_date": "2024-01-01",
          "max_date": "2024-12-31",
          "date_range_days": 365,
          "inferred_freq": "D",
          "gaps_count": 5,
          "seasonality_hint": "daily",
          "timezone": "naive"
        }
      },
      "correlations": {
        "pearson": {
          "revenue__quantity": 0.72
        },
        "cramers_v": {
          "category__region": 0.31
        },
        "top_corr_pairs": [
          { "col_a": "revenue", "col_b": "quantity", "method": "pearson", "value": 0.72 }
        ]
      },
      "distributions": {
        "revenue": {
          "normality_test": { "method": "shapiro", "p_value": 0.00012, "is_normal": false },
          "dist_type_hint": "right-skewed",
          "histogram_bins": [
            { "range": "[0.5,980.5)", "count": 2140 }
          ],
          "outlier_summary": {
            "count": 48,
            "pct": 0.89,
            "lower_fence": -820.0,
            "upper_fence": 2240.0,
            "preview_idx": [12, 47, 203]
          }
        }
      },
      "data_quality_score": {
        "completeness": 0.9977,
        "uniqueness": 0.9994,
        "consistency": 0.9911,
        "timeliness": 0.9863,
        "overall_score": 0.9944,
        "flags": [
          "5 datetime gaps in 'date'"
        ]
      }
    }
  }
}
```

---

### POST /api/eda/{eda_task_id}/review 🔒

Queue an LLM review task for a completed EDA. The backend sends the full EDA report to Groq; the LLM returns a structured JSON analysis (not plain text).

**Response 202**
```json
{ "task_id": "review_e5f6g7h8" }
```

**Error 400** - EDA task is not yet `done`.

---

### GET /api/eda/{eda_task_id}/review/{review_task_id} 🔒

Poll review task status.

`status` values: `pending` → `running` → `done` | `error`

When `status == "done"`, `result` is a structured object with three sections. The frontend renders each section separately - `issues` as severity-tagged cards, `prep_steps` as a priority-tagged action list, and `opportunities` as a plain bullet list.

**Response 200 (done)**
```json
{
  "task_id": "review_e5f6g7h8",
  "eda_task_id": "eda_a1b2c3d4",
  "status": "done",
  "progress": 100,
  "result": {
    "issues": [
      {
        "col": "revenue",
        "severity": "high",
        "detail": "12% missing values detected - above the 5% warning threshold.",
        "impact": "May bias downstream aggregations and model training."
      },
      {
        "col": "category",
        "severity": "medium",
        "detail": "Rare categories account for 3.2% of values.",
        "impact": "Low-frequency labels may cause issues with encoding strategies."
      }
    ],
    "prep_steps": [
      {
        "action": "median imputation",
        "col": "revenue",
        "priority": "must",
        "rationale": "Right-skewed distribution - median is more robust than mean for imputation."
      },
      {
        "action": "IQR clip",
        "col": "revenue",
        "priority": "should",
        "rationale": "48 outliers (0.89%) detected above the upper fence."
      },
      {
        "action": "onehot encoding",
        "col": "category",
        "priority": "optional",
        "rationale": "Low cardinality (5 values) - one-hot is safe and interpretable."
      }
    ],
    "opportunities": [
      "Strong Pearson correlation (0.72) between revenue and quantity - consider feature interaction.",
      "Daily seasonality detected in 'date' - time-based aggregations may reveal trends.",
      "Electronics dominates at 34% - segment-level analysis may surface category-specific patterns."
    ]
  },
  "usage": {
    "prompt_tokens": 2100,
    "completion_tokens": 380,
    "total_tokens": 2480,
    "total_cost_usd": 0.000821
  },
  "error": null
}
```

#### Field reference

`issues[].severity`: `"high"` | `"medium"` | `"low"`

`prep_steps[].priority`: `"must"` | `"should"` | `"optional"`

`prep_steps[].col`: column name, or `null` for dataset-level steps.

---

## Preprocess

The preprocessing pipeline is strategy-based (fit / transform). Operations are chained, executed as a background task, and the cleaned file is saved to S3 on confirm.

### POST /api/preprocess/run 🔒

Queue a preprocessing task.

**Request**
```json
{
  "file_id": 7,
  "project_id": 1,
  "steps": [
    {
      "operation": "missing",
      "strategy": "median",
      "cols": ["revenue", "quantity"]
    },
    {
      "operation": "outlier",
      "strategy": "iqr",
      "action": "clip",
      "cols": ["revenue"]
    },
    {
      "operation": "scaling",
      "strategy": "minmax",
      "cols": ["revenue", "quantity"]
    },
    {
      "operation": "encoding",
      "strategy": "onehot",
      "cols": ["category"]
    }
  ],
  "output_filename": "sales_q3_cleaned.csv"
}
```

`cols` is optional - omitting it applies the strategy to all applicable columns.

Available strategies per operation:

| `operation` | `strategy` options | Extra params |
|---|---|---|
| `missing` | `mean`, `median`, `mode`, `constant`, `drop_row`, `drop_col` | `fill_value` (constant only) |
| `outlier` | `iqr`, `zscore`, `percentile_clip` | `action`: `clip`\|`drop`; `threshold` (zscore); `lower`, `upper` (percentile) |
| `scaling` | `minmax`, `standard`, `robust` | `feature_range` (minmax, default `[0, 1]`) |
| `encoding` | `onehot`, `ordinal`, `label` | `order` dict (ordinal only) |

**Response 202**
```json
{
  "task_id": "pre_x1y2z3w4",
  "status": "pending",
  "progress": 0
}
```

---

### GET /api/preprocess/status/{task_id} 🔒

`status` values: `pending` → `running` → `done` | `error`

**Response 200**
```json
{
  "task_id": "pre_x1y2z3w4",
  "status": "running",
  "progress": 60
}
```

---

### POST /api/preprocess/confirm/{task_id} 🔒

Save the cleaned DataFrame to S3 and register it in the DB as a new file.

**Response 200**
```json
{
  "file_id": 12,
  "filename": "sales_q3_cleaned.csv",
  "project_id": 1
}
```

**Error 400** - task not `done`. **Error 403** - not the task owner.

---

### DELETE /api/preprocess/cancel/{task_id} 🔒

Discard the task and its result from Redis. No file is written.

**Response 204**
**Error 403** - not the task owner.

---

## Settings

### GET /api/settings 🔒

**Response 200**
```json
{
  "use_own_key": false,
  "groq_api_key": "gsk_****...****Ab"
}
```

`groq_api_key` is `null` if no key is stored.

---

### PUT /api/settings 🔒

**Request**
```json
{
  "use_own_key": true,
  "groq_api_key": "gsk_xxxxxxxxxxxxxxxxxxxx"
}
```

`groq_api_key` is optional - omit to keep the existing stored key. Setting `use_own_key: true` without a stored key and without providing one returns **Error 400**.

**Response 200** - same shape as GET.

---

### DELETE /api/settings/groq-key 🔒

Remove the stored key. `use_own_key` is automatically set to `false`.

**Response 200**
```json
{
  "use_own_key": false,
  "groq_api_key": null
}
```

---

## Notes for frontend

**Token storage** - store `access_token` in memory (React state / Zustand). Do not put it in `localStorage`. The refresh cookie is `httpOnly` - call `POST /api/auth/refresh` on app load to silently hydrate a new access token.

**OAuth flow** - navigate the browser directly to `/auth/google` or `/auth/github` (not `fetch`). On return to `FRONTEND_URL?access_token=...`, read and store the token, then call `window.history.replaceState` to strip it from the URL.

**Polling** - poll EDA and preprocess tasks every 1–2 seconds until `status` is `done` or `error`. Stop polling on either terminal state and surface the `error` string if present.

**EDA progress** - use `step` for a labelled step indicator and `progress` (0–100) for the numeric bar. The seven step keys in display order: `schema` → `missing_and_duplicates` → `univariate` → `datetime` → `correlations` → `distributions` → `data_quality_score`.

**EDA result rendering** - the dashboard is tab-based: Overview, Schema, Univariate, Distributions, Correlations, Datetime. Charts and histograms are rendered with inline SVG and CSS bars - no third-party chart library.

**Review result** - only trigger the review endpoint after EDA `status == "done"`. The `result` object has three keys consumed independently by the UI: `issues` (severity-tagged problem cards), `prep_steps` (priority-tagged preprocessing suggestions), and `opportunities` (plain-string insight list). The `usage` object includes `total_cost_usd` for display in the review panel header.

**Preprocess confirm** - only enable the confirm button when preprocess `status == "done"`. After confirm, the returned `file_id` can be used immediately as input for a new EDA run.

**JSON export** - the EDA result dashboard includes a download button that serialises the full `result` object as `eda_{filename}.json`.