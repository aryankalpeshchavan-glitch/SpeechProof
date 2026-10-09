from typing import Protocol, Dict, Any, List
from dataclasses import dataclass

@dataclass
class Region:
    type: str
    start_s: float
    end_s: float
    value: float
    measure: str = ""
    threshold: float = 0.0
    words_before: str = ""
    words_after: str = ""

@dataclass
class ScorerOutput:
    scorer_name: str
    scorer_version: str
    scores: Dict[str, float]
    regions: List[Region]
    events: List[Dict[str, Any]]
    quality_flags: List[str]
    audio_sha256: str
    duration_s: float
    metadata: Dict[str, Any]

class ScorerProtocol(Protocol):
    def score(self, audio_path: str) -> ScorerOutput:
        ...
