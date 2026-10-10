import pytest
from eval.ablations import validate_ablation_prereqs

def test_ablation_prereq_missing():
    res = validate_ablation_prereqs("A1", False)
    assert res['status'] == 'INCONCLUSIVE'

def test_ablation_prereq_present():
    res = validate_ablation_prereqs("A1", True)
    assert res['status'] == 'RUNNABLE'
