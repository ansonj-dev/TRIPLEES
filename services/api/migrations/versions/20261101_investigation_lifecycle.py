"""Persistent investigation jobs, executions, and audit trail.

Revision ID: 20261101_investigation_lifecycle
Revises: 20261031_document_intelligence
"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_investigation_lifecycle"
down_revision = "20261031_document_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("project_id", sa.String(80), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.String(80), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("request_key", sa.String(100)),
        sa.Column("title", sa.String(240), nullable=False), sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("evidence_ids_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("external_ai_authorized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("public_research_authorized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_token_budget", sa.Integer(), nullable=False, server_default="6000"),
        sa.Column("ai_tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failure_summary", sa.Text()), sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)), sa.Column("worker_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("created_by", "request_key", name="uq_investigation_idempotency_key"),
    )
    for col in ("project_id", "created_by", "status"):
        op.create_index(f"ix_investigations_{col}", "investigations", [col])
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_key", sa.String(64), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("task_summary", sa.Text(), nullable=False), sa.Column("output_json", sa.Text()),
        sa.Column("error_code", sa.String(64)), sa.Column("worker_id", sa.String(100)),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("investigation_id", "agent_key", "attempt_number", name="uq_investigation_agent_attempt"),
    )
    for col in ("investigation_id", "status"):
        op.create_index(f"ix_agent_executions_{col}", "agent_executions", [col])
    op.create_table(
        "agent_audit_events",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(80), sa.ForeignKey("agent_executions.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(64), nullable=False), sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_audit_events_investigation_id", "agent_audit_events", ["investigation_id"])
    op.create_index("ix_agent_audit_events_execution_id", "agent_audit_events", ["execution_id"])
    with op.batch_alter_table("model_usage") as batch:
        batch.add_column(sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", name="fk_model_usage_investigation_id_investigations", ondelete="SET NULL")))
        batch.add_column(sa.Column("execution_id", sa.String(80), sa.ForeignKey("agent_executions.id", name="fk_model_usage_execution_id_agent_executions", ondelete="SET NULL")))
    op.create_index("ix_model_usage_investigation_id", "model_usage", ["investigation_id"])
    op.create_index("ix_model_usage_execution_id", "model_usage", ["execution_id"])


def downgrade() -> None:
    op.drop_index("ix_model_usage_execution_id", table_name="model_usage")
    op.drop_index("ix_model_usage_investigation_id", table_name="model_usage")
    with op.batch_alter_table("model_usage") as batch:
        batch.drop_column("execution_id")
        batch.drop_column("investigation_id")
    op.drop_index("ix_agent_audit_events_execution_id", table_name="agent_audit_events")
    op.drop_index("ix_agent_audit_events_investigation_id", table_name="agent_audit_events")
    op.drop_table("agent_audit_events")
    op.drop_index("ix_agent_executions_status", table_name="agent_executions")
    op.drop_index("ix_agent_executions_investigation_id", table_name="agent_executions")
    op.drop_table("agent_executions")
    op.drop_index("ix_investigations_status", table_name="investigations")
    op.drop_index("ix_investigations_created_by", table_name="investigations")
    op.drop_index("ix_investigations_project_id", table_name="investigations")
    op.drop_table("investigations")
