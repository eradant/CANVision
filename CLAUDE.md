# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TachyonCAN** is an automotive telemetry interface that bridges a vehicle's CAN bus to a hosted dashboard. It uses a dual-controller architecture with galvanic isolation for safety.

## Architecture

The system has three layers connected in sequence:

```
Vehicle OBD-II → [Chassis Domain] → ISO7721 Isolator → [Logic Domain] → Web Dashboard
                  Feather RP2040 CAN                    Particle Tachyon
                  (CircuitPython)                       (Node-RED)
```

**Two galvanically isolated ground domains (physical moat on PCB):**
- **Domain 1 (GND1, Chassis):** 12V input, protection chain, OKI-78SR 5V regulator, Feather RP2040 CAN
- **Domain 2 (GND2, Logic):** Particle Tachyon, SK6812mini-E status LED, I2C breakout

The isolation barrier (ISO7721D) is safety-critical — never create continuity between GND1 and GND2.

## Repository Layout

| Directory | Contents |
|---|---|
| `Firmware/` | CircuitPython `code.py` for Feather RP2040 CAN |
| `Hardware/` | KiCad schematic and PCB files (not yet committed) |
| `nodered/` | Node-RED flow exports for Tachyon dashboard (not yet committed) |
| `Docs/` | BOM, pinouts, isolation domain notes |

## Firmware

**Language:** CircuitPython (no compilation, no build step, no external libraries)

**Deployment:** Copy `Firmware/code.py` directly to the Feather's `CIRCUITPY` drive (USB mass storage). The file runs immediately on save.

**UART frame format** (sent from Feather → Tachyon via ISO7721 at 115200 baud):
```
ID,EXT,DLC,DATA_HEX\n
07E8,0,8,0141000000000000
HEARTBEAT frames=42
```

**Debug:** Connect USB to Feather and open serial REPL — all frames and heartbeats are echoed there. Use `screen /dev/tty.usbmodem* 115200` or similar.

## Key Hardware Details

- CAN bus speed: 500kbps (listen-only mode — firmware never transmits on bus)
- Power input: 12V via J2 Phoenix screw terminal (OBD-II pins 4/5 = GND, pin 16 = 12V, pins 6/14 = CANH/CANL)
- 5V rail is chassis-domain only; Tachyon is powered separately via its own connector (J1)
