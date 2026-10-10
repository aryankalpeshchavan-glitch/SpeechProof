import json
import math
from typing import Dict, List

def calculate_variance_ratio(speaker_scores: Dict[str, List[float]]) -> Optional[float]:
    speakers = list(speaker_scores.keys())
    if len(speakers) < 2:
        return None
        
    all_scores = [s for takes in speaker_scores.values() for s in takes]
    global_mean = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Between-speaker variance
    between_var = sum(len(takes) * ((sum(takes)/len(takes)) - global_mean)**2 for takes in speaker_scores.values() if takes) / (len(speakers) - 1)
    
    # Within-speaker variance
    total_takes = sum(len(takes) for takes in speaker_scores.values())
    if total_takes - len(speakers) <= 0:
        return None
        
    within_var = sum(sum((s - (sum(takes)/len(takes)))**2 for s in takes) for takes in speaker_scores.values() if takes) / (total_takes - len(speakers))
    
    if within_var == 0:
        return float('inf') if between_var > 0 else 0.0
        
    return between_var / within_var

def run():
    print("Running T7 Variance...")
    res = {
        'test_id': 'T7',
        'status': 'NOT_RUN',
        'reason': 'No multiple speakers data available',
        'metric': 'variance_ratio',
        'value': None,
        'limitations': ['N=1 speaker']
    }
    with open('eval/t7_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)

if __name__ == '__main__':
    run()
