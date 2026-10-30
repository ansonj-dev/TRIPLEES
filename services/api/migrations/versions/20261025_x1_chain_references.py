"""Add durable project and evidence anchor references for X1.

Revision ID: 20261025_x1
Revises: 87f71832eccc
"""
from alembic import op
import sqlalchemy as sa

revision = "20261025_x1"
down_revision = "87f71832eccc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("chain_project_id", sa.String(length=80), nullable=True))
    op.add_column("projects", sa.Column("chain_id", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("contract_address", sa.String(length=80), nullable=True))
    op.add_column("projects", sa.Column("tx_hash", sa.String(length=80), nullable=True))
    op.add_column("evidence_files", sa.Column("anchor_chain_id", sa.Integer(), nullable=True))
    op.add_column("evidence_files", sa.Column("anchor_contract_address", sa.String(length=80), nullable=True))
    op.add_column("evidence_files", sa.Column("anchor_tx_hash", sa.String(length=80), nullable=True))
    op.add_column("evidence_files", sa.Column("anchor_block_number", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("evidence_files", "anchor_block_number")
    op.drop_column("evidence_files", "anchor_tx_hash")
    op.drop_column("evidence_files", "anchor_contract_address")
    op.drop_column("evidence_files", "anchor_chain_id")
    op.drop_column("projects", "tx_hash")
    op.drop_column("projects", "contract_address")
    op.drop_column("projects", "chain_id")
    op.drop_column("projects", "chain_project_id")
