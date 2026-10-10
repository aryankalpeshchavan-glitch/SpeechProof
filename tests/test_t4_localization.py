import pytest
from eval.t4_localisation import calculate_iou, evaluate_localization, Region

def test_iou_exact():
    assert calculate_iou(0, 1, 0, 1) == 1.0

def test_iou_partial():
    assert abs(calculate_iou(0, 2, 1, 3) - (1.0/3.0)) < 1e-6

def test_iou_boundary():
    assert calculate_iou(0, 1, 1, 2) == 0.0

def test_iou_no_overlap():
    assert calculate_iou(0, 1, 2, 3) == 0.0

def test_localization_exact_match():
    preds = [Region(0, 1, "pausing")]
    gts = [Region(0, 1, "pausing")]
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 1 and res['fp'] == 0 and res['fn'] == 0
    assert res['precision'] == 1.0 and res['recall'] == 1.0 and res['f1'] == 1.0
    assert res['median_onset_error'] == 0.0

def test_localization_wrong_type():
    preds = [Region(0, 1, "pace")]
    gts = [Region(0, 1, "pausing")]
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 0 and res['fp'] == 1 and res['fn'] == 1
    assert res['f1'] == 0.0

def test_localization_duplicate_pred():
    preds = [Region(0, 1, "pausing"), Region(0, 1, "pausing")]
    gts = [Region(0, 1, "pausing")]
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 1 and res['fp'] == 1 and res['fn'] == 0

def test_localization_no_preds():
    preds = []
    gts = [Region(0, 1, "pausing")]
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 0 and res['fn'] == 1 and res['f1'] == 0.0

def test_localization_no_gts():
    preds = [Region(0, 1, "pausing")]
    gts = []
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 0 and res['fp'] == 1 and res['f1'] == 0.0

def test_localization_malformed_times():
    preds = [Region(2, 1, "pausing")] # end before start
    gts = [Region(1, 2, "pausing")]
    res = evaluate_localization(preds, gts)
    assert res['tp'] == 0 # union <= 0 -> iou 0
