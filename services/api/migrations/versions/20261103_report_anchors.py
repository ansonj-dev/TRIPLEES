"""Add reviewer-approved report commitment records.

Revision ID: 20261103_report_anchors
Revises: 20261102_findings_reports
"""
from alembic import op
import sqlalchemy as sa

revision = "20261103_report_anchors"
down_revision = "20261102_findings_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigation_report_anchors",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("report_id", sa.String(80), sa.ForeignKey("investigation_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anchor_key", sa.String(66), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("canonicalization", sa.String(48), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="approved"),
        sa.Column("approval_reason", sa.Text(), nullable=False),
        sa.Column("approved_by", sa.String(80), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("chain_id", sa.Integer()),
        sa.Column("contract_address", sa.String(80)),
        sa.Column("tx_hash", sa.String(80)),
        sa.Column("block_number", sa.Integer()),
        sa.Column("anchored_at", sa.DateTime(timezone=True)),
        sa.Column("failure_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("report_id", name="uq_report_anchor_report_id"),
        sa.UniqueConstraint("anchor_key", name="uq_report_anchor_anchor_key"),
    )
    op.create_index("ix_investigation_report_anchors_report_id", "investigation_report_anchors", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_investigation_report_anchors_report_id", table_name="investigation_report_anchors")
    op.drop_table("investigation_report_anchors")
