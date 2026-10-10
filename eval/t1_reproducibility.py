import json
import time
import subprocess
import hashlib
import traceback
import os
from typing import List, Dict, Any, Union
from pathlib import Path

from speechproof.pipeline import SpeechProofScorer
from speechproof.config import config

def canonical_fingerprint(data: Any) -> str:
    """Calculate a deterministic hash for comparison."""
    if data is None:
        return ""
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def run_t1():
    audio_path = "data/real/aryan_test.wav"
    print(f"Starting T1 - Reproducibility Evaluation on {audio_path}")

    if not Path(audio_path).exists():
        print(f"BLOCKER: Authorized recording {audio_path} is missing.")
        return

def compare_runs(successful_runs: List[Dict[str, Any]], attempted_runs: int = 5) -> tuple:
    comparisons = {
        "scores_match": "INCONCLUSIVE",
        "words_match": "INCONCLUSIVE",
        "regions_match": "INCONCLUSIVE",
        "evidence_hashes_match": "INCONCLUSIVE"
    }

    if len(successful_runs) == 0:
        overall_status = "FAILED (Zero successful runs)"
        actual_comparisons = 0
    elif len(successful_runs) < attempted_runs:
        overall_status = f"INCONCLUSIVE (Only {len(successful_runs)}/{attempted_runs} successful runs)"
        actual_comparisons = max(0, len(successful_runs) - 1)
        # We can still run the comparisons to report them, but overall is INCONCLUSIVE
        reference = successful_runs[0]

        scores_match = True
        words_match = True
        regions_match = True
        hashes_match = True

        for r in successful_runs[1:]:
            if r.get("scores") != reference.get("scores") or r.get("overall_score") != reference.get("overall_score"):
                scores_match = False
            if r.get("word_fingerprint") != reference.get("word_fingerprint"):
                words_match = False
            if r.get("region_fingerprint") != reference.get("region_fingerprint") or r.get("region_count") != reference.get("region_count"):
                regions_match = False
            if r.get("evidence_sha256") != reference.get("evidence_sha256"):
                hashes_match = False

        if actual_comparisons > 0:
            comparisons["scores_match"] = "MATCH" if scores_match else "MISMATCH"
            comparisons["words_match"] = "MATCH" if words_match else "MISMATCH"
            comparisons["regions_match"] = "MATCH" if regions_match else "MISMATCH"
            comparisons["evidence_hashes_match"] = "MATCH" if hashes_match else "MISMATCH"
    else:
        reference = successful_runs[0]
        actual_comparisons = len(successful_runs) - 1

        scores_match = True
        words_match = True
        regions_match = True
        hashes_match = True

        for r in successful_runs[1:]:
            if r.get("scores") != reference.get("scores") or r.get("overall_score") != reference.get("overall_score"):
                scores_match = False
            if r.get("word_fingerprint") != reference.get("word_fingerprint"):
                words_match = False
            if r.get("region_fingerprint") != reference.get("region_fingerprint") or r.get("region_count") != reference.get("region_count"):
                regions_match = False
            if r.get("evidence_sha256") != reference.get("evidence_sha256"):
                hashes_match = False

        comparisons["scores_match"] = "MATCH" if scores_match else "MISMATCH"
        comparisons["words_match"] = "MATCH" if words_match else "MISMATCH"
        comparisons["regions_match"] = "MATCH" if regions_match else "MISMATCH"
        comparisons["evidence_hashes_match"] = "MATCH" if hashes_match else "MISMATCH"

        if not (scores_match and words_match and regions_match and hashes_match):
            overall_status = "MISMATCH"
        else:
            overall_status = "MATCH"

    return overall_status, actual_comparisons, comparisons

