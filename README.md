# DALreaDone

> **Data analytics, simplified.** Upload a CSV or Excel file, get automated statistical profiling, data quality scores, and AI-generated insights - no code required.

---

## What it does

DALreaDone is a full-stack data analytics platform. You upload a file and the app runs two independent pipelines:

- **EDA pipeline** - profiles the dataset across 7 dimensions (schema, missing values, statistics, datetime patterns, correlations, distributions, data quality), then sends the report to an LLM which returns a structured review: data quality issues, preprocessing suggestions, and analytical opportunities
- **Preprocessing pipeline** - lets you apply cleaning and transformation operations (missing value imputation, outlier handling, scaling, encoding) using a composable strategy-based pipeline; the cleaned file is saved back to S3 as a new file

Both pipelines are async: the backend queues them as background tasks and the frontend polls for status updates.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache / Task store | Redis |
| LLM | Groq (llama-3.3-70b-versatile) - structured review after EDA only |
| File storage | AWS S3 |
| Auth | JWT (access + refresh tokens) + OAuth (Google, GitHub) |
| Infra | Docker Compose |

Charts and histograms are rendered with inline SVG and CSS bars - no third-party chart library.

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git
- A [Groq API key](https://console.groq.com) (free tier available)
- An AWS S3 bucket with access credentials

---

## Quick start

### 1. Clone

```bash
git clone <repo-url>
cd dalreadone
```

### 2. Create `.env` in the root directory

```env
# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
JWT_SECRET_KEY=           # openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
GROQ_API_KEY=
MODEL_ID=llama-3.3-70b-versatile

# S3
AWS_REGION=
S3_BUCKET_NAME=
S3_ACCESS_KEY=
S3_SECRET_KEY=

# Encryption
ENCRYPTION_KEY=

# OAuth (optional - leave blank to disable social login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# App
ENV=development
FRONTEND_URL=http://localhost:3000
VITE_API_BASE_URL=/api
```

### 3. Build and run

```bash
docker compose up --build
```

The first build takes a few minutes. Subsequent starts are faster:

```bash
docker compose up
```

### 4. Open the app

| Service | URL |
|---|---|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Project structure

```
dalreadone/
├── docker-compose.yml
├── .env                            # created manually, never commit
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/                   # config, security, encryption
│       ├── db/                     # session
│       ├── routers/                # auth, oauth, projects, files, eda, preprocess, settings
│       ├── services/               # auth, file, oauth, project, eda, preprocess, settings
│       ├── models/                 # ORM models + Pydantic schemas
│       ├── pipelines/
│       │   ├── eda/
│       │   │   ├── eda_01_ingest.py              # file reading (CSV, Excel, JSON, JSONL, Parquet)
│       │   │   ├── eda_02_schema_profile.py      # dtype, nulls, cardinality per column
│       │   │   ├── eda_03_missing_duplicates.py  # null %, duplicate row count
│       │   │   ├── eda_04_stat_analysis.py       # numeric + categorical univariate stats
│       │   │   ├── eda_05_datetime_analysis.py   # date range, freq, gaps, seasonality
│       │   │   ├── eda_06_correlation_measure.py # Pearson + Cramér's V
│       │   │   ├── eda_07_distribution_analysis.py # normality, histogram, outliers
│       │   │   ├── eda_08_quality_score.py       # completeness/uniqueness/consistency/timeliness
│       │   │   └── pipeline.py                   # orchestrates steps 02–08, emits progress
│       │   └── preprocess/
│       │       ├── operation.py                  # BaseStrategy + BaseOperation (fit/transform)
│       │       ├── pipeline.py                   # Pipeline - chains operations, pickle save/load
│       │       ├── preprocess_missing_operation.py
│       │       ├── preprocess_outlier_operation.py
│       │       ├── preprocess_scaling_operation.py
│       │       └── preprocess_encoding_operation.py
│       ├── llm/                    # Groq client, review prompt, cost tracker
│       └── storage/
│           ├── redis.py            # Redis client + task state store
│           └── s3_client.py        # S3 upload/download/delete
└── frontend/
    ├── Dockerfile
    └── src/
        ├── api/                    # axios client, typed API functions
        ├── components/
        │   ├── layout/             # AppLayout, Sidebar
        │   ├── projects/           # ProjectCard, ProjectModal, DeleteConfirm
        │   ├── eda/
        │   │   ├── EDASection.tsx          # container: run button, progress, result + review
        │   │   ├── EDAResultDashboard.tsx  # tabbed result view + JSON download
        │   │   ├── EDAReviewPanel.tsx      # LLM review: issues, prep_steps, opportunities
        │   │   ├── EDATabOverview.tsx      # quality score + missing values summary
        │   │   ├── EDATabSchema.tsx        # column table
        │   │   ├── EDATabUnivariate.tsx    # numeric / categorical stats
        │   │   ├── EDATabDistributions.tsx # histogram sparklines + normality test
        │   │   ├── EDATabCorrelations.tsx  # Pearson + Cramér's V pairs
        │   │   ├── EDATabDatetime.tsx      # datetime column cards
        │   │   ├── EDATypes.ts             # TypeScript interfaces for EDA report
        │   │   └── EDAHelpers.tsx          # shared primitives: InfoCard, MiniBar, Sparkline
        │   └── ui/                 # shared icons, primitives
        ├── hooks/                  # useEDA, useReview, useAuth, useFiles, useProjects
        ├── pages/                  # LoginPage, ProjectsPage, EDAPage, PreprocessPage
        └── store/                  # authStore, historyStore (Zustand)
```

---

## EDA pipeline

The EDA pipeline is a pure-Python statistical profiler - no LLM is involved during computation. The LLM is called once after profiling completes, via a separate review endpoint, and returns a structured JSON analysis.

### Steps

| # | Module | What it computes |
|---|---|---|
| 1 | `eda_01_ingest` | Reads file from S3 (CSV, Excel, JSON, JSONL, Parquet) |
| 2 | `eda_02_schema_profile` | Row/col count, memory usage, dtype, null count, cardinality per column |
| 3 | `eda_03_missing_duplicates` | Null % per column, duplicate row count and % |
| 4 | `eda_04_stat_analysis` | Mean, median, std, skewness, kurtosis, outlier % (numeric); top values, entropy, mode (categorical) |
| 5 | `eda_05_datetime_analysis` | Date range, inferred frequency, gap count, seasonality hint, timezone |
| 6 | `eda_06_correlation_measure` | Pearson (numeric pairs), Cramér's V (categorical pairs), top correlated pairs |
| 7 | `eda_07_distribution_analysis` | Shapiro normality test, distribution type hint, histogram bins, IQR outlier summary |
| 8 | `eda_08_quality_score` | Completeness, uniqueness, consistency, timeliness → weighted overall score + warning flags |

Progress is emitted via the `on_step` callback at each stage (10 % → 95 %) so the frontend can display a labelled step list and a numeric progress bar simultaneously.

### Data quality score

| Dimension | Weight | How it is computed |
|---|---|---|
| Completeness | 35 % | `1 − (total nulls / total cells)` |
| Uniqueness | 25 % | `1 − (duplicate rows / total rows)` |
| Consistency | 25 % | `1 − (mean outlier rate across numeric columns)` |
| Timeliness | 15 % | Gap count vs expected date range for datetime columns |

### LLM review

After the statistical report is ready, the backend sends the full JSON report to Groq. The LLM returns a structured JSON object - not plain text - with three sections consumed independently by the frontend:

- **`issues`** - per-column problems with `severity` (`high` / `medium` / `low`), a detail message, and an impact description
- **`prep_steps`** - concrete preprocessing recommendations with `priority` (`must` / `should` / `optional`), the target column, and a rationale
- **`opportunities`** - plain-string analytical observations (correlations worth exploring, seasonal patterns, segment imbalances, etc.)

The response also includes `usage` with `total_tokens` and `total_cost_usd` displayed in the review panel header.

### Result dashboard

The EDA result is rendered in a six-tab dashboard (Overview, Schema, Univariate, Distributions, Correlations, Datetime). All charts - histogram sparklines, correlation bars, missing value bars, quality score rings - are rendered with inline SVG and Tailwind CSS. No third-party chart library is used. A JSON download button exports the full raw report.

### Async flow

```
POST /eda/files/{file_id}                        → queue EDA task, return task_id (202)
GET  /eda/{task_id}                              → poll status / step / progress / result
POST /eda/{eda_task_id}/review                   → queue LLM review, return review_task_id (202)
GET  /eda/{eda_task_id}/review/{review_task_id}  → poll structured review result + usage
```

Task state is stored in Redis and expires after `EDA_TASK_TTL` seconds (default: 1 hour).

---

## Preprocessing pipeline

The preprocessing pipeline uses a composable strategy pattern. Each `Operation` wraps a `Strategy` and exposes a `fit / transform / fit_transform` interface, identical to scikit-learn conventions. Operations are chained into a `Pipeline` that can be serialized and reloaded with pickle.

### Available operations

**Missing values** - `MissingOperation`

| Strategy | Description |
|---|---|
| `MeanStrategy` | Fill with column mean (numeric only) |
| `MedianStrategy` | Fill with column median (numeric only) |
| `ModeStrategy` | Fill with column mode |
| `ConstantStrategy` | Fill with a fixed value or a per-column dict |
| `DropRowStrategy` | Drop rows where any target column is null |
| `DropColStrategy` | Drop the target columns entirely |

**Outliers** - `OutlierOperation`

| Strategy | Description |
|---|---|
| `IQRStrategy` | IQR fence detection; action: `clip` or `drop` |
| `ZScoreStrategy` | Z-score threshold detection; action: `clip` or `drop` |
| `PercentileClipStrategy` | Clip to configurable percentile bounds (default 5th–95th) |

**Scaling** - `ScalingOperation`

| Strategy | Description |
|---|---|
| `MinMaxStrategy` | Scale to `[0, 1]` or a custom `feature_range` |
| `StandardStrategy` | Standardise to zero mean, unit variance |
| `RobustStrategy` | Scale using median and IQR (outlier-resistant) |

**Encoding** - `EncodingOperation`

| Strategy | Description |
|---|---|
| `OneHotStrategy` | One-hot encode; aligns to fitted categories to handle unseen values |
| `OrdinalStrategy` | Map categories to integers with optional custom order |
| `LabelStrategy` | Alphabetical integer label encoding |

### Async flow

```
POST   /preprocess/run                → queue task, return task_id (202)
GET    /preprocess/status/{task_id}   → poll status / progress
POST   /preprocess/confirm/{task_id}  → save cleaned file to S3 + DB, return file_id
DELETE /preprocess/cancel/{task_id}   → discard task and result
```

After `confirm`, the cleaned file is stored on S3 and registered in the database as a regular file - it can immediately be used as input for a new EDA run.

Task state is stored in Redis and expires after `PREPROCESS_TASK_TTL` seconds (default: 1 hour).

---

## Supported file formats

| Format | Extension |
|---|---|
| CSV | `.csv` |
| Excel | `.xlsx`, `.xls` |
| JSON | `.json` |
| JSON Lines | `.jsonl` |
| Parquet | `.parquet` |

Max 5 files per project. Uploading a file with the same name overwrites the existing one.

---

## User settings

Each user can store their own Groq API key under **Settings**:

- `GET /settings` - returns current settings (key is masked, e.g. `gsk_****...****Ab`)
- `PUT /settings` - update `use_own_key` flag and/or store a new key (encrypted at rest)
- `DELETE /settings/groq-key` - removes the stored key

When `use_own_key` is enabled, the user's key is used for LLM review calls instead of the server-level `GROQ_API_KEY`. Keys are stored encrypted using `ENCRYPTION_KEY`.

---

## OAuth setup (optional)

### Google

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **Credentials**
2. Create an **OAuth 2.0 Client ID** → Application type: **Web application**
3. Add redirect URI: `http://localhost:8000/auth/google/callback`
4. Paste the Client ID and Secret into `.env`

### GitHub

1. Go to GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**
2. Homepage URL: `http://localhost:3000`
3. Callback URL: `http://localhost:8000/auth/github/callback`
4. Paste the Client ID and Secret into `.env`

---

## Common commands

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Rebuild after code changes
docker compose up --build

# Stream backend logs only
docker compose logs -f backend

# Stop everything
docker compose down

# Stop and wipe the database + Redis volumes
docker compose down -v

# Open a psql session
docker exec -it dalreadone-db-1 psql -U postgres -d dalreadone

# Open a Redis CLI session
docker exec -it dalreadone-redis-1 redis-cli
```

---

## Required environment variables

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Long random string used to sign JWTs (`openssl rand -hex 32`) |
| `GROQ_API_KEY` | Server-level key from [console.groq.com](https://console.groq.com) - used for LLM review |
| `S3_BUCKET_NAME` | S3 bucket for uploaded and preprocessed files |
| `S3_ACCESS_KEY` | AWS access key with S3 read/write permissions |
| `S3_SECRET_KEY` | Corresponding AWS secret key |
| `ENCRYPTION_KEY` | Key used to encrypt stored user Groq API keys |

All `GOOGLE_*` and `GITHUB_*` variables are optional.

---

## Notes

- Uploaded files are stored on S3 and never held on disk permanently
- EDA is entirely deterministic - the LLM is only called once after profiling completes, for structured review generation
- Access tokens expire after 15 minutes; the app silently refreshes them using an HTTP-only cookie
- EDA and preprocessing task state is stored in Redis with a configurable TTL (default: 1 hour)
- After preprocessing, the confirmed file is indistinguishable from a regular upload and can be used as EDA input
- Users can supply their own Groq API key via Settings; keys are encrypted at rest
- All data is per-user and fully isolated - users cannot access each other's files or results