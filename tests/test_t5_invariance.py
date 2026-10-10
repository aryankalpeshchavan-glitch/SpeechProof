import pytest
from eval.t5_invariance import calculate_tost

def test_tost_insufficient():
    assert calculate_tost([1.0], 0.5)['status'] == 'INCONCLUSIVE'
    
def test_tost_missing_margin():
    assert calculate_tost([1.0, 1.1], 0.0)['status'] == 'INCONCLUSIVE'

def test_tost_equivalence():
    res = calculate_tost([0.1, -0.1, 0.0, 0.2, -0.2], 0.5)
    assert res['status'] == 'MET'
    
def test_tost_non_equivalence():
    res = calculate_tost([1.0, 1.2, 0.9, 1.1, 1.3], 0.5)
    assert res['status'] == 'NOT_MET'

def test_tost_boundary():
    # Mean difference is exactly margin, shouldn't pass
    res = calculate_tost([0.5, 0.5, 0.5, 0.5], 0.5)
    assert res['status'] == 'NOT_MET'
