from speechproof.config import config

def test_config_values():
    assert config.rubric.pause_min_s == 0.4
    assert config.rubric.long_pause_min_s == 1.2
