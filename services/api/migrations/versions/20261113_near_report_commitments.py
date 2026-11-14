"""Add separate NEAR report commitment records.

Revision ID: 20261113_near_report_commitments
Revises: 20261103_report_anchors
"""
from alembic import op
import sqlalchemy as sa

revision = "20261113_near_report_commitments"
down_revision = "20261103_report_anchors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "near_commitments",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", sa.String(80), sa.ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_version", sa.Integer(), nullable=False),
        sa.Column("report_digest", sa.String(64), nullable=False),
        sa.Column("near_account_id", sa.String(64), nullable=False),
        sa.Column("contract_id", sa.String(64), nullable=False),
        sa.Column("approved_by", sa.String(80), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("approval_reason", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transaction_hash", sa.String(64)),
        sa.Column("network", sa.String(16), nullable=False, server_default="testnet"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_summary", sa.Text()),
        sa.UniqueConstraint("investigation_id", "report_version", name="uq_near_commitment_investigation_version"),
        sa.UniqueConstraint("transaction_hash", name="uq_near_commitment_transaction_hash"),
        sa.CheckConstraint("report_version > 0", name="ck_near_commitment_version_positive"),
        sa.CheckConstraint("status IN ('pending', 'confirmed', 'failed')", name="ck_near_commitment_status"),
    )
    op.create_index("ix_near_commitments_investigation_id", "near_commitments", ["investigation_id"])
    op.create_index("ix_near_commitments_report_id", "near_commitments", ["report_id"])
    op.create_index("ix_near_commitments_status", "near_commitments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_near_commitments_status", table_name="near_commitments")
    op.drop_index("ix_near_commitments_report_id", table_name="near_commitments")
    op.drop_index("ix_near_commitments_investigation_id", table_name="near_commitments")
    op.drop_table("near_commitments")