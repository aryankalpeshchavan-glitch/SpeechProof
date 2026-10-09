from contracts.scorer_protocol import ScorerProtocol
from speechproof.pipeline import SpeechProofScorer
import pytest

def test_scorer_protocol():
    scorer = SpeechProofScorer()
    with pytest.raises(ValueError, match="Audio file not found"):
        scorer.score('dummy.wav')
