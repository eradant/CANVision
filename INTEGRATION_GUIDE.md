# TachyonCAN — Bring-Up & Integration Guide

## Libraries Required

### Feather (CircuitPython)
| Library | Source | Notes |
|---|---|---|
| `canio` | Built-in | CAN bus |
| `busio` | Built-in | UART |
| `board` | Built-in | Pin definitions |
| `time` | Built-in | Timing |
| `neopixel` | Adafruit bundle | NeoPixel LED |

Install neopixel: copy `neopixel.mpy` from Adafruit CircuitPython bundle to `/lib/` on CIRCUITPY drive.

### Tachyon (Linux)
```bash
pip3 install pyserial --break-system-packages
pip3 install rpi_ws281x --break-system-packages   # optional, for SK6812 LED
```

---

## Step 1 — Flash Feather

1. Copy `firmware/code.py` to CIRCUITPY root
2. Copy `neopixel.mpy` to CIRCUITPY `/lib/`
3. LED should go RED on boot (waiting for CAN frames)

---

## Step 2 — Confirm Serial Port on Tachyon

```bash
ls /dev/tty*
# Look for /dev/ttyHS2 or similar
# If different, update SERIAL_PORT in tachyon_serial.py
```

Test raw serial first:
```bash
screen /dev/ttyHS2 115200
# Should see JSON lines when Feather is connected and CAN bus active
# Ctrl+A then K to exit screen
```

---

## Step 3 — Deploy Tachyon Script

```bash
# Create project directory
mkdir -p /home/user/tachyoncan

# Copy files
cp tachyon_serial.py /home/user/tachyoncan/
cp tachyoncan.service /etc/systemd/system/

# Install service
systemctl daemon-reload
systemctl enable tachyoncan
systemctl start tachyoncan

# Validate
systemctl status tachyoncan
journalctl -fu tachyoncan
```

---

## Step 4 — Terminal Validation

Run manually first (before enabling service) to watch live data:
```bash
python3 /home/user/tachyoncan/tachyon_serial.py
```

Expected output when connected to running vehicle:
```
{"id":"07E8","ch":"obd_response","pid":12,"name":"rpm","value":850.0,"unit":"rpm"}
{"id":"07E8","ch":"obd_response","pid":13,"name":"vehicle_speed","value":0,"unit":"kph"}
{"id":"07E8","ch":"obd_response","pid":5,"name":"coolant_temp","value":82,"unit":"C"}
```

---

## Step 5 — Node-RED Integration

### Serial In Node Setup
- Port: `/dev/ttyHS2`
- Baud rate: `115200`
- Delimiter: `\n`
- Output: `String`

### Wiring
```
[Serial In] -> [nodered_live_function.js] -> [existing dashboard nodes]
```

### Replacing Sim Data
1. Disable/delete your `heartbeat > sim engine function` nodes
2. Wire `[Serial In] -> [Live Data Function] -> [http out]`
3. The function outputs `msg.topic` = channel name, `msg.payload.value` = value
4. Update any dashboard functions that reference sim variable names to use the `channelMap` keys

### Channel Map (sim → live)
| Sim variable | Live channel | Unit |
|---|---|---|
| rpm | rpm | rpm |
| speed | vehicle_speed | kph |
| coolant | coolant_temp | °C |
| throttle | throttle_pos | % |
| load | engine_load | % |
| iat | intake_air_temp | °C |
| map | map_kpa | kPa |

---

## Step 6 — Headless Auto-Start Verification

After reboot, confirm everything starts automatically:
```bash
sudo reboot

# After boot:
systemctl status tachyoncan        # serial validator running?
systemctl status nodered           # node-red running?
systemctl status cloudflared       # tunnel running?

# Check log
journalctl -fu tachyoncan
```

---

## Pin Reference

### Feather RP2040 CAN
| Function | Pin |
|---|---|
| CAN RX | board.CAN_RX |
| CAN TX | board.CAN_TX |
| UART TX → ISO7721 | board.MOSI |
| UART RX ← ISO7721 | board.MISO |
| Status LED | board.NEOPIXEL |

### Tachyon
| Function | Pin |
|---|---|
| UART TX → ISO7721 | PIN 8 |
| UART RX ← ISO7721 | PIN 10 |
| SK6812 LED data | PIN 12 |
| I2C SDA (future GPS/IMU) | PIN 3 |
| I2C SCL (future GPS/IMU) | PIN 5 |

---

## LED Status Reference

| LED | Color | Meaning |
|---|---|---|
| Feather NeoPixel | RED | No CAN frames received |
| Feather NeoPixel | GREEN | CAN frames active |
| Tachyon SK6812 | RED | Serial port not receiving |
| Tachyon SK6812 | GREEN | Data flowing from Feather |

---

## Troubleshooting

**No frames on Feather REPL**
- Check CAN bus speed (500kbps for 2024 Tacoma)
- Verify CANH/CANL wiring at J2
- Try with ignition ON, engine running

**Frames on Feather but not on Tachyon**
- Confirm ISO7721 powered (3.3V confirmed on board)
- Check MOSI→PIN10 and MISO←PIN8 wiring
- Test with `screen /dev/ttyHS2 115200` directly

**Serial port not found**
- Run `ls /dev/tty*` with and without Feather powered
- Update `SERIAL_PORT` in `tachyon_serial.py`

**Node-RED not receiving data**
- Confirm Serial In node port matches `SERIAL_PORT`
- Check delimiter is set to `\n`
- Use Node-RED debug node on Serial In output before the function
