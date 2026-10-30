"""Normalize EVM transaction hashes to 0x-prefixed form.

Revision ID: 20261025_txhash
Revises: 20261025_x1
"""
from alembic import op

revision = "20261025_txhash"
down_revision = "20261025_x1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, column in (("credit_events", "tx_hash"), ("credit_batches", "tx_hash"), ("projects", "tx_hash"), ("evidence_files", "anchor_tx_hash")):
        op.execute(f"UPDATE {table} SET {column} = '0x' || {column} WHERE {column} IS NOT NULL AND substr({column}, 1, 2) <> '0x'")


def downgrade() -> None:
    # A tx hash without the conventional prefix remains valid hex. No data loss is required.
    pass
