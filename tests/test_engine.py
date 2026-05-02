import pytest
from engine import Engine


@pytest.fixture
def engine():
    return Engine()


@pytest.fixture
def kyc_verified_engine():
    e = Engine()
    e.register("alice")
    e.register("bob")
    e.verify_kyc("alice")
    e.verify_kyc("bob")
    e.set_reserve_report(1000)
    return e


class TestAccountLifecycle:
    def test_register_creates_pending_account(self, engine):
        engine.register("alice")
        a = engine.accounts["alice"]
        assert a.id == "alice"
        assert a.kyc_status == "PENDING"
        assert a.balance == 0
        assert not a.frozen
        assert not a.sanctioned

    def test_register_is_idempotent(self, engine):
        engine.register("alice")
        engine.register("alice")
        assert len(engine.accounts) == 1

    def test_get_unknown_account_raises(self, engine):
        with pytest.raises(ValueError, match="not found"):
            engine._get("ghost")


class TestKYC:
    def test_submit_then_verify(self, engine):
        engine.register("alice")
        engine.submit_kyc("alice", "hash123")
        assert engine.accounts["alice"].kyc_status == "SUBMITTED"
        assert engine.accounts["alice"].meta["kycHash"] == "hash123"
        engine.verify_kyc("alice")
        assert engine.accounts["alice"].kyc_status == "VERIFIED"


class TestReservesAndMint:
    def test_reserves_cannot_be_negative(self, engine):
        with pytest.raises(ValueError, match="negative"):
            engine.set_reserve_report(-1)

    def test_mint_blocked_without_reserves(self, kyc_verified_engine):
        kyc_verified_engine.set_reserve_report(0)
        with pytest.raises(ValueError, match="reserves"):
            kyc_verified_engine.mint("alice", 100)

    def test_mint_blocked_when_supply_exceeds_reserves(self, kyc_verified_engine):
        kyc_verified_engine.set_reserve_report(500)
        kyc_verified_engine.mint("alice", 500)
        with pytest.raises(ValueError, match="reserves"):
            kyc_verified_engine.mint("bob", 1)

    def test_mint_requires_kyc_verified(self, engine):
        engine.register("alice")
        engine.set_reserve_report(1000)
        with pytest.raises(ValueError, match="KYC"):
            engine.mint("alice", 100)

    def test_mint_requires_positive_amount(self, kyc_verified_engine):
        with pytest.raises(ValueError, match="positive"):
            kyc_verified_engine.mint("alice", 0)

    def test_mint_blocked_for_frozen_account(self, kyc_verified_engine):
        kyc_verified_engine.freeze_account("alice")
        with pytest.raises(ValueError, match="frozen"):
            kyc_verified_engine.mint("alice", 100)

    def test_successful_mint_updates_supply_and_balance(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 250)
        assert kyc_verified_engine.accounts["alice"].balance == 250
        assert kyc_verified_engine.supply == 250


class TestTransfer:
    def test_transfer_happy_path(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 500)
        kyc_verified_engine.transfer("alice", "bob", 100)
        assert kyc_verified_engine.accounts["alice"].balance == 400
        assert kyc_verified_engine.accounts["bob"].balance == 100

    def test_transfer_blocked_insufficient_balance(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 50)
        with pytest.raises(ValueError, match="Insufficient"):
            kyc_verified_engine.transfer("alice", "bob", 100)

    def test_transfer_blocked_when_sender_frozen(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        kyc_verified_engine.freeze_account("alice")
        with pytest.raises(ValueError, match="frozen"):
            kyc_verified_engine.transfer("alice", "bob", 100)

    def test_transfer_blocked_when_recipient_frozen(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        kyc_verified_engine.freeze_account("bob")
        with pytest.raises(ValueError, match="frozen"):
            kyc_verified_engine.transfer("alice", "bob", 100)

    def test_transfer_blocked_when_sender_sanctioned(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        kyc_verified_engine.sanction_account("alice")
        with pytest.raises(ValueError, match="sanctioned"):
            kyc_verified_engine.transfer("alice", "bob", 100)

    def test_transfer_blocked_when_recipient_sanctioned(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        kyc_verified_engine.sanction_account("bob")
        with pytest.raises(ValueError, match="sanctioned"):
            kyc_verified_engine.transfer("alice", "bob", 100)

    def test_transfer_emits_travel_rule_hash(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        ev = kyc_verified_engine.transfer(
            "alice", "bob", 100,
            travel_rule_payload={"sender": "alice", "recipient": "bob", "amount": 100},
        )
        assert ev["travelRuleHash"]
        assert len(ev["travelRuleHash"]) == 64  # SHA-256 hex

    def test_transfer_with_pqc_attaches_signature(self, kyc_verified_engine):
        kyc_verified_engine.mint("alice", 200)
        ev = kyc_verified_engine.transfer("alice", "bob", 100, attach_pqc=True)
        assert "pqcSig" in ev


class TestEvents:
    def test_register_emits_event(self, engine):
        engine.register("alice")
        assert engine.events[-1]["type"] == "AccountRegistered"

    def test_freeze_emits_event(self, engine):
        engine.register("alice")
        engine.freeze_account("alice")
        assert engine.events[-1]["type"] == "AccountFrozen"

    def test_full_lifecycle_event_count(self, kyc_verified_engine):
        # 2 registers + 2 verifies + 1 reserve = 5 events from fixture
        assert len(kyc_verified_engine.events) == 5
