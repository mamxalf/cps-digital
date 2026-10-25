"""rt400ctl: klien tipis untuk rt400d, plus perintah diagnostik langsung."""
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
    sub.add_parser("status", help="status daemon (JSON)")
    s = sub.add_parser("set", help="atur sumber/satuan")
    s.add_argument("--source", choices=daemon.SOURCES)
    s.add_argument("--unit", choices=("c", "f"))
    s.add_argument("--fixed", type=int, help="nilai 0-199 untuk source=fixed")
    d = sub.add_parser("dry-run", help="cetak paket yang akan dikirim, tanpa menulis ke perangkat")
    d.add_argument("--source", default="cpu", choices=("cpu", "gpu", "max"))
    d.add_argument("--unit", default="c", choices=("c", "f"))
    sub.add_parser("version", help="query versi firmware (menulis ke perangkat langsung)")
    args = p.parse_args(argv)

    if args.cmd == "dry-run":
        value = sensors.read(args.source)
        if value is None:
            sys.exit("sensor tidak tersedia")
        print(f"{value:.1f}C -> {protocol.to_display_value(value, args.unit)}")
        print(protocol.temperature_report(value, args.unit)[:8].hex(" "), "...")
    elif args.cmd == "version":
        with device.Display() as display:
            print(display.version()[:8].hex(" "), "... (mentah)")
    else:
        payload = {"cmd": args.cmd}
        if args.cmd == "set":
            payload.update({k: v for k, v in vars(args).items() if k in ("source", "unit", "fixed") and v is not None})
        try:
            print(json.dumps(request(payload)))
        except OSError as exc:
            sys.exit(f"rt400d tidak berjalan: {exc}")


if __name__ == "__main__":
    main()
