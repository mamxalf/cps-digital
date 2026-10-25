# PCCooler RT400 Digital di Linux (Omarchy)

- `rt400d` : daemon (systemd user) yang mengirim suhu CPU/GPU ke layar tiap detik
- `rt400ctl`: `status`, `set --source cpu|gpu|max|fixed --unit c|f --fixed N`, `dry-run`, `version`
- `plugin/`: widget bar Omarchy (klik membuka panel: sumber CPU/GPU/max/fixed dan satuan °C/°F)

Pasang: `./install.sh` (meminta sudo untuk udev rule). Detail protokol: `docs/PROTOCOL.md`.
Protokol dari proyek MIT ppfmr-arch/rt500-linux (RT500, perangkat serumpun).
Tes: `python3 -I -m unittest discover -s tests -t .`
