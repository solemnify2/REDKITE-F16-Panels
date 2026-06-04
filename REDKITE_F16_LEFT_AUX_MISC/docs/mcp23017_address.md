# MCP23017 I2C Address Configuration

## Address Pins (A0, A1, A2)
- Connect each pin directly to VDD (3.3V) or GND
- Do NOT leave floating

## Address Table

| Address | A2 | A1 | A0 |
|---------|----|----|-----|
| 0x20 | GND | GND | GND |
| 0x21 | GND | GND | VDD |
| 0x22 | GND | VDD | GND |
| 0x23 | GND | VDD | VDD |
| 0x24 | VDD | GND | GND |
| 0x25 | VDD | GND | VDD |
| 0x26 | VDD | GND | VDD |
| 0x27 | VDD | VDD | VDD |

- Max 8 devices on one I2C bus
- For 4 devices: fix A2=GND, use A0/A1 combinations (0x20~0x23)
