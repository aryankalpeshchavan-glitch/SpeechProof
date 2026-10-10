import json
def run():
    res = {'test_id': 'T7', 'status': 'NOT_RUN', 'reason': 'No multiple speakers data available', 'metric': 'variance_ratio'}
    with open('eval/t7_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
if __name__ == '__main__': run()
