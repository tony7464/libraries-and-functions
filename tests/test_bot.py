import random

from tidecaster.bot import Bot
from tidecaster.config import Config


class World:
    """Fake clock, keyboard, focus and audio stream."""

    block_seconds = 0.05

    def __init__(self, splash_at=None):
        self.now = 0.0
        self.pressed = []
        self.app = "World of Warcraft"
        self.splash_at = splash_at  # seconds after each cast, or None
        self.cast_time = 0.0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def press(self, key):
        self.pressed.append((round(self.now, 2), key))
        if key == "1":
            self.cast_time = self.now

    def frontmost_app(self):
        return self.app

    def flush(self):
        pass

    def read(self, timeout=0.5):
        self.now += self.block_seconds
        since = self.now - self.cast_time
        if self.splash_at is not None and self.splash_at <= since < self.splash_at + 0.5:
            return 0.3
        return 0.002


def make(world, **timing):
    cfg = Config()
    for k, v in timing.items():
        setattr(cfg.timing, k, v)
    bot = Bot(cfg, world, world.press, world.frontmost_app, clock=world.clock,
              sleep=world.sleep, rng=random.Random(1), log=lambda m: None)
    return cfg, bot


def test_bite_presses_interact_after_cast():
    world = World(splash_at=8.0)
    _, bot = make(world)
    assert bot.cycle() is True
    assert [k for _, k in world.pressed] == ["1", "f"]
    assert 8.0 < world.pressed[1][0] < 9.0


def test_timeout_recasts_without_interacting():
    world = World(splash_at=None)
    _, bot = make(world)
    assert bot.cycle() is False
    assert [k for _, k in world.pressed] == ["1"]
    assert 22.0 <= world.now < 23.0
    assert bot.stats.timeouts == 1


def test_no_keys_sent_while_game_not_in_front():
    world = World(splash_at=5.0)
    world.app = "Safari"
    _, bot = make(world, max_minutes=1)
    bot.run()
    assert world.pressed == []


def test_app_name_matching():
    world = World()
    cfg, bot = make(world)
    for app, expected in [("Wow", True), ("World of Warcraft Classic", True), ("Claude", False)]:
        world.app = app
        assert bot.focused() is expected
    cfg.app.name = "forever"
    world.app = "WoW Forever"
    assert bot.focused() is True


def test_lure_applied_first_and_on_schedule():
    world = World(splash_at=5.0)
    cfg, bot = make(world, max_minutes=25)
    cfg.keys.lure = "2"
    bot.run()
    lures = [t for t, k in world.pressed if k == "2"]
    assert len(lures) == 3 and lures[0] == 0.0
    assert all(b - a >= 600 for a, b in zip(lures, lures[1:]))


def test_max_minutes_stops_the_run():
    world = World(splash_at=5.0)
    _, bot = make(world, max_minutes=2)
    stats = bot.run()
    assert 120 <= world.now < 150
    assert stats.casts == stats.bites > 5
