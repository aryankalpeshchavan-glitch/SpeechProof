import pytest
import math
import json
import numpy as np
from eval.t3_cross_talk import compute_deltas

def test_score_delta_calculations():
    baseline = {"pace": 100.0, "pausing": 95.0, "energy": 80.0, "fluency": None}
    transformed = {"pace": 90.0, "pausing": 95.0, "energy": 85.0, "fluency": None}
    deltas = compute_deltas(baseline, transformed)
    assert deltas["pace"] == -10.0
    assert deltas["pausing"] == 0.0
    assert deltas["energy"] == 5.0
    assert deltas["fluency"] is None
    
def test_unavailable_fluency_handling():
    baseline = {"pace": 100.0, "fluency": None}
    transformed = {"pace": 100.0, "fluency": None}
    deltas = compute_deltas(baseline, transformed)
    assert deltas["fluency"] is None

def test_strict_json_serialization_handles_nulls():
    # If we pass None instead of NaN, json.dumps works with allow_nan=False
    data = {"fluency": None, "spearman": None}
    serialized = json.dumps(data, allow_nan=False)
    assert "null" in serialized

def test_missing_transformed_key_handled():
    baseline = {"pace": 100.0, "pausing": 95.0}
    transformed = {"pace": 90.0} # missing pausing
    deltas = compute_deltas(baseline, transformed)
    assert deltas["pausing"] is None
    assert deltas["pace"] == -10.0

def test_none_values_handled_gracefully():
    baseline = {"pace": None, "pausing": 95.0}
    transformed = {"pace": 90.0, "pausing": 90.0}
    deltas = compute_deltas(baseline, transformed)
    assert deltas["pace"] is None
    assert deltas["pausing"] == -5.0
