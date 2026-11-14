"""Persist internal agent task coordination and budget controls.

Revision ID: 20261113_agent_coordination
Revises: 20261113_near_report_commitments
"""
from alembic import op
import sqlalchemy as sa

revision = "20261113_agent_coordination"
down_revision = "20261113_near_report_commitments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("investigations", sa.Column("requested_agent_keys_json", sa.Text()))
    op.create_table(
        "investigation_budgets",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("budget_limit", sa.Float(), nullable=False),
        sa.Column("allocated_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("spent_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(40), nullable=False, server_default="internal_units"),
        sa.Column("approval_threshold", sa.Float(), nullable=False, server_default="1"),
        sa.Column("frozen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("emergency_stop", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("investigation_id", name="uq_investigation_budget_investigation"),
        sa.CheckConstraint("budget_limit >= 0 AND allocated_amount >= 0 AND spent_amount >= 0", name="ck_investigation_budget_nonnegative"),
    )
    op.create_index("ix_investigation_budgets_investigation_id", "investigation_budgets", ["investigation_id"])

    op.create_table(
        "agent_budgets",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("budget_limit", sa.Float(), nullable=False),
        sa.Column("allocated_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("spent_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(40), nullable=False, server_default="internal_units"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("investigation_id", "agent_id", name="uq_agent_budget_investigation_agent"),
        sa.CheckConstraint("budget_limit >= 0 AND allocated_amount >= 0 AND spent_amount >= 0", name="ck_agent_budget_nonnegative"),
    )
    op.create_index("ix_agent_budgets_investigation_id", "agent_budgets", ["investigation_id"])

    op.create_table(
        "agent_permissions",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("permission", sa.String(64), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("change_history_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("updated_by", sa.String(80), sa.ForeignKey("profiles.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_id", "permission", name="uq_agent_permission_agent_permission"),
    )
    op.create_index("ix_agent_permissions_agent_id", "agent_permissions", ["agent_id"])

    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_input_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("expected_output_schema", sa.String(120), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("budget_allocated", sa.Float(), nullable=False, server_default="0"),
        sa.Column("budget_spent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("budget_charged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by", sa.String(80), sa.ForeignKey("profiles.id")),
        sa.Column("approval_reason", sa.Text()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("result_reference", sa.String(80), sa.ForeignKey("agent_executions.id", ondelete="SET NULL")),
        sa.Column("error_info", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("investigation_id", "task_type", name="uq_agent_task_investigation_type"),
        sa.CheckConstraint("priority BETWEEN 1 AND 5", name="ck_agent_task_priority"),
        sa.CheckConstraint("budget_allocated >= 0 AND budget_spent >= 0", name="ck_agent_task_budget_nonnegative"),
        sa.CheckConstraint("status IN ('created', 'available', 'assigned', 'running', 'completed', 'failed', 'cancelled', 'awaiting_review')", name="ck_agent_task_status"),
    )
    op.create_index("ix_agent_tasks_investigation_id", "agent_tasks", ["investigation_id"])
    op.create_index("ix_agent_tasks_status", "agent_tasks", ["status"])

    op.create_table(
        "agent_bids",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("task_id", sa.String(80), sa.ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("estimated_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("capability_score", sa.Float(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("selection_status", sa.String(16), nullable=False, server_default="rejected"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("task_id", "agent_id", name="uq_agent_bid_task_agent"),
        sa.CheckConstraint("estimated_cost >= 0 AND estimated_duration_seconds >= 0", name="ck_agent_bid_estimates_nonnegative"),
        sa.CheckConstraint("capability_score BETWEEN 0 AND 1 AND reliability_score BETWEEN 0 AND 1", name="ck_agent_bid_scores_range"),
    )
    op.create_index("ix_agent_bids_task_id", "agent_bids", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_bids_task_id", table_name="agent_bids")
    op.drop_table("agent_bids")
    op.drop_index("ix_agent_tasks_status", table_name="agent_tasks")
    op.drop_index("ix_agent_tasks_investigation_id", table_name="agent_tasks")
    op.drop_table("agent_tasks")
    op.drop_index("ix_agent_permissions_agent_id", table_name="agent_permissions")
    op.drop_table("agent_permissions")
    op.drop_index("ix_agent_budgets_investigation_id", table_name="agent_budgets")
    op.drop_table("agent_budgets")
    op.drop_index("ix_investigation_budgets_investigation_id", table_name="investigation_budgets")
    op.drop_table("investigation_budgets")
    op.drop_column("investigations", "requested_agent_keys_json")