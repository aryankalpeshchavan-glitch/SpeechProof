CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY,
    audio_file TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    scorer_name TEXT,
    scorer_version TEXT,
    git_sha TEXT,
    dataset_id TEXT,
    overall_score REAL,
    sha256 TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS scores (
    run_id INTEGER,
    dimension TEXT NOT NULL,
    score REAL NOT NULL,
    penalty REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS features (
    run_id INTEGER,
    feature_name TEXT NOT NULL,
    feature_value REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS words (
    run_id INTEGER,
    word TEXT,
    start REAL,
    end REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
