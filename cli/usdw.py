#!/usr/bin/env python3
"""USDw command-line interface — wraps the simulation engine for headless use.

Examples:
    usdw scenario happy_path
    usdw register alice && usdw kyc verify alice
    usdw mint alice 500 --reserves 1000
    usdw transfer alice bob 100 --pqc
    usdw summary
    usdw events --type Transfer
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_sim"))

from engine import Engine  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

STATE_PATH = Path(os.environ.get("USDW_STATE", Path(tempfile.gettempdir()) / "usdw_cli_state.pkl"))


def load_engine() -> Engine:
    if STATE_PATH.exists():
        with open(STATE_PATH, "rb") as f:
            return pickle.load(f)
    return Engine()


def save_engine(e: Engine) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "wb") as f:
        pickle.dump(e, f)


def cmd_reset(args, e):
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    print(f"State cleared ({STATE_PATH})")
    return Engine()


def cmd_summary(args, e):
    print(json.dumps(e.get_summary(), indent=2))
    return e


def cmd_register(args, e):
    e.register(args.account_id)
    print(f"✓ Registered {args.account_id}")
    return e


def cmd_kyc(args, e):
    if args.kyc_action == "submit":
        e.submit_kyc(args.account_id, args.hash)
        print(f"✓ KYC submitted for {args.account_id}")
    else:
        e.verify_kyc(args.account_id)
        print(f"✓ KYC verified for {args.account_id}")
    return e


def cmd_mint(args, e):
    if args.reserves is not None:
        e.set_reserve_report(args.reserves)
    e.mint(args.account_id, args.amount)
    print(f"✓ Minted {args.amount} to {args.account_id} (supply={e.supply})")
    return e


def cmd_transfer(args, e):
    payload = {"sender": args.from_id, "recipient": args.to_id, "amount": args.amount}
    ev = e.transfer(args.from_id, args.to_id, args.amount,
                    travel_rule_payload=payload, attach_pqc=args.pqc)
    print(json.dumps(ev, indent=2, default=str))
    return e


def cmd_freeze(args, e):
    {"freeze": e.freeze_account, "unfreeze": e.unfreeze_account,
     "sanction": e.sanction_account, "unsanction": e.unsanction_account}[args.risk_action](args.account_id)
    print(f"✓ {args.risk_action} {args.account_id}")
    return e


def cmd_accounts(args, e):
    print(json.dumps(e.list_accounts(), indent=2))
    return e


def cmd_events(args, e):
    rows = e.events
    if args.type:
        rows = [r for r in rows if r["type"] == args.type]
    if args.limit:
        rows = rows[-args.limit:]
    print(json.dumps(rows, indent=2, default=str))
    return e


def cmd_scenario(args, e):
    if args.scenario_name not in SCENARIOS:
        sys.exit(f"Unknown scenario '{args.scenario_name}'. Available: {', '.join(SCENARIOS)}")
    label, _, fn = SCENARIOS[args.scenario_name]
    new_engine = fn()
    print(f"✓ Ran scenario: {label}")
    print(json.dumps(new_engine.get_summary(), indent=2))
    return new_engine


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="usdw", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("reset", help="Clear engine state").set_defaults(fn=cmd_reset)
    sub.add_parser("summary", help="Show aggregate metrics").set_defaults(fn=cmd_summary)
    sub.add_parser("accounts", help="List accounts").set_defaults(fn=cmd_accounts)

    reg = sub.add_parser("register", help="Register a new account")
    reg.add_argument("account_id"); reg.set_defaults(fn=cmd_register)

    kyc = sub.add_parser("kyc", help="KYC submit / verify")
    kyc.add_argument("kyc_action", choices=["submit", "verify"])
    kyc.add_argument("account_id")
    kyc.add_argument("--hash", default="0xkyc-hash", help="KYC document hash (for submit)")
    kyc.set_defaults(fn=cmd_kyc)

    mint = sub.add_parser("mint", help="Mint USDw to an account")
    mint.add_argument("account_id"); mint.add_argument("amount", type=int)
    mint.add_argument("--reserves", type=int, help="Set reserves before minting")
    mint.set_defaults(fn=cmd_mint)

    xfer = sub.add_parser("transfer", help="Transfer USDw between accounts")
    xfer.add_argument("from_id"); xfer.add_argument("to_id"); xfer.add_argument("amount", type=int)
    xfer.add_argument("--pqc", action="store_true", help="Attach mock PQC signature")
    xfer.set_defaults(fn=cmd_transfer)

    risk = sub.add_parser("risk", help="Freeze / sanction controls")
    risk.add_argument("risk_action", choices=["freeze", "unfreeze", "sanction", "unsanction"])
    risk.add_argument("account_id")
    risk.set_defaults(fn=cmd_freeze)

    ev = sub.add_parser("events", help="Show event log")
    ev.add_argument("--type", help="Filter by event type")
    ev.add_argument("--limit", type=int, help="Show last N events")
    ev.set_defaults(fn=cmd_events)

    sc = sub.add_parser("scenario", help="Run a pre-built scenario")
    sc.add_argument("scenario_name", choices=list(SCENARIOS.keys()))
    sc.set_defaults(fn=cmd_scenario)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = load_engine()
    try:
        engine = args.fn(args, engine)
    except Exception as ex:
        print(f"✗ {ex}", file=sys.stderr)
        return 1
    if args.command != "reset":
        save_engine(engine)
    return 0


if __name__ == "__main__":
    sys.exit(main())
