#!/usr/bin/env python3
"""Probe READ-ONLY untuk PCCooler RT400 (USB 1a2c:444d).

Hanya membaca sysfs: info USB dan HID report descriptor tiap interface.
Tidak membuka atau menulis ke /dev/hidraw, jadi aman dan tidak butuh udev rule.
"""
import glob
import os

VID, PID = "00001A2C", "0000444D"


def read(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def parse_descriptor(data):
    """Uraikan item HID secara sederhana (prefix, tag, nilai)."""
    names = {
        0x04: "Usage Page", 0x08: "Usage", 0x14: "Logical Min", 0x24: "Logical Max",
        0x74: "Report Size", 0x94: "Report Count", 0x84: "Report ID",
        0xA0: "Collection", 0xC0: "End Collection",
        0x80: "Input", 0x90: "Output", 0xB0: "Feature",
    }
    i, out = 0, []
    while i < len(data):
        b = data[i]
        size = (0, 1, 2, 4)[b & 3]
        key = b & 0xFC
        val = int.from_bytes(data[i + 1:i + 1 + size], "little")
        out.append(f"  {names.get(key, f'0x{key:02X}'):<16} 0x{val:X}")
        i += 1 + size
    return out


def main():
    found = False
    for dev in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        uevent = (read(f"{dev}/device/uevent") or b"").decode(errors="replace")
        if f"{VID}:{PID}" not in uevent:
            continue
        found = True
        real = os.path.realpath(f"{dev}/device")
        node = "/dev/" + os.path.basename(dev)
        access = "bisa dibaca" if os.access(node, os.R_OK | os.W_OK) else "TIDAK ada izin (pasang udev rule)"
        print(f"== {node}  [{access}]\n   {real}")
        desc = read(f"{dev}/device/report_descriptor")
        if desc is None:
            print("   (descriptor tidak terbaca)")
            continue
        print(f"   descriptor {len(desc)} byte: {desc.hex()}")
        print("\n".join(parse_descriptor(desc)))
    if not found:
        print("RT400 (1a2c:444d) tidak ditemukan.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
