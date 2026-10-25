"""Baca suhu CPU/GPU dari /sys/class/hwmon (derajat Celsius)."""
from pathlib import Path

HWMON = Path("/sys/class/hwmon")
CPU_DRIVERS = ("coretemp", "k10temp", "zenpower")
GPU_DRIVERS = ("amdgpu", "nouveau", "radeon")
CPU_LABELS = ("Package id 0", "Tctl", "Tdie")


def _read_milli(path):
    try:
        return int(path.read_text().strip()) / 1000
    except (OSError, ValueError):
        return None


def _find(drivers, preferred_labels=(), root=HWMON):
    for hwmon in sorted(root.glob("hwmon*")):
        try:
            name = (hwmon / "name").read_text().strip()
        except OSError:
            continue
        if name not in drivers:
            continue
        inputs = sorted(hwmon.glob("temp*_input"))
        chosen = None
        for inp in inputs:
            label = inp.with_name(inp.name.replace("_input", "_label"))
            if label.exists() and label.read_text().strip() in preferred_labels:
                chosen = inp
                break
        chosen = chosen or (inputs[0] if inputs else None)
        if chosen:
            return chosen
    return None


def cpu_temp(root=HWMON):
    path = _find(CPU_DRIVERS, CPU_LABELS, root)
    return _read_milli(path) if path else None


def gpu_temp(root=HWMON):
    path = _find(GPU_DRIVERS, (), root)
    return _read_milli(path) if path else None


def read(source, root=HWMON):
    """source: cpu | gpu | max. Kembalikan None bila sensor tak tersedia."""
    if source == "cpu":
        return cpu_temp(root)
    if source == "gpu":
        return gpu_temp(root)
    if source == "max":
        values = [v for v in (cpu_temp(root), gpu_temp(root)) if v is not None]
        return max(values) if values else None
    raise ValueError(f"sumber tidak dikenal: {source}")
