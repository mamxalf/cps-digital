# PCCooler RT400 Digital di Linux (Omarchy)

Layar RT400 hanya menerima angka 0-199 (lihat `docs/PROTOCOL.md`).

- `rt400d` : daemon (systemd user) yang mengirim nilai ke layar tiap detik
- `rt400ctl`: `status`, `set ...`, `dry-run`, `version`
- `plugin/`: widget bar Omarchy; klik membuka panel pengaturan

## Sumber angka
`cpu`, `gpu`, `max` (terpanas), `nvme` (suhu); `load` (beban CPU %), `ram` (%); `fixed` (angka sendiri);
`rotate` (bergantian antar sumber). Satuan °C/°F hanya berlaku untuk suhu.

```
rt400ctl set --source rotate --rotate-sources cpu,load,ram --rotate-seconds 5
rt400ctl set --alert on --alert-threshold 85     # berkedip ke 0 saat suhu >= ambang
```
Pengaturan tersimpan di `~/.config/rt400/config.json`.

## Pasang
`./install.sh` (meminta sudo untuk udev rule). Setelah mengubah QML plugin, jalankan `omarchy-restart-shell`:
shell Omarchy tidak memuat ulang QML otomatis.
Tes: `python3 -I -m unittest discover -s tests -t .`

Protokol dari proyek MIT ppfmr-arch/rt500-linux (RT500, perangkat serumpun), terkonfirmasi di RT400.
