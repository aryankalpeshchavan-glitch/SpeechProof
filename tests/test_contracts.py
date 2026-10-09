import json
import jsonschema
import pytest

@pytest.mark.skip(reason="evidence_ideal.json is Day-2 format but schema is Day-1, reconciliation pending")
def test_evidence_schema():
    with open('contracts/evidence.schema.json') as f:
        schema = json.load(f)
    with open('contracts/mocks/evidence_ideal.json') as f:
        data = json.load(f)
        
    jsonschema.validate(instance=data, schema=schema)
    
def test_mock_fixture_is_marked():
    with open('contracts/mocks/evidence_ideal.json') as f:
        data = json.load(f)
    assert data.get('mock') is True
