"""Chain boundary for the prototype.

The local Solidity registry is exercised on a local Hardhat chain. The API does
not broadcast transactions until an explicitly configured adapter can verify a
receipt, so callers receive a typed not-configured state rather than a fake tx.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChainResult:
    status: str
    chain_id: int | None = None
    transaction_hash: str | None = None
    block_number: int | None = None
    message: str = ""


class EVMRegistryAdapter(Protocol):
    """Transaction interface implemented by a configured EVM provider adapter."""

    def register_batch(self, batch_id: str, quantity_kg: int, evidence_hash: str) -> ChainResult: ...
    def transfer(self, batch_id: str, recipient: str, quantity_kg: int) -> ChainResult: ...
    def retire(self, batch_id: str, quantity_kg: int, retirement_ref: str) -> ChainResult: ...


class UnconfiguredEVMAdapter:
    def _not_configured(self) -> ChainResult:
        return ChainResult(
            status="not_configured",
            message="No verified EVM RPC, chain ID, contract address, or transaction signer is configured.",
        )

    def register_batch(self, batch_id: str, quantity_kg: int, evidence_hash: str) -> ChainResult:
        return self._not_configured()

    def transfer(self, batch_id: str, recipient: str, quantity_kg: int) -> ChainResult:
        return self._not_configured()

    def retire(self, batch_id: str, quantity_kg: int, retirement_ref: str) -> ChainResult:
        return self._not_configured()


def chain_adapter() -> EVMRegistryAdapter:
    """Return the safe local adapter until verified network integration exists."""
    return UnconfiguredEVMAdapter()
