"""rt400ctl: thin client for rt400d, plus a few direct diagnostic commands."""
import argparse
import json
import socket
import sys

from . import daemon, device, protocol, sensors


def request(payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(str(daemon.SOCKET))
        s.sendall((json.dumps(payload) + "\n").encode())
        return json.loads(s.makefile().readline())


def main(argv=None):
    p = argparse.ArgumentParser(prog="rt400ctl")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="daemon status (JSON)")
    s = sub.add_parser("set", help="change source, unit and other settings")
    s.add_argument("--source", choices=daemon.SOURCES)
    s.add_argument("--unit", choices=("c", "f"))
    s.add_argument("--fixed", type=int, help="value 0-199 for source=fixed")
    s.add_argument("--rotate-sources", help="comma-separated list for source=rotate, e.g. cpu,load")
    s.add_argument("--rotate-seconds", type=int, help="seconds per source (2-60)")
    s.add_argument("--alert", choices=("on", "off"), help="blink the display when the temperature passes the threshold")
    s.add_argument("--alert-threshold", type=int, help="alert threshold in Celsius (30-110)")
    d = sub.add_parser("dry-run", help="print the packet that would be sent, without writing to the device")
    d.add_argument("--source", default="cpu", choices=("cpu", "gpu", "max", "nvme", "load", "ram"))
    d.add_argument("--unit", default="c", choices=("c", "f"))
    sub.add_parser("version", help="query the firmware version (writes to the device directly)")
    args = p.parse_args(argv)

    if args.cmd == "dry-run":
        value = sensors.read(args.source)
        if value is None:
            sys.exit("sensor unavailable")
        unit = args.unit if args.source in sensors.TEMP_SOURCES else "c"
        print(f"{value:.1f} -> {protocol.to_display_value(value, unit)}")
        print(protocol.temperature_report(value, unit)[:8].hex(" "), "...")
    elif args.cmd == "version":
        with device.Display() as display:
            print(display.version()[:8].hex(" "), "... (raw)")
    else:
        payload = {"cmd": args.cmd}
        if args.cmd == "set":
            for key in ("source", "unit", "fixed", "rotate_seconds", "alert_threshold"):
                if getattr(args, key) is not None:
                    payload[key] = getattr(args, key)
            if args.rotate_sources is not None:
                payload["rotate_sources"] = [x for x in args.rotate_sources.split(",") if x]
            if args.alert is not None:
                payload["alert"] = args.alert == "on"
        try:
            print(json.dumps(request(payload)))
        except OSError as exc:
            sys.exit(f"rt400d is not running: {exc}")


if __name__ == "__main__":
    main()
