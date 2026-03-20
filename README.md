# TachyonCAN

An isolated automotive telemetry and visualization interface that bridges a vehicle's CAN bus with a high-level single-board computer.

## Overview

TachyonCAN uses a dual-controller architecture to safely interface with a vehicle's CAN bus and present live telemetry data on a hosted dashboard.

- **Adafruit Feather RP2040 CAN** — real-time CAN bus communication (dirty/chassis domain)
- **Particle Tachyon** — high-level processing, UART ingestion, Node-RED dashboard hosting (clean/logic domain)
- **ISO7721 digital isolator** — galvanic isolation barrier between the two domains

The board is designed around a 12V automotive input with a full protection chain: Fuse → Schottky → TVS → Bulk Cap → OKI-78SR 5V regulator.

## Repository Structure

```
TachyonCAN/
├── hardware/        # KiCad schematic and PCB files
├── firmware/        # CircuitPython firmware for Feather RP2040 CAN
├── nodered/         # Node-RED flow exports for Tachyon dashboard
└── docs/            # BOM, pinouts, notes, and bring-up procedures
```

## Hardware

### Architecture

The board is divided into two galvanically isolated domains separated by a physical moat and the ISO7721 digital isolator.

| Domain | Ground | Contents |
|---|---|---|
| Domain 1 (Chassis) | GND1 | 12V input, protection circuit, OKI-78SR regulator, Feather RP2040 CAN, CAN transceiver |
| Domain 2 (Logic) | GND2 | Particle Tachyon, SK6812mini-E status LED, I2C breakout |

### Protection Chain

```
12V IN → Fuse (F1) → Schottky (D1) → TVS SMAJ15A (D2) → 100µF Bulk Cap (C6) → OKI-78SR 5V → Feather
```

### Key Components

| Ref | Component | Description |
|---|---|---|
| A1 | Adafruit Feather RP2040 CAN | Real-time CAN controller |
| J1 | 2×20 pin socket | Particle Tachyon connector |
| J2 | Phoenix 5-pos screw terminal | 12V power + CAN bus input |
| J3 | 1×4 pin header | I2C breakout |
| U1 | ISO7721D | High-speed digital isolator |
| U2 | OKI-78SR-5/1.5-W36-C | 5V buck regulator |
| D1 | B340A-13-F | 40V/3A Schottky (reverse polarity) |
| D2 | SMAJ15A | 15V TVS (transient protection) |
| D3 | SK6812mini-E | Addressable RGB status LED |
| F1 | Fuse 1206 | Overcurrent protection |

### OBD-II Connector Pinout

| OBD-II Pin | Signal | Board Connection |
|---|---|---|
| 6 | CAN High | J2 CANH |
| 14 | CAN Low | J2 CANL |
| 4 or 5 | Chassis GND | J2 GND |
| 16 | 12V | J2 VIN |

## Firmware

CircuitPython on the Feather RP2040 CAN. See `firmware/` for `code.py`.

### Features
- Passive CAN bus sniffing @ 500kbps
- Listen-only mode (no bus interference)
- Frames forwarded over UART to Tachyon via ISO7721
- USB REPL output for development/debugging
- Onboard LED activity indicator

### Frame Format (UART output)
Frames are sent as CSV lines:
```
ID,EXT,DLC,DATA_HEX\n
07E8,0,8,0141000000000000
```

### Libraries Required
All dependencies are built into CircuitPython — no external libraries needed:
- `canio`
- `busio`
- `digitalio`

### CircuitPython Version
Download the Feather RP2040 CAN specific build from [circuitpython.org](https://circuitpython.org/board/adafruit_feather_rp2040_can/)

## Dashboard

Node-RED running on the Particle Tachyon. See `nodered/` for flow exports.

- Receives UART stream from Feather via ISO7721
- Parses CAN frames
- Displays live telemetry on hosted web dashboard

## Bring-Up Procedure

1. Solder all components **except** the Feather
2. Apply 12V @ 1.5A from bench supply via J2
3. Verify 5V at Feather power pins
4. Verify GND1 and GND2 are isolated (no continuity)
5. Solder Feather headers and seat Feather
6. Flash latest CircuitPython firmware
7. Copy `firmware/code.py` to Feather CIRCUITPY drive
8. Connect to vehicle OBD-II port and monitor REPL

## Target Vehicle

Initial development and testing: **2024 Toyota Tacoma**
- CAN bus speed: 500kbps
- Interface: OBD-II port (gatewayed)

## Status

- [x] PCB design complete
- [x] Board ordered for fabrication
- [x] Components ordered
- [ ] Board bring-up
- [ ] CAN bus validation
- [ ] UART pipeline (Feather → Tachyon)
- [ ] Node-RED live data integration
- [ ] V2 planning

## License

MIT
