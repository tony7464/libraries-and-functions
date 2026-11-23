"""Game-audio capture through a loopback input device (e.g. BlackHole)."""

from __future__ import annotations

import queue

BLOCK_SECONDS = 0.05


def list_devices() -> list[str]:
    import sounddevice as sd

    return [
        f"{i}: {d['name']} ({d['max_input_channels']} in)"
        for i, d in enumerate(sd.query_devices())
        if d["max_input_channels"] > 0
    ]


def find_device(name: str) -> int:
    import sounddevice as sd

    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and name.lower() in d["name"].lower():
            return i
    raise RuntimeError(
        f"no audio input device matching {name!r}. Run `tidecaster devices` "
        "to see what is available; see the README for the BlackHole setup."
    )


class Listener:
    """Yields the loudness (RMS, 0..1) of successive 50 ms blocks."""

    block_seconds = BLOCK_SECONDS

    def __init__(self, device: str):
        import numpy as np
        import sounddevice as sd

        index = find_device(device)
        info = sd.query_devices(index)
        rate = int(info["default_samplerate"])
        self._queue: queue.Queue[float] = queue.Queue()

        def callback(indata, frames, time, status):
            self._queue.put(float(np.sqrt(np.mean(np.square(indata)))))

        self._stream = sd.InputStream(
            device=index,
            channels=min(2, info["max_input_channels"]),
            samplerate=rate,
            blocksize=int(rate * BLOCK_SECONDS),
            dtype="float32",
            callback=callback,
        )

    def __enter__(self):
        self._stream.start()
        return self

    def __exit__(self, *exc):
        self._stream.stop()
        self._stream.close()

    def flush(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def read(self, timeout: float = 0.5) -> float | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
