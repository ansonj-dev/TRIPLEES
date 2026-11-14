"""Track task-level execution identity for agent work.

Revision ID: 20261114_task_execution_identity
Revises: 20261113_agent_coordination
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_task_execution_identity"
down_revision = "20261113_agent_coordination"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("investigations", sa.Column("requested_agent_task_id", sa.String(80), nullable=True))
    op.add_column("agent_executions", sa.Column("task_id", sa.String(80), nullable=True))
    op.create_index("ix_agent_executions_task_id", "agent_executions", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_executions_task_id", table_name="agent_executions")
    op.drop_column("agent_executions", "task_id")
    op.drop_column("investigations", "requested_agent_task_id")
