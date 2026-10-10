import pytest
from eval.t7_variance import calculate_variance_ratio

def test_t7_single_speaker():
    assert calculate_variance_ratio({'speakerA': [1.0, 2.0]}) is None
    
def test_t7_zero_within_variance():
    res = calculate_variance_ratio({'sp1': [1.0, 1.0], 'sp2': [2.0, 2.0]})
    assert res == float('inf')
    
def test_t7_constant_scores():
    res = calculate_variance_ratio({'sp1': [1.0, 1.0], 'sp2': [1.0, 1.0]})
    assert res == 0.0
    
def test_t7_valid_ratio():
    res = calculate_variance_ratio({'sp1': [1.0, 3.0], 'sp2': [4.0, 6.0]})
    # means: sp1=2, sp2=5, global=3.5
    # between = (2 * (2-3.5)^2 + 2 * (5-3.5)^2) / 1 = 2 * 2.25 + 2 * 2.25 = 9.0
    # within = ((1-2)^2 + (3-2)^2 + (4-5)^2 + (6-5)^2) / 2 = (1+1+1+1)/2 = 2.0
    # ratio = 9.0 / 2.0 = 4.5
    assert abs(res - 4.5) < 1e-6
