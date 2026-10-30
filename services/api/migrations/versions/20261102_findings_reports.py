"""Persist source-linked findings, review decisions, and report snapshots.

Revision ID: 20261102_findings_reports
Revises: 20261101_investigation_lifecycle
"""
from alembic import op
import sqlalchemy as sa

revision = "20261102_findings_reports"
down_revision = "20261101_investigation_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_findings",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(80), sa.ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_index", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False), sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(300), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("claim", sa.Text()), sa.Column("observed_value", sa.Text()),
        sa.Column("evidence_ids_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("source_ids_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("basis", sa.String(24), nullable=False), sa.Column("recommendation", sa.Text()),
        sa.Column("review_decision", sa.String(32)), sa.Column("review_reason", sa.Text()),
        sa.Column("reviewer_id", sa.String(80), sa.ForeignKey("profiles.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("execution_id", "finding_index", name="uq_execution_finding_index"),
    )
    for col in ("investigation_id", "execution_id", "category", "severity", "status", "review_decision"):
        op.create_index(f"ix_agent_findings_{col}", "agent_findings", [col])

    op.create_table(
        "source_references",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(80), sa.ForeignKey("agent_executions.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(300), nullable=False), sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("publisher", sa.String(200)), sa.Column("domain", sa.String(255)),
        sa.Column("retrieved_at", sa.String(40)), sa.Column("published_at", sa.String(40)), sa.Column("excerpt", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("investigation_id", "url", name="uq_investigation_source_url"),
    )
    op.create_index("ix_source_references_investigation_id", "source_references", ["investigation_id"])
    op.create_index("ix_source_references_execution_id", "source_references", ["execution_id"])

    op.create_table(
        "finding_reviews",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("finding_id", sa.String(80), sa.ForeignKey("agent_findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.String(80), sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False), sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_finding_reviews_finding_id", "finding_reviews", ["finding_id"])
    op.create_index("ix_finding_reviews_reviewer_id", "finding_reviews", ["reviewer_id"])

    op.create_table(
        "investigation_reports",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("investigation_id", sa.String(80), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False), sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_by", sa.String(80), sa.ForeignKey("profiles.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("investigation_id", "version", name="uq_investigation_report_version"),
    )
    op.create_index("ix_investigation_reports_investigation_id", "investigation_reports", ["investigation_id"])
    op.create_index("ix_investigation_reports_created_at", "investigation_reports", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_investigation_reports_created_at", table_name="investigation_reports")
    op.drop_index("ix_investigation_reports_investigation_id", table_name="investigation_reports")
    op.drop_table("investigation_reports")
    op.drop_index("ix_finding_reviews_reviewer_id", table_name="finding_reviews")
    op.drop_index("ix_finding_reviews_finding_id", table_name="finding_reviews")
    op.drop_table("finding_reviews")
    op.drop_index("ix_source_references_execution_id", table_name="source_references")
    op.drop_index("ix_source_references_investigation_id", table_name="source_references")
    op.drop_table("source_references")
    for col in ("review_decision", "status", "severity", "category", "execution_id", "investigation_id"):
        op.drop_index(f"ix_agent_findings_{col}", table_name="agent_findings")
    op.drop_table("agent_findings")
