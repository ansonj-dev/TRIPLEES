from __future__ import annotations

import base64
import json
import re

import httpx

from .. import config

ACCOUNT_ID_RE = re.compile(r"^[a-z0-9]+(?:[-_.][a-z0-9]+)*$")
TRANSACTION_HASH_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{43,44}$")


class NearChainError(Exception):
    pass


class NearConfigurationError(NearChainError):
    pass


class NearNetworkError(NearChainError):
    pass


class NearRpcError(NearChainError):
    pass


class NearTransactionMismatch(NearChainError):
    pass


def valid_account_id(value: str) -> bool:
    return 2 <= len(value) <= 64 and ACCOUNT_ID_RE.fullmatch(value) is not None


def valid_transaction_hash(value: str) -> bool:
    return TRANSACTION_HASH_RE.fullmatch(value) is not None


class NearChainClient:
    def __init__(self) -> None:
        if config.NEAR_NETWORK != "testnet":
            raise NearConfigurationError("TRIPLEES NEAR integration is restricted to testnet.")
        if not config.NEAR_RPC_URL.startswith("https://"):
            raise NearConfigurationError("NEAR RPC must use HTTPS.")
        self.rpc_url = config.NEAR_RPC_URL
        self.timeout = config.NEAR_RPC_TIMEOUT_SECONDS

    def _rpc(self, method: str, params):
        try:
            response = httpx.post(
                self.rpc_url,
                json={"jsonrpc": "2.0", "id": "triplees-near", "method": method, "params": params},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise NearRpcError("NEAR testnet RPC request failed.") from exc
        if payload.get("error") or "result" not in payload:
            raise NearRpcError("NEAR testnet RPC returned an error response.")
        return payload["result"]

    def _assert_testnet(self) -> None:
        result = self._rpc("status", [])
        if result.get("chain_id") != "testnet":
            raise NearNetworkError("The configured NEAR RPC is not connected to testnet.")

    def get_report_commitment(self, contract_id: str, investigation_id: str, report_version: int):
        self._assert_testnet()
        args = base64.b64encode(json.dumps({
            "investigation_id": investigation_id,
            "report_version": report_version,
        }, separators=(",", ":")).encode("utf-8")).decode("ascii")
        result = self._rpc("query", {
            "request_type": "call_function",
            "finality": "final",
            "account_id": contract_id,
            "method_name": "verify_report",
            "args_base64": args,
        })
        try:
            value = json.loads(bytes(result["result"]).decode("utf-8"))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            raise NearRpcError("NEAR report view returned an invalid response.") from exc
        return value if isinstance(value, dict) else None

    def verify_report_transaction(
        self,
        transaction_hash: str,
        account_id: str,
        contract_id: str,
        expected: dict,
    ) -> str:
        if not valid_transaction_hash(transaction_hash):
            raise NearTransactionMismatch("Transaction hash is not a valid NEAR hash.")
        self._assert_testnet()
        result = self._rpc("EXPERIMENTAL_tx_status", [transaction_hash, account_id, "FINAL"])
        final = result.get("final_execution_outcome", result)
        transaction = final.get("transaction") or result.get("transaction") or {}
        if transaction.get("signer_id") != account_id or transaction.get("receiver_id") != contract_id:
            raise NearTransactionMismatch("NEAR transaction signer or contract does not match the prepared commitment.")
        actions = transaction.get("actions") or []
        function_call = actions[0].get("FunctionCall") if len(actions) == 1 and isinstance(actions[0], dict) else None
        if not function_call or function_call.get("method_name") != "commit_report":
            raise NearTransactionMismatch("NEAR transaction is not the prepared report-commitment call.")
        try:
            arguments = json.loads(base64.b64decode(function_call["args"], validate=True).decode("utf-8"))
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            raise NearTransactionMismatch("NEAR transaction arguments are invalid.") from exc
        required_args = {
            "investigation_id": expected["investigation_id"],
            "report_version": expected["report_version"],
            "report_digest": expected["report_digest"],
            "metadata_digest": None,
        }
        if arguments != required_args:
            raise NearTransactionMismatch("NEAR transaction arguments do not match the approved report digest.")

        status = final.get("status") or result.get("status") or {}
        if "Failure" in status:
            return "failed"
        if "SuccessValue" not in status:
            return "pending"
        record = self.get_report_commitment(contract_id, expected["investigation_id"], expected["report_version"])
        if not record or any((
            record.get("investigationId") != expected["investigation_id"],
            record.get("reportVersion") != expected["report_version"],
            record.get("reportDigest", "").lower() != expected["report_digest"].lower(),
            record.get("submitter") != account_id,
            record.get("metadataDigest") is not None,
        )):
            raise NearTransactionMismatch("Confirmed NEAR contract state does not match the prepared report commitment.")
        return "confirmed"