from pqc_mock import keygen, sign, verify


def test_keygen_returns_pk_sk():
    kp = keygen()
    assert "pk" in kp and "sk" in kp
    assert len(kp["pk"]) > 0
    assert len(kp["sk"]) > 0


def test_sign_then_verify_succeeds():
    msg = {"from": "alice", "to": "bob", "amount": 100}
    sig = sign(msg)
    assert verify(msg, sig)


def test_verify_fails_on_tampered_message():
    msg = {"from": "alice", "to": "bob", "amount": 100}
    sig = sign(msg)
    tampered = {"from": "alice", "to": "bob", "amount": 1000}
    assert not verify(tampered, sig)


def test_signature_is_deterministic():
    msg = {"from": "alice", "to": "bob", "amount": 100}
    assert sign(msg) == sign(msg)
