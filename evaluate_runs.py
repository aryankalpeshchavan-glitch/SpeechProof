
import csv
from pathlib import Path
from collections import Counter

from db.supabase_db import supabase
from speechproof.evidence import sha256_json


OUTPUT_FILE = Path("data") / "evaluation_report.csv"


def fetch_all(table, columns):
    """Fetch all rows in batches to avoid the default row limit."""
    rows = []
    offset = 0
    batch_size = 500

    while True:
        response = (
            supabase.table(table)
            .select(columns)
            .order("run_id")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        batch = response.data or []
        rows.extend(batch)

        if len(batch) < batch_size:
            break

        offset += batch_size

    return rows


def main():
    # Fetch saved runs and their dimension scores.
    runs = fetch_all(
        "runs",
        "run_id,audio_file,rubric_version,overall_score,sha256,evidence_json"
    )

    scores = fetch_all(
        "scores",
        "run_id,dimension,score,penalty"
    )

    if not runs:
        print("No saved runs found.")
        return

    # Organize dimension scores by run ID.
    scores_by_run = {}

    for row in scores:
        scores_by_run.setdefault(row["run_id"], {})[
            row["dimension"]
        ] = row["score"]

    report = []

    # Check evidence integrity for every run.
    for run in runs:
        stored_hash = run.get("sha256")
        raw_evidence = run.get("evidence_json")

        if raw_evidence is None or raw_evidence == {}:
            integrity_status = "MISSING EVIDENCE"

        else:
            calculated_hash = sha256_json(raw_evidence)

            if calculated_hash == stored_hash:
                integrity_status = "VERIFIED"
            else:
                integrity_status = "HASH MISMATCH"

        result = {
            "run_id": run["run_id"],
            "audio_file": run.get("audio_file"),
            "rubric_version": run.get("rubric_version"),
            "overall_score": run.get("overall_score"),
            "integrity_status": integrity_status,
        }

        # Add scores for each dimension.
        for dimension, score in scores_by_run.get(
            run["run_id"], {}
        ).items():
            result[dimension] = score

        report.append(result)

        # Print details for missing or mismatched evidence.
        if integrity_status != "VERIFIED":
            print(
                f"{integrity_status}: "
                f"Run {run['run_id']} | "
                f"audio={run.get('audio_file')}"
            )

    # Export results to CSV.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "run_id",
        "audio_file",
        "rubric_version",
        "overall_score",
        "integrity_status",
        "pace",
        "pausing",
        "fluency",
        "pitch_variety",
        "vocal_energy",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(report)

    # Print summary.
    status_counts = Counter(
        row["integrity_status"] for row in report
    )

    print("\n========== SPEECHPROOF EVALUATION ==========")
    print(f"Runs evaluated: {len(report)}")
    print(f"Verified: {status_counts['VERIFIED']}")
    print(f"Missing evidence: {status_counts['MISSING EVIDENCE']}")
    print(f"Hash mismatches: {status_counts['HASH MISMATCH']}")
    print(f"CSV report saved to: {OUTPUT_FILE}")

    # Show the ten most recent runs.
    print("\nRecent runs:")

    for row in report[-10:]:
        print(
            f"Run {row['run_id']}: "
            f"score={row['overall_score']}, "
            f"integrity={row['integrity_status']}, "
            f"audio={row['audio_file']}"
        )


if __name__ == "__main__":
    main()
