import pytest
from typing import Dict, Any

from eval.t1_reproducibility import compare_runs

def get_base_run() -> Dict[str, Any]:
    return {
        "scores": {"pace": 80.0},
        "overall_score": 85.0,
        "word_fingerprint": "wordhash123",
        "region_fingerprint": "regionhash123",
        "region_count": 1,
        "evidence_sha256": "evhash123"
    }

def test_identical_outputs_produce_match():
    runs = [get_base_run() for _ in range(5)]
    overall, count, comps = compare_runs(runs)
    assert count == 4
    assert overall == "MATCH"
    assert comps["scores_match"] == "MATCH"
    assert comps["words_match"] == "MATCH"
    assert comps["regions_match"] == "MATCH"
    assert comps["evidence_hashes_match"] == "MATCH"

def test_different_dimension_scores_produce_mismatch():
    runs = [get_base_run() for _ in range(5)]
    runs[2]["scores"]["pace"] = 90.0
    overall, count, comps = compare_runs(runs)
    assert count == 4
    assert overall == "MISMATCH"
    assert comps["scores_match"] == "MISMATCH"

def test_different_transcripts_produce_mismatch():
    runs = [get_base_run() for _ in range(5)]
    runs[1]["word_fingerprint"] = "different_wordhash"
    overall, count, comps = compare_runs(runs)
    assert count == 4
    assert overall == "MISMATCH"
    assert comps["words_match"] == "MISMATCH"

def test_evidence_differences_are_detected():
    runs = [get_base_run() for _ in range(5)]
    runs[3]["evidence_sha256"] = "different_evhash"
    overall, count, comps = compare_runs(runs)
    assert count == 4
    assert overall == "MISMATCH"
    assert comps["evidence_hashes_match"] == "MISMATCH"

def test_one_successful_run_produces_inconclusive():
    runs = [get_base_run()]
    overall, count, comps = compare_runs(runs)
    assert count == 0
    assert overall == "INCONCLUSIVE (Only 1/5 successful runs)"
    assert comps["scores_match"] == "INCONCLUSIVE"

def test_zero_successful_runs_produces_failure():
    runs = []
    overall, count, comps = compare_runs(runs)
    assert count == 0
    assert overall == "FAILED (Zero successful runs)"
    assert comps["scores_match"] == "INCONCLUSIVE"

def test_missing_output_fields_do_not_become_successful():
    runs = [get_base_run() for _ in range(2)]
    del runs[1]["overall_score"]
    overall, count, comps = compare_runs(runs, attempted_runs=2)
    assert count == 1
    assert overall == "MISMATCH"
    assert comps["scores_match"] == "MISMATCH"

def test_partial_success_produces_inconclusive():
    # Two successful runs, both matching, but 3 failed (attempted_runs = 5 by default)
    runs = [get_base_run() for _ in range(2)]
    overall, count, comps = compare_runs(runs)
    assert count == 1
    assert overall == "INCONCLUSIVE (Only 2/5 successful runs)"
    # The comparisons of the available runs should be matching
    assert comps["scores_match"] == "MATCH"
    assert comps["words_match"] == "MATCH"
    assert comps["regions_match"] == "MATCH"
    assert comps["evidence_hashes_match"] == "MATCH"
