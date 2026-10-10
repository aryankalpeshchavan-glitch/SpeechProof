import json
import math
from typing import List, Tuple

def spearman_rho(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    x_ranks = sorted(range(n), key=lambda i: x[i])
    y_ranks = sorted(range(n), key=lambda i: y[i])
    
    x_rank_vals = [0]*n
    y_rank_vals = [0]*n
    for i, r in enumerate(x_ranks): x_rank_vals[r] = i
    for i, r in enumerate(y_ranks): y_rank_vals[r] = i
    
    d_sq = sum((x_rank_vals[i] - y_rank_vals[i])**2 for i in range(n))
    rho = 1 - (6 * d_sq) / (n * (n**2 - 1))
    return rho

def calculate_icc(ratings: List[List[float]]) -> Optional[float]:
    # Synthetic ICC(2,k) calculation
    if not ratings or len(ratings[0]) < 2:
        return None
    # For testing purposes, implement a mock ICC
    return 0.8

def run():
    print("Running T6 Human Agreement...")
    res = {
        'test_id': 'T6',
        'status': 'NOT_RUN',
        'reason': 'No human rating data available',
        'metric': 'rho',
        'value': None,
        'limitations': ['No human raters']
    }
    with open('eval/t6_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)

if __name__ == '__main__':
    run()
