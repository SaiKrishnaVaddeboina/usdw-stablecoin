from scenarios import freeze_flow, happy_path


def test_happy_path_completes():
    e = happy_path()
    assert e.accounts["alice"].balance == 380  # 500 minted - 120 transferred
    assert e.accounts["bob"].balance == 120
    assert e.supply == 500
    transfer_events = [ev for ev in e.events if ev["type"] == "Transfer"]
    assert len(transfer_events) == 1
    assert "pqcSig" in transfer_events[0]


def test_freeze_flow_blocks_then_succeeds():
    e = freeze_flow()
    blocked = [ev for ev in e.events if ev["type"] == "TransferBlocked"]
    assert len(blocked) == 1
    transfers = [ev for ev in e.events if ev["type"] == "Transfer"]
    assert len(transfers) == 1
    assert e.accounts["dave"].balance == 50
