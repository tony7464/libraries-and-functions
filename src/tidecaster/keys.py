"""macOS key presses and frontmost-app lookup (needs Accessibility access)."""

from __future__ import annotations

import time

# Virtual key codes for an ANSI (US) keyboard layout.
KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8,
    "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17,
    "1": 18, "2": 19, "3": 20, "4": 21, "6": 22, "5": 23, "=": 24, "9": 25,
    "7": 26, "-": 27, "8": 28, "0": 29, "]": 30, "o": 31, "u": 32, "[": 33,
    "i": 34, "p": 35, "l": 37, "j": 38, "'": 39, "k": 40, ";": 41, "\\": 42,
    ",": 43, "/": 44, "n": 45, "m": 46, ".": 47, "`": 50,
    "tab": 48, "space": 49,
    "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97, "f7": 98,
    "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
}


def keycode(key: str) -> int:
    try:
        return KEYCODES[key.lower()]
    except KeyError:
        raise ValueError(
            f"unsupported key {key!r}; use one of: {' '.join(sorted(KEYCODES))}"
        ) from None


def press(key: str, pid: int | None = None, hold: float = 0.06) -> None:
    """Press a key: system-wide, or delivered only to process `pid`."""
    import Quartz

    code = keycode(key)
    for down in (True, False):
        event = Quartz.CGEventCreateKeyboardEvent(None, code, down)
        if pid is None:
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        else:
            Quartz.CGEventPostToPid(pid, event)
        if down:
            time.sleep(hold)


def matches(app_name: str, names: str | list[str]) -> bool:
    if isinstance(names, str):
        names = [names]
    app_name = app_name.lower()
    return any(n.lower() in app_name for n in names)


def frontmost_app() -> str:
    from AppKit import NSWorkspace

    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return str(app.localizedName()) if app else ""


def game_pid(names: str | list[str]) -> int | None:
    """Process id of the running game, or None if it is not open."""
    from AppKit import NSWorkspace

    for app in NSWorkspace.sharedWorkspace().runningApplications():
        # Regular (Dock) apps only, so helper processes are not picked up.
        if app.activationPolicy() == 0 and matches(str(app.localizedName() or ""), names):
            return int(app.processIdentifier())
    return None


def accessibility_granted() -> bool:
    import Quartz

    check = getattr(Quartz, "CGPreflightPostEventAccess", None)
    return bool(check()) if check else True
