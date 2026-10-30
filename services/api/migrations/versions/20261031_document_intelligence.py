"""Persist document extraction, chunks, candidate claims, and provenance links.

Revision ID: 20261031_document_intelligence
Revises: 20261030_model_usage
"""
from alembic import op
import sqlalchemy as sa

revision = "20261031_document_intelligence"
down_revision = "20261030_model_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_extractions",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("evidence_file_id", sa.String(length=80), sa.ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="processing"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("character_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning", sa.Text(), nullable=True),
        sa.Column("reused_from_id", sa.String(length=80), sa.ForeignKey("document_extractions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("evidence_file_id", name="uq_extraction_evidence_file"),
    )
    op.create_index("ix_document_extractions_evidence_file_id", "document_extractions", ["evidence_file_id"])
    op.create_index("ix_document_extractions_content_sha256", "document_extractions", ["content_sha256"])
    op.create_index("ix_document_extractions_status", "document_extractions", ["status"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("extraction_id", sa.String(length=80), sa.ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_file_id", sa.String(length=80), sa.ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_location", sa.String(length=160), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("extraction_id", "chunk_index", name="uq_extraction_chunk_index"),
    )
    op.create_index("ix_document_chunks_extraction_id", "document_chunks", ["extraction_id"])
    op.create_index("ix_document_chunks_evidence_file_id", "document_chunks", ["evidence_file_id"])

    op.create_table(
        "extracted_claims",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("extraction_id", sa.String(length=80), sa.ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_file_id", sa.String(length=80), sa.ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_location", sa.String(length=160), nullable=False),
        sa.Column("claim_sha256", sa.String(length=64), nullable=False),
        sa.Column("extraction_method", sa.String(length=48), nullable=False, server_default="heuristic_candidate"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="candidate"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("extraction_id", "claim_sha256", name="uq_extraction_claim_hash"),
    )
    op.create_index("ix_extracted_claims_extraction_id", "extracted_claims", ["extraction_id"])
    op.create_index("ix_extracted_claims_evidence_file_id", "extracted_claims", ["evidence_file_id"])

    op.create_table(
        "claim_evidence_links",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("claim_id", sa.String(length=80), sa.ForeignKey("extracted_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_file_id", sa.String(length=80), sa.ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship", sa.String(length=24), nullable=False, server_default="extracted_from"),
        sa.Column("source_location", sa.String(length=160), nullable=False),
        sa.Column("evidence_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("claim_id", "evidence_file_id", name="uq_claim_evidence_link"),
    )
    op.create_index("ix_claim_evidence_links_claim_id", "claim_evidence_links", ["claim_id"])
    op.create_index("ix_claim_evidence_links_evidence_file_id", "claim_evidence_links", ["evidence_file_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_evidence_links_evidence_file_id", table_name="claim_evidence_links")
    op.drop_index("ix_claim_evidence_links_claim_id", table_name="claim_evidence_links")
    op.drop_table("claim_evidence_links")
    op.drop_index("ix_extracted_claims_evidence_file_id", table_name="extracted_claims")
    op.drop_index("ix_extracted_claims_extraction_id", table_name="extracted_claims")
    op.drop_table("extracted_claims")
    op.drop_index("ix_document_chunks_evidence_file_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_extraction_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_document_extractions_status", table_name="document_extractions")
    op.drop_index("ix_document_extractions_content_sha256", table_name="document_extractions")
    op.drop_index("ix_document_extractions_evidence_file_id", table_name="document_extractions")
    op.drop_table("document_extractions")
