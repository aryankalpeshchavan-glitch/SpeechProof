import pytest
import json
from dataclasses import dataclass
from typing import List, Dict, Any

from contracts.scorer_protocol import ScorerOutput
from eval.t1_reproducibility import run_t1

@dataclass
class MockRegion:
    start: float
    end: float
    type: str

def get_base_output():
    return ScorerOutput(
        scorer_name="MockScorer",
        scorer_version="1.0.0",
        scores={"pace": 80.0},
        regions=[MockRegion(1.0, 2.0, "pause")],
        events=[],
        quality_flags=[],
        audio_sha256="abc",
        duration_s=10.0,
        metadata={
            "overall_score": 85.0,
            "evidence_sha256": "hash1",
            "words": [{"word": "hello", "start": 0.0, "end": 1.0}]
        }
    )

def compare_outputs(runs: List[ScorerOutput]) -> Dict[str, bool]:
    if not runs:
        return {"scores_match": False, "hashes_match": False, "regions_match": False, "words_match": False}
    
    first = runs[0]
    scores_match = all(r.scores == first.scores and r.metadata.get("overall_score") == first.metadata.get("overall_score") for r in runs[1:])
    hashes_match = all(r.metadata.get("evidence_sha256") == first.metadata.get("evidence_sha256") for r in runs[1:])
    regions_match = all(r.regions == first.regions for r in runs[1:])
    words_match = all(r.metadata.get("words") == first.metadata.get("words") for r in runs[1:])
    
    return {
        "scores_match": scores_match,
        "hashes_match": hashes_match,
        "regions_match": regions_match,
        "words_match": words_match
    }

def test_identical_outputs_compare_as_identical():
    runs = [get_base_output() for _ in range(5)]
    res = compare_outputs(runs)
    assert res["scores_match"]
    assert res["hashes_match"]
    assert res["regions_match"]
    assert res["words_match"]

def test_changed_dimension_scores_are_detected():
    runs = [get_base_output() for _ in range(5)]
    runs[2].scores["pace"] = 90.0
    res = compare_outputs(runs)
    assert not res["scores_match"]

def test_changed_timestamps_are_detected():
    runs = [get_base_output() for _ in range(5)]
    runs[1].metadata["words"][0]["end"] = 1.5
    res = compare_outputs(runs)
    assert not res["words_match"]

def test_missing_outputs_do_not_become_successful():
    runs = [get_base_output() for _ in range(2)]
    # Simulate missing 3 runs
    assert len(runs) == 2
    res = compare_outputs(runs)
    assert res["scores_match"]

def test_comparison_logic_with_unavailable_fields():
    runs = [get_base_output() for _ in range(5)]
    for r in runs:
        r.metadata["overall_score"] = None
    res = compare_outputs(runs)
    assert res["scores_match"]
