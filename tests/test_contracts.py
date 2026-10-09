import json
import jsonschema
import pytest

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
