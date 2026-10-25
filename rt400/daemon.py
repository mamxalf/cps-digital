"""rt400d: kirim suhu ke layar RT400 tiap detik, kontrol lewat Unix socket JSON."""
import json
import os
import socket
import threading
import time
from pathlib import Path

from . import device, sensors

SOCKET = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "rt400.sock"
SOURCES = ("cpu", "gpu", "max", "fixed")


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.source = "cpu"
        self.unit = "c"
        self.fixed = 0
        self.interval = 1.0
        self.shown = None  # nilai terakhir (Celsius) yang dikirim
        self.error = None

    def snapshot(self):
        with self.lock:
            return {"source": self.source, "unit": self.unit, "fixed": self.fixed,
                    "interval": self.interval, "shown": self.shown, "error": self.error}

    def apply(self, req):
        with self.lock:
            if "source" in req:
                if req["source"] not in SOURCES:
                    raise ValueError(f"source harus salah satu dari {SOURCES}")
                self.source = req["source"]
            if "unit" in req:
                if req["unit"] not in ("c", "f"):
                    raise ValueError("unit harus c atau f")
                self.unit = req["unit"]
            if "fixed" in req:
                self.fixed = max(0, min(199, int(req["fixed"])))


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


def pick_value(state):
    snap = state.snapshot()
    if snap["source"] == "fixed":
        return snap["fixed"]
    return sensors.read(snap["source"])


def main():
    if already_running():
        raise SystemExit("rt400d sudah berjalan (cek: systemctl --user status rt400d)")
    state = State()
    threading.Thread(target=serve, args=(state,), daemon=True).start()
    display = None
    try:
        while True:
            try:
                display = display or device.Display()
                value = pick_value(state)
                if value is None:
                    raise RuntimeError("sensor tidak tersedia")
                # Mode fixed menampilkan angka apa adanya; konversi F hanya untuk suhu sensor.
                unit = "c" if state.source == "fixed" else state.unit
                display.show(value, unit)
                with state.lock:
                    state.shown, state.error = value, None
            except (OSError, RuntimeError) as exc:
                if display:
                    display.close()
                    display = None
                with state.lock:
                    state.error = str(exc)
            time.sleep(state.interval)
    finally:
        if display:
            display.close()
        SOCKET.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
