#!/usr/bin/env bash
# Remove everything install.sh created. Your settings in ~/.config/rt400 are kept.
set -euo pipefail

systemctl --user disable --now rt400d.service 2>/dev/null || true
rm -f ~/.config/systemd/user/rt400d.service ~/.local/bin/rt400ctl ~/.local/bin/rt400d
systemctl --user daemon-reload

sudo rm -f /etc/udev/rules.d/70-pccooler-rt400.rules
sudo udevadm control --reload-rules

echo "Done. Remove the bar plugin with: omarchy plugin remove io.github.mamxalf.pccooler-rt400"
echo "Optional: rm -r ~/.config/rt400   (saved settings)"
