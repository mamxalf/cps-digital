"""USB HID packets for the PCCooler RT400 Digital display (1a2c:444d, vendor collection 0xff01).

Same protocol as the RT500 Digital; see docs/PROTOCOL.md for the sources.
"""

VID, PID = 0x1A2C, 0x444D
REPORT_ID = 7
REPORT_SIZE = 64  # including the report ID
MAX_VALUE = 199

CMD_VERSION = 0xFD
CMD_TEMPERATURE = 0xFF

# Fragment of the report descriptor that marks the display collection (usage page 0xff01, report ID 7).
DISPLAY_COLLECTION = bytes.fromhex("0601ff0901a1018507")


def to_display_value(celsius, unit="c"):
    """Match the vendor app: truncate to int, convert to F on the host, clamp to 0..199."""
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
