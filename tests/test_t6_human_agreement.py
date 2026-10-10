import pytest
from eval.t6_human_agreement import spearman_rho, calculate_icc

def test_spearman_perfect():
    assert spearman_rho([1, 2, 3], [1, 2, 3]) == 1.0

def test_spearman_inverse():
    assert spearman_rho([1, 2, 3], [3, 2, 1]) == -1.0

def test_spearman_insufficient():
    assert spearman_rho([1], [1]) == 0.0
    
def test_spearman_invalid():
    assert spearman_rho([1, 2], [1]) == 0.0

def test_icc_missing():
    assert calculate_icc([]) is None
