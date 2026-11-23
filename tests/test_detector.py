from tidecaster.detector import SplashDetector

DT = 0.05


def feed(det, values):
    return [det.feed(v, DT) for v in values]


def test_splash_after_quiet_triggers():
    det = SplashDetector(warmup=0.5, hold_blocks=2)
    assert not any(feed(det, [0.002] * 100))
    assert feed(det, [0.2, 0.2]) == [False, True]


def test_cast_noise_during_warmup_ignored():
    det = SplashDetector(warmup=2.0)
    assert not any(feed(det, [0.5] * 40))


def test_single_click_does_not_trigger():
    det = SplashDetector(warmup=0.0, hold_blocks=2)
    feed(det, [0.002] * 40)
    assert not any(feed(det, [0.3, 0.002, 0.3, 0.002]))


def test_steady_noise_raises_the_bar():
    det = SplashDetector(warmup=0.0, ratio=4.0, min_rms=0.01)
    assert not any(feed(det, [0.008] * 80))  # constant rain-like noise
    assert not any(feed(det, [0.02] * 5))  # louder, but under 4x background
    assert any(feed(det, [0.1] * 3))


def test_reset_restarts_warmup():
    det = SplashDetector(warmup=1.0, hold_blocks=1)
    feed(det, [0.002] * 40)
    det.reset()
    assert det.feed(0.5, DT) is False
