import json
import os
import hashlib
from typing import Dict, Any, List
from pathlib import Path
import numpy as np

from speechproof.pipeline import SpeechProofScorer
from inject.pace import inject_pace
from inject.volume import inject_volume
from inject.pause import inject_pause

def get_file_sha256(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def score_and_extract(scorer: SpeechProofScorer, audio_path: str) -> Dict[str, Any]:
    output = scorer.score(audio_path)
    return {
        "scores": output.scores,
        "overall_score": output.metadata.get("overall_score"),
        "raw_words": output.metadata.get("words", []),
        "raw_regions": [vars(r) if hasattr(r, '__dict__') else r for r in output.regions]
    }

def compute_deltas(baseline: Dict[str, float], transformed: Dict[str, float]) -> Dict[str, float]:
    deltas = {}
    for k in baseline:
        if k in transformed and baseline[k] is not None and transformed[k] is not None:
            deltas[k] = round(transformed[k] - baseline[k], 2)
        else:
            deltas[k] = None
    return deltas

def run_t3():
    audio_path = "data/real/aryan_test.wav"
    print(f"Starting T3 - Cross-Talk Matrix on {audio_path}")

    if not Path(audio_path).exists():
        print(f"BLOCKER: Authorized recording {audio_path} is missing.")
        return

    scorer = SpeechProofScorer()
    os.makedirs("eval/outputs/t3_injected", exist_ok=True)

    # Expected primary effects
    expected_effects = {
        "pace": {"primary_target": "pace", "description": "Changing rate multiplier should directly impact the pace dimension."},
        "volume": {"primary_target": "energy", "description": "Applying volume gain directly scales audio. However, standard deviation metric might be invariant unless clipping occurs."},
        "pause": {"primary_target": "pausing", "description": "Inserting a long silence should directly penalize the pausing score."}
    }

    try:
        import subprocess
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        git_commit = "unknown"

    from speechproof.config import config

    results_summary = {
        "experiment_id": "T3-Cross-Talk",
        "metadata": {
            "git_commit": git_commit,
            "asr_model": config.asr.model_name,
            "device": config.asr.device,
            "compute_type": config.asr.compute_type
        },
        "expected_effects": expected_effects,
        "caveats": [
            "This single-recording matrix is an exploratory pilot only.",
            "Do not claim statistical significance or generalization without independent recordings.",
            "Fluency score is currently unavailable from the scorer pipeline and encoded as None."
        ],
        "interpretations": {
            "pace": "Pace at 1.15x produced no pace-score change because the score remained at 100.",
            "volume": "Volume at -6 dB left energy unchanged but changed pausing. Do not infer a proven cause for the volume-related pausing change.",
            "pause": "The two-second pause reduced the pausing score by 36.38 points."
        },
        "conditions": []
    }
    raw_artifacts = []

    # 0. Baseline
    print("\n--- Scoring Baseline ---")
    baseline_sha256 = get_file_sha256(audio_path)
    try:
        baseline_res = score_and_extract(scorer, audio_path)
        baseline_scores = baseline_res["scores"].copy()
        baseline_scores["overall"] = baseline_res["overall_score"]

        # Explicitly add fluency as None
        baseline_scores["fluency"] = None

        results_summary["baseline"] = {
            "input_sha256": baseline_sha256,
            "scores": baseline_scores
        }
        raw_artifacts.append({"condition": "baseline", "words": baseline_res["raw_words"], "regions": baseline_res["raw_regions"]})
        print(f"Baseline scored successfully: {baseline_scores}")
    except Exception as e:
        print(f"Failed to score baseline: {e}")
        return

    interventions = [
        {"type": "pace", "dose": 1.15},
        {"type": "volume", "dose": -6.0},
        {"type": "pause", "dose": 2.0} # 2 second pause
    ]

    for intervention in interventions:
        itype = intervention["type"]
        dose = intervention["dose"]
        print(f"\n--- Applying {itype} intervention (dose: {dose}) ---")

        out_path = f"eval/outputs/t3_injected/{itype}_{dose}.wav"
        success = False
        clipping = False
        error_msg = None

        try:
            if itype == "pace":
                meta = inject_pace(audio_path, out_path, dose)
                clipping = meta.get("clipping_occurred", False)
            elif itype == "volume":
                meta = inject_volume(audio_path, out_path, dose)
                clipping = meta.get("clipping_occurred", False)
            elif itype == "pause":
                # Use a safe position between "Aryan." and "Today,"
                inject_pause(audio_path, out_path, pause_sec=dose, position_sec=2.70)
                clipping = False

            out_sha256 = get_file_sha256(out_path)
            res = score_and_extract(scorer, out_path)

            scores = res["scores"].copy()
            scores["overall"] = res["overall_score"]
            scores["fluency"] = None

            deltas = compute_deltas(baseline_scores, scores)

            success = True
            raw_artifacts.append({"condition": f"{itype}_{dose}", "words": res["raw_words"], "regions": res["raw_regions"]})
            print(f"Success. Deltas: {deltas}")
        except Exception as e:
            error_msg = str(e)
            print(f"Failed: {error_msg}")

        condition_data = {
            "intervention": itype,
            "dose": dose,
            "success": success,
            "clipping_occurred": clipping,
            "error": error_msg,
            "input_sha256": baseline_sha256,
            "output_sha256": out_sha256 if success else None,
            "scores": scores if success else None,
            "deltas": deltas if success else None
        }
        if itype == "pause":
            condition_data["pause_insertion_position_sec"] = 2.70
            condition_data["pause_duration_sec"] = dose

        results_summary["conditions"].append(condition_data)

    with open("eval/t3_results.json", "w") as f:
        json.dump(results_summary, f, indent=2, allow_nan=False)

    with open("eval/outputs/t3_raw_artifacts.json", "w") as f:
        json.dump(raw_artifacts, f, indent=2, allow_nan=False)

    print("\nT3 Cross-Talk Evaluation complete.")
    print("Sanitized results saved to eval/t3_results.json")
    print("Raw artifacts saved to eval/outputs/t3_raw_artifacts.json")

if __name__ == "__main__":
    run_t3()
