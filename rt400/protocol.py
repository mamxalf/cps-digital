"""Paket USB HID untuk PCCooler RT400 Digital (1a2c:444d, vendor collection 0xff01).

Protokol sama dengan RT500 Digital; lihat docs/PROTOCOL.md untuk sumbernya.
"""

VID, PID = 0x1A2C, 0x444D
REPORT_ID = 7
REPORT_SIZE = 64  # termasuk report ID
MAX_VALUE = 199

CMD_VERSION = 0xFD
CMD_TEMPERATURE = 0xFF

# Potongan report descriptor yang menandai collection layar (Usage Page 0xff01, report ID 7).
DISPLAY_COLLECTION = bytes.fromhex("06 01 ff 09 01 a1 01 85 07".replace(" ", ""))


def to_display_value(celsius, unit="c"):
    """Samakan dengan vendor: potong ke int, konversi F di host, clamp 0..199."""
    value = int(celsius)
    if unit == "f":
        value = int(value * 1.8 + 32)
    return max(0, min(MAX_VALUE, value))


def temperature_report(celsius, unit="c"):
    value = to_display_value(celsius, unit)
    report = bytearray(REPORT_SIZE)
    report[0] = REPORT_ID
    report[1] = CMD_TEMPERATURE
    report[2] = 0xFF
    report[3] = value // 100
    report[4] = value // 10 % 10
    report[5] = value % 10
    return bytes(report)


def version_report():
    report = bytearray(REPORT_SIZE)
    report[0] = REPORT_ID
    report[1] = CMD_VERSION
    return bytes(report)
