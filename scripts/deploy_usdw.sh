#!/usr/bin/env bash
set -euo pipefail

FABRIC_SAMPLES="../fabric-samples"
TEST_NETWORK="${FABRIC_SAMPLES}/test-network"
CHAINCODE_PATH="$(pwd)/chaincode/usdw"

pushd "${TEST_NETWORK}" >/dev/null
  ./network.sh deployCC -ccn usdw -ccp "${CHAINCODE_PATH}" -ccl javascript
popd >/dev/null

echo "[ok] USDw chaincode deployed."