def run_t1():
    audio_path = "data/real/aryan_test.wav"
    print(f"Starting T1 - Reproducibility Evaluation on {audio_path}")

    if not Path(audio_path).exists():
        print(f"BLOCKER: Authorized recording {audio_path} is missing.")
        return

    with open(audio_path, 'rb') as f:
        input_audio_sha256 = hashlib.sha256(f.read()).hexdigest()

    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        git_commit = "unknown"

    experiment_metadata = {
        "experiment_id": "T1-Reproducibility",
        "input_audio_sha256": input_audio_sha256,
        "scorer_version": "1.0.0",
        "rubric_version": "rubric-v0.1",
        "git_commit": git_commit,
        "asr_model": config.asr.model_name,
        "device": config.asr.device,
        "compute_type": config.asr.compute_type,
        "start_time": time.time()
    }

    print("Metadata:", experiment_metadata)

    runs_data = []
    successful_runs = []
    failed_runs = 0
    scorer = SpeechProofScorer()

    for i in range(5):
        run_idx = i + 1
        print(f"Executing run {run_idx}/5...")
        run_start = time.time()

        run_record = {
            "run_index": run_idx,
            "success": False,
            "elapsed_time_s": 0.0,
            "audio_sha256": input_audio_sha256,
            "scorer_version": experiment_metadata["scorer_version"],
            "rubric_version": experiment_metadata["rubric_version"],
            "git_commit": experiment_metadata["git_commit"],
            "asr_model": experiment_metadata["asr_model"],
            "device": experiment_metadata["device"],
            "compute_type": experiment_metadata["compute_type"],
        }

        try:
            output = scorer.score(audio_path)
            run_end = time.time()

            words = output.metadata.get("words", [])
            words_fingerprint = canonical_fingerprint(words)

            regions = [vars(r) if hasattr(r, '__dict__') else r for r in output.regions]
            regions_fingerprint = canonical_fingerprint(regions)

            run_record.update({
                "success": True,
                "elapsed_time_s": run_end - run_start,
                "scores": output.scores,
                "overall_score": output.metadata.get("overall_score"),
                "duration_s": output.duration_s,
                "evidence_sha256": output.metadata.get("evidence_sha256"),
                "word_fingerprint": words_fingerprint,
                "region_count": len(output.regions),
                "region_fingerprint": regions_fingerprint,
                "raw_words": words, # Kept for raw artifact
                "raw_regions": regions # Kept for raw artifact
            })

            runs_data.append(run_record)
            successful_runs.append(run_record)
            print(f"Run {run_idx} completed successfully.")
        except Exception as e:
            run_end = time.time()
            run_record.update({
                "success": False,
                "elapsed_time_s": run_end - run_start,
                "error_category": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            })
            runs_data.append(run_record)
            failed_runs += 1
            print(f"Run {run_idx} failed: {e}")

    # Save raw outputs (ignored in git)
    os.makedirs("eval/outputs", exist_ok=True)
    with open("eval/outputs/t1_raw_runs.json", "w") as f:
        json.dump({"metadata": experiment_metadata, "runs": runs_data}, f, indent=2)

    print("\n--- Reproducibility Checks ---")
    overall_status, actual_comparisons, comparisons = compare_runs(successful_runs)

    print(f"Status: {overall_status}")
    print(f"Comparisons performed: {actual_comparisons}")
    for k, v in comparisons.items():
        print(f"{k}: {v}")

    # Prepare sanitized summary report
    sanitized_runs = []
    for r in runs_data:
        sanitized_run = {k: v for k, v in r.items() if k not in ["raw_words", "raw_regions", "traceback"]}
        sanitized_runs.append(sanitized_run)

    summary_report = {
        "experiment": experiment_metadata,
        "execution": {
            "runs_attempted": 5,
            "runs_successful": len(successful_runs),
            "runs_failed": failed_runs,
            "actual_comparisons_performed": actual_comparisons
        },
        "reproducibility": comparisons,
        "overall_local_status": overall_status,
        "cross_machine_test": "NOT RUN (only one machine available)",
        "runs_summary": sanitized_runs
    }

    with open("eval/t1_results.json", "w") as f:
        json.dump(summary_report, f, indent=2)

    print("\nEvaluation complete. Sanitized summary saved to eval/t1_results.json")
    print("Raw artifacts saved to eval/outputs/t1_raw_runs.json")

if __name__ == "__main__":
    run_t1()
