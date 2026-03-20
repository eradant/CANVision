# TachyonCAN — Bill of Materials

| Ref | Value | Package | Description | Source |
|---|---|---|---|---|
| A1 | Adafruit Feather RP2040 CAN | Feather | Real-time CAN controller | Adafruit #5724 |
| J1 | Conn_02x20 | PinSocket 2x20 2.54mm | Particle Tachyon connector | — |
| J2 | Screw Terminal | Phoenix PT-1,5-5-3.5-H | 5-pos 3.5mm pitch power/CAN input | — |
| J3 | Conn_01x04 | PinHeader 1x4 2.54mm | I2C breakout | — |
| U1 | ISO7721D | SOIC-8 | High-speed 2ch digital isolator | TI |
| U2 | OKI-78SR-5/1.5-W36-C | SIP vertical | 5V/1.5A buck regulator | Murata |
| D1 | B340A-13-F | SMA (DO-214AC) | 40V/3A Schottky, reverse polarity | Diodes Inc. |
| D2 | SMAJ15A | SMA (DO-214AC) | 15V TVS, transient protection | — |
| D3 | SK6812mini-E | 3228 reverse-mount | Addressable RGB status LED | — |
| F1 | Fuse | 1206 | Overcurrent protection | — |
| C1-C5 | 10µF | 0805 / 50V | Ceramic decoupling capacitors | — |
| C6 | 100µF | 6.3x5.4mm SMD | Bulk electrolytic capacitor | Panasonic EEE-FT1V101AP |

---

# Pinouts

## J2 — Power / CAN Input (Phoenix 5-pos, 3.5mm pitch)

| Pin | Signal | Notes |
|---|---|---|
| 1 | VIN | 12V automotive input |
| 2 | GND | Chassis ground |
| 3 | CANH | CAN bus high |
| 4 | CANL | CAN bus low |
| 5 | SHIELD | Optional cable shield ground |

## J3 — I2C Breakout (1x4, 2.54mm pitch)

| Pin | Signal |
|---|---|
| 1 | VCC (3.3V) |
| 2 | GND2 |
| 3 | SDA |
| 4 | SCL |

## OBD-II to J2 Wiring

| OBD-II Pin | Signal | J2 Pin |
|---|---|---|
| 16 | 12V | VIN |
| 4 or 5 | GND | GND |
| 6 | CAN High | CANH |
| 14 | CAN Low | CANL |

---

# Isolation Domains

| Domain | Ground Net | Covers |
|---|---|---|
| Domain 1 (Chassis) | GND1 | 12V input, protection chain, OKI-78SR, Feather, CAN transceiver |
| Domain 2 (Logic) | GND2 | Particle Tachyon, SK6812 LED, I2C |

Isolation barrier: ISO7721D (SOIC-8), physical moat in PCB copper pours.
GND1 and GND2 must never be bridged.
