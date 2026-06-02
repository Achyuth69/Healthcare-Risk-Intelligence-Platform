# Free Deployment Guide — Healthcare Risk Intelligence Platform
## 100% Free — No Credit Card Required

---

## Free Platform Stack

| Layer | Free Platform | Free Limit |
|-------|--------------|------------|
| Backend API | **Render.com** | 750 hrs/month, 512MB RAM |
| Frontend | **Vercel** | Unlimited deploys |
| Database | **Supabase** | 500MB PostgreSQL, free forever |
| LLM (Llama 3) | **Groq API** | 14,400 req/day free |
| Cache | **Upstash Redis** | 10,000 req/day free |
| CI/CD | **GitHub Actions** | 2,000 min/month free |
| Domain | **yourapp.vercel.app** | Free subdomain |

**Total: $0/month**

---

## Architecture

```
Browser
  │
  ▼
Vercel (React frontend — yourapp.vercel.app)
  │  HTTPS API calls
  ▼
Render.com (FastAPI backend — yourapi.onrender.com)
  ├── Supabase PostgreSQL  (predictions, users, patients)
  ├── Upstash Redis        (rate limiting, caching)
  └── Groq API             (Llama 3 70B — free LLM)
```

---

## STEP 1 — Push Code to GitHub

```bash
# From your project root
git init
git add .
git commit -m "feat: Healthcare Risk Intelligence Platform"

# Create repo at github.com/new, then:
git remote add origin https://github.com/YOUR_USERNAME/healthcare-risk-platform.git
git branch -M main
git push -u origin main
```

---

## STEP 2 — Supabase (Free PostgreSQL)

### 2.1 Create project
1. Go to **https://supabase.com** → **Sign Up** (use GitHub)
2. **New Project** → Name: `healthrisk` → set a strong password → **Create**
3. Wait ~2 minutes

### 2.2 Get connection string
1. **Settings** → **Database** → scroll to **Connection String**
2. Select **URI** tab → copy it
3. Replace `[YOUR-PASSWORD]` with your actual password
4. It looks like:
   ```
   postgresql://postgres:YOUR_PASS@db.abcdefgh.supabase.co:5432/postgres
   ```
5. For asyncpg, change `postgresql://` → `postgresql+asyncpg://`

