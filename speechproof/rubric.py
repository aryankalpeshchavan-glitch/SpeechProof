import json


CONFIG = {
    "pace": {
        "min_wpm": 100,
        "max_wpm": 180
    },
    "pausing": {
        "max_pause_ratio": 0.20
    },
    "fluency": {
        "max_filler_rate": 5
    },
    "pitch": {
        "min_pitch_std_semitones": 1.0
    },
    "energy": {
        "min_rms_std_db": 3.0
    },
    "rubric_version": "rubric-v0.1"
}


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def score(features, config=CONFIG):

    scores = {}
    penalties = {}

    # -------------------------
    # 1. Pace
    # -------------------------
    wpm = features.get("speech_rate_wpm", 0)

    if wpm == 0:
        pace_score = 0
        pace_penalty = 100
    elif config["pace"]["min_wpm"] <= wpm <= config["pace"]["max_wpm"]:
        pace_score = 100
        pace_penalty = 0
    else:
        if wpm < config["pace"]["min_wpm"]:
            distance = config["pace"]["min_wpm"] - wpm
        else:
            distance = wpm - config["pace"]["max_wpm"]

        pace_penalty = min(distance, 100)
        pace_score = clamp(100 - pace_penalty)

    scores["pace"] = round(pace_score, 2)
    penalties["pace"] = round(pace_penalty, 2)

    # -------------------------
    # 2. Pausing
    # -------------------------
    pause_ratio = features.get("pause_ratio", 0)

    max_ratio = config["pausing"]["max_pause_ratio"]

    if pause_ratio <= max_ratio:
        pause_score = 100
    else:
        excess = pause_ratio - max_ratio
        pause_score = clamp(100 - excess * 500)

    scores["pausing"] = round(pause_score, 2)
    penalties["pausing"] = round(100 - pause_score, 2)

    # -------------------------
    # 3. Fluency
    # -------------------------
    filler_rate = features.get("filler_rate_per_min", 0)

    max_fillers = config["fluency"]["max_filler_rate"]

    if filler_rate <= max_fillers:
        fluency_score = 100
    else:
        fluency_score = clamp(
            100 - (filler_rate - max_fillers) * 10
        )

    scores["fluency"] = round(fluency_score, 2)
    penalties["fluency"] = round(100 - fluency_score, 2)

    # -------------------------
    # 4. Pitch Variety
    # -------------------------
    pitch_variety = features.get(
        "pitch_std_semitones"
    )

    if pitch_variety is None:
        pitch_score = 0
    elif pitch_variety >= config["pitch"]["min_pitch_std_semitones"]:
        pitch_score = 100
    else:
        pitch_score = clamp(
            pitch_variety /
            config["pitch"]["min_pitch_std_semitones"]
            * 100
        )

    scores["pitch_variety"] = round(pitch_score, 2)
    penalties["pitch_variety"] = round(100 - pitch_score, 2)

    # -------------------------
    # 5. Vocal Energy
    # -------------------------
    energy_std = features.get("rms_db_std", 0)

    min_energy = config["energy"]["min_rms_std_db"]

    if energy_std >= min_energy:
        energy_score = 100
    else:
        energy_score = clamp(
            energy_std / min_energy * 100
        )

    scores["vocal_energy"] = round(energy_score, 2)
    penalties["vocal_energy"] = round(100 - energy_score, 2)

    # -------------------------
    # Overall
    # -------------------------
    overall = sum(scores.values()) / len(scores)

    return {
        "rubric_version": config["rubric_version"],
        "scores": scores,
        "penalties": penalties,
        "overall_score": round(overall, 2)
    }


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python speechproof\\rubric.py <features.json>"
        )
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        features = json.load(f)

    result = score(features)

    print(json.dumps(result, indent=2))
