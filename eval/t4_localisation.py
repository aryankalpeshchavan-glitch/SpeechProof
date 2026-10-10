import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Region:
    start_s: float
    end_s: float
    type: str

def calculate_iou(pred_start, pred_end, gt_start, gt_end):
    intersection = max(0, min(pred_end, gt_end) - max(pred_start, gt_start))
    union = max(pred_end, gt_end) - min(pred_start, gt_start)
    if union <= 0:
        return 0.0
    return intersection / union

def evaluate_localization(predictions: List[Region], ground_truths: List[Region], iou_threshold=0.5):
    # One-to-one matching based on max IoU
    matches = []
    unmatched_gt = list(range(len(ground_truths)))
    unmatched_pred = list(range(len(predictions)))
    
    # Sort predictions and ground truths by start time to make it deterministic
    pred_sorted = sorted(enumerate(predictions), key=lambda x: x[1].start_s)
    gt_sorted = sorted(enumerate(ground_truths), key=lambda x: x[1].start_s)
    
    tp, fp, fn = 0, 0, 0
    onset_errors = []
    ious = []
    
    for p_idx, p in pred_sorted:
        best_iou = -1
        best_gt_idx = -1
        
        for g_idx, g in gt_sorted:
            if g_idx not in unmatched_gt:
                continue
            if p.type != g.type:
                continue
            
            iou = calculate_iou(p.start_s, p.end_s, g.start_s, g.end_s)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = g_idx
                
        if best_iou >= iou_threshold:
            tp += 1
            unmatched_gt.remove(best_gt_idx)
            unmatched_pred.remove(p_idx)
            onset_errors.append(abs(p.start_s - ground_truths[best_gt_idx].start_s))
            ious.append(best_iou)
        else:
            fp += 1
            
    fn = len(unmatched_gt)
    fp += len(unmatched_pred) - len([p_idx for p_idx, _ in pred_sorted if p_idx not in unmatched_pred]) # Wait, if it didn't match it's already counted if best_iou < threshold
    # Actually:
    # Everything in predictions that didn't match a GT with IoU >= threshold is an FP.
    fp = len(predictions) - tp
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    onset_errors.sort()
    median_onset_error = onset_errors[len(onset_errors)//2] if onset_errors else None
    p90_idx = int(0.9 * len(onset_errors))
    p90_onset_error = onset_errors[p90_idx] if onset_errors else None
    
    mean_iou = sum(ious) / len(ious) if ious else 0.0
    
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "mean_iou_matched": mean_iou,
        "median_onset_error": median_onset_error,
        "p90_onset_error": p90_onset_error,
        "n_predictions": len(predictions),
        "n_ground_truths": len(ground_truths)
    }

def run():
    print("Running T4 Localization...")
    audio_path = "eval/outputs/t3_injected/pause_2.0.wav"
    
    if not Path(audio_path).exists():
        res = {'test_id': 'T4', 'status': 'NOT_RUN', 'reason': 'T3 output missing', 'limitations': []}
        with open('eval/t4_results.json', 'w') as f:
            json.dump(res, f, allow_nan=False)
        return
        
    try:
        from speechproof.pipeline import SpeechProofScorer
        scorer = SpeechProofScorer()
        output = scorer.score(audio_path)
        
        preds = []
        for r in output.regions:
            rd = r if isinstance(r, dict) else vars(r)
            dim = rd.get('dimension') or rd.get('type')
            start = rd.get('start_s') or rd.get('start', 0)
            end = rd.get('end_s') or rd.get('end', 0)
            preds.append(Region(start, end, dim))
            
        gts = [Region(2.70, 4.70, "pausing")]
        metrics = evaluate_localization(preds, gts)
        
        status = "PILOT" # single interval
        
        res = {
            'test_id': 'T4',
            'status': status,
            'metric': 'F1',
            'value': round(metrics['f1'], 4),
            'target': 'F1 >= 0.7, median onset error <= 0.25',
            'tp': metrics['tp'],
            'fp': metrics['fp'],
            'fn': metrics['fn'],
            'precision': round(metrics['precision'], 4),
            'recall': round(metrics['recall'], 4),
            'mean_iou': round(metrics['mean_iou_matched'], 4),
            'onset_error': round(metrics['median_onset_error'], 4) if metrics['median_onset_error'] is not None else None,
            'p90_onset_error': round(metrics['p90_onset_error'], 4) if metrics['p90_onset_error'] is not None else None,
            'reason': 'Single pause injection pilot',
            'limitations': ['N=1 pilot, cannot claim population-level validation']
        }
        
    except Exception as e:
        res = {'test_id': 'T4', 'status': 'FAILED', 'reason': str(e), 'limitations': []}
        
    with open('eval/t4_results.json', 'w') as f:
        json.dump(res, f, allow_nan=False)
    print("T4 finished.")

if __name__ == '__main__':
    run()
