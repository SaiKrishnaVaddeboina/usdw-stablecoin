"""Tests for the engine helpers added in the v2 enhancements."""
import pytest
from engine import Engine


@pytest.fixture
def populated():
    e = Engine()
    e.set_reserve_report(1000)
    for aid in ("alice", "bob", "carol"):
        e.register(aid)
        e.verify_kyc(aid)
        e.mint(aid, 200)
    e.freeze_account("bob")
    e.sanction_account("carol")
    return e


class TestSummary:
    def test_empty_engine_summary(self):
        s = Engine().get_summary()
        assert s["total_accounts"] == 0
        assert s["supply"] == 0
        assert s["reserve_ratio"] == float("inf")
        assert s["transfer_count"] == 0

    def test_summary_counts_states(self, populated):
        s = populated.get_summary()
        assert s["total_accounts"] == 3
        assert s["verified_accounts"] == 3
        assert s["frozen_accounts"] == 1
        assert s["sanctioned_accounts"] == 1
        assert s["supply"] == 600
        assert s["reserves"] == 1000

    def test_reserve_ratio_calculation(self, populated):
        s = populated.get_summary()
        assert s["reserve_ratio"] == pytest.approx(1000 / 600)

    def test_transfer_volume_aggregation(self):
        e = Engine()
        e.set_reserve_report(1000)
        for aid in ("a", "b"):
            e.register(aid); e.verify_kyc(aid)
        e.mint("a", 500)
        e.transfer("a", "b", 100)
        e.transfer("a", "b", 50)
        s = e.get_summary()
        assert s["transfer_count"] == 2
        assert s["transfer_volume"] == 150


class TestSignatureVerification:
    def test_verify_valid_signature(self):
        e = Engine()
        e.set_reserve_report(1000)
        for aid in ("a", "b"):
            e.register(aid); e.verify_kyc(aid)
        e.mint("a", 500)
        ev = e.transfer("a", "b", 100, attach_pqc=True)
        assert e.verify_transfer_signature(ev) is True

    def test_verify_returns_false_when_no_sig(self):
        e = Engine()
        e.set_reserve_report(1000)
        for aid in ("a", "b"):
            e.register(aid); e.verify_kyc(aid)
        e.mint("a", 500)
        ev = e.transfer("a", "b", 100)  # no PQC
        assert e.verify_transfer_signature(ev) is False

    def test_verify_detects_tampering(self):
        e = Engine()
        e.set_reserve_report(1000)
        for aid in ("a", "b"):
            e.register(aid); e.verify_kyc(aid)
        e.mint("a", 500)
        ev = e.transfer("a", "b", 100, attach_pqc=True)
        ev["amount"] = 999  # tamper
        assert e.verify_transfer_signature(ev) is False


class TestExportState:
    def test_export_includes_everything(self, populated):
        snap = populated.export_state()
        assert set(snap) == {"accounts", "events", "reserves", "supply"}
        assert len(snap["accounts"]) == 3
        assert snap["supply"] == 600

    def test_export_is_json_serializable(self, populated):
        import json
        snap = populated.export_state()
        # Should not raise.
        json.dumps(snap, default=str)


class TestEventTimestamps:
    def test_every_event_has_ts(self, populated):
        for ev in populated.events:
            assert "ts" in ev
            assert isinstance(ev["ts"], float)

    def test_timestamps_are_monotonic(self):
        e = Engine()
        e.set_reserve_report(1000)
        e.register("a"); e.verify_kyc("a"); e.mint("a", 100)
        timestamps = [ev["ts"] for ev in e.events]
        assert timestamps == sorted(timestamps)
