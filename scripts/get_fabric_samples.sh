#!/usr/bin/env bash
set -euo pipefail

FABRIC_SAMPLES_DEFAULT="../fabric-samples"

if [ -d "${FABRIC_SAMPLES_DEFAULT}" ]; then
  echo "[ok] fabric-samples already present at ${FABRIC_SAMPLES_DEFAULT}"
else
  echo "[*] Cloning fabric-samples..."
  git clone https://github.com/hyperledger/fabric-samples "${FABRIC_SAMPLES_DEFAULT}"
  echo "[ok] cloned."
fi

