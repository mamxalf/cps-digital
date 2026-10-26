"""rt400d: sends a value to the RT400 display every second; controlled over a JSON Unix socket."""
import json
import os
import socket
import threading
import time
from pathlib import Path

from . import device, sensors

SOCKET = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "rt400.sock"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "rt400" / "config.json"
ROTATABLE = tuple(k for k in sensors.KINDS if k != "fixed")
SOURCES = ROTATABLE + ("fixed", "rotate")
PERSISTED = ("source", "unit", "fixed", "rotate_sources", "rotate_seconds", "alert", "alert_threshold")
BLINK_PERIOD = 0.5
STALL_LIMIT = 5        # consecutive EPIPE writes before the device is USB-reset
RESET_COOLDOWN = 30.0  # seconds between resets


class StallWatch:
    """Counts consecutive write stalls (EPIPE) and says when a USB reset is due."""

    def __init__(self, limit=STALL_LIMIT, cooldown=RESET_COOLDOWN):
        self.limit, self.cooldown = limit, cooldown
        self.count = 0
        self.last_reset = None

    def ok(self):
        self.count = 0

    def failed(self, exc, now):
        if not isinstance(exc, BrokenPipeError):
            self.count = 0
            return False
        self.count += 1
        if self.count < self.limit:
            return False
        if self.last_reset is not None and now - self.last_reset < self.cooldown:
            return False
        self.count, self.last_reset = 0, now
        return True


class State:
    def __init__(self, config=CONFIG):
        self.lock = threading.Lock()
        self.config = config
        self.source = "cpu"
        self.unit = "c"
        self.fixed = 0
        self.rotate_sources = ["cpu", "load"]
        self.rotate_seconds = 5
        self.alert = False
        self.alert_threshold = 85  # degrees Celsius
        self.interval = 1.0
        self.shown = None   # last value read (before blink/conversion)
        self.active = None  # source currently on the display (differs from source while rotating)
        self.alerting = False
        self.error = None
        self._load()

    def _load(self):
        try:
            saved = json.loads(self.config.read_text())
            self.apply({k: v for k, v in saved.items() if k in PERSISTED}, save=False)
        except (OSError, ValueError, TypeError):
            pass  # missing or corrupt config: keep the defaults

    def _save(self):
        try:
            self.config.parent.mkdir(parents=True, exist_ok=True)
            self.config.write_text(json.dumps({k: getattr(self, k) for k in PERSISTED}))
        except OSError:
            pass

    def snapshot(self):
        with self.lock:
            out = {k: getattr(self, k) for k in PERSISTED}
            out.update(interval=self.interval, shown=self.shown, active=self.active,
                       alerting=self.alerting, error=self.error,
                       kind=sensors.KINDS.get(self.active or self.source, "raw"))
            return out

    def apply(self, req, save=True):
        with self.lock:
            if "source" in req:
                if req["source"] not in SOURCES:
                    raise ValueError(f"source must be one of {SOURCES}")
                self.source = req["source"]
            if "unit" in req:
                if req["unit"] not in ("c", "f"):
                    raise ValueError("unit must be c or f")
                self.unit = req["unit"]
            if "fixed" in req:
                self.fixed = max(0, min(199, int(req["fixed"])))
            if "rotate_sources" in req:
                lst = list(req["rotate_sources"])
                if not lst or any(s not in ROTATABLE for s in lst):
                    raise ValueError(f"rotate_sources must be a non-empty list of {ROTATABLE}")
                self.rotate_sources = lst
            if "rotate_seconds" in req:
                self.rotate_seconds = max(2, min(60, int(req["rotate_seconds"])))
            if "alert" in req:
                self.alert = bool(req["alert"])
            if "alert_threshold" in req:
                self.alert_threshold = max(30, min(110, int(req["alert_threshold"])))
            if save:
                self._save()


def choose(snap, now, read=sensors.read):
    """Pick (active source, value) for now. Rotation skips sources without a sensor."""
    if snap["source"] == "fixed":
        return "fixed", snap["fixed"]
    if snap["source"] != "rotate":
        return snap["source"], read(snap["source"])
    lst = snap["rotate_sources"]
    start = int(now // snap["rotate_seconds"]) % len(lst)
    for i in range(len(lst)):
        source = lst[(start + i) % len(lst)]
        value = read(source)
        if value is not None:
            return source, value
    return lst[start], None


def to_send(snap, active, value, now):
    """Final value for the display: blinks to 0 while the alert is active. Returns (value, alerting)."""
    alerting = bool(snap["alert"] and active in sensors.TEMP_SOURCES and value is not None
                    and value >= snap["alert_threshold"])
    if alerting and int(now / BLINK_PERIOD) % 2:
        return 0, True
    return value, alerting


def handle(conn, state):
    with conn:
        try:
            req = json.loads(conn.makefile().readline() or "{}")
            if req.get("cmd") == "set":
                state.apply(req)
            reply = {"ok": True, **state.snapshot()}
        except (ValueError, TypeError) as exc:
            reply = {"ok": False, "error": str(exc)}
        conn.sendall((json.dumps(reply) + "\n").encode())


def already_running(path=SOCKET):
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def serve(state, path=SOCKET):
    path.unlink(missing_ok=True)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(path))
    os.chmod(path, 0o600)
    srv.listen(4)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn, state), daemon=True).start()


def main():
    if already_running():
        raise SystemExit("rt400d is already running (check: systemctl --user status rt400d)")
    state = State()
    threading.Thread(target=serve, args=(state,), daemon=True).start()
    display = None
    watch = StallWatch()
    try:
        while True:
            now = time.time()
            snap = state.snapshot()
            alerting = False
            try:
                display = display or device.Display()
                active, value = choose(snap, now)
                if value is None:
                    raise RuntimeError("sensor unavailable")
                out, alerting = to_send(snap, active, value, now)
                # Only temperatures are converted to F; percentages and fixed values are shown as is.
                unit = snap["unit"] if active in sensors.TEMP_SOURCES else "c"
                display.show(out, unit)
                with state.lock:
                    state.shown, state.active, state.alerting, state.error = value, active, alerting, None
                watch.ok()
            except (OSError, RuntimeError) as exc:
                if display:
                    display.close()
                    display = None
                with state.lock:
                    state.error = str(exc)
                if watch.failed(exc, now):
                    try:
                        device.reset()
                        time.sleep(2)  # let the device re-enumerate
                    except OSError as reset_exc:
                        with state.lock:
                            state.error = f"{exc}; reset failed: {reset_exc}"
            time.sleep(BLINK_PERIOD if alerting else snap["interval"])
    finally:
        if display:
            display.close()
        SOCKET.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
