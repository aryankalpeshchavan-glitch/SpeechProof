import json
import math
from typing import List, Tuple, Optional

def calculate_mdc95(test_retest_pairs: List[Tuple[float, float]]) -> Optional[float]:
    if not test_retest_pairs or len(test_retest_pairs) < 2:
        return None
    diffs = [take2 - take1 for take1, take2 in test_retest_pairs]
    mean_diff = sum(diffs) / len(diffs)
    variance = sum((d - mean_diff)**2 for d in diffs) / (len(diffs) - 1)
    sd = math.sqrt(variance)
    return 1.96 * sd

def improvement_gate(take1: float, take2: float, mdc95: float) -> bool:
    if mdc95 is None or mdc95 < 0:
        return False
    # True if improvement exceeds MDC95
    return (take2 - take1) > mdc95

def run():
    print("Running T8 MDC95...")
    res = {
        'test_id': 'T8',
        'status': 'INCONCLUSIVE',
        'reason': 'No repeated takes to calculate MDC95',
        'metric': 'MDC95',
        'value': None,
        'limitations': ['No test-retest pairs']
    }
    with open('eval/t8_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)

if __name__ == '__main__':
    run()
