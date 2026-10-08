from dataclasses import dataclass

@dataclass
class ASRConfig:
    model_name: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    model_cache_dir: str = "./model_cache"
    language: str = "en"
    beam_size: int = 5
    word_timestamps: bool = True
    vad_filter: bool = True
    condition_on_previous_text: bool = False

@dataclass
class RubricConfig:
    # PACE
    pace_window_s: float = 5.0
    pace_hop_s: float = 2.5
    # CALIBRATION_REQUIRED: articulation rate outside calibration 5th-95th percentile
    
    # PAUSING
    pause_min_s: float = 0.4
    long_pause_min_s: float = 1.2
    
    # PITCH
    pitch_window_s: float = 5.0
    
    # ENERGY
    energy_min_duration_s: float = 1.0

from dataclasses import dataclass, field

@dataclass
class AppConfig:
    asr: ASRConfig = field(default_factory=ASRConfig)
    rubric: RubricConfig = field(default_factory=RubricConfig)

config = AppConfig()
