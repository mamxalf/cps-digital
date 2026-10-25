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


def nvme_temp(root=HWMON):
    path = _find(("nvme",), ("Composite",), root)
    return _read_milli(path) if path else None


_prev_cpu = None


def cpu_load(stat="/proc/stat"):
    """Beban CPU 0-100 sejak panggilan sebelumnya (pertama kali: 0)."""
    global _prev_cpu
    with open(stat) as f:
        vals = [int(v) for v in f.readline().split()[1:]]
    idle, total = vals[3] + vals[4], sum(vals)
    prev, _prev_cpu = _prev_cpu, (idle, total)
    if prev is None or total <= prev[1]:
        return 0.0
    return 100.0 * (1 - (idle - prev[0]) / (total - prev[1]))


def ram_percent(meminfo="/proc/meminfo"):
    info = {}
    with open(meminfo) as f:
        for line in f:
            key, _, rest = line.partition(":")
            info[key] = int(rest.split()[0])
    total, avail = info.get("MemTotal"), info.get("MemAvailable")
    return 100.0 * (1 - avail / total) if total and avail is not None else None


# Jenis nilai: "temp" dikonversi ke F bila diminta, "percent" diberi sufiks %.
KINDS = {"cpu": "temp", "gpu": "temp", "max": "temp", "nvme": "temp",
         "load": "percent", "ram": "percent", "fixed": "raw"}
TEMP_SOURCES = tuple(k for k, v in KINDS.items() if v == "temp")


def read(source, root=HWMON):
    """Kembalikan nilai sumber, atau None bila sensor tak tersedia."""
    if source == "cpu":
        return cpu_temp(root)
    if source == "gpu":
        return gpu_temp(root)
    if source == "nvme":
        return nvme_temp(root)
    if source == "max":
        values = [v for v in (cpu_temp(root), gpu_temp(root), nvme_temp(root)) if v is not None]
        return max(values) if values else None
    if source == "load":
        return cpu_load()
    if source == "ram":
        return ram_percent()
    raise ValueError(f"sumber tidak dikenal: {source}")
