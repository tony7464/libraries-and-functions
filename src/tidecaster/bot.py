"""The fishing loop: cast, listen for the splash, interact, repeat."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from .config import Config
from .detector import SplashDetector


class AudioSource(Protocol):
    block_seconds: float

    def flush(self) -> None: ...
    def read(self, timeout: float = 0.5) -> float | None: ...


@dataclass
class Stats:
    casts: int = 0
    bites: int = 0
    timeouts: int = 0
    lures: int = 0


class Bot:
    def __init__(
        self,
        config: Config,
        listener: AudioSource,
        press: Callable[[str], None],
        frontmost_app: Callable[[], str],
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        log: Callable[[str], None] = print,
    ):
        self.config = config
        self.listener = listener
        self.press = press
        self.frontmost_app = frontmost_app
        self.clock = clock
        self.sleep = sleep
        self.rng = rng or random.Random()
        self.log = log
        self.stats = Stats()
        self.detector = SplashDetector(
            ratio=config.audio.ratio,
            min_rms=config.audio.min_rms,
            hold_blocks=config.audio.hold_blocks,
            warmup=config.audio.warmup,
        )
        self._next_lure = 0.0
        self._paused = False

    def focused(self) -> bool:
        names = self.config.app.name
        if isinstance(names, str):
            names = [names]
        app = self.frontmost_app().lower()
        return any(n.lower() in app for n in names)

    def run(self) -> Stats:
        timing = self.config.timing
        start = self.clock()
        self._next_lure = start
        while True:
            if timing.max_minutes and self.clock() - start >= timing.max_minutes * 60:
                self.log("Time limit reached.")
                return self.stats
            if not self.focused():
                if not self._paused:
                    self.log("Game is not in front - paused.")
                    self._paused = True
                self.sleep(1.0)
                continue
            if self._paused:
                self.log("Game is in front - resuming.")
                self._paused = False
            self.cycle()

    def cycle(self) -> bool:
        """One cast. Returns True if a bite was detected and looted."""
        timing = self.config.timing
        keys = self.config.keys

        if keys.lure and self.clock() >= self._next_lure:
            self.press(keys.lure)
            self.stats.lures += 1
            self._next_lure = self.clock() + timing.lure_minutes * 60
            self.sleep(timing.lure_cast_time)

        self.press(keys.cast)
        self.stats.casts += 1
        self.detector.reset()
        self.listener.flush()

        if not self._wait_for_bite():
            self.stats.timeouts += 1
            self.log(f"Cast {self.stats.casts}: no bite heard.")
            return False

        self.sleep(self.rng.uniform(*timing.reaction))
        if not self.focused():
            return False
        self.press(keys.interact)
        self.stats.bites += 1
        self.log(f"Cast {self.stats.casts}: bite ({self.stats.bites} total).")
        self.sleep(self.rng.uniform(*timing.loot_delay))
        return True

    def _wait_for_bite(self) -> bool:
        deadline = self.clock() + self.config.timing.bite_timeout
        while self.clock() < deadline:
            rms = self.listener.read(0.5)
            if rms is None:
                continue
            if self.detector.feed(rms, self.listener.block_seconds):
                return True
        return False
