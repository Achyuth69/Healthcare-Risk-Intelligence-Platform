"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    op.execute("CREATE TYPE user_role_enum AS ENUM ('admin','clinician','researcher','patient','readonly')")

    # users
    op.create_table(
        "users",
        sa.Column("id",              postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email",           sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name",       sa.String(255), nullable=False),
        sa.Column("role",            sa.Enum("admin","clinician","researcher","patient","readonly", name="user_role_enum"), nullable=False, server_default="readonly"),
        sa.Column("is_active",       sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified",     sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # patients
    op.create_table(
        "patients",
        sa.Column("id",                           postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("encrypted_ssn",                sa.Text(), nullable=True),
        sa.Column("encrypted_dob",                sa.Text(), nullable=True),
        sa.Column("age",                          sa.Integer(), nullable=False),
        sa.Column("gender",                       sa.String(20), nullable=False),
        sa.Column("ethnicity",                    sa.String(100), nullable=True),
        sa.Column("zip_code",                     sa.String(10), nullable=True),
        sa.Column("bmi",                          sa.Float(), nullable=True),
        sa.Column("blood_pressure_systolic",      sa.Float(), nullable=True),
        sa.Column("blood_pressure_diastolic",     sa.Float(), nullable=True),
        sa.Column("heart_rate",                   sa.Float(), nullable=True),
        sa.Column("glucose_level",                sa.Float(), nullable=True),
        sa.Column("hba1c",                        sa.Float(), nullable=True),
        sa.Column("cholesterol_total",            sa.Float(), nullable=True),
        sa.Column("cholesterol_ldl",              sa.Float(), nullable=True),
        sa.Column("cholesterol_hdl",              sa.Float(), nullable=True),
        sa.Column("triglycerides",                sa.Float(), nullable=True),
        sa.Column("smoking_status",               sa.String(50), nullable=True),
        sa.Column("alcohol_use",                  sa.String(50), nullable=True),
        sa.Column("physical_activity_level",      sa.String(50), nullable=True),
        sa.Column("has_diabetes",                 sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_hypertension",             sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_heart_disease",            sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_kidney_disease",           sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("family_history_diabetes",      sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("family_history_heart_disease", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("medications",                  postgresql.JSONB(), nullable=True),
        sa.Column("created_at",                   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",                   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # prediction_records
    op.create_table(
        "prediction_records",
        sa.Column("id",                 postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("patient_id",         postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=True),
        sa.Column("requested_by",       postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",    ondelete="SET NULL"), nullable=True),
        sa.Column("disease_type",       sa.String(50), nullable=False),
        sa.Column("model_type",         sa.String(50), nullable=False),
        sa.Column("model_version",      sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("risk_score",         sa.Float(), nullable=False),
        sa.Column("risk_category",      sa.String(20), nullable=False),
        sa.Column("confidence",         sa.Float(), nullable=False),
        sa.Column("input_features",     postgresql.JSONB(), nullable=False),
        sa.Column("shap_values",        postgresql.JSONB(), nullable=True),
        sa.Column("lime_explanation",   postgresql.JSONB(), nullable=True),
        sa.Column("feature_importance", postgresql.JSONB(), nullable=True),
        sa.Column("llm_explanation",    sa.Text(), nullable=True),
        sa.Column("created_at",         sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",         sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_predictions_patient",  "prediction_records", ["patient_id"])
    op.create_index("ix_predictions_disease",  "prediction_records", ["disease_type"])
    op.create_index("ix_predictions_created",  "prediction_records", ["created_at"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action",        sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id",   sa.String(255), nullable=True),
        sa.Column("ip_address",    sa.String(45),  nullable=True),
        sa.Column("user_agent",    sa.Text(),       nullable=True),
        sa.Column("metadata",      postgresql.JSONB(), nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_user",    "audit_logs", ["user_id"])
    op.create_index("ix_audit_action",  "audit_logs", ["action"])
    op.create_index("ix_audit_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("prediction_records")
    op.drop_table("patients")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
