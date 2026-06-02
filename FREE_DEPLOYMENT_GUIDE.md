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
  │  HTTPS API calls
  ▼
Render.com  (FastAPI backend — https://healthrisk-backend.onrender.com)
  ├── Supabase PostgreSQL   via Transaction Pooler port 6543
  ├── Upstash Redis         rate limiting, caching
  └── Groq API              Llama 3 70B — free LLM
```

---

## ⚠️ Important: Supabase Connection on Render Free

Render free tier **blocks port 5432** (direct PostgreSQL).
You **must** use Supabase's **Transaction Pooler on port 6543** instead.

| Connection Type | Port | Works on Render Free? |
|----------------|------|----------------------|
| Direct connection | 5432 | ❌ Blocked |
| Transaction Pooler | 6543 | ✅ Works |

---

## STEP 1 — GitHub (already done)

```
https://github.com/Achyuth69/Healthcare-Risk-Intelligence-Platform
```

---

## STEP 2 — Supabase (Free PostgreSQL)

### 2.1 Create project
1. Go to **https://supabase.com** → **Sign Up** (GitHub login)
2. **New Project** → Name: `healthrisk` → set password → **Create**
3. Wait ~2 minutes

### 2.2 Get Transaction Pooler URL (NOT direct connection)

> ⚠️ This is the critical step. Use the **Transaction Pooler**, NOT the direct URI.

1. **Settings** → **Database**
2. Scroll to **Connection Pooling** section
3. Set **Pool Mode** to **Transaction**
4. Copy the **Connection String** from the pooler section

It looks like this:
```
postgres://postgres.pmhazxdanfriuhzvjodn:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

5. Change `postgres://` → `postgresql+asyncpg://` for SQLAlchemy:
```
postgresql+asyncpg://postgres.pmhazxdanfriuhzvjodn:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

6. Save this — you'll need it as `DATABASE_URL` in Render (STEP 5)

### 2.3 Run the database schema
1. **SQL Editor** → **New Query** → paste this entire block → click **Run**

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

-- Default admin user (password: Admin@123!)
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
2. **Create Database** → Name: `healthrisk-cache` → Region: US-East-1 → **Create**
3. Copy the **Redis URL** from the Details tab:
   ```
   rediss://default:PASSWORD@us1-xxxx.upstash.io:6379
   ```

---

## STEP 4 — Groq API Key (Free Llama 3 70B)

1. Go to **https://console.groq.com** → **Sign Up** (GitHub login, no credit card)
2. **API Keys** → **Create API Key** → name: `healthrisk`
3. Copy the key: `gsk_xxxxxxxxxxxxxxxxxxxx`

> Free: 14,400 req/day · 6,000 tokens/min

---

## STEP 5 — Deploy Backend on Render

### 5.1 Create Web Service
1. **https://render.com** → **Sign Up** (GitHub login)
2. **New +** → **Web Service**
3. Connect **Healthcare-Risk-Intelligence-Platform** repo
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

| Key | Value |
|-----|-------|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `APP_VERSION` | `1.0.0` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.pmhazxdanfriuhzvjodn:YOUR_PASS@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres` |
| `SECRET_KEY` | click **Generate** |
| `JWT_SECRET_KEY` | click **Generate** |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `ENCRYPTION_KEY` | any 32-char string e.g. `HealthRiskEncKey32BytesOk2024!!` |
| `REDIS_URL` | `rediss://default:PASSWORD@us1-xxxx.upstash.io:6379` |
| `GROQ_API_KEY` | `gsk_your_key_here` |
| `GROQ_MODEL` | `llama3-70b-8192` |
| `CHROMA_HOST` | `localhost` |
| `CHROMA_PORT` | `8001` |
| `CHROMA_COLLECTION_NAME` | `healthcare_docs` |
| `MODEL_ARTIFACTS_DIR` | `/tmp/models` |
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | `json` |
| `ALLOWED_ORIGINS` | `*` |

### 5.3 Deploy
Click **Create Web Service** → Render builds in ~3 min.

Verify:
```
https://healthrisk-backend.onrender.com/health
→ {"status":"healthy","version":"1.0.0","environment":"production"}

https://healthrisk-backend.onrender.com/docs
→ Full Swagger UI
```

---

## STEP 6 — Deploy Frontend on Vercel

1. **https://vercel.com** → **Sign Up** → **Add New Project**
2. Import **Healthcare-Risk-Intelligence-Platform**
3. Configure:

| Field | Value |
|-------|-------|
| Framework Preset | `Vite` |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

4. Add Environment Variable:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://healthrisk-backend.onrender.com/api/v1` |

5. Click **Deploy** → live in ~1 min

---

## STEP 7 — Set Up GitHub Actions CI/CD

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to find |
|--------|--------------|
| `RENDER_API_KEY` | Render → Account Settings → API Keys → Create |
| `RENDER_SERVICE_ID` | Render → healthrisk-backend → Settings → Service ID |
| `VERCEL_TOKEN` | vercel.com → Settings → Tokens → Create |
| `VERCEL_ORG_ID` | vercel.com → Settings → General → Team ID |
| `VERCEL_PROJECT_ID` | Vercel project → Settings → General → Project ID |

Workflow file `.github/workflows/deploy-free.yml` is already in the repo.

---

## STEP 8 — Keep Render Awake 24/7 (Free)

1. **https://uptimerobot.com** → Sign up free
2. **Add New Monitor**
   - Type: `HTTP(s)`
   - URL: `https://healthrisk-backend.onrender.com/health`
   - Interval: **14 minutes**
3. **Create Monitor** — backend stays awake forever

---

## STEP 9 — Verify End-to-End

```
1. https://YOUR_APP.vercel.app
   → Login page ✅

2. Login: admin@healthrisk.ai / Admin@123!
   → Dashboard with charts ✅

3. Register new user
   → /register → fill form → Create Account ✅

4. Risk Assessment
   → Fill patient data → Run → risk score + SHAP + Groq narrative ✅

5. Clinical AI Chat
   → Ask: "What are the main risk factors for diabetes?"
   → Groq Llama 3 answer ✅

6. API Docs
   → https://healthrisk-backend.onrender.com/docs ✅
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `503 Service Unavailable` on register/login | Wrong DATABASE_URL | Use Transaction Pooler URL (port 6543) from Supabase |
| `CORS blocked` | ALLOWED_ORIGINS wrong | Set `ALLOWED_ORIGINS=*` in Render env vars |
| `net::ERR_FAILED` | Backend sleeping | Wait 30s (cold start) or set up UptimeRobot |
| `422 Unprocessable Entity` | Password too weak | Must have uppercase, number, special char |
| `401 Unauthorized` | Wrong credentials | Check email/password, user must be registered |

---

## Free Tier Limits

| Limit | Workaround |
|-------|-----------|
| Render sleeps after 15 min idle | UptimeRobot ping every 14 min |
| Supabase 500 MB DB | ~500,000 prediction records |
| Groq 14,400 req/day | ~600 predictions/hour |
| Render 512 MB RAM | No local LLM (Groq API handles it) |

---

## Your Live URLs

```
Frontend  → https://healthcare-risk-intelligence-platfo.vercel.app
Backend   → https://healthrisk-backend.onrender.com
API Docs  → https://healthrisk-backend.onrender.com/docs
Login     → admin@healthrisk.ai / Admin@123!
Cost      → $0/month
```

---

## Upgrade Path

| Need | Solution | Cost |
|------|----------|------|
| Always-on backend | Render Starter | $7/month |
| More DB storage | Supabase Pro | $25/month |
| Custom domain | Vercel Pro | $20/month |
| Full production (AWS EKS) | See `DEPLOYMENT_GUIDE.md` | ~$717/month |
