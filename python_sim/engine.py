from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field


@dataclass
class Account:
    id: str
    kyc_status: str = "PENDING"
    frozen: bool = False
    sanctioned: bool = False
    balance: int = 0
    meta: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

class Engine:
    def __init__(self):
        self.accounts: dict[str, Account] = {}
        self.events: list[dict] = []
        self.reserves: int = 0
        self.supply: int = 0

    def _emit(self, etype: str, payload: dict):
        payload = dict(payload)
        payload["type"] = etype
        payload["ts"] = time.time()
        self.events.append(payload)

    def _get(self, id: str) -> Account:
        if id not in self.accounts:
            raise ValueError(f"Account {id} not found")
        return self.accounts[id]

    # lifecycle
    def register(self, id: str):
        if id in self.accounts:
            return
        self.accounts[id] = Account(id=id)
        self._emit("AccountRegistered", {"accountId": id})

    def submit_kyc(self, id: str, kyc_hash: str):
        a = self._get(id)
        a.meta["kycHash"] = kyc_hash
        a.kyc_status = "SUBMITTED"
        self._emit("KYCUploaded", {"accountId": id})

    def verify_kyc(self, id: str):
        a = self._get(id)
        a.kyc_status = "VERIFIED"
        self._emit("KYCVerified", {"accountId": id})

    def freeze_account(self, id: str):
        a = self._get(id)
        a.frozen = True
        self._emit("AccountFrozen", {"accountId": id})

    def unfreeze_account(self, id: str):
        a = self._get(id)
        a.frozen = False
        self._emit("AccountUnfrozen", {"accountId": id})

    def sanction_account(self, id: str):
        a = self._get(id)
        a.sanctioned = True
        self._emit("AccountSanctioned", {"accountId": id})

    def unsanction_account(self, id: str):
        a = self._get(id)
        a.sanctioned = False
        self._emit("AccountUnsanctioned", {"accountId": id})

    def set_reserve_report(self, amount: int):
        if amount < 0: raise ValueError("negative reserves")
        self.reserves = amount
        self._emit("ReserveUpdated", {"reserves": amount})

    def mint(self, to: str, amount: int):
        if amount <= 0: raise ValueError("mint must be positive")
        if self.supply + amount > self.reserves:
            raise ValueError("mint blocked: reserves would be below supply")
        a = self._get(to)
        if a.kyc_status != "VERIFIED":
            raise ValueError("recipient must be KYC-VERIFIED")
        if a.frozen or a.sanctioned:
            raise ValueError("recipient frozen or sanctioned")
        a.balance += amount
        self.supply += amount
        self._emit("Mint", {"to": to, "amount": amount, "supply": self.supply})

    def transfer(self, from_id: str, to_id: str, amount: int,
                 travel_rule_payload: dict | None = None,
                 attach_pqc: bool = False):
        s = self._get(from_id); r = self._get(to_id)
        if s.kyc_status != "VERIFIED" or r.kyc_status != "VERIFIED":
            raise ValueError("KYC not verified")
        if s.frozen or r.frozen:
            raise ValueError("One of the accounts is frozen")
        if s.sanctioned or r.sanctioned:
            raise ValueError("Transfer blocked: sanctioned party")
        if s.balance < amount:
            raise ValueError("Insufficient balance")

        s.balance -= amount
        r.balance += amount

        tr_hash = ""
        if travel_rule_payload:
            blob = json.dumps(travel_rule_payload, sort_keys=True).encode("utf-8")
            tr_hash = hashlib.sha256(blob).hexdigest()

        event = {"from": from_id, "to": to_id, "amount": amount, "travelRuleHash": tr_hash}

        if attach_pqc:
            from pqc_mock import sign
            event["pqcSig"] = sign({"from": from_id, "to": to_id, "amount": amount, "travelRuleHash": tr_hash})

        self._emit("Transfer", event)
        return event

    def verify_transfer_signature(self, transfer_event: dict) -> bool:
        """Verify the PQC signature on a transfer event. Returns True if valid."""
        sig = transfer_event.get("pqcSig")
        if not sig:
            return False
        from pqc_mock import verify
        payload = {
            "from": transfer_event["from"],
            "to": transfer_event["to"],
            "amount": transfer_event["amount"],
            "travelRuleHash": transfer_event.get("travelRuleHash", ""),
        }
        return verify(payload, sig)

    # helpers for UI
    def list_accounts(self):
        out = {}
        for aid, a in self.accounts.items():
            out[aid] = {
                "id": a.id, "kyc_status": a.kyc_status, "frozen": a.frozen,
                "sanctioned": a.sanctioned, "balance": a.balance
            }
        return out

    def get_balances(self):
        return { aid: a.balance for aid, a in self.accounts.items() }

    def get_summary(self) -> dict:
        """Aggregate metrics for the dashboard."""
        accts = list(self.accounts.values())
        verified = sum(1 for a in accts if a.kyc_status == "VERIFIED")
        frozen = sum(1 for a in accts if a.frozen)
        sanctioned = sum(1 for a in accts if a.sanctioned)
        ratio = (self.reserves / self.supply) if self.supply > 0 else float("inf")
        transfers = [e for e in self.events if e["type"] == "Transfer"]
        volume = sum(e["amount"] for e in transfers)
        return {
            "total_accounts": len(accts),
            "verified_accounts": verified,
            "frozen_accounts": frozen,
            "sanctioned_accounts": sanctioned,
            "supply": self.supply,
            "reserves": self.reserves,
            "reserve_ratio": ratio,
            "transfer_count": len(transfers),
            "transfer_volume": volume,
            "event_count": len(self.events),
        }

    def export_state(self) -> dict:
        """Snapshot the full engine state — for download / replay."""
        return {
            "accounts": {aid: a.__dict__ for aid, a in self.accounts.items()},
            "events": list(self.events),
            "reserves": self.reserves,
            "supply": self.supply,
        }
