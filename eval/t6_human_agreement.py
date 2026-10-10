import json
def run():
    res = {'test_id': 'T6', 'status': 'NOT_RUN', 'reason': 'No human rating data available', 'metric': 'rho'}
    with open('eval/t6_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
if __name__ == '__main__': run()
