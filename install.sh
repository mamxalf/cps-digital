#!/usr/bin/env bash
# Pasang RT400: udev rule (sudo), daemon + CLI (user), service systemd user, plugin bar Omarchy.
# Bila udev rule lama (99-) ada: sudo rm /etc/udev/rules.d/99-pccooler-rt400.rules
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

sudo rm -f /etc/udev/rules.d/99-pccooler-rt400.rules
sudo install -m 0644 udev/70-pccooler-rt400.rules /etc/udev/rules.d/70-pccooler-rt400.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=hidraw

mkdir -p ~/.local/bin ~/.config/systemd/user
ln -sf "$ROOT/bin/rt400ctl" ~/.local/bin/rt400ctl
ln -sf "$ROOT/bin/rt400d" ~/.local/bin/rt400d
install -m 0644 systemd/rt400d.service ~/.config/systemd/user/rt400d.service
systemctl --user daemon-reload
systemctl --user enable rt400d.service
systemctl --user restart rt400d.service

# Plugin: salin (validator menolak symlink di dalam folder plugin)
rm -rf ~/.config/omarchy/plugins/local.pccooler-rt400
mkdir -p ~/.config/omarchy/plugins
cp -r plugin ~/.config/omarchy/plugins/local.pccooler-rt400
omarchy-shell shell rescanPlugins || true
omarchy plugin enable local.pccooler-rt400 2>/dev/null || true
echo "Selesai. Taruh di bar: omarchy bar move local.pccooler-rt400 --section right"
