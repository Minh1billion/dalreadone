# DALreaDone - API spec

Base URL: `http://localhost:8000` (dev) - set via `VITE_API_BASE_URL`.

All protected endpoints require `Authorization: Bearer <access_token>` header.
Refresh token is stored in an `httpOnly` cookie, managed automatically by the browser.

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
Log in with username + password.

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
Get a new access token using the refresh cookie.

No request body. Cookie is sent automatically.

**Response 200**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```
**Error 401** - cookie missing or expired.

---

### POST /api/auth/logout
Clear the refresh cookie.

**Response 200**
```json
{ "message": "Logged out" }
```

---

### GET /auth/google
Redirects browser to Google OAuth consent screen. No frontend fetch needed - navigate directly.

---

### GET /auth/google/callback
OAuth callback - handled by backend. On success, redirects to:
```
{FRONTEND_URL}?access_token=<jwt>
```
Frontend should read `access_token` from the query string on landing, store it, then strip it from the URL.

---

### GET /auth/github
Redirects browser to GitHub OAuth consent screen.

---

### GET /auth/github/callback
Same pattern as Google callback.

---

## Projects

### POST /api/projects
Create a new project. 🔒

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

### GET /api/projects
List all projects for the current user. 🔒

**Response 200**
```json
[
  { "id": 1, "name": "Q3 Sales Analysis", "user_id": 42, "created_at": "..." }
]
```

---

### GET /api/projects/{project_id}
Get a single project. 🔒

**Response 200** - same shape as above.
**Error 404** - project not found.
**Error 403** - not the owner.

---

### PATCH /api/projects/{project_id}
Rename a project. 🔒

**Request**
```json
{ "name": "Q4 Sales Analysis" }
```
**Response 200** - updated project object.

---

### DELETE /api/projects/{project_id}
Delete project and all its files (S3 + DB). 🔒

**Response 204** - no content.

---

## Files

### POST /api/projects/{project_id}/files
Upload a CSV or Excel file to a project. 🔒

**Request** - `multipart/form-data`
- field: `file` - the file to upload (`.csv`, `.xlsx`, `.xls`)

If a file with the same name already exists in the project it is overwritten.
Max 5 files per project.

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
**Error 400** - unsupported file type, or project at 5-file limit.

---

### GET /api/projects/{project_id}/files
List files in a project. 🔒

**Response 200**
```json
[
  {
    "id": 7,
    "filename": "sales_q3.csv",
    "s3_key": "projects/1/sales_q3.csv",
    "project_id": 1,
    "uploaded_by_id": 42,
    "uploaded_at": "2025-01-01T00:00:00"
  }
]
```

---

### DELETE /api/projects/{project_id}/files/{file_id}
Delete a file from S3 and DB. 🔒

**Response 204** - no content.
**Error 404** - file not found in this project.

---

## Query

### POST /api/projects/{project_id}/files/{file_id}/query
Run an EDA/analysis query against a file. 🔒

This is the core endpoint. The LLM runs two passes (explore + anomaly detection) and returns results, charts, and a plain-text insight. May take 10–30 seconds.

**Request**
```json
{ "question": "Which product category had the highest return rate?" }
```
`question` is optional - omit or pass `""` for free exploration.

**Response 200**
```json
{
  "user_question": "Which product category had the highest return rate?",

  "explore_reason": "Comparing return rates across product categories using groupby on category and return_flag columns.",
  "result": "| category   | return_rate |\n|---|---|\n| Electronics | 0.18 |",
  "charts": [
    {
      "type": "bar",
      "title": "Return rate by category",
      "labels": ["Electronics", "Clothing", "Home"],
      "data": [0.18, 0.12, 0.07]
    }
  ],

  "interesting_reason": "Electronics shows a return rate 2.5× the median - worth breaking down by sub-category.",
  "interesting_result": "| sub_category | return_rate |\n|---|---|\n| Laptops | 0.31 |",
  "interesting_charts": [
    {
      "type": "bar",
      "title": "Electronics sub-category return rates",
      "labels": ["Laptops", "Phones", "Tablets"],
      "data": [0.31, 0.15, 0.09]
    }
  ],

  "insight": "Electronics has the highest return rate at 18%, driven mainly by Laptops (31%). This is significantly above the dataset median of 7%...",

  "code": "result = {\n  'return_by_category': df.groupby('category')['return_flag'].mean()\n}",

  "cost_report": {
    "total_tokens": 3420,
    "total_prompt_tokens": 2800,
    "total_completion_tokens": 620,
    "total_cost_usd": 0.002418,
    "total_latency_ms": 8340,
    "skipped_stages": [],
    "calls": [
      {
        "stage": "generate_code",
        "prompt_tokens": 900,
        "completion_tokens": 280,
        "cost_usd": 0.000752,
        "latency_ms": 2100,
        "skipped": false,
        "skip_reason": ""
      }
    ]
  }
}
```

**Chart types** the backend can return: `bar`, `line`, `pie`, `scatter`, `histogram`, `grouped_bar`.

`grouped_bar` has an extra field:
```json
{
  "type": "grouped_bar",
  "title": "...",
  "labels": ["Q1", "Q2", "Q3"],
  "series_labels": ["2023", "2024"],
  "data": [[10, 20, 15], [12, 18, 22]]
}
```

`interesting_reason`, `interesting_result`, and `interesting_charts` are `null` when pass-2 was skipped (result too short or empty).

**Error 500** - code execution failed after 3 retries, or LLM error.

---

## Error shape

All errors follow FastAPI's default:
```json
{ "detail": "Human-readable error message" }
```

Common codes:
| Code | Meaning |
|------|---------|
| 400 | Bad request (file type, project limit) |
| 401 | Missing or expired token |
| 403 | Not the resource owner |
| 404 | Resource not found |
| 500 | LLM or execution failure |

---

## Notes for frontend

**Token storage** - store `access_token` in memory (React state / Zustand). Do not put it in `localStorage`. The refresh cookie is `httpOnly` so JS cannot touch it - call `POST /auth/refresh` on app load to hydrate a new access token silently.

**OAuth flow** - for Google/GitHub, navigate the browser to `/auth/google` or `/auth/github` directly (not a fetch). On return to `FRONTEND_URL?access_token=...`, read and store the token, then `window.history.replaceState` to clean the URL.

**Query timeout** - the query endpoint can take 30+ seconds. Set Axios timeout to at least 60 000 ms for this route only.

**Recharts mapping**:
- `bar` → `<BarChart>`
- `line` → `<LineChart>`
- `pie` → `<PieChart>`
- `scatter` → `<ScatterChart>`
- `histogram` → treat as `<BarChart>` with no gap between bars
- `grouped_bar` → `<BarChart>` with multiple `<Bar>` components, one per `series_labels` entry; `data` is an array of series arrays indexed to match `labels`
