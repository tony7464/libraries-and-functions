# Tidecaster

A sound-based AFK fishing bot for World of Warcraft on macOS.

It casts, listens to the game's audio for the bobber splash, presses your
Interact key to loot, and repeats. It never reads game memory and never moves
the mouse: everything goes through two keybinds and your Mac's audio output.

> **Account risk.** Automating gameplay breaks Blizzard's Terms of Service and
> can get an account suspended or banned. Use this at your own risk.

## How it works

1. Presses the **cast** key.
2. Ignores the first 2 seconds (the cast is noisy), then tracks the background
   loudness of the game audio.
3. When loudness jumps to several times the background for ~100 ms, that is the
   splash. After a short random reaction delay it presses the **interact** key,
   which loots the bobber through WoW's soft-target interact.
4. If nothing is heard for 22 seconds it simply recasts.
5. Optionally presses a **lure** key every 10 minutes.

Keys are only sent while WoW is the frontmost app; switch away and the bot
pauses, switch back and it resumes.

## Setup

### 1. Install

Needs Python 3.11+ (`brew install python`).

```sh
git clone <this repo> && cd <this repo>
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. Route game audio to the bot

macOS cannot record its own output, so install the free
[BlackHole](https://github.com/ExistentialAudio/BlackHole) loopback driver:

```sh
brew install blackhole-2ch
```

Then open **Audio MIDI Setup**, click **+** > **Create Multi-Output Device**,
tick both your speakers/headphones and **BlackHole 2ch**, and select that
Multi-Output Device as the sound output (System Settings > Sound). You still
hear the game, and the bot hears it too.

### 3. Permissions

System Settings > Privacy & Security:

- **Accessibility**: enable your terminal app (needed to send key presses).
- **Microphone**: allow your terminal when prompted (BlackHole is an input
  device, so macOS treats it as a microphone).

### 4. In-game

- Bind **Fishing** to `1` (or put it on action bar slot 1).
- Options > Gameplay > Controls: tick **Enable Interact Key**, and bind
  **Interact With Target** to `F` in Keybindings.
- Run these once in chat so the bobber is picked up as a soft target:

  ```
  /console SoftTargetInteractArc 2
  /console SoftTargetInteractRange 30
  ```

- Enable **Auto Loot**.
- Sound: turn **Sound Effects** up, and **Music**, **Ambience** and **Dialog**
  off. Enable **Sound in Background** if you ever unfocus the window.
- Stand somewhere quiet, zoom in to first person, and face open water.

## Use

```sh
tidecaster devices     # confirm BlackHole is listed
tidecaster calibrate   # fish by hand; the level should jump on each splash
tidecaster             # start fishing (5 s countdown, Ctrl+C to stop)
```

To change keys, thresholds, lure interval or a session time limit, copy
`config.example.toml` to `config.toml` and edit it.

### Tuning

- **Misses splashes**: lower `ratio` (try 3) or `min_rms`; raise the in-game
  Sound Effects volume.
- **Triggers too early**: raise `ratio` or `hold_blocks`, and turn off other
  sounds (ambience, Discord, music apps - anything on the same output).
- `calibrate` shows the quiet level and the splash peak; `min_rms` should sit
  between them.

## Development

```sh
pip install -e '.[dev]'
pytest
```

The fishing loop and splash detector are plain Python and are tested with a
fake clock and audio stream; the macOS pieces (`keys.py`, `audio.py`) are thin
wrappers around Quartz and `sounddevice`.