### 2.3 Run schema
1. Go to **SQL Editor** → **New Query** → paste this → **Run**:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'readonly',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients (
    id                           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    encrypted_ssn                TEXT,
    encrypted_dob                TEXT,
    age                          INTEGER NOT NULL,
    gender                       VARCHAR(20) NOT NULL,
    ethnicity                    VARCHAR(100),
    zip_code                     VARCHAR(10),
    bmi                          FLOAT,
    blood_pressure_systolic      FLOAT,
    blood_pressure_diastolic     FLOAT,
    heart_rate                   FLOAT,
    glucose_level                FLOAT,
    hba1c                        FLOAT,
    cholesterol_total            FLOAT,
    cholesterol_ldl              FLOAT,
    cholesterol_hdl              FLOAT,
    triglycerides                FLOAT,
    smoking_status               VARCHAR(50),
    alcohol_use                  VARCHAR(50),
    physical_activity_level      VARCHAR(50),
    has_diabetes                 BOOLEAN NOT NULL DEFAULT FALSE,
    has_hypertension             BOOLEAN NOT NULL DEFAULT FALSE,
    has_heart_disease            BOOLEAN NOT NULL DEFAULT FALSE,
    has_kidney_disease           BOOLEAN NOT NULL DEFAULT FALSE,
    family_history_diabetes      BOOLEAN NOT NULL DEFAULT FALSE,
    family_history_heart_disease BOOLEAN NOT NULL DEFAULT FALSE,
    medications                  JSONB,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prediction_records (
    id                 VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id         VARCHAR(36),
    requested_by       VARCHAR(36),
    disease_type       VARCHAR(50) NOT NULL,
    model_type         VARCHAR(50) NOT NULL,
    model_version      VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    risk_score         FLOAT NOT NULL,
    risk_category      VARCHAR(20) NOT NULL,
    confidence         FLOAT NOT NULL,
    input_features     JSONB NOT NULL,
    shap_values        JSONB,
    lime_explanation   JSONB,
    feature_importance JSONB,
    llm_explanation    TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id            VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       VARCHAR(36),
    action        VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id   VARCHAR(255),
    ip_address    VARCHAR(45),
    user_agent    TEXT,
    extra_data    JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Default admin user  (password: Admin@123!)
INSERT INTO users (email, hashed_password, full_name, role, is_active, is_verified)
VALUES (
    'admin@healthrisk.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.',
    'System Administrator', 'admin', TRUE, TRUE
) ON CONFLICT (email) DO NOTHING;
```

---

## STEP 3 — Upstash Redis (Free Cache)

1. Go to **https://upstash.com** → **Sign Up** (GitHub login)
2. **Create Database**
   - Name: `healthrisk-cache`
   - Type: **Regional**
   - Region: **US-East-1**
   - Click **Create**
3. Copy the **Redis URL** from the dashboard:
   ```
   rediss://default:PASSWORD@us1-xxxx.upstash.io:6379
   ```

---

## STEP 4 — Groq API Key (Free Llama 3 70B)

1. Go to **https://console.groq.com** → **Sign Up** (GitHub login)
2. **API Keys** → **Create API Key** → name it `healthrisk`
3. Copy the key: `gsk_xxxxxxxxxxxxxxxxxxxx`

> Free tier: **14,400 requests/day**, **6,000 tokens/min** — more than enough.

---

## STEP 5 — Deploy Backend on Render

### 5.1 Create Web Service
1. Go to **https://render.com** → **Sign Up** (GitHub login)
2. **New** → **Web Service**
3. Connect your GitHub repo → select `healthcare-risk-platform`
4. Configure:
   - **Name:** `healthrisk-backend`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements-render.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`

### 5.2 Add Environment Variables
Click **Environment** → **Add Environment Variable** — add each one:

| Key | Value |
|-----|-------|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:PASS@db.XXX.supabase.co:5432/postgres` |
| `SECRET_KEY` | *(click "Generate")* |
| `JWT_SECRET_KEY` | *(click "Generate")* |
| `ENCRYPTION_KEY` | *(any 32-char random string)* |
| `GROQ_API_KEY` | `gsk_your_key_here` |
| `GROQ_MODEL` | `llama3-70b-8192` |
| `REDIS_URL` | `rediss://default:PASS@us1-xxx.upstash.io:6379` |
| `MODEL_ARTIFACTS_DIR` | `/tmp/models` |
| `ALLOWED_ORIGINS` | `https://YOUR_APP.vercel.app` |
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | `json` |

### 5.3 Deploy
Click **Create Web Service** → Render builds and deploys automatically.

After ~3 minutes you'll get a URL like:
```
https://healthrisk-backend.onrender.com
```

Test it:
```
https://healthrisk-backend.onrender.com/health
→ {"status":"healthy","version":"1.0.0","environment":"production"}

https://healthrisk-backend.onrender.com/docs
→ Full Swagger UI with all 20+ endpoints
```

> **Note:** Free tier spins down after 15 min of inactivity. First request takes ~30s to wake up. Upgrade to Render Starter ($7/month) to keep it always-on.

---

## STEP 6 — Deploy Frontend on Vercel

### 6.1 Import project
1. Go to **https://vercel.com** → **Sign Up** (GitHub login)
2. **Add New** → **Project**
3. Import your `healthcare-risk-platform` repo
4. Configure:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 6.2 Add Environment Variable
Click **Environment Variables** → Add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://healthrisk-backend.onrender.com/api/v1` |

### 6.3 Deploy
Click **Deploy** → Vercel builds in ~1 minute.

You get a URL like:
```
https://healthcare-risk-platform.vercel.app
```

---

## STEP 7 — Connect Frontend to Backend (CORS)

Go back to **Render** → your backend service → **Environment**  
Update `ALLOWED_ORIGINS`:
```
https://healthcare-risk-platform.vercel.app,http://localhost:3000
```

Click **Save Changes** → Render redeploys automatically.

---

## STEP 8 — Set Up GitHub Actions CI/CD

Add these secrets to your GitHub repo:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|-------|
| `RENDER_API_KEY` | Render → Account Settings → API Keys → Create |
| `RENDER_SERVICE_ID` | Render → your service → Settings → Service ID |

Create the workflow file:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Render + Vercel

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pytest pytest-asyncio httpx pydantic==2.10.6 pydantic-settings python-jose bcrypt cryptography structlog fastapi sqlalchemy aiosqlite
        working-directory: backend
      - run: python -m pytest tests/ -v --tb=short -x
        working-directory: backend
        env:
          DATABASE_URL: sqlite+aiosqlite:///./test.db
          SECRET_KEY: test-secret-key-32-chars-minimum-ok
          JWT_SECRET_KEY: test-jwt-secret-32-chars-minimum-ok
          ENCRYPTION_KEY: test-encryption-key-32-bytes-here
          APP_ENV: test

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST \
            "https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys" \
            -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"clearCache": false}'

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: frontend
          vercel-args: '--prod'
```

Add the extra Vercel secrets:
| Secret | Where to find |
|--------|--------------|
| `VERCEL_TOKEN` | vercel.com → Settings → Tokens → Create |
| `VERCEL_ORG_ID` | vercel.com → Settings → General → Team ID |
| `VERCEL_PROJECT_ID` | Vercel project → Settings → General → Project ID |

---

## STEP 9 — Verify Everything Works

```
1. Open: https://healthcare-risk-platform.vercel.app
   → Should show the login page

2. Login with: admin@healthrisk.ai / Admin@123!
   → Should reach the Dashboard

3. Go to Risk Assessment → fill in patient data → Run
   → Should return risk score + SHAP chart + Groq LLM narrative

4. Go to Clinical AI → ask a question
   → Should return an AI-generated answer

5. API Docs: https://healthrisk-backend.onrender.com/docs
   → Full interactive Swagger UI
```

---

## Free Tier Limits & Workarounds

| Limit | Workaround |
|-------|-----------|
| Render spins down after 15 min | Use UptimeRobot (free) to ping /health every 14 min |
| Supabase 500MB DB | Predictions are small JSON — holds ~500,000 records |
| Groq 14,400 req/day | ~600 predictions/hour — plenty for demo/small clinic |
| Vercel 100GB bandwidth | Static files are tiny — no issue |

### Keep Render Awake (Free)
1. Go to **https://uptimerobot.com** → Sign up free
2. **Add New Monitor**
   - Monitor Type: HTTP(s)
   - URL: `https://healthrisk-backend.onrender.com/health`
   - Monitoring Interval: **14 minutes**
3. Click **Create Monitor** — your backend stays awake 24/7

---

## Upgrade Path (When You Need More)

| Need | Solution | Cost |
|------|----------|------|
| Always-on backend | Render Starter | $7/month |
| More DB storage | Supabase Pro | $25/month |
| Custom domain | Vercel Pro | $20/month |
| More LLM requests | Groq paid | Pay-per-token |
| Full production | AWS EKS (see DEPLOYMENT_GUIDE.md) | ~$717/month |

---

## Summary — Your Live URLs

After completing all steps:

```
Frontend  → https://YOUR_APP.vercel.app
Backend   → https://healthrisk-backend.onrender.com
API Docs  → https://healthrisk-backend.onrender.com/docs
Login     → admin@healthrisk.ai / Admin@123!
```

**Total time to deploy: ~20 minutes**
**Total cost: $0**
