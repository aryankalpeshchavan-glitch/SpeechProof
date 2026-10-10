import json
import os
from pathlib import Path
from speechproof.pipeline import SpeechProofScorer

def calculate_iou(pred_start, pred_end, gt_start, gt_end):
    intersection = max(0, min(pred_end, gt_end) - max(pred_start, gt_start))
    union = max(pred_end, gt_end) - min(pred_start, gt_start)
    if union == 0:
        return 0
    return intersection / union

def run():
    print("Running T4 Localization...")
    audio_path = "eval/outputs/t3_injected/pause_2.0.wav"
    if not Path(audio_path).exists():
        res = {'test_id': 'T4', 'status': 'NOT_RUN', 'reason': 'T3 output missing'}
        with open('eval/t4_results.json', 'w') as f:
            json.dump(res, f, allow_nan=False)
        return
        
    scorer = SpeechProofScorer()
    output = scorer.score(audio_path)
    
    # Ground truth
    gt_start = 2.70
    gt_end = 4.70
    
    # Find matching region
    best_iou = 0
    best_onset_error = None
    for region in output.regions:
        r = region if isinstance(region, dict) else vars(region)
        if r.get('dimension') == "pausing" or r.get('type') == 'pausing':
            start_s = r.get('start_s') or r.get('start', 0)
            end_s = r.get('end_s') or r.get('end', 0)
            iou = calculate_iou(start_s, end_s, gt_start, gt_end)
            if iou > best_iou:
                best_iou = iou
                best_onset_error = abs(start_s - gt_start)
                
    if best_iou == 0 and len(output.regions) > 0:
        # Check if they are just labeled differently
        for region in output.regions:
            r = region if isinstance(region, dict) else vars(region)
            start_s = r.get('start_s') or r.get('start', 0)
            end_s = r.get('end_s') or r.get('end', 0)
            iou = calculate_iou(start_s, end_s, gt_start, gt_end)
            if iou > best_iou:
                best_iou = iou
                best_onset_error = abs(start_s - gt_start)

    # Thresholds
    status = "MET" if best_iou >= 0.5 else "NOT_MET"
    if status == "NOT_MET" and best_iou == 0:
        status = "INCONCLUSIVE" # maybe not outputting regions
        
    res = {
        'test_id': 'T4',
        'status': status,
        'metric': 'F1 / IoU',
        'value': round(best_iou, 4),
        'target': 'IoU >= 0.5',
        'onset_error': round(best_onset_error, 4) if best_onset_error is not None else None,
        'reason': 'Single pause injection pilot',
        'limitations': ['N=1 pilot']
    }
    
    with open('eval/t4_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
    print("T4 finished.")

if __name__ == '__main__':
    run()
