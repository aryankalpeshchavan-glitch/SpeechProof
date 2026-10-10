import json
import time
import os
import hashlib
import traceback
from typing import List, Dict, Any, Tuple
from pathlib import Path
import scipy.stats as stats
import numpy as np

from speechproof.pipeline import SpeechProofScorer
from inject.pace import inject_pace
from inject.volume import inject_volume

def get_file_sha256(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def spearman_with_ci(x: List[float], y: List[float], confidence=0.95) -> Tuple[float, float, float, float]:
    """Calculate Spearman correlation and its confidence interval via Fisher transformation."""
    if len(x) < 3 or len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return np.nan, np.nan, np.nan, np.nan
        
    rho, p_value = stats.spearmanr(x, y)
    
    # Fisher transform for CI
    if abs(rho) == 1.0:
        return rho, p_value, rho, rho
        
    z = np.arctanh(rho)
    se = 1.0 / np.sqrt(len(x) - 3)
    z_crit = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    ci_lower = np.tanh(z - z_crit * se)
    ci_upper = np.tanh(z + z_crit * se)
    
    return rho, p_value, ci_lower, ci_upper

def run_t2():
    audio_path = "data/real/aryan_test.wav"
    print(f"Starting T2 - Dose-Response Evaluation on {audio_path}")
    
    if not Path(audio_path).exists():
        print(f"BLOCKER: Authorized recording {audio_path} is missing.")
        return

    scorer = SpeechProofScorer()
    os.makedirs("eval/outputs/t2_injected", exist_ok=True)
    
    results_summary = {
        "experiment_id": "T2-Dose-Response",
        "interventions": {}
    }
    
    raw_artifacts = []

    # 1. Pace Injection
    print("\n--- Pace Injection ---")
    pace_strengths = [0.7, 0.85, 1.0, 1.15, 1.3]
    pace_runs = []
    
    for rate in pace_strengths:
        out_path = f"eval/outputs/t2_injected/pace_{rate:.2f}.wav"
        print(f"Applying pace rate={rate}...")
        try:
            meta = inject_pace(audio_path, out_path, rate)
            output = scorer.score(out_path)
            words = output.metadata.get("words", [])
            wpm = (len(words) / output.duration_s * 60) if output.duration_s > 0 else 0
            
            run_data = {
                "strength": rate,
                "success": True,
                "input_sha256": meta["input_sha256"],
                "output_sha256": meta["output_sha256"],
                "scores": output.scores,
                "overall_score": output.metadata.get("overall_score"),
                "wpm": wpm
            }
            pace_runs.append(run_data)
            raw_artifacts.append({"intervention": "pace", "strength": rate, "words": words, "regions": [vars(r) if hasattr(r, '__dict__') else r for r in output.regions]})
            print(f"Success. WPM: {wpm:.1f}, Pace Score: {output.scores.get('pace')}")
        except Exception as e:
            print(f"Failed rate={rate}: {e}")
            pace_runs.append({"strength": rate, "success": False, "error": str(e)})

    # Analyze Pace
    successful_pace = [r for r in pace_runs if r["success"]]
    if len(successful_pace) > 2:
        x_pace = [r["strength"] for r in successful_pace]
        y_wpm = [r["wpm"] for r in successful_pace]
        
        rho_wpm, p_wpm, ci_l_wpm, ci_u_wpm = spearman_with_ci(x_pace, y_wpm)
        
        pace_analysis = {
            "attempted": len(pace_strengths),
            "successful": len(successful_pace),
            "failed": len(pace_strengths) - len(successful_pace),
            "expected_direction": "Positive correlation between rate_multiplier and Measured WPM.",
            "spearman_wpm_rho": rho_wpm,
            "spearman_wpm_p_value": p_wpm,
            "spearman_wpm_ci_95": [ci_l_wpm, ci_u_wpm],
            "conclusion": "INCONCLUSIVE" if np.isnan(rho_wpm) else "COMPLETED",
            "runs": pace_runs
        }
    else:
        pace_analysis = {"attempted": len(pace_strengths), "successful": len(successful_pace), "conclusion": "INCONCLUSIVE"}
        
    results_summary["interventions"]["pace"] = pace_analysis

    # 2. Volume Injection
    print("\n--- Volume Injection ---")
    volume_strengths = [-12.0, -6.0, 0.0, 6.0, 12.0]
    volume_runs = []
    
    for gain in volume_strengths:
        out_path = f"eval/outputs/t2_injected/volume_{gain:.1f}dB.wav"
        print(f"Applying volume gain={gain}dB...")
        try:
            meta = inject_volume(audio_path, out_path, gain)
            output = scorer.score(out_path)
            
            run_data = {
                "strength": gain,
                "success": True,
                "input_sha256": meta["input_sha256"],
                "output_sha256": meta["output_sha256"],
                "clipping_occurred": meta["clipping_occurred"],
                "scores": output.scores,
                "overall_score": output.metadata.get("overall_score"),
            }
            volume_runs.append(run_data)
            words = output.metadata.get("words", [])
            raw_artifacts.append({"intervention": "volume", "strength": gain, "words": words, "regions": [vars(r) if hasattr(r, '__dict__') else r for r in output.regions]})
            print(f"Success. Energy Score: {output.scores.get('energy')}, Clipping: {meta['clipping_occurred']}")
        except Exception as e:
            print(f"Failed gain={gain}dB: {e}")
            volume_runs.append({"strength": gain, "success": False, "error": str(e)})

    # Analyze Volume
    successful_vol = [r for r in volume_runs if r["success"]]
    if len(successful_vol) > 2:
        x_vol = [r["strength"] for r in successful_vol]
        y_energy = [r["scores"].get("energy", 0) for r in successful_vol]
        
        rho_energy, p_energy, ci_l_energy, ci_u_energy = spearman_with_ci(x_vol, y_energy)
        
        vol_analysis = {
            "attempted": len(volume_strengths),
            "successful": len(successful_vol),
            "failed": len(volume_strengths) - len(successful_vol),
            "expected_direction": "Linear correlation is NOT necessarily expected for energy standard deviation, as scaling volume may preserve relative dB variance unless clipping occurs.",
            "spearman_energy_rho": rho_energy,
            "spearman_energy_p_value": p_energy,
            "spearman_energy_ci_95": [ci_l_energy, ci_u_energy],
            "conclusion": "INCONCLUSIVE" if np.isnan(rho_energy) else "COMPLETED",
            "runs": volume_runs
        }
    else:
        vol_analysis = {"attempted": len(volume_strengths), "successful": len(successful_vol), "conclusion": "INCONCLUSIVE"}
        
    results_summary["interventions"]["volume"] = vol_analysis
    
    with open("eval/t2_results.json", "w") as f:
        json.dump(results_summary, f, indent=2)
        
    with open("eval/outputs/t2_raw_artifacts.json", "w") as f:
        json.dump(raw_artifacts, f, indent=2)
        
    print("\nT2 Dose-Response Evaluation complete.")
    print("Sanitized results saved to eval/t2_results.json")
    print("Raw artifacts saved to eval/outputs/t2_raw_artifacts.json")

if __name__ == "__main__":
    run_t2()
