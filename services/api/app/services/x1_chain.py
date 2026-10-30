from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from eth_account import Account
from web3 import HTTPProvider, Web3
from web3.contract import Contract

from ..config import ROOT_DIR

EXPECTED_X1_CHAIN_ID = 10778
ROLE_ENV = {
    "deployer": "X1_DEPLOYER_PRIVATE_KEY",
    "registrar": "X1_REGISTRAR_PRIVATE_KEY",
    "reviewer": "X1_REVIEWER_PRIVATE_KEY",
}


@dataclass(frozen=True)
class X1Settings:
    rpc_url: str
    chain_id: int
    explorer_url: str
    native_currency: str
    contract_address: str
    report_anchor_contract_address: str = ""

    @classmethod
    def from_env(cls) -> "X1Settings":
        return cls(
            rpc_url=os.getenv("X1_TESTNET_RPC_URL", "").strip(),
            chain_id=int(os.getenv("X1_TESTNET_CHAIN_ID", str(EXPECTED_X1_CHAIN_ID))),
            explorer_url=os.getenv("X1_TESTNET_EXPLORER_URL", "https://maculatus-scan.x1eco.com").rstrip("/"),
            native_currency=os.getenv("X1_TESTNET_NATIVE_CURRENCY", "X1T").strip() or "X1T",
            contract_address=os.getenv("X1_REGISTRY_CONTRACT_ADDRESS", "").strip(),
            report_anchor_contract_address=os.getenv("X1_REPORT_ANCHOR_CONTRACT_ADDRESS", "").strip(),
        )


class X1ConfigurationError(RuntimeError):
    pass


class X1NetworkError(RuntimeError):
    pass


