#!/usr/bin/env bash
# Install the RT400 daemon and CLI. The bar plugin itself is installed with
# `omarchy plugin add` (see README).
#
# What this script does:
#   - sudo: copies one udev rule to /etc/udev/rules.d and reloads udev (the only privileged step)
#   - links rt400ctl and rt400d into ~/.local/bin
#   - installs and starts the systemd *user* service rt400d
# It does not download anything and installs no packages.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

sudo install -m 0644 "$ROOT/udev/70-pccooler-rt400.rules" /etc/udev/rules.d/70-pccooler-rt400.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=hidraw

mkdir -p ~/.local/bin ~/.config/systemd/user
ln -sf "$ROOT/bin/rt400ctl" ~/.local/bin/rt400ctl
ln -sf "$ROOT/bin/rt400d" ~/.local/bin/rt400d
install -m 0644 "$ROOT/systemd/rt400d.service" ~/.config/systemd/user/rt400d.service
systemctl --user daemon-reload
systemctl --user enable rt400d.service
systemctl --user restart rt400d.service

echo "Done. Check with: rt400ctl status"
