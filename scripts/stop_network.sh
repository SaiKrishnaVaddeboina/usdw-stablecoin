#!/usr/bin/env bash
set -euo pipefail

FABRIC_SAMPLES="../fabric-samples"
TEST_NETWORK="${FABRIC_SAMPLES}/test-network"

pushd "${TEST_NETWORK}" >/dev/null
  ./network.sh down || true
popd >/dev/null

echo "[ok] Fabric network stopped."

