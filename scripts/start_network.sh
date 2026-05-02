#!/usr/bin/env bash
set -euo pipefail

FABRIC_SAMPLES="../fabric-samples"
TEST_NETWORK="${FABRIC_SAMPLES}/test-network"

pushd "${TEST_NETWORK}" >/dev/null
  ./network.sh down || true
  ./network.sh up
  ./network.sh createChannel
popd >/dev/null

echo "[ok] Fabric network started."

