import json
import math
from typing import List, Tuple, Optional

def calculate_tost(paired_diffs: List[float], equivalence_margin: float, alpha=0.05) -> dict:
    if not paired_diffs or len(paired_diffs) < 2:
        return {"status": "INCONCLUSIVE", "reason": "Insufficient observations"}
    if equivalence_margin is None or equivalence_margin <= 0:
        return {"status": "INCONCLUSIVE", "reason": "Missing or invalid margin"}
        
    n = len(paired_diffs)
    mean_diff = sum(paired_diffs) / n
    variance = sum((x - mean_diff)**2 for x in paired_diffs) / (n - 1)
    sd = math.sqrt(variance)
    se = sd / math.sqrt(n) if n > 0 else float('inf')
    
    if se == 0:
        t1 = float('inf') if mean_diff + equivalence_margin > 0 else float('-inf')
        t2 = float('-inf') if mean_diff - equivalence_margin < 0 else float('inf')
    else:
        t1 = (mean_diff + equivalence_margin) / se
        t2 = (mean_diff - equivalence_margin) / se
        
    # Simplified p-value logic since we can't use scipy easily. Using approximation or just t-value check
    # For a large n, critical t is approx 1.645 for alpha=0.05. We will just return the stats.
    # To pass TOST, we need t1 > t_crit and t2 < -t_crit.
    t_crit = 1.645 # Approximation
    passed = (t1 > t_crit) and (t2 < -t_crit)
    
    return {
        "status": "MET" if passed else "NOT_MET",
        "mean_diff": mean_diff,
        "sd": sd,
        "se": se,
        "t1": t1,
        "t2": t2,
        "margin": equivalence_margin,
        "n": n
    }

def run():
    print("Running T5 Invariance...")
    # No repeated takes in N=1
    res = {
        'test_id': 'T5',
        'status': 'INCONCLUSIVE',
        'reason': 'Equivalence margin undefined (N=1, no repeated takes)',
        'metric': 'TOST',
        'value': None,
        'limitations': ['N=1 pilot']
    }
    with open('eval/t5_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)

if __name__ == '__main__':
    run()
