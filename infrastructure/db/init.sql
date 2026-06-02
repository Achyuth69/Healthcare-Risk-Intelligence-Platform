-- ============================================================
-- Healthcare Risk Intelligence Platform — Database Schema
-- PostgreSQL 16
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enums ─────────────────────────────────────────────────────
CREATE TYPE user_role_enum AS ENUM (
    'admin', 'clinician', 'researcher', 'patient', 'readonly'
);

CREATE TYPE risk_category_enum AS ENUM (
    'low', 'medium', 'high', 'critical'
);

-- ── Users Table ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            user_role_enum NOT NULL DEFAULT 'readonly',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ── Patients Table ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- Encrypted PII
    encrypted_ssn               TEXT,
    encrypted_dob               TEXT,
    -- Demographics
    age                         INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    gender                      VARCHAR(20) NOT NULL,
    ethnicity                   VARCHAR(100),
    zip_code                    VARCHAR(10),
    -- Vitals
    bmi                         FLOAT CHECK (bmi > 0),
    blood_pressure_systolic     FLOAT,
    blood_pressure_diastolic    FLOAT,
    heart_rate                  FLOAT,
    glucose_level               FLOAT,
    hba1c                       FLOAT,
    cholesterol_total           FLOAT,
    cholesterol_ldl             FLOAT,
    cholesterol_hdl             FLOAT,
    triglycerides               FLOAT,
    -- Lifestyle
    smoking_status              VARCHAR(50),
    alcohol_use                 VARCHAR(50),
    physical_activity_level     VARCHAR(50),
    -- Medical History
    has_diabetes                BOOLEAN NOT NULL DEFAULT FALSE,
    has_hypertension            BOOLEAN NOT NULL DEFAULT FALSE,
    has_heart_disease           BOOLEAN NOT NULL DEFAULT FALSE,
    has_kidney_disease          BOOLEAN NOT NULL DEFAULT FALSE,
    family_history_diabetes     BOOLEAN NOT NULL DEFAULT FALSE,
    family_history_heart_disease BOOLEAN NOT NULL DEFAULT FALSE,
    -- Medications (JSONB for flexibility)
    medications                 JSONB,
    -- Audit
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_patients_created ON patients(created_at DESC);

-- ── Prediction Records Table ──────────────────────────────────
CREATE TABLE IF NOT EXISTS prediction_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          UUID REFERENCES patients(id) ON DELETE CASCADE,
    requested_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    -- Prediction Details
    disease_type        VARCHAR(50) NOT NULL,
    model_type          VARCHAR(50) NOT NULL,
    model_version       VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    -- Risk Assessment
    risk_score          FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
    risk_category       VARCHAR(20) NOT NULL,
    confidence          FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    -- Input snapshot
    input_features      JSONB NOT NULL,
    -- Explanations
    shap_values         JSONB,
    lime_explanation    JSONB,
    feature_importance  JSONB,
    -- LLM narrative
    llm_explanation     TEXT,
    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_predictions_patient ON prediction_records(patient_id);
CREATE INDEX idx_predictions_disease ON prediction_records(disease_type);
CREATE INDEX idx_predictions_created ON prediction_records(created_at DESC);
CREATE INDEX idx_predictions_risk_category ON prediction_records(risk_category);

-- ── Audit Logs Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     VARCHAR(255),
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);

-- ── Model Registry Table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_registry (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      VARCHAR(100) NOT NULL,
    model_type      VARCHAR(50) NOT NULL,
    disease_type    VARCHAR(50) NOT NULL,
    version         VARCHAR(50) NOT NULL,
    artifact_path   TEXT NOT NULL,
    metrics         JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    deployed_at     TIMESTAMPTZ,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(model_type, disease_type, version)
);

-- ── Updated_at Trigger ────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at
    BEFORE UPDATE ON prediction_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Seed Admin User ───────────────────────────────────────────
-- Password: Admin@123! (bcrypt hash — change in production)
INSERT INTO users (email, hashed_password, full_name, role, is_active, is_verified)
VALUES (
    'admin@healthrisk.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.',
    'System Administrator',
    'admin',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

COMMENT ON TABLE patients IS 'Patient records with encrypted PII fields';
COMMENT ON TABLE prediction_records IS 'ML prediction results with SHAP/LIME explanations';
COMMENT ON TABLE audit_logs IS 'Immutable audit trail for HIPAA compliance';
