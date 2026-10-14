
from speechproof.rubric import score, clamp


def test_clamp_keeps_values_within_range():
    assert clamp(-10) == 0
    assert clamp(50) == 50
    assert clamp(120) == 100


def test_ideal_features_receive_full_score():
    features = {
        "speech_rate_wpm": 140,
        "pause_ratio": 0,
        "pause_max_sec": 0,
        "pause_count": 0,
        "filler_rate_per_min": 2,
        "pitch_std_semitones": 1.5,
        "rms_db_std": 4.0,
    }

    result = score(features)

    assert result["overall_score"] == 100
    assert all(value == 100 for value in result["scores"].values())


def test_slow_speech_lowers_pace_score():
    features = {
        "speech_rate_wpm": 80,
        "pause_ratio": 0,
        "pause_max_sec": 0,
        "pause_count": 0,
        "filler_rate_per_min": 0,
        "pitch_std_semitones": 1.5,
        "rms_db_std": 4.0,
    }

    result = score(features)

    assert result["scores"]["pace"] == 80
    assert result["scores"]["pausing"] == 100


def test_long_pause_lowers_pausing_score():
    features = {
        "speech_rate_wpm": 140,
        "pause_ratio": 0.1,
        "pause_max_sec": 1.8,
        "pause_count": 3,
        "filler_rate_per_min": 0,
        "pitch_std_semitones": 1.5,
        "rms_db_std": 4.0,
    }

    result = score(features)

    # 0.1 * 200 + (1.8 - 0.8) * 20 + (3 - 2) * 2 = 42
    assert result["scores"]["pausing"] == 58


def test_scores_and_penalties_stay_within_range():
    features = {
        "speech_rate_wpm": 0,
        "pause_ratio": 1.0,
        "pause_max_sec": 10,
        "pause_count": 20,
        "filler_rate_per_min": 30,
        "pitch_std_semitones": None,
        "rms_db_std": 0,
    }

    result = score(features)

    for value in result["scores"].values():
        assert 0 <= value <= 100

    for value in result["penalties"].values():
        assert 0 <= value <= 100

    assert 0 <= result["overall_score"] <= 100


def test_fluency_absence_does_not_bias_overall_score():
    features_without_fluency = {
        "speech_rate_wpm": 140,
        "pause_ratio": 0,
        "pause_max_sec": 0,
        "pause_count": 0,
        "pitch_std_semitones": 1.5,
        "rms_db_std": 4.0,
    }
    result = score(features_without_fluency)
    assert "fluency" not in result["scores"]
    assert "fluency" not in result["penalties"]
    assert result["overall_score"] == 100.0


def test_fluency_penalty_proportional_to_excess_fillers():
    features = {
        "speech_rate_wpm": 140,
        "pause_ratio": 0,
        "pause_max_sec": 0,
        "pause_count": 0,
        "filler_rate_per_min": 7,  # max is 5, excess is 2 -> penalty = 20 -> score = 80
        "pitch_std_semitones": 1.5,
        "rms_db_std": 4.0,
    }
    result = score(features)
    assert result["scores"]["fluency"] == 80.0
    assert result["penalties"]["fluency"] == 20.0
