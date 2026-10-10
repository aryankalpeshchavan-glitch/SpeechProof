import json
from typing import List, Dict, Optional

def evaluate_gaming_attack(trials: List[Dict]) -> dict:
    attempted = len(trials)
    successful_transforms = 0
    gaming_successes = 0
    evaluable = 0
    unknown = 0
    
    for t in trials:
        if not t.get('transform_success', False):
            continue
        successful_transforms += 1
        
        mdc95 = t.get('mdc95')
        delta = t.get('score_after', 0) - t.get('score_before', 0)
        
        if mdc95 is None:
            unknown += 1
            continue
            
        evaluable += 1
        flaw_changed = t.get('flaw_changed', None)
        
        if flaw_changed is None:
            unknown += 1
            continue
            
        if not flaw_changed and delta > mdc95:
            gaming_successes += 1
            
    success_rate = gaming_successes / evaluable if evaluable > 0 else None
    
    return {
        "attempted": attempted,
        "transform_success": successful_transforms,
        "evaluable": evaluable,
        "unknown": unknown,
        "gaming_successes": gaming_successes,
        "success_rate": success_rate
    }

def run():
    print("Running T9 Gaming...")
    res = {
        'test_id': 'T9',
        'status': 'INCONCLUSIVE',
        'reason': 'Dependent on T8 MDC95 which is INCONCLUSIVE',
        'metric': 'Attack_Success_Rate',
        'value': None,
        'limitations': ['No MDC95']
    }
    with open('eval/t9_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)

if __name__ == '__main__':
    run()
