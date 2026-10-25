import tempfile
import unittest
from pathlib import Path

from rt400 import daemon, sensors


def fake_read(values):
    return lambda source: values.get(source)


def snap(**kw):
    base = dict(source="cpu", fixed=0, rotate_sources=["cpu", "load"], rotate_seconds=5,
                alert=False, alert_threshold=85)
    base.update(kw)
    return base


class Choose(unittest.TestCase):
    def test_plain_source(self):
        self.assertEqual(daemon.choose(snap(), 0, fake_read({"cpu": 40})), ("cpu", 40))

    def test_fixed(self):
        self.assertEqual(daemon.choose(snap(source="fixed", fixed=88), 0, fake_read({})), ("fixed", 88))

    def test_rotation_alternates(self):
        s, r = snap(source="rotate"), fake_read({"cpu": 40, "load": 12})
        self.assertEqual(daemon.choose(s, 0, r)[0], "cpu")
        self.assertEqual(daemon.choose(s, 5, r)[0], "load")
        self.assertEqual(daemon.choose(s, 10, r)[0], "cpu")

    def test_rotation_skips_missing_sensor(self):
        s = snap(source="rotate", rotate_sources=["gpu", "load"])
        self.assertEqual(daemon.choose(s, 0, fake_read({"load": 12})), ("load", 12))


class Alert(unittest.TestCase):
    def test_no_alert_below_threshold(self):
        self.assertEqual(daemon.to_send(snap(alert=True), "cpu", 70, 0), (70, False))

    def test_blinks_above_threshold(self):
        s = snap(alert=True)
        self.assertEqual(daemon.to_send(s, "cpu", 90, 0.0), (90, True))
        self.assertEqual(daemon.to_send(s, "cpu", 90, 0.6), (0, True))

    def test_percent_source_never_alerts(self):
        self.assertEqual(daemon.to_send(snap(alert=True), "load", 99, 0.6), (99, False))

    def test_disabled(self):
        self.assertEqual(daemon.to_send(snap(alert=False), "cpu", 99, 0.6), (99, False))


class Persistence(unittest.TestCase):
    def test_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "rt400" / "config.json"
            a = daemon.State(cfg)
            a.apply({"source": "rotate", "alert": True, "alert_threshold": 90, "rotate_sources": ["cpu", "ram"]})
            b = daemon.State(cfg)
            self.assertEqual((b.source, b.alert, b.alert_threshold, b.rotate_sources),
                             ("rotate", True, 90, ["cpu", "ram"]))
            with self.assertRaises(ValueError):
                a.apply({"rotate_sources": ["bogus"]})
            with self.assertRaises(ValueError):
                a.apply({"source": "bogus"})


class Sensors(unittest.TestCase):
    def test_ram_percent(self):
        with tempfile.NamedTemporaryFile("w", suffix=".info") as f:
            f.write("MemTotal: 1000 kB\nMemAvailable: 250 kB\n")
            f.flush()
            self.assertEqual(sensors.ram_percent(f.name), 75.0)

    def test_cpu_load_delta(self):
        sensors._prev_cpu = None
        with tempfile.NamedTemporaryFile("w") as f:
            f.write("cpu 100 0 100 700 100 0 0 0\n"); f.flush()
            self.assertEqual(sensors.cpu_load(f.name), 0.0)
            f.seek(0); f.write("cpu 200 0 200 800 100 0 0 0\n"); f.truncate(); f.flush()
            self.assertAlmostEqual(sensors.cpu_load(f.name), 66.666, places=2)


if __name__ == "__main__":
    unittest.main()
