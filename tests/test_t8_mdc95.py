import pytest
from eval.t8_mdc95 import calculate_mdc95, improvement_gate

def test_mdc95_insufficient():
    assert calculate_mdc95([(1.0, 2.0)]) is None

def test_mdc95_exact():
    # pairs: (0, 0), (0, 1), diffs = 0, 1
    # mean_diff = 0.5
    # variance = ((0-0.5)^2 + (1-0.5)^2) / 1 = 0.25 + 0.25 = 0.5
    # sd = sqrt(0.5) = 0.7071
    # MDC95 = 1.96 * 0.7071 = 1.3859
    res = calculate_mdc95([(0.0, 0.0), (0.0, 1.0)])
    assert abs(res - 1.3859) < 1e-3
    
def test_mdc95_zero_variance():
    assert calculate_mdc95([(1.0, 2.0), (2.0, 3.0)]) == 0.0 # diffs are 1, 1 -> var 0

def test_gate_above():
    assert improvement_gate(0.0, 2.0, 1.0) == True

def test_gate_equal():
    assert improvement_gate(0.0, 1.0, 1.0) == False
    
def test_gate_below():
    assert improvement_gate(0.0, 0.5, 1.0) == False

def test_gate_negative():
    assert improvement_gate(1.0, 0.0, 1.0) == False
    
def test_gate_missing_mdc():
    assert improvement_gate(0.0, 2.0, None) == False
