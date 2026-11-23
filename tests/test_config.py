from pathlib import Path

import pytest

from tidecaster import config
from tidecaster.keys import keycode


def test_example_config_matches_defaults():
    example = Path(__file__).parent.parent / "config.example.toml"
    assert config.load(example) == config.Config()


def test_overrides_and_validation(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text('[keys]\ncast = "f5"\n[timing]\nreaction = [0.1, 0.2]\n')
    cfg = config.load(path)
    assert cfg.keys.cast == "f5" and cfg.timing.reaction == (0.1, 0.2)

    path.write_text("[keys]\ncats = 1\n")
    with pytest.raises(ValueError, match="cats"):
        config.load(path)


def test_keycodes():
    assert keycode("F") == 3 and keycode("1") == 18
    with pytest.raises(ValueError):
        keycode("ctrl+1")
