"""hidraw access for the RT400 display through the HIDIOCSFEATURE/HIDIOCGFEATURE ioctls."""
import fcntl
import os
from pathlib import Path

from . import protocol

SYSFS = Path("/sys/class/hidraw")


def _feature_ioctl(number, size=protocol.REPORT_SIZE):
    # _IOC(READ|WRITE, 'H', number, size)
    return 0xC0000000 | (size << 16) | (ord("H") << 8) | number


HIDIOCSFEATURE = _feature_ioctl(0x06)
HIDIOCGFEATURE = _feature_ioctl(0x07)


def find_display(sysfs=SYSFS):
    """Return the /dev/hidraw* path of the display's vendor interface, or None."""
    for dev in sorted(sysfs.glob("hidraw*")):
        try:
            uevent = (dev / "device" / "uevent").read_text()
            descriptor = (dev / "device" / "report_descriptor").read_bytes()
        except OSError:
            continue
        ident = f"HID_ID=0003:{protocol.VID:08X}:{protocol.PID:08X}"
        if ident in uevent.upper() and protocol.DISPLAY_COLLECTION in descriptor:
            return Path("/dev") / dev.name
    return None


class Display:
    def __init__(self, path=None):
        path = path or find_display()
        if path is None:
            raise FileNotFoundError("RT400 display (1a2c:444d) not found")
        self.path = Path(path)
        self.fd = os.open(self.path, os.O_RDWR)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _set_feature(self, report):
        fcntl.ioctl(self.fd, HIDIOCSFEATURE, bytearray(report), True)

    def show(self, celsius, unit="c"):
        self._set_feature(protocol.temperature_report(celsius, unit))

    def version(self):
        """Return the raw 64-byte reply to the version query (not mapped to a version number)."""
        self._set_feature(protocol.version_report())
        buf = bytearray(protocol.REPORT_SIZE)
        buf[0] = protocol.REPORT_ID
        fcntl.ioctl(self.fd, HIDIOCGFEATURE, buf, True)
        return bytes(buf)
