# PCCooler RT400 for Omarchy

Linux support for the **PCCooler RT400 Digital** air cooler's number display, which has no Linux
software. It comes as an Omarchy bar widget with a settings panel, backed by a small daemon.

The display shows a number from 0 to 199. This project chooses which one:

| Source | Shows |
| --- | --- |
| `cpu`, `gpu`, `nvme` | temperature of the CPU, an AMD/Nouveau GPU, or the NVMe SSD |
| `max` | the hottest of the three |
| `load`, `ram` | CPU load or RAM usage, in percent |
| `fixed` | a number you choose (0-199) |
| `rotate` | cycles through a list of the sources above |

Temperatures can be shown in °C or °F. An optional **alert** makes the display blink to `0` while the
temperature is above a threshold. The display cannot show text; see [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Requirements

- Omarchy with the shell plugin system, `systemd --user`, Python 3.10+ (no pip packages)
- A PCCooler RT400 Digital connected through its internal USB cable. It shows up as
  `1a2c:444d`, "SEMICO USB Gaming Keyboard". Other models with the same USB ID (the RT500 uses it) may
  work but are untested.
- NVIDIA GPUs are not supported for the `gpu` source (no hwmon sensor); `max` and the others still work.

## Install

```sh
omarchy plugin add https://github.com/mamxalf/cps-digital.git --enable
~/.config/omarchy/plugins/io.github.mamxalf.pccooler-rt400/install.sh
omarchy bar move io.github.mamxalf.pccooler-rt400 --section right
```

`install.sh` is the only step that needs `sudo`, and only to copy one udev rule
(`udev/70-pccooler-rt400.rules`) to `/etc/udev/rules.d` and reload udev. It then links `rt400ctl` and
`rt400d` into `~/.local/bin` and enables the `rt400d` systemd **user** service. It downloads nothing and
installs no packages. Read it first: it is about 20 lines.

Click the widget in the bar to open the settings panel. After editing the QML yourself, run
`omarchy-restart-shell`; the Omarchy shell does not reload plugin QML on its own.

## Remove

```sh
~/.config/omarchy/plugins/io.github.mamxalf.pccooler-rt400/uninstall.sh
omarchy plugin remove io.github.mamxalf.pccooler-rt400
```

Your settings stay in `~/.config/rt400/config.json`; delete that folder to remove them too.

## Command line

```sh
rt400ctl status
rt400ctl set --source rotate --rotate-sources cpu,load,ram --rotate-seconds 5
rt400ctl set --source cpu --unit f
rt400ctl set --alert on --alert-threshold 85
rt400ctl dry-run --source cpu        # print the packet without sending it
```

## What it touches

- Writes only the temperature command (`ff`) to the display's vendor HID interface, once a second.
  `rt400ctl version` additionally sends the version query (`fd`).
- Reads `/sys/class/hwmon`, `/proc/stat` and `/proc/meminfo`. No network access.
- Control socket: `$XDG_RUNTIME_DIR/rt400.sock`, mode 0600.
- `tools/probe.py` is read-only (sysfs only) and is meant for diagnosing a device that is not found.

## Development

```sh
python3 -I -m unittest discover -s tests -t .
omarchy plugin validate .
```

## Credits and license

The packet layout comes from [ppfmr-arch/rt500-linux](https://github.com/ppfmr-arch/rt500-linux) (MIT),
confirmed here on RT400 hardware. This project is not affiliated with PCCooler.
MIT licensed, see [LICENSE](LICENSE).
