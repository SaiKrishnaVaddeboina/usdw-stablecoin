"""Smoke tests for the CLI tool."""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest


@pytest.fixture
def cli_state(tmp_path, monkeypatch):
    """Use an isolated state file for each test."""
    state_path = tmp_path / "state.pkl"
    monkeypatch.setenv("USDW_STATE", str(state_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cli"))
    if "usdw" in sys.modules:
        del sys.modules["usdw"]
    import importlib

    import usdw  # noqa: F401
    importlib.reload(sys.modules["usdw"])
    return state_path


def run_cli(*args) -> str:
    import usdw
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = usdw.main(list(args))
    assert rc == 0, f"CLI exited with {rc}"
    return buf.getvalue()


def test_register_and_list(cli_state):
    run_cli("reset")
    run_cli("register", "alice")
    out = run_cli("accounts")
    data = json.loads(out)
    assert "alice" in data


def test_full_flow(cli_state):
    run_cli("reset")
    run_cli("register", "alice")
    run_cli("register", "bob")
    run_cli("kyc", "verify", "alice")
    run_cli("kyc", "verify", "bob")
    run_cli("mint", "alice", "500", "--reserves", "1000")
    out = run_cli("transfer", "alice", "bob", "100", "--pqc")
    ev = json.loads(out)
    assert ev["from"] == "alice"
    assert ev["amount"] == 100
    assert "pqcSig" in ev


def test_summary_after_scenario(cli_state):
    run_cli("reset")
    run_cli("scenario", "happy_path")
    summary = json.loads(run_cli("summary"))
    assert summary["supply"] == 500
    assert summary["transfer_count"] == 1
