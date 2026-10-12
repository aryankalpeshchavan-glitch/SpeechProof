
import sys

from db.supabase_db import supabase
from speechproof.evidence import sha256_json

# Use the supplied run ID, or default to Run 22
RUN_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 22

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
integrity_ok = sha256_json(evidence) == stored_hash

print("Run ID:", row["run_id"])
print("Integrity check:", integrity_ok)

# Test tampering on a copy without changing the database
modified = dict(evidence)
modified["overall_score"] = 0

tampering_detected = sha256_json(modified) != stored_hash
print("Tampering detected:", tampering_detected)
