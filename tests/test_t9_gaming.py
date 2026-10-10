import pytest
from eval.t9_gaming import evaluate_gaming_attack

def test_gaming_no_trials():
    res = evaluate_gaming_attack([])
    assert res['attempted'] == 0
    assert res['success_rate'] is None

def test_gaming_failed_transform():
    res = evaluate_gaming_attack([{'transform_success': False}])
    assert res['transform_success'] == 0
    assert res['evaluable'] == 0

def test_gaming_missing_mdc95():
    res = evaluate_gaming_attack([{'transform_success': True, 'mdc95': None}])
    assert res['unknown'] == 1
    assert res['evaluable'] == 0

def test_gaming_unknown_ground_truth():
    res = evaluate_gaming_attack([{'transform_success': True, 'mdc95': 1.0, 'flaw_changed': None}])
    # It evaluates if MDC95 is there, but wait, my code says flaw_changed is None -> unknown. Let's trace it.
    # evaluable increases when MDC95 is present. Then flaw_changed is None, unknown increases.
    assert res['evaluable'] == 1
    assert res['unknown'] == 1

def test_gaming_success():
    trials = [
        {'transform_success': True, 'mdc95': 1.0, 'flaw_changed': False, 'score_before': 10, 'score_after': 12}
    ]
    res = evaluate_gaming_attack(trials)
    assert res['evaluable'] == 1
    assert res['gaming_successes'] == 1
    assert res['success_rate'] == 1.0

def test_gaming_failure():
    trials = [
        {'transform_success': True, 'mdc95': 1.0, 'flaw_changed': False, 'score_before': 10, 'score_after': 10}, # below mdc95
        {'transform_success': True, 'mdc95': 1.0, 'flaw_changed': True, 'score_before': 10, 'score_after': 12} # flaw actually changed
    ]
    res = evaluate_gaming_attack(trials)
    assert res['evaluable'] == 2
    assert res['gaming_successes'] == 0
    assert res['success_rate'] == 0.0
