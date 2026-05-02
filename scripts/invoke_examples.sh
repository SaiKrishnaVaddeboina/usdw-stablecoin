#!/usr/bin/env bash
set -euo pipefail

CHANNEL="mychannel"
CC="usdw"

peer_invoke() {
  local ARGS="$1"
  peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls \
    --cafile "$ORDERER_CA" -C "$CHANNEL" -n "$CC" \
    --peerAddresses localhost:7051 --tlsRootCertFiles "$CORE_PEER_TLS_ROOTCERT_FILE" \
    --peerAddresses localhost:9051 --tlsRootCertFiles "../fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" \
    -c "$ARGS"
}

peer_invoke '{"Args":["RegisterAccount","alice"]}'
peer_invoke '{"Args":["RegisterAccount","bob"]}'
peer_invoke '{"Args":["VerifyKYC","alice"]}'
peer_invoke '{"Args":["VerifyKYC","bob"]}'
peer_invoke '{"Args":["SetReserveReport","1000"]}'
peer_invoke '{"Args":["Mint","alice","500"]}'
peer_invoke '{"Args":["Transfer","alice","bob","120","hash123"]}'

peer chaincode query -C "$CHANNEL" -n "$CC" -c '{"Args":["GetAccount","alice"]}'
peer chaincode query -C "$CHANNEL" -n "$CC" -c '{"Args":["GetAccount","bob"]}'
peer chaincode query -C "$CHANNEL" -n "$CC" -c '{"Args":["TxHistory","alice"]}'

