#!/usr/bin/env python3
"""
TachyonCAN - Serial Validator
Runs on Particle Tachyon (Linux)
Reads UART from Feather via ISO7721
PIN8=TX, PIN10=RX, PIN12=SK6812 LED data

Auto-starts at boot via systemd (see tachyoncan.service)
Logs to /var/log/tachyoncan.log
Also prints to stdout for terminal validation

Usage:
  python3 tachyon_serial.py           # terminal mode
  journalctl -fu tachyoncan           # follow systemd log
"""

import serial, json, time, sys, os, logging
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
SERIAL_PORT  = "/dev/ttyHS2"   # Tachyon UART - confirm with: ls /dev/tty*
BAUD         = 115200
LOG_FILE     = "/var/log/tachyoncan.log"
LED_PIN      = 12              # SK6812 data pin - driven via rpi_ws281x or similar
PRINT_RAW    = True            # set False to suppress raw frame spam

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("tachyoncan")

# ── SK6812 LED (optional - requires rpi_ws281x) ───────────────────────────────
# Install: pip3 install rpi_ws281x --break-system-packages
# If not available, LED control is skipped gracefully
LED_AVAILABLE = False
strip = None
try:
    from rpi_ws281x import PixelStrip, Color
    strip = PixelStrip(1, LED_PIN, 800000, 5, False, 255, 0)
    strip.begin()
    LED_AVAILABLE = True
    log.info("SK6812 LED initialized on pin {}".format(LED_PIN))
except Exception as e:
    log.warning("SK6812 not available: {} - continuing without LED".format(e))

def set_led(r, g, b):
    if LED_AVAILABLE and strip:
        strip.setPixelColor(0, Color(r, g, b))
        strip.show()

set_led(50, 0, 0)  # Red = waiting for data

# ── Channel state (latest values) ────────────────────────────────────────────
# This dict is what Node-RED will read - keys match dashboard channel names
state = {
    "rpm":              None,
    "vehicle_speed":    None,
    "coolant_temp":     None,
    "intake_air_temp":  None,
    "throttle_pos":     None,
    "engine_load":      None,
    "map_kpa":          None,
    "maf_g_per_sec":    None,
    "stft_b1":          None,
    "ltft_b1":          None,
    "oil_temp":         None,
    "fuel_level":       None,
    "fuel_flow":        None,
    "baro_kpa":         None,
    "ambient_air_temp": None,
    "run_time":         None,
    "last_frame_ts":    None,
    "frame_count":      0,
}

def process_line(raw):
    """Parse incoming JSON line from Feather. Update state. Return parsed dict."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Bad JSON: {}".format(raw))
        return None

    # Decoded OBD channel
    if "name" in obj and "value" in obj:
        ch = obj["name"]
        if ch in state:
            state[ch] = obj["value"]
        state["last_frame_ts"] = datetime.now().isoformat()
        state["frame_count"] += 1

    # Heartbeat
    if obj.get("status") == "HB":
        log.info("Feather HB: {} frames".format(obj.get("frames", "?")))

    # Ready
    if obj.get("status") == "READY":
        log.info("Feather online: {}".format(raw))

    return obj

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("TachyonCAN serial validator starting on {}".format(SERIAL_PORT))

    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
            log.info("Serial port open")
            set_led(0, 50, 0)  # Green = connected

            last_data = time.time()

            while True:
                line = ser.readline().decode("utf-8", errors="replace")
                if line:
                    last_data = time.time()
                    obj = process_line(line)
                    if obj and PRINT_RAW:
                        print(line, end="")
                    set_led(0, 50, 0)  # Green flash on data
                else:
                    # No data for 5s -> red
                    if time.time() - last_data > 5:
                        set_led(50, 0, 0)

        except serial.SerialException as e:
            log.error("Serial error: {} - retrying in 3s".format(e))
            set_led(50, 0, 0)
            time.sleep(3)
        except KeyboardInterrupt:
            log.info("Stopped by user")
            set_led(0, 0, 0)
            sys.exit(0)

if __name__ == "__main__":
    main()
