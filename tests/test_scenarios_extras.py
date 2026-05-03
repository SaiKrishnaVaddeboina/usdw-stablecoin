"""Tests for the additional scenarios and the SCENARIOS registry."""
import pytest
from scenarios import SCENARIOS, reserve_breach_attempt, sanctions_flow, stress_test


def test_registry_exposes_all_scenarios():
    assert {"happy_path", "freeze_flow", "sanctions_flow",
            "reserve_breach_attempt", "stress_test"} <= set(SCENARIOS)


@pytest.mark.parametrize("key", list(SCENARIOS))
def test_every_scenario_runs_and_returns_engine(key):
    label, desc, fn = SCENARIOS[key]
    e = fn()
    assert e.get_summary()["total_accounts"] > 0


def test_sanctions_flow_blocks_then_succeeds():
    e = sanctions_flow()
    blocked = [ev for ev in e.events if ev["type"] == "TransferBlocked"]
    transfers = [ev for ev in e.events if ev["type"] == "Transfer"]
    assert len(blocked) == 1
    assert len(transfers) == 1
    assert e.accounts["mallory"].balance == 100


def test_reserve_breach_attempt_records_block_event():
    e = reserve_breach_attempt()
    blocked = [ev for ev in e.events if ev["type"] == "MintBlocked"]
    assert len(blocked) == 1
    assert "reserves" in blocked[0]["reason"].lower()
    assert e.supply == 1000  # 500 + 500 after top-up


def test_stress_test_produces_many_events():
    e = stress_test(n_accounts=5, transfers_per_account=2)
    s = e.get_summary()
    assert s["total_accounts"] == 5
    assert s["transfer_count"] == 10  # 5 accounts × 2 transfers
