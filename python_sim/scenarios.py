"""Pre-built demo flows that exercise the engine end-to-end."""
from engine import Engine


def happy_path() -> Engine:
    """Register → KYC → mint → transfer with travel-rule + PQC sig."""
    e = Engine()
    e.register("alice"); e.register("bob")
    e.submit_kyc("alice", "hashA"); e.verify_kyc("alice")
    e.submit_kyc("bob", "hashB"); e.verify_kyc("bob")
    e.set_reserve_report(1000)
    e.mint("alice", 500)
    e.transfer("alice", "bob", 120,
               travel_rule_payload={"sender": "alice", "recipient": "bob", "amount": 120},
               attach_pqc=True)
    return e


def freeze_flow() -> Engine:
    """Transfer blocked while account frozen, succeeds after unfreeze."""
    e = Engine()
    e.register("carol"); e.register("dave")
    e.verify_kyc("carol"); e.verify_kyc("dave")
    e.set_reserve_report(1000)
    e.mint("carol", 400)
    e.freeze_account("dave")
    try:
        e.transfer("carol", "dave", 50)
    except Exception as ex:
        e._emit("TransferBlocked", {"reason": str(ex)})
    e.unfreeze_account("dave")
    e.transfer("carol", "dave", 50)
    return e


def sanctions_flow() -> Engine:
    """Sanctioned recipient blocks transfer; clearing sanctions allows it."""
    e = Engine()
    e.register("eve"); e.register("mallory")
    e.verify_kyc("eve"); e.verify_kyc("mallory")
    e.set_reserve_report(2000)
    e.mint("eve", 800)
    e.sanction_account("mallory")
    try:
        e.transfer("eve", "mallory", 100)
    except Exception as ex:
        e._emit("TransferBlocked", {"reason": str(ex)})
    e.unsanction_account("mallory")
    e.transfer("eve", "mallory", 100,
               travel_rule_payload={"sender": "eve", "recipient": "mallory", "amount": 100},
               attach_pqc=True)
    return e


def reserve_breach_attempt() -> Engine:
    """Issuer tries to over-mint past reserves — should be blocked."""
    e = Engine()
    e.register("treasury")
    e.verify_kyc("treasury")
    e.set_reserve_report(500)
    e.mint("treasury", 500)  # at the limit, should succeed
    try:
        e.mint("treasury", 1)  # one over — should fail
    except Exception as ex:
        e._emit("MintBlocked", {"reason": str(ex)})
    e.set_reserve_report(1000)  # top up reserves
    e.mint("treasury", 500)  # now allowed
    return e


def stress_test(n_accounts: int = 10, transfers_per_account: int = 3) -> Engine:
    """Many accounts and transfers — useful for charts and audit-log demos."""
    e = Engine()
    e.set_reserve_report(1_000_000)
    for i in range(n_accounts):
        aid = f"acct_{i:03d}"
        e.register(aid)
        e.verify_kyc(aid)
        e.mint(aid, 1000)
    ids = list(e.accounts.keys())
    for i, sender in enumerate(ids):
        for j in range(transfers_per_account):
            recipient = ids[(i + j + 1) % len(ids)]
            amount = 10 + (i * j)
            e.transfer(sender, recipient, amount,
                       travel_rule_payload={"sender": sender, "recipient": recipient, "amount": amount})
    return e


SCENARIOS = {
    "happy_path": ("Happy Path", "Register → KYC → mint → transfer with travel-rule hash + PQC signature.", happy_path),
    "freeze_flow": ("Freeze Flow", "Transfer blocked while frozen, succeeds after unfreeze.", freeze_flow),
    "sanctions_flow": ("Sanctions Flow", "Sanctioned recipient blocks transfer; clearing sanctions allows it.", sanctions_flow),
    "reserve_breach_attempt": ("Reserve Breach", "Over-mint blocked at the reserves boundary, succeeds after top-up.", reserve_breach_attempt),
    "stress_test": ("Stress Test (10 accounts × 3 transfers)", "Populate many accounts and transfers for charts.", stress_test),
}
