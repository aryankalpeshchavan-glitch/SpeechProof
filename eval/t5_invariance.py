import json
def run():
    res = {'test_id': 'T5', 'status': 'INCONCLUSIVE', 'reason': 'Equivalence margin undefined (N=1)', 'metric': 'TOST'}
    with open('eval/t5_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
if __name__ == '__main__': run()
