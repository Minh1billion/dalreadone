# DALreaDone

AI-powered data analysis app — upload CSV/Excel files, ask questions, and get automated charts and insights.

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

---

## Setup & Run

### 1. Clone the repo

```bash
git clone <repo-url>
cd dalreadone
```

### 2. Create a `.env` file in the root directory

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

# OAuth - Google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# OAuth - GitHub
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# App
ENV=development
FRONTEND_URL=http://localhost:3000
```

### 3. Build and run

Install necessary library for backend:

```bash
pip install -r ./backend/requirements.txt
```
Then run:

```bash
docker compose up --build
```

The first run will take a few minutes to build. Subsequent runs are faster:

```bash
docker compose up
```

### 4. Access

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000      |
| Backend  | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |

---

## Project Structure

```
dalreadone/
├── docker-compose.yml
├── .env                    # Created manually, do not commit
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/           # config, security, oauth
│       ├── routers/        # auth, oauth, projects, files, query
│       ├── services/       # business logic
│       ├── models/         # ORM models + schemas
│       ├── db/             # session, migrations
│       └── storage/        # S3 helpers
└── frontend/
    ├── Dockerfile
    └── src/
```

---

## OAuth Setup (optional)

### Google

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **Credentials**
2. Create an **OAuth 2.0 Client ID** → Application type: **Web application**
3. Add Authorized redirect URI: `http://localhost:8000/auth/google/callback`
4. Copy the Client ID and Secret into `.env`

### GitHub

1. Go to GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**
2. Homepage URL: `http://localhost:3000`
3. Authorization callback URL: `http://localhost:8000/auth/github/callback`
4. Copy the Client ID and Secret into `.env`

---

## Common Commands

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Stream backend logs
docker compose logs -f backend

# Stream all logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and delete all data (including database)
docker compose down -v

# Rebuild after code changes
docker compose up --build
```

## Access the Database

```bash
# Open psql inside the postgres container
docker exec -it dalreadone-db-1 psql -U postgres -d dalreadone
```

---

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | Secret string for signing JWTs — use a long random value |
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |
| `S3_BUCKET_NAME` | S3 bucket name for storing uploaded files |
| `S3_ACCESS_KEY` | AWS Access Key with S3 permissions |
| `S3_SECRET_KEY` | Corresponding AWS Secret Key |

OAuth variables (`GOOGLE_*`, `GITHUB_*`) are optional — leave blank to disable social login.
