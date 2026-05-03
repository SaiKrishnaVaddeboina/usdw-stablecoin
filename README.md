# USDw — Regulated Stablecoin (Teaching Project)

[![🚀 Live Demo](https://img.shields.io/badge/%F0%9F%9A%80-Live%20Demo-FF4B4B?style=for-the-badge)](https://saikrishnavaddeboina-usdw-stablecoin-uiapp-apogkm.streamlit.app)
&nbsp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Hyperledger Fabric](https://img.shields.io/badge/Hyperledger-Fabric%202.5-2F3134.svg)](https://www.hyperledger.org/use/fabric)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![CI](https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin/actions/workflows/ci.yml/badge.svg)](https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin/actions/workflows/ci.yml)

> A reference implementation of a regulated, permissioned stablecoin aligned with the **GENIUS Act** compliance pillars — built with Hyperledger Fabric chaincode and a Python simulation engine for fast iteration.

> 👉 **[Try the live demo](https://saikrishnavaddeboina-usdw-stablecoin-uiapp-apogkm.streamlit.app)** — runs entirely in your browser, no setup required.
>
> ⚠️ **Teaching project.** No real funds, no real PII, no production guarantees. Cryptography is mocked for clarity (see [PQC notes](#post-quantum-cryptography-pqc)).

---

## Table of Contents

- [Live Demo](#live-demo)

- [Why USDw?](#why-usdw)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start — Simulator](#quick-start--simulator)
- [Quick Start — Chaincode](#quick-start--chaincode)
- [GENIUS Act Compliance Mapping](#genius-act-compliance-mapping)
- [Post-Quantum Cryptography (PQC)](#post-quantum-cryptography-pqc)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Live Demo

🌐 **<https://saikrishnavaddeboina-usdw-stablecoin-uiapp-apogkm.streamlit.app>** — hosted on Streamlit Community Cloud, free for anyone to try.

Suggested 60-second tour:

1. Click **🎬 Scenarios → Happy Path ▶** to populate the system with sample data
2. Switch to **📊 Dashboard** to see the reserves-vs-supply chart, balance distribution, and transfer-volume timeline
3. Open **📜 Audit Log** to inspect the immutable event stream — filter by event type, full-text search, download as CSV/JSON
4. Try **🛡️ Risk Controls → Freeze** an account, then attempt a **💸 Mint & Transfer** to that account to see the compliance gate in action

## Screenshots

<div align="center">

[![Open Live Demo](https://img.shields.io/badge/%E2%96%B6%EF%B8%8F%20Open%20Live%20Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://saikrishnavaddeboina-usdw-stablecoin-uiapp-apogkm.streamlit.app)

**The live demo is the most up-to-date showcase.** Click above to try it instantly.

</div>

<details>
<summary><b>What you'll see (click to expand)</b></summary>

| Tab | What it shows |
|---|---|
| **📊 Dashboard** | Live metrics in the sidebar (accounts, supply, reserves, ratio), plus three charts: reserves vs supply, balance distribution, transfer-volume timeline |
| **👤 Accounts** | Searchable account table with KYC status, freeze, and sanctions flags |
| **✅ Compliance (KYC)** | Submit/verify KYC; smart selectboxes only show eligible accounts |
| **💸 Mint & Transfer** | Issuer-restricted mint with reserve enforcement; travel-rule payload preview before submit; on-screen ✅ verification of the PQC signature on transfer receipts |
| **🛡️ Risk Controls** | One-click freeze/unfreeze/sanction/unsanction with current-state metrics |
| **📜 Audit Log** | Filterable + searchable event stream; CSV + full-state JSON export |
| **🎬 Scenarios** | Five one-click flows: happy path, freeze, sanctions, reserve breach, stress test |

</details>

> **Want to add static screenshots?** Drop PNGs into [`docs/screenshots/`](docs/screenshots/) — see the README in that folder for the recommended filenames and capture tips.

## Why USDw?

Most stablecoin demos either skip compliance entirely or bury it in production-grade code. USDw is built for **teaching and prototyping**: every regulatory control (KYC, reserves, freeze, sanctions, travel-rule) is a small, readable function you can step through in either the on-chain (Fabric) or off-chain (Python) implementation.

The same logic appears in two places so you can compare:
- **`chaincode/usdw/`** — Hyperledger Fabric Node.js smart contract (production-shape)
- **`python_sim/`** — pure-Python engine + Streamlit UI (instant feedback)

## Features

| Capability | Chaincode | Simulator | CLI | Notes |
|---|:---:|:---:|:---:|---|
| Account lifecycle | ✅ | ✅ | ✅ | Register, freeze, unfreeze |
| KYC submit & verify | ✅ | ✅ | ✅ | Hash-only, no PII on-chain |
| Issuer-restricted mint | ✅ | ✅ | ✅ | `Org1MSP` only in chaincode |
| Reserves ≥ supply enforcement | ✅ | ✅ | ✅ | Mint blocks if reserves break |
| Sanctions screening | ✅ | ✅ | ✅ | Blocks on either side of transfer |
| Travel-rule hash | ✅ | ✅ | ✅ | SHA-256 of off-chain FATF payload |
| Account history / events | ✅ | ✅ | ✅ | `TxHistory` + event log w/ timestamps |
| Post-quantum signature + verify (mock) | — | ✅ | ✅ | Sign + on-screen verification badge |
| Live dashboard with charts | — | ✅ | — | Reserves, supply, balance distribution, transfer-volume timeline |
| Audit log filtering & CSV/JSON export | — | ✅ | — | Filter by event type, full-text search, download |
| Demo scenarios | — | ✅ | ✅ | `happy_path`, `freeze_flow`, `sanctions_flow`, `reserve_breach_attempt`, `stress_test` |
| Docker one-command run | — | ✅ | — | `docker compose up` |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Streamlit UI (ui/app.py)                │
│  Sidebar metrics · Dashboard charts · Accounts · KYC ·       │
│  Mint/Transfer · Risk · Audit Log · Scenarios                │
└─────────────────────────┬────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐  ┌─────▼──────┐  ┌──────▼────────────┐
│  Python Engine │  │  CLI tool  │  │  PQC Mock         │
│ (python_sim/)  │←→│ (cli/)     │  │ (Dilithium-style) │
└───────┬────────┘  └────────────┘  └───────────────────┘
        │ same business rules
        │
┌───────▼──────────────────────────────────────────────────────┐
│            Hyperledger Fabric Chaincode (Node.js)            │
│       chaincode/usdw/  — Org1MSP issuer, multi-org peers     │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure

```
usdw-stablecoin/
├── chaincode/usdw/             # Fabric Node.js chaincode
│   ├── lib/usdwContract.js     # Smart contract logic
│   ├── index.js
│   └── package.json
├── python_sim/                 # Pure-Python engine
│   ├── engine.py               # Account, Mint, Transfer, KYC, freeze, summary
│   ├── pqc_mock.py             # Mock PQC signature primitives
│   ├── scenarios.py            # Pre-built demo flows (5 scenarios)
│   └── requirements.txt
├── ui/app.py                   # Streamlit demo (7 tabs + sidebar)
├── cli/usdw.py                 # Headless CLI wrapping the engine
├── scripts/                    # Fabric network + chaincode automation
├── tests/                      # pytest suite (51 tests)
├── docs/GENIUS_mapping_template.md
├── Dockerfile + docker-compose.yml + .streamlit/
├── .github/workflows/ci.yml    # CI: lint + tests
└── README.md
```

## Prerequisites

- **Python ≥ 3.10** (simulator + UI)
- **Node.js ≥ 16** and **Docker** (chaincode + Fabric test network)
- **Hyperledger Fabric 2.5+** samples (only for the on-chain path; see [scripts/get_fabric_samples.sh](scripts/get_fabric_samples.sh))

## Quick Start — Simulator

### Option A — Docker (one command)

```bash
git clone https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin.git
cd usdw-stablecoin
docker compose up
```

Open <http://localhost:8501>.

### Option B — Local Python

```bash
git clone https://github.com/SaiKrishnaVaddeboina/usdw-stablecoin.git
cd usdw-stablecoin

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run ui/app.py
```

Try the **Scenarios → Happy Path ▶** button to populate the dashboard.

## Quick Start — CLI

For headless / scripted use without the UI:

```bash
python cli/usdw.py scenario happy_path
python cli/usdw.py summary
python cli/usdw.py register dave
python cli/usdw.py kyc verify dave
python cli/usdw.py mint dave 200 --reserves 2000
python cli/usdw.py transfer alice dave 50 --pqc
python cli/usdw.py events --type Transfer --limit 5
```

State persists in `$TMPDIR/usdw_cli_state.pkl` between invocations. Override with `USDW_STATE=/path/to/state.pkl`.

## Quick Start — Chaincode

Run the same logic on a real Fabric network:

```bash
# 1. Fetch the Fabric samples / test-network into ../fabric-samples
./scripts/get_fabric_samples.sh

# 2. Bring up the test network and create a channel
./scripts/start_network.sh

# 3. Deploy USDw chaincode
./scripts/deploy_usdw.sh

# 4. Run the example invocations
source ./scripts/org1_env.sh
./scripts/invoke_examples.sh

# 5. Tear down when done
./scripts/stop_network.sh
```

## GENIUS Act Compliance Mapping

| GENIUS Pillar | How USDw Implements It |
|---|---|
| Licensing & Governance | Mint and reserve updates restricted to `Org1MSP` (issuer); all changes emit events |
| Reserves & Disclosures | `SetReserveReport` state; `Mint` enforces **reserves ≥ supply** before issuance |
| KYC / AML | `VerifyKYC` required before mint or transfer for both sender and recipient |
| Sanctions | `SanctionAccount` / `UnsanctionAccount` block transfers on either side |
| Freeze / Risk Controls | `FreezeAccount` / `UnfreezeAccount` halt account movement immediately |
| Travel Rule | `Transfer` records `travelRuleHash` (SHA-256 of off-chain FATF payload) — no PII on-chain |
| Transparency & Audit | Events on every state change; `TxHistory` for per-account provenance |
| Cryptographic Agility | Simulator attaches PQC signatures to transfers; design path to Dilithium/Kyber |

Full mapping: [docs/GENIUS_mapping_template.md](docs/GENIUS_mapping_template.md).

## Post-Quantum Cryptography (PQC)

USDw is designed for **cryptographic agility**. The current ledger uses conventional Fabric signatures, but the simulator demonstrates a drop-in path to **CRYSTALS-Dilithium** (signatures) and **CRYSTALS-Kyber** (key establishment).

In `python_sim/engine.py`, transfers can include a `pqcSig` field, and the event log records a `travelRuleHash` (SHA-256 of compliance metadata) without storing PII on-chain. The PQC primitives in `pqc_mock.py` are intentionally **mock implementations** — production use should swap in [`liboqs-python`](https://github.com/open-quantum-safe/liboqs-python) or equivalent.

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q
```

CI runs the suite on every push and pull request — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Roadmap

- [ ] Replace `pqc_mock.py` with real `liboqs-python` Dilithium signatures
- [ ] Add private-data collections for FATF travel-rule payloads
- [ ] Multi-issuer support (consortium minting with M-of-N approval)
- [ ] On-chain reserve attestation via oracle
- [ ] Caliper performance benchmarks

## Contributing

Issues and PRs welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE) — free for teaching, research, and modification.

## Disclaimer

This is a **teaching and reference implementation**. It is **not** production-ready, has **not** been security-audited, and must **not** be used to handle real funds or personal data. The "regulatory mapping" reflects publicly discussed GENIUS Act pillars at a conceptual level and is not legal advice.
