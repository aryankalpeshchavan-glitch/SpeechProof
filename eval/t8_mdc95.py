import json
def run():
    res = {'test_id': 'T8', 'status': 'INCONCLUSIVE', 'reason': 'No repeated takes to calculate MDC95', 'metric': 'MDC95'}
    with open('eval/t8_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
if __name__ == '__main__': run()
