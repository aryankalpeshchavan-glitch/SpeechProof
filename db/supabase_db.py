import os
from dotenv import load_dotenv

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in .env")
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client



def save_run(evidence):
    # 1. Save the main run
    run_data = {
        "audio_file": evidence["audio_file"],
        "rubric_version": evidence["rubric_version"],
        "overall_score": evidence.get("overall_score"),
        "sha256": evidence["sha256"]
    }

    supabase = get_supabase_client()
    run_response = (
        supabase
        .table("runs")
        .insert(run_data)
        .execute()
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
        get_supabase_client().table("scores").insert(score_rows).execute()

    # 3. Save the measured features
    feature_rows = []

    for name, value in evidence["features"].items():
        if isinstance(value, (int, float)):
            feature_rows.append({
                "run_id": run_id,
                "feature_name": name,
                "feature_value": value
            })

    if feature_rows:
        get_supabase_client().table("features").insert(feature_rows).execute()

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
        get_supabase_client().table("words").insert(word_rows).execute()

    print(f"Saved SpeechProof run successfully!")
    print(f"run_id = {run_id}")

    return run_id


if __name__ == "__main__":
    supabase = get_supabase_client()
    print("Supabase connection successful!")

    response = (
        supabase
        .table("runs")
        .select("*")
        .limit(1)
        .execute()
    )

    print(response.data)