class X1ChainClient:
    """Verified Maculatus JSON-RPC access and server-side role signers."""

    def __init__(self, settings: X1Settings | None = None, web3: Web3 | None = None):
        self.settings = settings or X1Settings.from_env()
        self.w3 = web3 or (Web3(HTTPProvider(self.settings.rpc_url, request_kwargs={"timeout": 15})) if self.settings.rpc_url else None)

    def check_network(self) -> dict[str, Any]:
        from datetime import datetime, timezone
        checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result: dict[str, Any] = {
            "network_name": "X1 EcoChain Testnet (Maculatus)",
            "configured_chain_id": self.settings.chain_id,
            "expected_chain_id": EXPECTED_X1_CHAIN_ID,
            "explorer_url": self.settings.explorer_url,
            "native_currency": self.settings.native_currency,
            "rpc_configured": bool(self.settings.rpc_url),
            "rpc_connected": False,
            "actual_chain_id": None,
            "latest_block": None,
            "contract_address": self.settings.contract_address or None,
            "contract_deployed": False,
            "report_anchor_contract_address": self.settings.report_anchor_contract_address or None,
            "report_anchor_contract_deployed": False,
            "checked_at": checked_at,
            "state": "rpc_unavailable",
            "error": None,
        }
        if self.settings.chain_id != EXPECTED_X1_CHAIN_ID:
            result.update(state="network_mismatch", error=f"Configured chain ID must be {EXPECTED_X1_CHAIN_ID} for Maculatus.")
            return result
        if not self.w3:
            result["error"] = "X1_TESTNET_RPC_URL is not configured."
            return result
        try:
            if not self.w3.is_connected():
                result["error"] = "The configured X1 RPC did not respond."
                return result
            actual_id = self.w3.eth.chain_id
            result["rpc_connected"] = True
            result["actual_chain_id"] = actual_id
            if actual_id != EXPECTED_X1_CHAIN_ID:
                result.update(state="network_mismatch", error=f"RPC chain ID {actual_id} does not match Maculatus {EXPECTED_X1_CHAIN_ID}.")
                return result
            result["latest_block"] = self.w3.eth.block_number
            if self.settings.contract_address:
                if not Web3.is_address(self.settings.contract_address):
                    result.update(state="contract_address_invalid", error="Configured registry contract address is invalid.")
                    return result
                result["contract_deployed"] = bool(self.w3.eth.get_code(Web3.to_checksum_address(self.settings.contract_address)))
            if self.settings.report_anchor_contract_address and Web3.is_address(self.settings.report_anchor_contract_address):
                result["report_anchor_contract_deployed"] = bool(self.w3.eth.get_code(Web3.to_checksum_address(self.settings.report_anchor_contract_address)))
            result["state"] = "x1_testnet_connected"
        except Exception as exc:
            result["error"] = f"RPC check failed: {type(exc).__name__}."
        return result

    def require_network(self) -> Web3:
        status = self.check_network()
        if status["state"] != "x1_testnet_connected" or not self.w3:
            raise X1NetworkError(status.get("error") or f"X1 network state is {status['state']}.")
        return self.w3

    def role_account(self, role: str):
        if role not in ROLE_ENV:
            raise X1ConfigurationError("Unknown signer role.")
        private_key = os.getenv(ROLE_ENV[role], "").strip()
        if not private_key:
            raise X1ConfigurationError(f"{ROLE_ENV[role]} is not configured.")
        try:
            return Account.from_key(private_key)
        except Exception as exc:
            raise X1ConfigurationError(f"{ROLE_ENV[role]} is not a valid EVM private key.") from exc

    def wallet_status(self) -> list[dict[str, Any]]:
        w3 = self.require_network()
        wallets = []
        for role, env_name in ROLE_ENV.items():
            key = os.getenv(env_name, "").strip()
            if not key:
                wallets.append({"role": role, "configured": False, "address": None, "balance": None, "currency": self.settings.native_currency})
                continue
            try:
                account = Account.from_key(key)
                balance = w3.eth.get_balance(account.address)
                wallets.append({
                    "role": role, "configured": True, "address": account.address,
                    "balance_wei": str(balance), "balance": str(Decimal(balance) / Decimal(10**18)),
                    "currency": self.settings.native_currency,
                })
            except Exception:
                wallets.append({"role": role, "configured": True, "address": None, "balance": None, "currency": self.settings.native_currency, "error": "Wallet key could not be validated."})
        return wallets

    def contract(self) -> Contract:
        w3 = self.require_network()
        address = self.settings.contract_address
        if not address or not Web3.is_address(address):
            raise X1ConfigurationError("X1_REGISTRY_CONTRACT_ADDRESS is not configured with a valid address.")
        artifact_path = ROOT_DIR / "services" / "contracts" / "artifacts" / "contracts" / "VericarbRegistry.sol" / "VericarbRegistry.json"
        if not artifact_path.is_file():
            raise X1ConfigurationError("Compile VericarbRegistry.sol before using contract methods.")
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=artifact["abi"])
        if not w3.eth.get_code(contract.address):
            raise X1ConfigurationError("No contract bytecode exists at the configured address on Maculatus.")
        return contract

    def report_anchor_contract(self) -> Contract:
        w3 = self.require_network()
        address = self.settings.report_anchor_contract_address
        if not address or not Web3.is_address(address):
            raise X1ConfigurationError("X1_REPORT_ANCHOR_CONTRACT_ADDRESS is not configured with a valid address.")
        artifact_path = ROOT_DIR / "services" / "contracts" / "artifacts" / "contracts" / "InvestigationReportAnchorRegistry.sol" / "InvestigationReportAnchorRegistry.json"
        if not artifact_path.is_file():
            raise X1ConfigurationError("Compile InvestigationReportAnchorRegistry.sol before using report anchors.")
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=artifact["abi"])
        if not w3.eth.get_code(contract.address):
            raise X1ConfigurationError("No report anchor contract bytecode exists at the configured address on Maculatus.")
        return contract

    def send_contract_transaction(self, role: str, function: Any, wait_timeout: int = 120,
                                  contract: Contract | None = None,
                                  on_broadcast: Callable[[str], None] | None = None) -> dict[str, Any]:
        w3 = self.require_network()
        contract = contract or self.contract()
        account = self.role_account(role)
        if not Web3.is_address(account.address):
            raise X1ConfigurationError("Signer address is invalid.")
        try:
            gas_estimate = function.estimate_gas({"from": account.address})
            gas_price = w3.eth.gas_price
            balance = w3.eth.get_balance(account.address)
            max_cost = int(gas_estimate * 1.25) * gas_price
            if balance < max_cost:
                raise X1ConfigurationError(f"Signer balance is insufficient for estimated gas; estimated maximum is {max_cost} wei.")
            nonce = w3.eth.get_transaction_count(account.address, "pending")
            transaction = function.build_transaction({
                "from": account.address, "nonce": nonce, "chainId": EXPECTED_X1_CHAIN_ID,
                "gas": int(gas_estimate * 1.25), "gasPrice": gas_price,
            })
            signed = account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hash_hex = Web3.to_hex(tx_hash)
            if on_broadcast:
                on_broadcast(tx_hash_hex)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=wait_timeout)
            if receipt.status != 1:
                return {"status": "failed", "transaction_hash": tx_hash_hex, "block_number": receipt.blockNumber, "gas_used": receipt.gasUsed, "sender": account.address, "contract_address": contract.address, "failure_reason": "Transaction receipt status was reverted."}
            return {"status": "confirmed", "transaction_hash": tx_hash_hex, "block_number": receipt.blockNumber, "gas_used": receipt.gasUsed, "sender": account.address, "contract_address": contract.address, "chain_id": EXPECTED_X1_CHAIN_ID}
        except X1ConfigurationError:
            raise
        except Exception as exc:
            raise X1NetworkError(f"X1 transaction did not confirm: {type(exc).__name__}.") from exc

    def wallet_presence(self) -> dict[str, bool]:
        return {role: bool(os.getenv(env_name, "").strip()) for role, env_name in ROLE_ENV.items()}


def validated_x1_settings() -> X1Settings:
    settings = X1Settings.from_env()
    if settings.chain_id != EXPECTED_X1_CHAIN_ID:
        raise X1ConfigurationError(f"X1_TESTNET_CHAIN_ID must be {EXPECTED_X1_CHAIN_ID} for Maculatus.")
    return settings
