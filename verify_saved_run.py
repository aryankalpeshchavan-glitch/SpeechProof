
from db.supabase_db import supabase
from speechproof.evidence import sha256_json

RUN_ID = 11

row = (
    supabase.table("runs")
    .select("run_id, sha256, evidence_json")
    .eq("run_id", RUN_ID)
    .single()
    .execute()
).data

evidence = row["evidence_json"]
stored_hash = row["sha256"]

# Verify the saved evidence
print("Run ID:", row["run_id"])
print("Integrity check:", sha256_json(evidence) == stored_hash)

# Test tampering on a copy, without changing the database
modified = dict(evidence)
modified["overall_score"] = 0

print("Tampering detected:", sha256_json(modified) != stored_hash)