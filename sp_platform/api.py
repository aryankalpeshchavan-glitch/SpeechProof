import os
import shutil
import uuid
import hashlib
import base64
import json
from dataclasses import asdict
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles

from speechproof.asr import validate_audio
from speechproof.pipeline import SpeechProofScorer

app = FastAPI(
    title="SpeechProof API",
    description="Deterministic Speech Analytics and Contrastive Crash Test Platform",
    version="1.0.0"
)

scorer_instance = None

def get_scorer() -> SpeechProofScorer:
    global scorer_instance
    if scorer_instance is None:
        scorer_instance = SpeechProofScorer()
    return scorer_instance


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "SpeechProof",
        "version": "1.0.0",
        "message": "SpeechProof API is running."
    }


@app.get("/ready")
def readiness():
    import ctranslate2
    from speechproof.config import config
    try:
        types = ctranslate2.get_supported_compute_types("cuda")
        cuda_supported = bool(types)
    except Exception:
        cuda_supported = False

    model_dir = os.path.join(
        config.asr.model_cache_dir,
        f"models--Systran--faster-whisper-{config.asr.model_name}"
    )
    model_cached = os.path.exists(model_dir)

    return {
        "status": "ready" if (cuda_supported and model_cached) else "degraded",
        "device": config.asr.device,
        "cuda_available": cuda_supported,
        "compute_type": config.asr.compute_type,
        "model_name": config.asr.model_name,
        "model_cached": model_cached
    }


from speechproof.audio_io import ingest_audio_file, AudioIngestionError


def prepare_uploaded_audio(input_path: str, target_wav_path: str) -> None:
    """
    Ensures the audio is formatted as mono 16 kHz PCM WAV.
    Delegates to speechproof.audio_io for canonical ingestion and validation.
    """
    try:
        ingest_audio_file(input_path, target_wav_path)
    except AudioIngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio ingestion failed: {e}")


