"""Configuration: defaults overlaid with an optional TOML file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Keys:
    cast: str = "1"
    interact: str = "f"
    lure: str = ""


@dataclass
class Audio:
    device: str = "BlackHole"
    ratio: float = 4.0
    min_rms: float = 0.01
    hold_blocks: int = 2
    warmup: float = 2.0


@dataclass
class Timing:
    bite_timeout: float = 22.0
    reaction: tuple[float, float] = (0.25, 0.7)
    loot_delay: tuple[float, float] = (1.0, 1.8)
    lure_minutes: float = 10.0
    lure_cast_time: float = 5.5
    max_minutes: float = 0.0


@dataclass
class App:
    # Substrings of the game's app name; a single string also works.
    name: list[str] = field(default_factory=lambda: ["warcraft", "wow"])


@dataclass
class Config:
    keys: Keys = field(default_factory=Keys)
    audio: Audio = field(default_factory=Audio)
    timing: Timing = field(default_factory=Timing)
    app: App = field(default_factory=App)


def _fill(section, values: dict, where: str):
    known = {f.name for f in fields(section)}
    for name, value in values.items():
        if name not in known:
            raise ValueError(f"unknown setting [{where}] {name}")
        if isinstance(getattr(section, name), tuple):
            if not (isinstance(value, list) and len(value) == 2 and value[0] <= value[1]):
                raise ValueError(f"[{where}] {name} must be [min, max]")
            value = (float(value[0]), float(value[1]))
        setattr(section, name, value)


def load(path: str | Path | None) -> Config:
    config = Config()
    if path is None:
        return config
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    for where, values in data.items():
        if not hasattr(config, where):
            raise ValueError(f"unknown section [{where}]")
        _fill(getattr(config, where), values, where)
    return config
