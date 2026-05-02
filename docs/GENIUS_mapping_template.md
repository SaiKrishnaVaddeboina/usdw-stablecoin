# GENIUS Act Mapping – USDw

| GENIUS Pillar | How USDw Meets It |
|---|---|
| Licensing & Governance | Mint restricted to issuer MSP (Org1MSP). Reserve updates restricted to issuer. Events for audit. |
| Reserves & Disclosures | `SetReserveReport` state; `Mint` enforces **reserves ≥ supply** before issuance. |
| KYC / AML | `VerifyKYC` required before Mint/Transfer; only KYC-VERIFIED can receive or send. |
| Sanctions | `SanctionAccount` / `UnsanctionAccount`; `Transfer` denies if sender/recipient sanctioned. |
| Freeze / Risk Controls | `FreezeAccount` / `UnfreezeAccount` halt movement instantly. |
| Travel Rule | `Transfer` logs `travelRuleHash` (SHA-256 of off-chain FATF data, no PII on-chain). |
| Transparency & Audit | Events on Mint/Transfer/Reserves; `TxHistory` for per-account provenance. |
| PQC / Agility | Simulation attaches PQC signature to transfers; README describes Dilithium/Kyber path. |
