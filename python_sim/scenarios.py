from engine import Engine


def happy_path():
    e = Engine()
    e.register("alice"); e.register("bob")
    e.submit_kyc("alice","hashA"); e.verify_kyc("alice")
    e.submit_kyc("bob","hashB"); e.verify_kyc("bob")
    e.set_reserve_report(1000)
    e.mint("alice", 500)
    e.transfer("alice","bob",120, travel_rule_payload={"sender":"alice","recipient":"bob","amount":120}, attach_pqc=True)
    return e

def freeze_flow():
    e = Engine()
    e.register("carol"); e.register("dave")
    e.verify_kyc("carol"); e.verify_kyc("dave")
    e.set_reserve_report(1000)
    e.mint("carol", 400)
    e.freeze_account("dave")
    try:
        e.transfer("carol","dave",50)
    except Exception as ex:
        e._emit("TransferBlocked", {"reason": str(ex)})
    e.unfreeze_account("dave")
    e.transfer("carol","dave",50)
    return e
