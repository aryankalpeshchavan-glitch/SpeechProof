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
            
            # Temporary run creation just to get a run_id for now, we will update scorer name later from output
            # Alternatively we could require the scorer to report its name upfront, but we get it from score().
            # So we will run the first one to get metadata, or just wait to insert.
            
            run_id = None
            
            for path in audio_paths:
                output = scorer.score(path)
                
                # validate
                if not getattr(output, "scorer_name", None):
                    raise ValueError(f"Invalid contract output from scorer on {path}")
                    
                if run_id is None:
                    cursor.execute(
                        "INSERT INTO runs (scorer_name, scorer_version, git_sha, dataset_id) VALUES (?, ?, ?, ?)",
                        (output.scorer_name, output.scorer_version, git_sha, dataset)
                    )
                    run_id = cursor.lastrowid
                    
                cursor.execute(
                    "INSERT INTO scores (run_id, audio_sha256, pace, pausing, fluency, pitch, energy) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        run_id,
                        output.audio_sha256,
                        output.scores.get("pace"),
                        output.scores.get("pausing"),
                        output.scores.get("fluency"),
                        output.scores.get("pitch"),
                        output.scores.get("energy")
                    )
                )
            conn.commit()

