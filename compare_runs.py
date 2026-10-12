
import csv
from pathlib import Path

from db.supabase_db import supabase


OUTPUT_FILE = Path("data") / "pause_comparison.csv"

# These are the known paired runs from your tests.
RUN_PAIRS = [
    {
        "test": "Pause injection comparison",
        "original_run_id": 20,
        "injected_run_id": 21,
    }
]


def get_run(run_id):
    """Fetch one run and its dimension scores from Supabase."""
    response = (
        supabase.table("runs")
        .select("run_id,audio_file,overall_score,rubric_version")
        .eq("run_id", run_id)
        .single()
        .execute()
    )

    run = response.data

    score_response = (
        supabase.table("scores")
        .select("dimension,score")
        .eq("run_id", run_id)
        .execute()
    )

    run["scores"] = {
        row["dimension"]: row["score"]
        for row in (score_response.data or [])
    }

    return run


def main():
    rows = []

    for pair in RUN_PAIRS:
        original = get_run(pair["original_run_id"])
        injected = get_run(pair["injected_run_id"])

        original_scores = original["scores"]
        injected_scores = injected["scores"]

        original_pausing = original_scores.get("pausing")
        injected_pausing = injected_scores.get("pausing")

        original_overall = original.get("overall_score")
        injected_overall = injected.get("overall_score")

        row = {
            "test": pair["test"],
            "original_run_id": original["run_id"],
            "injected_run_id": injected["run_id"],
            "original_audio": original["audio_file"],
            "injected_audio": injected["audio_file"],
            "original_overall": original_overall,
            "injected_overall": injected_overall,
            "overall_change": (
                round(injected_overall - original_overall, 2)
                if original_overall is not None
                and injected_overall is not None
                else None
            ),
            "original_pausing": original_pausing,
            "injected_pausing": injected_pausing,
            "pausing_change": (
                round(injected_pausing - original_pausing, 2)
                if original_pausing is not None
                and injected_pausing is not None
                else None
            ),
        }

        rows.append(row)

        print(f"\n{pair['test']}")
        print(f"Original run: {original['run_id']}")
        print(f"Injected run: {injected['run_id']}")
        print(f"Original overall: {original_overall}")
        print(f"Injected overall: {injected_overall}")
        print(f"Overall change: {row['overall_change']}")
        print(f"Original pausing: {original_pausing}")
        print(f"Injected pausing: {injected_pausing}")
        print(f"Pausing change: {row['pausing_change']}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nComparison CSV saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
