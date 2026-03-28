# DALreaDone

> **Data analytics, simplified.** Upload a CSV or Excel file, ask a question in plain English, and get automated charts, statistical breakdowns, and AI-generated insights — no code required.

---

## What it does

DALreaDone is a full-stack AI data analyst. You upload a file, ask a question (or leave it blank to auto-explore), and the app runs a two-pass LLM analysis pipeline:

- **Pass 1** — explores the dataset from multiple angles: summaries, trends, outliers, distributions, correlations
- **Pass 2** — digs into anomalies and interesting patterns found in pass 1
- **Insight** — synthesises both passes into a plain-English summary

The pipeline automatically detects whether the dataset is **structured/tabular** or **text-heavy** (reviews, articles, survey responses) and routes to the appropriate analysis engine. Text-heavy datasets get NLP-specific features: sentiment analysis, keyword extraction, topic clustering, and word clouds.

Results are returned as interactive charts, markdown tables, and a cost report showing token usage per stage. All results are saved to history and can be exported as PDF.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| LLM | Groq (llama-3.3-70b-versatile) |
| File storage | AWS S3 |
| Auth | JWT (access + refresh tokens) + OAuth (Google, GitHub) |
| Infra | Docker Compose |

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
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=dalreadone
POSTGRES_HOST=db
POSTGRES_PORT=5432

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM
GROQ_API_KEY=your-groq-api-key
MODEL_ID=llama-3.3-70b-versatile

# S3
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# OAuth (optional — leave blank to disable social login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# App
ENV=development
FRONTEND_URL=http://localhost:3000
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
├── .env                          # created manually, never commit
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/                 # config, security
│       ├── db/                   # session
│       ├── routers/              # auth, oauth, projects, files, query, history
│       ├── services/             # auth, file, oauth, project, query, query_result
│       ├── models/               # ORM models + Pydantic schemas
│       ├── llm/
│       │   ├── engine/           # base, structured, nlp — LLM invocation layer
│       │   ├── strategies/       # context builders: structured, nlp, features
│       │   ├── template/         # prompt templates (.txt)
│       │   ├── context_builder.py
│       │   ├── cost_tracker.py
│       │   ├── insights.py
│       │   └── text_detector.py
│       ├── sandbox/              # safe Python code execution
│       └── storage/              # S3 client
└── frontend/
    ├── Dockerfile
    └── src/
        ├── api/                  # axios client, typed API functions
        ├── components/
        │   ├── layout/           # AppLayout, Sidebar
        │   ├── projects/         # ProjectCard, ProjectModal, DeleteConfirm
        │   ├── query/            # FilePanel, ResultPanel, ChartCard,
        │   │                     # HistoryPanel, ExportPdfButton
        │   └── ui/               # shared icons, primitives
        ├── hooks/                # useAuth, useFiles, useFilePanel,
        │                         # useProjects, useQueryPage,
        │                         # useQueryHistory, useRunQuery
        ├── pages/                # LoginPage, ProjectsPage, QueryPage
        └── store/                # authStore, historyStore (Zustand)
```

---

## Analysis pipeline

### Structured data (CSV/Excel with numeric/categorical columns)

1. `context_builder.py` loads the file and detects it is not text-heavy
2. `strategies/structured.py` builds schema, sample rows, and descriptive stats
3. `engine/structured.py` calls the LLM with `generate_code.txt` → executes in sandbox
4. Pass 2 runs `find_interesting.txt` if pass 1 result is substantial
5. `insights.py` synthesises both passes into a plain-English summary

### NLP data (text-heavy columns: reviews, articles, comments)

1. `text_detector.py` flags columns with average length ≥ 50 chars
2. `strategies/nlp.py` computes vocabulary size, top words, bigrams
3. `strategies/features.py` pre-computes sentiment scores, TF-IDF keywords, topic clusters, length distribution
4. `engine/nlp.py` calls the LLM with `generate_code_nlp.txt`, injecting pre-computed features
5. Pass 2 and insights follow the same pattern as structured

### Sandbox

Generated Python code runs in a restricted `exec()` environment:
- No `import` statements allowed
- No file I/O, no `__builtins__` escape hatches
- Pre-injected: `df`, `pd`, `np`, `re`, `collections`, `math`, `itertools`, `functools`, `datetime`
- NLP pipeline additionally injects `nlp_features`
- Up to 3 retries with LLM-assisted error correction

### Chart types

| Type | Description |
|---|---|
| `bar` | Categorical comparison |
| `line` | Trend over time |
| `pie` | Part-to-whole |
| `scatter` | Correlation between two numeric variables |
| `histogram` | Distribution of a numeric variable |
| `grouped_bar` | Multi-series categorical comparison |
| `wordcloud_data` | Keyword importance (NLP) |
| `sentiment_distribution` | Positive / Negative / Neutral breakdown (NLP) |
| `top_phrases` | Top keywords or bigrams with scores (NLP) |

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

## Running tests

Tests live in `backend/test/` and require the stack to be running (`docker compose up`).

```bash
# Run all tests
docker exec -it dalreadone-backend-1 python scripts/run_tests.py

# Skip LLM-heavy query tests
docker exec -it dalreadone-backend-1 python test/test_query.py --fast

# Run extra stress rounds (N LLM calls)
QUERY_ROUNDS=3 python test/test_query.py
```

| Test file | Coverage |
|---|---|
| `test_auth.py` | Register, login, refresh, JWT expiry |
| `test_projects.py` | CRUD, ownership isolation |
| `test_files.py` | Upload, list, delete, overwrite, S3 cascade |
| `test_query.py` | Happy path, wrong owner, not found, chart validation |
| `test_history.py` | List, pagination, detail, isolation, delete |
| `test_db.py` | DB connectivity |
| `test_s3.py` | S3 connectivity |
| `test_groq.py` | Groq API connectivity |

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

# Stop and wipe the database
docker compose down -v

# Open a psql session
docker exec -it dalreadone-db-1 psql -U postgres -d dalreadone
```

---

## Required environment variables

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Long random string used to sign JWTs |
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |
| `S3_BUCKET_NAME` | S3 bucket for uploaded files |
| `S3_ACCESS_KEY` | AWS access key with S3 read/write permissions |
| `S3_SECRET_KEY` | Corresponding AWS secret key |

All `GOOGLE_*` and `GITHUB_*` variables are optional.

---

## Notes

- Uploaded files are stored on S3 and never held on disk permanently
- The LLM sandbox runs generated Python code in a restricted environment — no file I/O, no imports, no shell access
- Access tokens expire after 15 minutes; the app silently refreshes them using an HTTP-only cookie
- Charts are rendered client-side with Chart.js using Seaborn-inspired colour palettes
- `NaN` and `Inf` values are sanitized before saving query results to PostgreSQL
- Query history is per-user and fully isolated — users cannot access each other's results