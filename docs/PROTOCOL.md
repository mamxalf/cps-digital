# Protokol layar RT400 Digital

USB `1a2c:444d` ("SEMICO USB Gaming Keyboard"), interface 1, vendor collection
Usage Page `0xff01`, Report ID 7, Feature/Output 63 byte (64 dengan report ID).

Dikirim lewat `HIDIOCSFEATURE(64)` (`0xc0404806`):

| Byte | Nilai | Arti |
| --- | --- | --- |
| 0 | `07` | Report ID |
| 1 | `ff` | Perintah suhu (`fd` = query versi) |
| 2 | `ff` | Prefix konstan |
| 3-5 | digit | ratusan (0-1), puluhan, satuan; rentang 0-199 |
| 6-63 | `00` | Padding |

Layar hanya menampilkan angka 0-199, bukan teks bebas. Satuan F dikonversi di host
(`int(int(C)*1.8+32)`, clamp 199).

## Sumber dan status verifikasi
- Pemetaan paket berasal dari https://github.com/ppfmr-arch/rt500-linux (MIT), yang
  menganalisis `DeviceDriver.exe` CPS-Digital dan memvalidasinya di **RT500**.
- Kesamaan dengan RT400: VID:PID sama, `DeviceDriver.exe` dari installer 1.0.1.4 memuat
  `VID_1A2C&PID_444D`, dan descriptor hidraw7 di mesin ini cocok persis dengan koleksi di atas.
- **Belum diverifikasi di RT400**: paket belum pernah dikirim ke perangkat ini.
