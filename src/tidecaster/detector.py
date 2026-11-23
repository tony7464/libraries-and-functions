"""Splash detection from a stream of audio loudness values."""

from __future__ import annotations

from collections import deque
from statistics import median


class SplashDetector:
    """Flags a bite when loudness jumps well above the recent background.

    Feed it one RMS value per audio block. The background is the median of
    the quiet blocks seen since the last reset, so steady noise (rain, a
    waterfall) raises the bar instead of triggering it.
    """

    def __init__(
        self,
        ratio: float = 4.0,
        min_rms: float = 0.01,
        hold_blocks: int = 2,
        warmup: float = 2.0,
        history: float = 4.0,
    ):
        self.ratio = ratio
        self.min_rms = min_rms
        self.hold_blocks = max(1, hold_blocks)
        self.warmup = warmup
        self.history = history
        self.reset()

    def reset(self) -> None:
        self._elapsed = 0.0
        self._quiet: deque[tuple[float, float]] = deque()
        self._loud = 0

    @property
    def threshold(self) -> float:
        background = median(r for _, r in self._quiet) if self._quiet else 0.0
        return max(self.min_rms, background * self.ratio)

    def feed(self, rms: float, seconds: float) -> bool:
        """Add one block; return True when a splash is detected."""
        self._elapsed += seconds
        if self._elapsed <= self.warmup:
            # The cast itself is noisy: ignore it entirely.
            return False
        if rms >= self.threshold:
            self._loud += 1
            return self._loud >= self.hold_blocks
        self._loud = 0
        self._quiet.append((self._elapsed, rms))
        while self._quiet and self._quiet[0][0] < self._elapsed - self.history:
            self._quiet.popleft()
        return False
