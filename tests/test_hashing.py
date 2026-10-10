from speechproof.hashing import hash_audio, canonical_json_dumps, hash_evidence

def test_hash_audio():
    h1 = hash_audio(b'test')
    h2 = hash_audio(b'test')
    h3 = hash_audio(b'other')
    assert h1 == h2
    assert h1 != h3

def test_hash_evidence_excludes_output():
    ev = {"a": 1, "output_sha256": "123"}
    ev2 = {"a": 1, "output_sha256": "456"}
    assert hash_evidence(ev) == hash_evidence(ev2)

def test_hash_json_key_order():
    ev1 = {"a": 1, "b": 2}
    ev2 = {"b": 2, "a": 1}
    assert hash_evidence(ev1) == hash_evidence(ev2)

def test_hash_json_whitespace():
    # Because hash_evidence dict-ifies, we test canonical_json_dumps instead for whitespace
    obj = {"a": 1, "b": 2}
    import json
    # different whitespace
    s1 = json.dumps(obj, indent=4)
    s2 = json.dumps(obj, separators=(', ', ': '))
    
    # decode back and hash
    assert hash_evidence(json.loads(s1)) == hash_evidence(json.loads(s2))
    
    # directly check canonical string
    canon = canonical_json_dumps(obj)
    assert ' ' not in canon
    assert '\n' not in canon

def test_hash_json_values():
    assert hash_evidence({"a": 1}) != hash_evidence({"a": 2})

def test_hash_unicode():
    ev1 = {"text": "café"}
    ev2 = {"text": "caf\u00e9"}
    assert hash_evidence(ev1) == hash_evidence(ev2)

def test_evidence_idempotent():
    ev = {"scores": {"pace": 1.0}}
    h1 = hash_evidence(ev)
    ev["output_sha256"] = h1
    h2 = hash_evidence(ev)
    assert h1 == h2
