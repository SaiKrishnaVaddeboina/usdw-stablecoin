# USDw Chaincode

Hyperledger Fabric Node.js chaincode for the USDw regulated stablecoin.

## Contract surface

| Method | Caller | Description |
|---|---|---|
| `RegisterAccount(id)` | any | Create an account in `PENDING` KYC state |
| `SubmitKYC(id, kycHash)` | any | Attach a KYC hash; status → `SUBMITTED` |
| `VerifyKYC(id)` | any | Mark KYC as `VERIFIED` |
| `FreezeAccount(id)` / `UnfreezeAccount(id)` | any | Toggle the account freeze flag |
| `SanctionAccount(id)` / `UnsanctionAccount(id)` | any | Toggle the sanctions flag |
| `SetReserveReport(amount)` | **Org1MSP** | Update declared reserves |
| `Mint(toId, amount)` | **Org1MSP** | Mint USDw to a verified account; enforces reserves ≥ supply |
| `Transfer(fromId, toId, amount, travelRuleHash)` | any | Move USDw between verified, unfrozen, unsanctioned accounts |
| `GetAccount(id)` | any | Query an account's full state |
| `TxHistory(id)` | any | Query the per-account write history |

## Events

Every state-changing method emits an event so off-chain auditors and indexers can stream changes:

`AccountRegistered`, `KYCUploaded`, `KYCVerified`, `AccountFrozen`, `AccountUnfrozen`, `AccountSanctioned`, `AccountUnsanctioned`, `ReserveUpdated`, `Mint`, `Transfer`.

## Deploying

See [`scripts/`](../../scripts/) at the repo root — `start_network.sh`, `deploy_usdw.sh`, and `invoke_examples.sh` cover the standard test-network workflow.

## Security model

- **Issuer privilege** is gated by MSP ID (`Org1MSP`). In a real deployment, set this through chaincode definition policies (endorsement + lifecycle).
- **Travel-rule data** is hashed off-chain and only the digest is recorded — this keeps PII off the ledger while preserving auditability.
- **Reserves accounting** uses `BigInt` to avoid floating-point loss for large supplies.

## Testing

The Python simulator in [`../../python_sim/`](../../python_sim/) implements the same business rules and is fully unit-tested. Use it to validate logic changes before porting them here.
