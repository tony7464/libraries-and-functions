"""Command line: run, calibrate, devices."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__, config as config_mod

DEFAULT_CONFIG = Path("config.toml")


def _load(args) -> config_mod.Config:
    path = args.config
    if path is None and DEFAULT_CONFIG.exists():
        path = DEFAULT_CONFIG
    return config_mod.load(path)


def cmd_devices(args) -> int:
    from . import audio

    print("\n".join(audio.list_devices()) or "No audio input devices found.")
    return 0


def cmd_calibrate(args) -> int:
    """Show live loudness so the user can check routing and pick thresholds."""
    from . import audio

    cfg = _load(args)
    peak = 0.0
    print("Listening. Fish by hand and watch the level jump on a splash. Ctrl+C to stop.")
    with audio.Listener(cfg.audio.device) as listener:
        try:
            while True:
                rms = listener.read(1.0)
                if rms is None:
                    continue
                peak = max(peak, rms)
                bar = "#" * min(50, int(rms * 400))
                print(f"\rlevel {rms:.4f}  peak {peak:.4f}  {bar:<50}", end="", flush=True)
        except KeyboardInterrupt:
            print()
    if peak == 0.0:
        print("Heard only silence: game audio is not reaching this device (see README).")
    return 0


def cmd_run(args) -> int:
    from . import audio, keys
    from .bot import Bot

    cfg = _load(args)
    for key in (cfg.keys.cast, cfg.keys.interact, cfg.keys.lure):
        if key:
            keys.keycode(key)  # fail early on a typo
    if not keys.accessibility_granted():
        print(
            "Accessibility access is missing, so key presses would be dropped.\n"
            "Grant it to your terminal in System Settings > Privacy & Security > "
            "Accessibility, then restart the terminal.",
            file=sys.stderr,
        )
        return 1

    names = cfg.app.name
    if args.background or cfg.app.background:
        # Keys go only to the game process, so it can sit behind other windows.
        game = {"pid": None}

        def ready() -> bool:
            game["pid"] = keys.game_pid(names)
            return game["pid"] is not None

        def press(key: str) -> None:
            keys.press(key, pid=game["pid"])

        waiting = "Game is not running"
        hint = "background mode, keep the game window open (not minimized)"
    else:
        def ready() -> bool:
            return keys.matches(keys.frontmost_app(), names)

        press = keys.press
        waiting = "Game is not in front"
        hint = "switch to the game"

    with audio.Listener(cfg.audio.device) as listener:
        bot = Bot(cfg, listener, press, ready, waiting=waiting)
        print(f"Starting in {args.delay:.0f}s - {hint}. Ctrl+C here to stop.")
        time.sleep(args.delay)
        try:
            bot.run()
        except KeyboardInterrupt:
            print()
        s = bot.stats
        print(f"Casts {s.casts}, bites {s.bites}, timeouts {s.timeouts}, lures {s.lures}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tidecaster", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-c", "--config", type=Path, help="TOML config (default: ./config.toml if present)")
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="start fishing (default)")
    run.add_argument("--delay", type=float, default=5.0, help="seconds before the first cast")
    run.add_argument("--background", action="store_true",
                     help="send keys straight to the game so it can run behind other windows")
    sub.add_parser("calibrate", help="show live audio levels")
    sub.add_parser("devices", help="list audio input devices")
    args = parser.parse_args(argv)
    if args.command is None:
        args.command, args.delay, args.background = "run", 5.0, False
    try:
        return {"run": cmd_run, "calibrate": cmd_calibrate, "devices": cmd_devices}[args.command](args)
    except (ValueError, RuntimeError, OSError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
