# Free Deployment Guide — Healthcare Risk Intelligence Platform
## 100% Free — No Credit Card Required

---

## Free Platform Stack

| Layer | Free Platform | Free Limit |
|-------|--------------|------------|
| Backend API | **Render.com** | 750 hrs/month, 512 MB RAM |
| Frontend | **Vercel** | Unlimited deploys |
| Database | **Supabase** | 500 MB PostgreSQL, free forever |
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
Vercel  (React frontend — https://YOUR_APP.vercel.app)
  │  HTTPS API calls to /api/v1/...
  ▼
Render.com  (FastAPI backend — https://healthrisk-backend.onrender.com)
  ├── Supabase PostgreSQL   predictions, users, patients
  ├── Upstash Redis         rate limiting, caching
  └── Groq API              Llama 3 70B — free LLM narratives
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/.env` | Local dev secrets (gitignored) |
| `backend/.env.render` | Render env var template (gitignored) |
| `.env.example` | Documented template committed to repo |
| `render.yaml` | Render infrastructure-as-code |
| `frontend/vercel.json` | Vercel SPA routing config |
| `backend/requirements-render.txt` | Slim deps for free 512 MB Render tier |
| `.github/workflows/deploy-free.yml` | CI/CD: test → Render + Vercel |

---

## STEP 1 — GitHub (already done)

Your code is already at:
```
https://github.com/Achyuth69/Healthcare-Risk-Intelligence-Platform
```
All other platforms connect directly to this repo.

---

## STEP 2 — Supabase (Free PostgreSQL)

### 2.1 Create project
1. Go to **https://supabase.com** → **Sign Up** (GitHub login)
2. **New Project**
   - Name: `healthrisk`
   - Database Password: generate strong one → **copy and save it**
   - Region: closest to you
3. Wait ~2 minutes for provisioning

### 2.2 Get your connection string
1. **Settings** → **Database** → scroll to **Connection String**
2. Select the **URI** tab → copy the string
3. It looks like:
   ```
   postgresql://postgres:YOUR_PASSWORD@db.abcdefghijkl.supabase.co:5432/postgres
   ```
4. Change the driver prefix for asyncpg:
   ```
   postgresql+asyncpg://postgres:YOUR_PASSWORD@db.abcdefghijkl.supabase.co:5432/postgres
   ```
5. Save this — you'll need it in Render (STEP 5)

### 2.3 Run the database schema
1. **SQL Editor** → **New Query** → paste the entire block below → click **Run**

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50)  NOT NULL DEFAULT 'readonly',
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
3. After creation, go to **Details** tab
4. Copy the **Redis URL** — it looks like:
   ```
   rediss://default:AxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxX@us1-xxxx-xxxx.upstash.io:6379
   ```
5. Save this — you'll need it in Render (STEP 5)

---

## STEP 4 — Groq API Key (Free Llama 3 70B)

1. Go to **https://console.groq.com** → **Sign Up** (GitHub login, no credit card)
2. **API Keys** in the left sidebar → **Create API Key**
3. Name: `healthrisk` → **Submit**
4. Copy the key — it starts with `gsk_` and looks like:
   ```
   gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Save this — you'll need it in Render (STEP 5) and your local `.env`

> **Free limits:** 14,400 requests/day · 6,000 tokens/min · Llama 3 70B included

### Add to local `.env` right now

Open `backend/.env` and update this line:
```env
GROQ_API_KEY=gsk_paste_your_actual_key_here
```

---

## STEP 5 — Deploy Backend on Render

### 5.1 Create Web Service
1. Go to **https://render.com** → **Sign Up** (GitHub login)
2. **New +** → **Web Service**
3. Connect GitHub → select **Healthcare-Risk-Intelligence-Platform**
4. Configure:

   | Field | Value |
   |-------|-------|
   | Name | `healthrisk-backend` |
   | Root Directory | `backend` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements-render.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Plan | `Free` |

### 5.2 Add Environment Variables

Click **Environment** → **Add Environment Variable** for each row:

| Key | Value | Where to get it |
|-----|-------|-----------------|
| `APP_ENV` | `production` | hardcode |
| `DEBUG` | `false` | hardcode |
| `APP_VERSION` | `1.0.0` | hardcode |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:PASS@db.XXX.supabase.co:5432/postgres` | Supabase STEP 2.2 |
| `SECRET_KEY` | *(click **Generate**)* | Render auto-generates |
| `JWT_SECRET_KEY` | *(click **Generate**)* | Render auto-generates |
| `JWT_ALGORITHM` | `HS256` | hardcode |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | hardcode |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | hardcode |
| `ENCRYPTION_KEY` | any 32-char random string | e.g. `MyR@ndomEncryptionKey32Chars!!` |
| `REDIS_URL` | `rediss://default:PASS@us1-xxx.upstash.io:6379` | Upstash STEP 3 |
| `GROQ_API_KEY` | `gsk_your_key_here` | Groq STEP 4 |
| `GROQ_MODEL` | `llama3-70b-8192` | hardcode |
| `CHROMA_HOST` | `localhost` | hardcode |
| `CHROMA_PORT` | `8001` | hardcode |
| `CHROMA_COLLECTION_NAME` | `healthcare_docs` | hardcode |
| `MODEL_ARTIFACTS_DIR` | `/tmp/models` | hardcode |
| `LOG_LEVEL` | `INFO` | hardcode |
| `LOG_FORMAT` | `json` | hardcode |
| `ALLOWED_ORIGINS` | `https://YOUR_APP.vercel.app,http://localhost:3000` | update after STEP 6 |

> **Tip:** Use `backend/.env.render` in this repo as your reference checklist.

### 5.3 Deploy
Click **Create Web Service** → Render pulls from GitHub and builds.

After ~3 minutes:
```
✅ https://healthrisk-backend.onrender.com/health
   → {"status":"healthy","version":"1.0.0","environment":"production"}

✅ https://healthrisk-backend.onrender.com/docs
   → Full Swagger UI — all 20+ endpoints interactive
```

> **Free tier note:** Spins down after 15 min idle. First request takes ~30s to wake. See STEP 9 to keep it awake 24/7 for free.

---

## STEP 6 — Deploy Frontend on Vercel

### 6.1 Import project
1. Go to **https://vercel.com** → **Sign Up** (GitHub login)
2. **Add New** → **Project**
3. Import **Healthcare-Risk-Intelligence-Platform** from GitHub
4. Configure:

   | Field | Value |
   |-------|-------|
   | Framework Preset | `Vite` |
   | Root Directory | `frontend` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |

### 6.2 Add Environment Variable
**Environment Variables** section → Add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://healthrisk-backend.onrender.com/api/v1` |

### 6.3 Deploy
Click **Deploy** → Vercel builds in ~1 minute.

Your frontend URL:
```
https://healthcare-risk-intelligence-platform.vercel.app
```

---

## STEP 7 — Connect Frontend ↔ Backend (CORS)

Go to **Render** → **healthrisk-backend** → **Environment**

Update `ALLOWED_ORIGINS` to your real Vercel URL:
```
https://healthcare-risk-intelligence-platform.vercel.app,http://localhost:3000
```

Click **Save Changes** → Render redeploys in ~1 minute automatically.

---

## STEP 8 — Set Up CI/CD (GitHub Actions)

Every `git push` to `main` will automatically test → deploy backend → deploy frontend.

Add these secrets to GitHub:
**repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Where to find the value |
|-------------|------------------------|
| `RENDER_API_KEY` | Render → Account Settings → API Keys → Create API Key |
| `RENDER_SERVICE_ID` | Render → healthrisk-backend → Settings → Service ID |
| `VERCEL_TOKEN` | vercel.com → Settings → Tokens → Create |
| `VERCEL_ORG_ID` | vercel.com → Settings → General → Team ID |
| `VERCEL_PROJECT_ID` | Vercel project → Settings → General → Project ID |

The workflow file `.github/workflows/deploy-free.yml` is already in your repo and runs automatically.

---

## STEP 9 — Keep Render Awake 24/7 (Free)

Free Render services sleep after 15 min of inactivity. Fix with UptimeRobot:

1. Go to **https://uptimerobot.com** → **Sign Up** (free)
2. **Add New Monitor**
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `HealthRisk Backend`
   - URL: `https://healthrisk-backend.onrender.com/health`
   - Monitoring Interval: **14 minutes**
3. Click **Create Monitor**

Your backend now stays awake 24/7 at zero cost.

---

## STEP 10 — Verify Everything End-to-End

```
1. Frontend login page
   → https://healthcare-risk-intelligence-platform.vercel.app
   → Should show the HealthRisk AI login screen

2. Login
   → Email:    admin@healthrisk.ai
   → Password: Admin@123!
   → Should reach the Dashboard with charts

3. Risk Assessment
   → Go to "Risk Assessment" tab
   → Fill in patient data (age 52, BMI 31, glucose 118...)
   → Click "Run Risk Assessment"
   → Should return: risk score % + SHAP waterfall chart + Groq AI narrative

4. Clinical AI Chat
   → Go to "Clinical AI" tab
   → Ask: "What are the main risk factors for Type 2 Diabetes?"
   → Should return a Groq Llama 3 generated answer

5. API Docs (interactive)
   → https://healthrisk-backend.onrender.com/docs
   → All 20+ endpoints listed with Try-it-out support
```

---

## All Free Tier Limits & Workarounds

| Limit | Impact | Workaround |
|-------|--------|-----------|
| Render sleeps after 15 min idle | 30s cold start | UptimeRobot ping every 14 min (STEP 9) |
| Render 512 MB RAM | No local LLM | Groq API handles LLM (no RAM needed) |
| Supabase 500 MB DB | ~500,000 predictions | Plenty for demo + small clinic |
| Groq 14,400 req/day | ~600 predictions/hour | More than enough for most use cases |
| Vercel 100 GB bandwidth | ~10M page loads/month | Not an issue for this app |
| GitHub Actions 2,000 min/month | ~100 deploys/month | Each deploy takes ~2 min |

---

## Upgrade Path

| When you need more | Upgrade to | Cost |
|-------------------|------------|------|
| Always-on backend (no cold start) | Render Starter | $7/month |
| More DB storage | Supabase Pro | $25/month |
| Custom domain (yourapp.com) | Vercel Pro | $20/month |
| More LLM requests | Groq pay-as-you-go | ~$0.27/million tokens |
| Full production (AWS EKS) | See `DEPLOYMENT_GUIDE.md` | ~$717/month |

---

## Summary

```
✅ Frontend  → https://healthcare-risk-intelligence-platform.vercel.app
✅ Backend   → https://healthrisk-backend.onrender.com
✅ API Docs  → https://healthrisk-backend.onrender.com/docs
✅ Login     → admin@healthrisk.ai  /  Admin@123!
✅ Cost      → $0/month
✅ Time      → ~20 minutes to deploy
```

### The 5 accounts you need (all free, all GitHub login)

```
1. github.com          → already done ✅
2. supabase.com        → PostgreSQL database
3. upstash.com         → Redis cache
4. console.groq.com    → Llama 3 70B LLM
5. render.com          → Backend hosting
6. vercel.com          → Frontend hosting
```
