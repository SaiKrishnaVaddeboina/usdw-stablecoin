import hashlib
import json
import os


def keygen(): return {"pk": os.urandom(16).hex(), "sk": os.urandom(16).hex()}
def sign(message_obj):
    blob = json.dumps(message_obj, sort_keys=True).encode('utf-8')
    return hashlib.sha256(blob + b'USDwPQC').hexdigest()
def verify(message_obj, signature):
    blob = json.dumps(message_obj, sort_keys=True).encode('utf-8')
    return hashlib.sha256(blob + b'USDwPQC').hexdigest() == signature
