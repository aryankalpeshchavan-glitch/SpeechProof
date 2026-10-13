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
    """
    Calculates Intraclass Correlation Coefficient ICC(2,k):
    Two-way random effects, absolute agreement, average of k raters (Shrout & Fleiss, 1979).
    ratings: n x k matrix where rows are targets and columns are raters.
    """
    if not ratings or len(ratings) < 2:
        return None
    k = len(ratings[0])
    if k < 2:
        return None
    for row in ratings:
        if len(row) != k:
            return None

    n = len(ratings)
    total_ratings = n * k
    grand_mean = sum(val for row in ratings for val in row) / total_ratings

    row_means = [sum(row) / k for row in ratings]
    col_means = [sum(ratings[i][j] for i in range(n)) / n for j in range(k)]

    ssr = k * sum((rm - grand_mean) ** 2 for rm in row_means)
    msr = ssr / (n - 1)

    ssc = n * sum((cm - grand_mean) ** 2 for cm in col_means)
    msc = ssc / (k - 1)

    sst = sum((val - grand_mean) ** 2 for row in ratings for val in row)
    sse = max(0.0, sst - ssr - ssc)
    df_e = (n - 1) * (k - 1)
    if df_e <= 0:
        return None
    mse = sse / df_e

    denominator = msr + (msc - mse) / n
    if denominator == 0:
        return 0.0 if (msr - mse) == 0 else None

    icc = (msr - mse) / denominator
    return float(icc)

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
