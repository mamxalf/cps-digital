# RT400 Digital display protocol

USB `1a2c:444d` ("SEMICO USB Gaming Keyboard"), interface 1, vendor collection
usage page `0xff01`, report ID 7, feature/output reports of 63 bytes (64 with the report ID).

Sent with `HIDIOCSFEATURE(64)` (`0xc0404806`):

| Byte | Value | Meaning |
| --- | --- | --- |
| 0 | `07` | Report ID |
| 1 | `ff` | Temperature command (`fd` = version query) |
| 2 | `ff` | Constant prefix |
| 3-5 | digits | hundreds (0-1), tens, ones; range 0-199 |
| 6-63 | `00` | Padding |

The display only shows the number 0-199; it cannot show free text. Fahrenheit is converted on the
host (`int(int(C) * 1.8 + 32)`, clamped to 199).

## Sources and verification status

- The packet layout comes from https://github.com/ppfmr-arch/rt500-linux (MIT), which analysed the
  official CPS-Digital `DeviceDriver.exe` and validated it on an **RT500**.
- Why it applies to the RT400: the same VID:PID, `DeviceDriver.exe` from CPS-Digital 1.0.1.4 contains
  `VID_1A2C&PID_444D`, and the hidraw descriptor of an RT400 matches the collection above exactly.
- **Confirmed on an RT400**: the temperature command was sent to real hardware and the number on the
  display matched the CPU temperature. The version query (`fd`) is implemented but its reply is not
  mapped to a version number.
- No other command was found or sent. Anything beyond `ff` and `fd` is unexplored; do not guess
  at bytes, the same interface also carries the keyboard-style collections of the device.