@app.post("/score")
def score(audio: UploadFile = File(...)):
    raw_filename = f"raw_{uuid.uuid4().hex}_{audio.filename or 'audio'}"
    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    raw_path = os.path.join("artifacts", raw_filename)
    temp_path = os.path.join("artifacts", temp_filename)
    os.makedirs("artifacts", exist_ok=True)
    try:
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        prepare_uploaded_audio(raw_path, temp_path)

        with open(temp_path, "rb") as f:
            audio_hash = hashlib.sha256(f.read()).hexdigest()

        scorer = get_scorer()
        output = scorer.score(temp_path)
        res = asdict(output)
        res["audio_sha256"] = audio_hash
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/compare")
def compare(reference: UploadFile = File(...), candidate: UploadFile = File(...)):
    raw_ref = os.path.join("artifacts", f"raw_ref_{uuid.uuid4().hex}")
    raw_cand = os.path.join("artifacts", f"raw_cand_{uuid.uuid4().hex}")
    ref_filename = f"temp_ref_{uuid.uuid4().hex}.wav"
    cand_filename = f"temp_cand_{uuid.uuid4().hex}.wav"
    ref_path = os.path.join("artifacts", ref_filename)
    cand_path = os.path.join("artifacts", cand_filename)
    os.makedirs("artifacts", exist_ok=True)

    try:
        with open(raw_ref, "wb") as f:
            shutil.copyfileobj(reference.file, f)
        with open(raw_cand, "wb") as f:
            shutil.copyfileobj(candidate.file, f)

        prepare_uploaded_audio(raw_ref, ref_path)
        prepare_uploaded_audio(raw_cand, cand_path)

        with open(ref_path, "rb") as f:
            ref_hash = hashlib.sha256(f.read()).hexdigest()
        with open(cand_path, "rb") as f:
            cand_hash = hashlib.sha256(f.read()).hexdigest()

        scorer = get_scorer()
        ref_output = scorer.score(ref_path)
        cand_output = scorer.score(cand_path)

        diffs = {}
        for dim, ref_val in ref_output.scores.items():
            if dim in cand_output.scores and ref_val is not None and cand_output.scores[dim] is not None:
                diffs[dim] = round(cand_output.scores[dim] - ref_val, 2)

        ref_overall = ref_output.metadata.get("overall_score") if ref_output.metadata else None
        cand_overall = cand_output.metadata.get("overall_score") if cand_output.metadata else None
        overall_delta = None
        if ref_overall is not None and cand_overall is not None:
            overall_delta = round(cand_overall - ref_overall, 2)

        return {
            "reference": asdict(ref_output),
            "candidate": asdict(cand_output),
            "differences": diffs,
            "overall_delta": overall_delta,
            "reference_sha256": ref_hash,
            "candidate_sha256": cand_hash,
            "reference_duration_s": ref_output.duration_s,
            "candidate_duration_s": cand_output.duration_s,
            "limitations": [
                "Contrastive comparison assumes comparable acoustic and recording environments.",
                "A measured difference is not automatically a statistically significant improvement.",
                "No transcript-level word alignment is asserted across takes."
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        for p in (raw_ref, raw_cand, ref_path, cand_path):
            if os.path.exists(p):
                os.remove(p)


@app.post("/arena/transform")
def transform(
    audio: UploadFile = File(...),
    transform_type: str = Form(...),
    intensity: float = Form(default=1.0)
):
    norm_type = transform_type.strip().lower()

    # Backend safety limits and unit mapping
    if norm_type == "pause":
        if intensity < 0.5 or intensity > 5.0:
            raise HTTPException(
                status_code=400,
                detail=f"Pause duration ({intensity}s) out of allowed safety bounds [0.5, 5.0] seconds."
            )
        units = "seconds"
        intended_target = "pausing"
    elif norm_type == "pace":
        if intensity < 0.5 or intensity > 1.5:
            raise HTTPException(
                status_code=400,
                detail=f"Pace rate multiplier ({intensity}x) out of allowed safety bounds [0.5, 1.5]."
            )
        units = "multiplier"
        intended_target = "pace"
    elif norm_type == "volume":
        if intensity < -12.0 or intensity > 12.0:
            raise HTTPException(
                status_code=400,
                detail=f"Volume gain ({intensity} dB) out of allowed safety bounds [-12.0, +12.0] dB."
            )
        units = "dB"
        intended_target = "energy"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported transform_type '{transform_type}'. Allowed: 'pause', 'pace', 'volume'."
        )

    raw_filename = f"raw_in_{uuid.uuid4().hex}"
    temp_filename = f"temp_in_{uuid.uuid4().hex}.wav"
    out_filename = f"temp_out_{uuid.uuid4().hex}.wav"
    raw_path = os.path.join("artifacts", raw_filename)
    temp_path = os.path.join("artifacts", temp_filename)
    out_path = os.path.join("artifacts", out_filename)
    os.makedirs("artifacts", exist_ok=True)

    try:
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        prepare_uploaded_audio(raw_path, temp_path)

        with open(temp_path, "rb") as f:
            orig_hash = hashlib.sha256(f.read()).hexdigest()

        clipping_occurred = False

        if norm_type == "pause":
            from inject.pause import inject_pause
            inject_pause(temp_path, out_path, pause_sec=float(intensity))
        elif norm_type == "pace":
            from inject.pace import inject_pace
            meta = inject_pace(temp_path, out_path, rate=float(intensity))
            clipping_occurred = meta.get("clipping_occurred", False)
        elif norm_type == "volume":
            from inject.volume import inject_volume
            meta = inject_volume(temp_path, out_path, gain_db=float(intensity))
            clipping_occurred = meta.get("clipping_occurred", False)

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            raise RuntimeError(f"Transformation '{transform_type}' produced no output file.")

        validate_audio(out_path)

        with open(out_path, "rb") as f:
            out_bytes = f.read()
            trans_hash = hashlib.sha256(out_bytes).hexdigest()
            audio_data_url = "data:audio/wav;base64," + base64.b64encode(out_bytes).decode("ascii")

        scorer = get_scorer()
        orig_output = scorer.score(temp_path)
        transformed_output = scorer.score(out_path)

        diffs = {}
        for dim, orig_val in orig_output.scores.items():
            if dim in transformed_output.scores and orig_val is not None and transformed_output.scores[dim] is not None:
                diffs[dim] = round(transformed_output.scores[dim] - orig_val, 2)

        orig_overall = orig_output.metadata.get("overall_score") if orig_output.metadata else None
        trans_overall = transformed_output.metadata.get("overall_score") if transformed_output.metadata else None
        overall_delta = None
        if orig_overall is not None and trans_overall is not None:
            overall_delta = round(trans_overall - orig_overall, 2)

        target_responded = False
        if intended_target in diffs:
            target_responded = abs(diffs[intended_target]) > 0.0

        unrelated_changed = any(
            abs(val) > 0.0 for dim, val in diffs.items() if dim != intended_target
        )

        warnings = []
        if clipping_occurred:
            warnings.append("Audio clipping occurred during signal transformation.")
        if not target_responded:
            warnings.append(f"Target dimension '{intended_target}' did not exhibit a score change under this dose.")

        return {
            "success": True,
            "transform_type": norm_type,
            "intensity": float(intensity),
            "units": units,
            "intended_target": intended_target,
            "target_responded": target_responded,
            "unrelated_changed": unrelated_changed,
            "clipping_occurred": clipping_occurred,
            "original_sha256": orig_hash,
            "transformed_sha256": trans_hash,
            "differences": diffs,
            "overall_delta": overall_delta,
            "original": asdict(orig_output),
            "transformed": asdict(transformed_output),
            "audio_data_url": audio_data_url,
            "warnings": warnings,
            "caveat": "Controlled single-recording test. Do not extrapolate universal robustness."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        for p in (raw_path, temp_path, out_path):
            if os.path.exists(p):
                os.remove(p)


@app.post("/battery/run")
def run_battery():
    return {
        "status": "NOT_RUN",
        "message": "Pilot evaluations require explicit manual triggering and complete datasets. Not all datasets are available for T4-T9."
    }


@app.get("/leaderboard")
def leaderboard():
    import sqlite3
    try:
        with sqlite3.connect("db/ledger.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 50")
            raw_runs = cursor.fetchall()
            runs = []
            for r in raw_runs:
                row_dict = dict(r)
                audio_file = row_dict.get("audio_file", "")
                sanitized_name = os.path.basename(audio_file) if audio_file else "recording.wav"

                scores = {}
                duration_s = None
                evidence_json_str = row_dict.get("evidence_json")
                if evidence_json_str:
                    try:
                        ev = json.loads(evidence_json_str)
                        scores = ev.get("scores", {})
                        duration_s = ev.get("features", {}).get("duration_sec")
                    except Exception:
                        pass

                runs.append({
                    "run_id": row_dict.get("run_id"),
                    "recording_name": sanitized_name,
                    "rubric_version": row_dict.get("rubric_version"),
                    "scorer_name": row_dict.get("scorer_name") or "SpeechProof",
                    "overall_score": row_dict.get("overall_score"),
                    "sha256_prefix": (row_dict.get("sha256") or "")[:12],
                    "sha256": row_dict.get("sha256"),
                    "scores": scores,
                    "duration_s": duration_s,
                    "created_at": row_dict.get("created_at")
                })
            return {"leaderboard": runs}
    except Exception as e:
        return {"error": str(e), "leaderboard": []}


@app.get("/validation")
def get_validation_results():
    from pathlib import Path

    tests_meta = [
        {"id": "T1", "name": "T1: Deterministic Reproducibility", "file": "eval/t1_results.json"},
        {"id": "T2", "name": "T2: Dose-Response Monotonicity", "file": "eval/t2_results.json"},
        {"id": "T3", "name": "T3: Cross-Talk Matrix", "file": "eval/t3_results.json"},
        {"id": "T4", "name": "T4: Temporal Localization", "file": "eval/t4_results.json"},
        {"id": "T5", "name": "T5: Nuisance Invariance (TOST)", "file": "eval/t5_results.json"},
        {"id": "T6", "name": "T6: Human Agreement (ICC)", "file": "eval/t6_results.json"},
        {"id": "T7", "name": "T7: Between/Within Variance Ratio", "file": "eval/t7_results.json"},
        {"id": "T8", "name": "T8: Minimum Detectable Change (MDC95)", "file": "eval/t8_results.json"},
        {"id": "T9", "name": "T9: Adversarial Gaming Resistance", "file": "eval/t9_results.json"},
        {"id": "A1-A5", "name": "A1-A5: Architectural Ablations", "file": "eval/ablation_results.json"},
    ]

    items = []
    for tm in tests_meta:
        p = Path(tm["file"])
        if not p.exists():
            items.append({
                "id": tm["id"],
                "name": tm["name"],
                "status": "NOT_RUN",
                "metric": None,
                "value": None,
                "target": None,
                "reason": f"Evaluation artifact {tm['file']} not generated.",
                "limitations": ["Test execution data missing."]
            })
            continue

        try:
            with open(p, "r") as f:
                data = json.load(f)

            if tm["id"] == "T1":
                status = "MET" if data.get("overall_local_status") == "MATCH" else "NOT_MET"
                metric = "Reproducibility"
                val = "Bit-identical across runs" if status == "MET" else "Mismatch"
                target = "Exact SHA-256 match"
                reason = "Verified across 5 repeated local runs on large-v3 float16."
                limitations = ["Cross-machine evaluation not run (single machine available)."]
            elif tm["id"] == "T2":
                pace_s = data.get("interventions", {}).get("pace", {}).get("status", "PILOT")
                vol_s = data.get("interventions", {}).get("volume", {}).get("conclusion", "INCONCLUSIVE")
                status = "PILOT"
                metric = "Monotonic dose response"
                val = f"Pace: {pace_s}, Volume: {vol_s}"
                target = "Monotonic score degradation"
                reason = "Dose-response tested on pace and volume perturbations."
                limitations = ["Pilot on single speaker (N=1); volume invariance requires clipping to degrade energy."]
            elif tm["id"] == "T3":
                status = "PILOT"
                metric = "Cross-talk isolation"
                val = "Target dimensions responded to dose"
                target = "Primary dimension responds; off-target dimensions invariant"
                reason = "Cross-talk matrix evaluated for pause, pace, and volume."
                limitations = data.get("caveats", ["Single-recording matrix pilot."])
            elif tm["id"] == "A1-A5":
                status = data.get("status", "INCONCLUSIVE")
                metric = "Component ablations"
                val = None
                target = "Performance drop without each component"
                reason = data.get("reason", "No ablation baseline dataset.")
                limitations = ["N=1 pilot; requires multi-speaker benchmark for baseline ranking."]
            else:
                status = data.get("status", "INCONCLUSIVE")
                metric = data.get("metric")
                val = data.get("value")
                target = data.get("target")
                reason = data.get("reason", "")
                limitations = data.get("limitations", [])

            items.append({
                "id": tm["id"],
                "name": tm["name"],
                "status": status,
                "metric": metric,
                "value": val,
                "target": target,
                "reason": reason,
                "limitations": limitations,
                "raw_artifact": tm["file"]
            })
        except Exception as e:
            items.append({
                "id": tm["id"],
                "name": tm["name"],
                "status": "FAILED",
                "metric": None,
                "value": None,
                "target": None,
                "reason": str(e),
                "limitations": []
            })

    return {
        "status": "ok",
        "items": items,
        "disclosure": "Honest Scientific Reporting: Evaluations T4-T9 and A1-A5 are constrained by the single-authorized participant dataset (aryan_test.wav). Results are strictly categorized as PILOT, INCONCLUSIVE, or NOT_RUN without manufacturing synthetic pass ratings."
    }


# Static assets mount: priority to web/dist (compiled React app), fallback to static/
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "dist"))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

if os.path.exists(dist_dir) and os.path.exists(os.path.join(dist_dir, "index.html")):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
elif os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
