import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python_sim')))
import pandas as pd
import streamlit as st
from engine import Engine

st.set_page_config(page_title="USDw Demo", page_icon="💵")

st.title("USDw – Regulated Stablecoin (Simulation)")
st.caption("Regulated design • GENIUS Act mapping • KYC/AML • Reserves ≥ Supply • Freeze/Sanctions • Travel‑Rule Hash • PQC signature (mock)")

if "engine" not in st.session_state:
    st.session_state.engine = Engine()
e = st.session_state.engine

def _notice(msg, kind="info"):
    if kind == "info": st.info(msg)
    elif kind == "warn": st.warning(msg)
    elif kind == "err": st.error(msg)
    elif kind == "ok": st.success(msg)

def _require_account(id_):
    try:
        _ = e._get(id_)
        return True
    except Exception:
        _notice(f"Account '{id_}' not found. Please register first.", "err")
        return False

def _require_kyc_verified(id_):
    try:
        a = e._get(id_)
        if a.kyc_status != "VERIFIED":
            _notice(f"Account '{id_}' KYC is not VERIFIED.", "err")
            return False
        return True
    except Exception:
        _notice(f"Account '{id_}' not found. Please register first.", "err")
        return False

tab_accounts, tab_compliance, tab_mint, tab_risk, tab_events, tab_scenarios = st.tabs([
    "Accounts", "Compliance (KYC)", "Mint & Transfer", "Risk Controls", "Events & Export", "Scenarios"
])

with tab_accounts:
    st.subheader("Create / View Accounts")
    c1, c2 = st.columns([2,1])
    with c1:
        new_id = st.text_input("New Account ID", "alice")
        if st.button("Register Account", type="primary"):
            try:
                e.register(new_id); _notice(f"Registered '{new_id}'", "ok")
            except Exception as ex:
                _notice(str(ex), "err")
    with c2:
        if st.button("Reset All (fresh state)"):
            from engine import Engine as _E
            st.session_state.engine = _E()
            e = st.session_state.engine
            _notice("Engine reset — all state cleared.", "ok")

    st.markdown("### Current Accounts")
    data = e.list_accounts()
    if data:
        df = pd.DataFrame(data.values())
        st.dataframe(df, use_container_width=True)
        st.caption("Tip: use Compliance tab to submit & verify KYC before transacting.")
    else:
        st.caption("No accounts yet. Register one above.")

with tab_compliance:
    st.subheader("KYC – Submit & Verify")
    k1, k2 = st.columns(2)
    with k1:
        aid = st.text_input("Account ID (KYC)", "alice")
        kyc_hash = st.text_input("KYC Hash (store hash only; no PII)", "hash123")
        if st.button("Submit KYC"):
            if _require_account(aid):
                try: e.submit_kyc(aid, kyc_hash); _notice(f"KYC submitted for '{aid}'", "ok")
                except Exception as ex: _notice(str(ex), "err")
    with k2:
        vid = st.text_input("Account ID to Verify", "alice")
        if st.button("Verify KYC"):
            if _require_account(vid):
                try: e.verify_kyc(vid); _notice(f"KYC verified for '{vid}'", "ok")
                except Exception as ex: _notice(str(ex), "err")

with tab_mint:
    st.subheader("Reserves & Mint")
    m1, m2 = st.columns(2)
    with m1:
        new_res = st.number_input("Set/Update Reserves (issuer control)", 0, 10_000_000, max(1000, e.reserves), 100)
        if st.button("Update Reserves"):
            try: e.set_reserve_report(int(new_res)); _notice(f"Reserves set to {new_res}", "ok")
            except Exception as ex: _notice(str(ex), "err")
    with m2:
        to = st.text_input("Mint to Account", "alice")
        amt = st.number_input("Mint amount", 0, 1_000_000, 500, 50)
        if st.button("Mint"):
            if _require_account(to) and _require_kyc_verified(to):
                try: e.mint(to, int(amt)); _notice(f"Minted {amt} to '{to}'", "ok")
                except Exception as ex: _notice(str(ex), "err")

    st.markdown("---")
    st.subheader("Transfer (Requires VERIFIED sender & recipient)")
    s, r = st.columns(2)
    with s: from_id = st.text_input("From", "alice")
    with r: to_id = st.text_input("To", "bob")
    tcol1, tcol2 = st.columns([1,1])
    with tcol1: t_amt = st.number_input("Amount", 0, 1_000_000, 120, 10)
    with tcol2: attach = st.checkbox("Attach PQC signature", value=True)

    if st.button("Transfer", type="primary"):
        ok = True
        ok &= _require_account(from_id)
        ok &= _require_account(to_id)
        ok &= _require_kyc_verified(from_id)
        ok &= _require_kyc_verified(to_id)
        if ok:
            try:
                ev = e.transfer(
                    from_id, to_id, int(t_amt),
                    travel_rule_payload={"sender": from_id, "recipient": to_id, "amount": int(t_amt)},
                    attach_pqc=attach
                )
                _notice("Transfer complete", "ok")
                st.json(ev, expanded=False)
            except Exception as ex:
                _notice(str(ex), "err")

    st.markdown("### Balances")
    st.write(e.get_balances() or "No accounts yet.")

with tab_risk:
    st.subheader("Freeze / Unfreeze / Sanction / Unsanction")
    who = st.text_input("Account", "bob")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Freeze"):
        if _require_account(who): e.freeze_account(who); _notice(f"{who} frozen", "warn")
    if c2.button("Unfreeze"):
        if _require_account(who): e.unfreeze_account(who); _notice(f"{who} unfrozen", "ok")
    if c3.button("Sanction"):
        if _require_account(who): e.sanction_account(who); _notice(f"{who} sanctioned", "warn")
    if c4.button("Unsanction"):
        if _require_account(who): e.unsanction_account(who); _notice(f"{who} unsanctioned", "ok")

with tab_events:
    st.subheader("Event Log")
    if e.events:
        rows = [dict(ev) for ev in e.events]
        import pandas as _pd
        df = _pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Events CSV", data=csv, file_name="usdw_events.csv", mime="text/csv")
    else:
        st.caption("No events yet. Perform actions in other tabs.")

with tab_scenarios:
    st.subheader("One‑Click Scenarios (for demo)")
    s1, s2 = st.columns(2)
    with s1:
        if st.button("Happy Path ▶"):
            from scenarios import happy_path
            st.session_state.engine = happy_path(); _notice("Happy path executed.", "ok")
    with s2:
        if st.button("Freeze Flow ▶"):
            from scenarios import freeze_flow
            st.session_state.engine = freeze_flow(); _notice("Freeze flow executed.", "ok")

st.markdown("---")
st.caption("Teaching simulation — no real funds or personal data.")
