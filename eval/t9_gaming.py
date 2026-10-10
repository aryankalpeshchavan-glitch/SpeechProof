import json
def run():
    res = {'test_id': 'T9', 'status': 'INCONCLUSIVE', 'reason': 'Dependent on T8 MDC95 which is INCONCLUSIVE', 'metric': 'Attack_Success_Rate'}
    with open('eval/t9_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
if __name__ == '__main__': run()
