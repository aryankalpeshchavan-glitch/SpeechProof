import os
from dotenv import load_dotenv
from supabase import create_client
from speechproof.evidence import sha256_json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_run(evidence):
    # 1. Save the main run
    run_data = {
        "audio_file": evidence["audio_file"],
        "rubric_version": evidence["rubric_version"],
        "overall_score": evidence.get("overall_score"),
        "sha256": evidence["sha256"],
        "evidence_json": {
            key: value
            for key, value in evidence.items()
            if key not in ("sha256", "run_id")
        }
    }

    run_response = (
        supabase.table("runs")
        .insert(run_data)
        .select("run_id")
        .execute()
    )

    if not run_response.data or not run_response.data[0].get("run_id"):
        raise RuntimeError(
            f"Supabase did not return a valid run_id: {run_response.data}"
        )

    run_id = run_response.data[0]["run_id"]

    # 2. Save the five scores
    score_rows = []

    for dimension, score in evidence["scores"].items():
        penalty = evidence["penalties"].get(dimension, 0)

        score_rows.append({
            "run_id": run_id,
            "dimension": dimension,
            "score": score,
            "penalty": penalty
        })

    if score_rows:
        supabase.table("scores").insert(score_rows).execute()

    # 3. Save measured features
    feature_rows = []

    for name, value in evidence["features"].items():
        if isinstance(value, (int, float)):
            feature_rows.append({
                "run_id": run_id,
                "feature_name": name,
                "feature_value": value
            })

    if feature_rows:
        supabase.table("features").insert(feature_rows).execute()

    # 4. Save ASR words and timestamps
    word_rows = []

    for item in evidence.get("words", []):
        word_rows.append({
            "run_id": run_id,
            "word": item["word"],
            "start_time": item["start"],
            "end_time": item["end"]
        })

    if word_rows:
        supabase.table("words").insert(word_rows).execute()

    print("Saved SpeechProof run successfully!")
    print(f"run_id = {run_id}")

    return run_id


def verify_saved_run(run_id):
    """Verify saved evidence against its stored SHA-256 hash."""

    response = (
        supabase.table("runs")
        .select("sha256, evidence_json")
        .eq("run_id", run_id)
        .single()
        .execute()
    )

    record = response.data

    if not record or not record.get("evidence_json"):
        return False

    calculated_hash = sha256_json(record["evidence_json"])

    return calculated_hash == record["sha256"]


if __name__ == "__main__":
    print("Supabase connection successful!")

    response = (
        supabase.table("runs")
        .select("run_id")
        .limit(1)
        .execute()
    )

    print(response.data)

