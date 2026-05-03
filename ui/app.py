"""USDw — Streamlit demo UI for the regulated stablecoin simulator."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python_sim")))

import pandas as pd
import streamlit as st
from engine import ENGINE_VERSION, Engine
from scenarios import SCENARIOS

st.set_page_config(
    page_title="USDw — Regulated Stablecoin",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────────────────────
# Session state
# ────────────────────────────────────────────────────────────────────────────
if "engine" not in st.session_state:
    st.session_state.engine = Engine()
if "last_transfer" not in st.session_state:
    st.session_state.last_transfer = None

e: Engine = st.session_state.engine

# Defensive check: if Streamlit Cloud has cached an old build of the engine,
# replace the session-state instance with a fresh one rather than crashing.
if not hasattr(e, "get_summary"):
    st.session_state.engine = Engine()
    e = st.session_state.engine


def reset_engine():
    st.session_state.engine = Engine()
    st.session_state.last_transfer = None


def _notice(msg: str, kind: str = "info"):
    {"info": st.info, "warn": st.warning, "err": st.error, "ok": st.success}[kind](msg)


def _require_account(id_: str) -> bool:
    if id_ not in e.accounts:
        _notice(f"Account '{id_}' not found. Register it first.", "err")
        return False
    return True


def _require_kyc_verified(id_: str) -> bool:
    if not _require_account(id_):
        return False
    if e.accounts[id_].kyc_status != "VERIFIED":
        _notice(f"Account '{id_}' KYC is not VERIFIED.", "err")
        return False
    return True


def _fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


# ────────────────────────────────────────────────────────────────────────────
# Sidebar — live metrics + global controls
# ────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💵 USDw")
    st.caption("Regulated Stablecoin · GENIUS Act-aligned · PQC-ready")

    summary = e.get_summary()

    st.markdown("### Live Metrics")
    m1, m2 = st.columns(2)
    m1.metric("Accounts", summary["total_accounts"])
    m2.metric("Verified", summary["verified_accounts"])

    m3, m4 = st.columns(2)
    m3.metric("Frozen", summary["frozen_accounts"])
    m4.metric("Sanctioned", summary["sanctioned_accounts"])

    st.markdown("---")
    st.metric("Total Supply", f"{summary['supply']:,}")
    st.metric("Reserves", f"{summary['reserves']:,}")

    ratio = summary["reserve_ratio"]
    if ratio == float("inf"):
        ratio_label, ratio_help = "n/a", "No supply yet"
    else:
        ratio_label = f"{ratio:.2f}×"
        ratio_help = "Reserves ÷ Supply (must be ≥ 1.00 for new mints)"
    st.metric("Reserve Ratio", ratio_label, help=ratio_help)

    st.markdown("---")
    st.metric("Transfers", summary["transfer_count"])
    st.metric("Volume", f"{summary['transfer_volume']:,}")

    st.markdown("---")
    st.button("🔄 Reset all state", on_click=reset_engine, use_container_width=True)

    st.markdown("---")
    st.caption("📂 [Source on GitHub](https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin)")
    st.caption(f"Engine v{ENGINE_VERSION} · Teaching project — no real funds.")


# ────────────────────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────────────────────
st.title("USDw — Regulated Stablecoin Simulator")
st.caption(
    "Hyperledger Fabric-backed stablecoin with KYC/AML, reserve enforcement, "
    "freeze & sanctions controls, travel-rule hashing, and a post-quantum signature path."
)

# ────────────────────────────────────────────────────────────────────────────
# Tabs
# ────────────────────────────────────────────────────────────────────────────
TABS = [
    "📊 Dashboard",
    "👤 Accounts",
    "✅ Compliance (KYC)",
    "💸 Mint & Transfer",
    "🛡️ Risk Controls",
    "📜 Audit Log",
    "🎬 Scenarios",
]
tab_dash, tab_accts, tab_kyc, tab_mint, tab_risk, tab_audit, tab_scen = st.tabs(TABS)


# ────────────────────────────────────────────────────────────────────────────
# Dashboard
# ────────────────────────────────────────────────────────────────────────────
with tab_dash:
    st.subheader("System Health")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total Supply", f"{summary['supply']:,}")
    col_b.metric("Reserves", f"{summary['reserves']:,}")
    headroom = summary["reserves"] - summary["supply"]
    col_c.metric("Mint Headroom", f"{headroom:,}", help="Reserves − Supply (max amount that can still be minted)")
    col_d.metric("Transfer Volume", f"{summary['transfer_volume']:,}")

    st.markdown("### Reserves vs Supply")
    chart_df = pd.DataFrame({"Metric": ["Reserves", "Supply"], "Amount": [summary["reserves"], summary["supply"]]})
    st.bar_chart(chart_df.set_index("Metric"), height=200)

    if summary["total_accounts"] > 0:
        st.markdown("### Balance Distribution")
        bal_df = pd.DataFrame(
            [{"Account": a.id, "Balance": a.balance, "Status": a.kyc_status} for a in e.accounts.values()]
        ).sort_values("Balance", ascending=False)
        st.bar_chart(bal_df.set_index("Account")["Balance"], height=240)

    if summary["transfer_count"] > 0:
        st.markdown("### Transfer Volume Over Time")
        transfers = [ev for ev in e.events if ev["type"] == "Transfer"]
        tdf = pd.DataFrame(
            [{"time": _fmt_ts(t["ts"]), "amount": t["amount"]} for t in transfers]
        )
        tdf["cumulative"] = tdf["amount"].cumsum()
        st.line_chart(tdf.set_index("time")[["amount", "cumulative"]], height=240)

    if not e.events:
        st.info("👋 New session. Try **Scenarios → Happy Path** to populate the dashboard with sample data.")


# ────────────────────────────────────────────────────────────────────────────
# Accounts
# ────────────────────────────────────────────────────────────────────────────
with tab_accts:
    st.subheader("Account Management")

    with st.form("register_form", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        new_id = c1.text_input("New Account ID", placeholder="e.g. alice")
        c2.markdown("&nbsp;")
        if c2.form_submit_button("Register", type="primary", use_container_width=True):
            if new_id.strip():
                try:
                    e.register(new_id.strip())
                    _notice(f"Registered '{new_id}'", "ok")
                except Exception as ex:
                    _notice(str(ex), "err")
            else:
                _notice("Account ID cannot be empty.", "err")

    st.markdown("### Current Accounts")
    accts = e.list_accounts()
    if accts:
        df = pd.DataFrame(accts.values())
        search = st.text_input("🔍 Filter by ID", "")
        if search:
            df = df[df["id"].str.contains(search, case=False, na=False)]
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "balance": st.column_config.NumberColumn("Balance", format="%d"),
                "kyc_status": st.column_config.TextColumn("KYC"),
                "frozen": st.column_config.CheckboxColumn("🧊 Frozen"),
                "sanctioned": st.column_config.CheckboxColumn("🚫 Sanctioned"),
            },
        )
    else:
        st.caption("No accounts yet — register one above or run a scenario.")


# ────────────────────────────────────────────────────────────────────────────
# Compliance (KYC)
# ────────────────────────────────────────────────────────────────────────────
with tab_kyc:
    st.subheader("KYC Submission & Verification")
    st.caption("Only the SHA-256 hash of off-chain KYC documents is stored — no PII.")

    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**Submit KYC**")
        aid = st.selectbox("Account", list(e.accounts.keys()) or [""], key="kyc_submit_id") or ""
        kyc_hash = st.text_input("KYC document hash", "0xabc123...", key="kyc_hash_input")
        if st.button("Submit KYC", use_container_width=True):
            if _require_account(aid):
                try:
                    e.submit_kyc(aid, kyc_hash)
                    _notice(f"KYC submitted for '{aid}'", "ok")
                except Exception as ex:
                    _notice(str(ex), "err")

    with k2:
        st.markdown("**Verify KYC**")
        submitted = [a.id for a in e.accounts.values() if a.kyc_status == "SUBMITTED"]
        vid = st.selectbox("Account", submitted or [""], key="kyc_verify_id",
                           help="Only accounts with SUBMITTED status appear here.") or ""
        st.markdown("&nbsp;")
        if st.button("Verify KYC", use_container_width=True, type="primary"):
            if _require_account(vid):
                try:
                    e.verify_kyc(vid)
                    _notice(f"KYC verified for '{vid}' — can now transact", "ok")
                except Exception as ex:
                    _notice(str(ex), "err")

    st.markdown("### KYC Status Overview")
    if e.accounts:
        status_counts = pd.DataFrame(
            [{"Status": a.kyc_status} for a in e.accounts.values()]
        ).value_counts().reset_index(name="Count")
        st.bar_chart(status_counts.set_index("Status"), height=200)


# ────────────────────────────────────────────────────────────────────────────
# Mint & Transfer
# ────────────────────────────────────────────────────────────────────────────
with tab_mint:
    st.subheader("Reserves & Mint")
    st.caption("Issuer (Org1MSP) sets reserves; mint is gated by **reserves ≥ supply**.")

    m1, m2 = st.columns(2)
    with m1:
        st.markdown("**Issuer Reserve Report**")
        new_res = st.number_input(
            "Declared reserves (USD-equivalent)",
            min_value=0, max_value=10_000_000,
            value=max(1000, e.reserves), step=100,
        )
        if st.button("Update Reserves", use_container_width=True):
            try:
                e.set_reserve_report(int(new_res))
                _notice(f"Reserves set to {new_res:,}", "ok")
            except Exception as ex:
                _notice(str(ex), "err")

    with m2:
        st.markdown("**Mint to Account**")
        verified = [a.id for a in e.accounts.values()
                    if a.kyc_status == "VERIFIED" and not a.frozen and not a.sanctioned]
        to = st.selectbox("Recipient (must be VERIFIED, unfrozen, unsanctioned)",
                          verified or [""], key="mint_recipient") or ""
        amt = st.number_input("Mint amount", 0, 1_000_000, 500, 50)
        if st.button("Mint", type="primary", use_container_width=True):
            if _require_kyc_verified(to):
                try:
                    e.mint(to, int(amt))
                    _notice(f"Minted {amt:,} to '{to}' (supply now {e.supply:,})", "ok")
                except Exception as ex:
                    _notice(str(ex), "err")

    st.markdown("---")
    st.subheader("Transfer")

    transferable = [a.id for a in e.accounts.values()
                    if a.kyc_status == "VERIFIED" and not a.frozen and not a.sanctioned]
    s, r = st.columns(2)
    from_id = s.selectbox("From", transferable or [""], key="xfer_from") or ""
    to_id = r.selectbox("To", transferable or [""], key="xfer_to") or ""

    tcol1, tcol2 = st.columns([2, 1])
    t_amt = tcol1.number_input("Amount", 0, 1_000_000, 120, 10)
    attach = tcol2.checkbox("Attach PQC signature", value=True,
                            help="Adds a mock CRYSTALS-Dilithium-style signature to the transfer event.")

    with st.expander("👁 Travel-rule payload preview (only the SHA-256 hash hits the ledger)"):
        payload = {"sender": from_id, "recipient": to_id, "amount": int(t_amt)}
        st.code(json.dumps(payload, indent=2), language="json")

    if st.button("Submit Transfer", type="primary", use_container_width=True):
        if from_id == to_id:
            _notice("Sender and recipient must differ.", "err")
        elif _require_kyc_verified(from_id) and _require_kyc_verified(to_id):
            try:
                ev = e.transfer(
                    from_id, to_id, int(t_amt),
                    travel_rule_payload={"sender": from_id, "recipient": to_id, "amount": int(t_amt)},
                    attach_pqc=attach,
                )
                st.session_state.last_transfer = ev
                _notice(f"Transferred {t_amt:,} from {from_id} → {to_id}", "ok")
            except Exception as ex:
                _notice(str(ex), "err")

    if st.session_state.last_transfer:
        st.markdown("### Last Transfer Receipt")
        ev = st.session_state.last_transfer
        st.json(ev)
        if "pqcSig" in ev:
            if e.verify_transfer_signature(ev):
                st.success("PQC signature ✅ verified")
            else:
                st.error("PQC signature ❌ invalid")


# ────────────────────────────────────────────────────────────────────────────
# Risk Controls
# ────────────────────────────────────────────────────────────────────────────
with tab_risk:
    st.subheader("Freeze, Unfreeze, Sanction, Unsanction")
    st.caption("These controls take effect immediately and block any further movement.")

    who = st.selectbox("Account", list(e.accounts.keys()) or [""], key="risk_target") or ""
    if who:
        a = e.accounts[who]
        s1, s2, s3 = st.columns(3)
        s1.metric("KYC", a.kyc_status)
        s2.metric("Frozen", "Yes" if a.frozen else "No")
        s3.metric("Sanctioned", "Yes" if a.sanctioned else "No")

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧊 Freeze", use_container_width=True, disabled=not who):
        if _require_account(who):
            e.freeze_account(who); _notice(f"{who} frozen", "warn")
    if c2.button("🔥 Unfreeze", use_container_width=True, disabled=not who):
        if _require_account(who):
            e.unfreeze_account(who); _notice(f"{who} unfrozen", "ok")
    if c3.button("🚫 Sanction", use_container_width=True, disabled=not who):
        if _require_account(who):
            e.sanction_account(who); _notice(f"{who} sanctioned", "warn")
    if c4.button("✅ Unsanction", use_container_width=True, disabled=not who):
        if _require_account(who):
            e.unsanction_account(who); _notice(f"{who} unsanctioned", "ok")


# ────────────────────────────────────────────────────────────────────────────
# Audit Log
# ────────────────────────────────────────────────────────────────────────────
with tab_audit:
    st.subheader("Event Log")
    if e.events:
        rows = []
        for ev in e.events:
            row = {k: v for k, v in ev.items() if k != "ts"}
            row["time"] = _fmt_ts(ev["ts"])
            rows.append(row)
        df = pd.DataFrame(rows)
        # Move time + type to the front for readability.
        ordered_cols = ["time", "type"] + [c for c in df.columns if c not in ("time", "type")]
        df = df[ordered_cols].iloc[::-1].reset_index(drop=True)

        f1, f2 = st.columns([2, 3])
        types = sorted({ev["type"] for ev in e.events})
        selected_types = f1.multiselect("Filter by type", types, default=types)
        text_filter = f2.text_input("🔍 Search (any column)", "")

        view = df[df["type"].isin(selected_types)]
        if text_filter:
            mask = view.astype(str).apply(lambda c: c.str.contains(text_filter, case=False, na=False)).any(axis=1)
            view = view[mask]

        st.dataframe(view, use_container_width=True, height=420)

        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇️ Download events (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="usdw_events.csv",
            mime="text/csv",
            use_container_width=True,
        )
        d2.download_button(
            "⬇️ Download full state (JSON)",
            json.dumps(e.export_state(), indent=2, default=str).encode("utf-8"),
            file_name="usdw_state.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.caption("No events yet. Perform actions in other tabs or run a scenario.")


# ────────────────────────────────────────────────────────────────────────────
# Scenarios
# ────────────────────────────────────────────────────────────────────────────
with tab_scen:
    st.subheader("One-Click Demo Scenarios")
    st.caption("Each scenario resets the engine and runs a representative flow end-to-end.")

    for key, (label, desc, fn) in SCENARIOS.items():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{label}**  \n_{desc}_")
            if c2.button("Run ▶", key=f"scen_{key}", use_container_width=True):
                st.session_state.engine = fn()
                st.session_state.last_transfer = None
                _notice(f"Scenario '{label}' executed — see Dashboard / Audit Log", "ok")
                st.rerun()
