"""Persist AI provider usage metadata.

Revision ID: 20261030_model_usage
Revises: 20261025_txhash
"""
from alembic import op
import sqlalchemy as sa

revision = "20261030_model_usage"
down_revision = "20261025_txhash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_usage",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("requested_by", sa.String(length=80), sa.ForeignKey("profiles.id"), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_usage_requested_by", "model_usage", ["requested_by"])
    op.create_index("ix_model_usage_created_at", "model_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_model_usage_created_at", table_name="model_usage")
    op.drop_index("ix_model_usage_requested_by", table_name="model_usage")
    op.drop_table("model_usage")
