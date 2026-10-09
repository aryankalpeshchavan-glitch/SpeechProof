import sqlite3
import os
import subprocess
from contracts.scorer_protocol import ScorerProtocol

class CrashTestLab:
    def __init__(self, db_path: str = "db/ledger.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # Initialize schema if missing
        with sqlite3.connect(self.db_path) as conn:
            with open("db/schema.sql") as f:
                conn.executescript(f.read())

    def _get_git_sha(self) -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        except:
            return "unknown"

    def run_battery(self, scorer: ScorerProtocol, dataset: str, audio_paths: list[str]):
        git_sha = self._get_git_sha()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for path in audio_paths:
                try:
                    output = scorer.score(path)
                except Exception as e:
                    print(f"Skipping recording {path} due to scoring error: {e}")
                    continue

                # validate
                if not getattr(output, "scorer_name", None):
                    raise ValueError(f"Invalid contract output from scorer on {path}")

                # Read from metadata since they are not top-level attributes
                metadata = output.metadata or {}
                rubric_version = metadata.get("rubric_version", "unknown")
                overall_score = metadata.get("overall_score")

                cursor.execute(
                    "INSERT INTO runs (audio_file, rubric_version, scorer_name, scorer_version, git_sha, dataset_id, overall_score, sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (path, rubric_version, output.scorer_name, output.scorer_version, git_sha, dataset, overall_score, output.audio_sha256)
                )
                run_id = cursor.lastrowid

                # Insert the five scores
                for dimension in ["pace", "pausing", "fluency", "pitch", "energy"]:
                    val = output.scores.get(dimension)
                    if val is not None:
                        cursor.execute(
                            "INSERT INTO scores (run_id, dimension, score, penalty) VALUES (?, ?, ?, ?)",
                            (run_id, dimension, val, 0.0)
                        )
            conn.commit()

