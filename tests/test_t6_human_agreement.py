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
    assert calculate_icc([[1.0]]) is None
    assert calculate_icc([[1.0, 2.0]]) is None  # only 1 target
    assert calculate_icc([[1.0, 2.0], [1.0]]) is None  # jagged rows

def test_icc_perfect_agreement():
    ratings = [
        [1.0, 1.0],
        [2.0, 2.0],
        [3.0, 3.0]
    ]
    icc = calculate_icc(ratings)
    assert icc is not None
    assert abs(icc - 1.0) < 1e-5

def test_icc_with_rater_bias():
    ratings = [
        [1.0, 2.0],
        [2.0, 3.0],
        [3.0, 4.0]
    ]
    icc = calculate_icc(ratings)
    assert icc is not None
    assert abs(icc - 0.8) < 1e-5
