"""
TachyonCAN v1 - Feather RP2040 CAN
Passive CAN sniffer + OBD-II decoder
Target: 2024 Toyota Tacoma @ 500kbps
UART: MOSI(TX) -> ISO7721 -> Tachyon PIN10(RX)
      MISO(RX) <- ISO7721 <- Tachyon PIN8(TX)

Libraries required (all built-in to CircuitPython):
  canio, busio, digitalio, neopixel, time, board
External bundle lib needed:
  neopixel (adafruit-circuitpython-neopixel)
"""

import board, busio, canio, time
import neopixel

# ── NeoPixel LED ──────────────────────────────────────────────────────────────
# Feather RP2040 CAN has onboard NeoPixel on board.NEOPIXEL
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.15, auto_write=True)
RED   = (50, 0, 0)
GREEN = (0, 50, 0)
OFF   = (0, 0, 0)
pixel[0] = RED  # Red until frames arrive

# ── UART to Tachyon via ISO7721 ───────────────────────────────────────────────
uart = busio.UART(tx=board.MOSI, rx=board.MISO, baudrate=115200, timeout=0)

# ── CAN @ 500kbps listen-only ─────────────────────────────────────────────────
can = canio.CAN(rx=board.CAN_RX, tx=board.CAN_TX, baudrate=500_000, auto_restart=True)
listener = can.listen(matches=[], timeout=0.1)

# ── OBD-II PID decode table ───────────────────────────────────────────────────
# Response ID 0x7E8 = ECU response to 0x7DF requests
# Format: pid -> (name, unit, formula(bytes))
# bytes = list of data bytes from OBD response (byte 0 = mode, byte 1 = PID, byte 2+ = data)
OBD_PIDS = {
    0x04: ("engine_load",      "%",   lambda b: round(b[2] / 2.55, 1)),
    0x05: ("coolant_temp",     "C",   lambda b: b[2] - 40),
    0x06: ("stft_b1",          "%",   lambda b: round((b[2] - 128) * 100 / 128, 1)),
    0x07: ("ltft_b1",          "%",   lambda b: round((b[2] - 128) * 100 / 128, 1)),
    0x0B: ("map_kpa",          "kPa", lambda b: b[2]),
    0x0C: ("rpm",              "rpm", lambda b: round(((b[2] * 256) + b[3]) / 4, 0)),
    0x0D: ("vehicle_speed",    "kph", lambda b: b[2]),
    0x0F: ("intake_air_temp",  "C",   lambda b: b[2] - 40),
    0x10: ("maf_g_per_sec",    "g/s", lambda b: round(((b[2] * 256) + b[3]) / 100, 2)),
    0x11: ("throttle_pos",     "%",   lambda b: round(b[2] / 2.55, 1)),
    0x1F: ("run_time",         "s",   lambda b: (b[2] * 256) + b[3]),
    0x2F: ("fuel_level",       "%",   lambda b: round(b[2] / 2.55, 1)),
    0x33: ("baro_kpa",         "kPa", lambda b: b[2]),
    0x46: ("ambient_air_temp", "C",   lambda b: b[2] - 40),
    0x5C: ("oil_temp",         "C",   lambda b: b[2] - 40),
    0x5E: ("fuel_flow",        "L/h", lambda b: round(((b[2] * 256) + b[3]) / 20, 2)),
}

# ── Toyota Tacoma known broadcast IDs (passive sniff) ────────────────────────
# These are observed frame IDs — decoded fields are best-effort
# Confirm/adjust values after live bus validation
TOYOTA_IDS = {
    0x025: "wheel_speeds",
    0x0AA: "brake_status",
    0x0B4: "vehicle_speed_raw",
    0x224: "throttle_raw",
    0x245: "engine_raw",
    0x360: "transmission",
    0x394: "steering_angle",
    0x3BC: "yaw_rate",
    0x620: "hvac",
    0x750: "gateway",
    0x7E8: "obd_response",
    0x7DF: "obd_request",
}

# ── State ─────────────────────────────────────────────────────────────────────
frame_count  = 0
last_hb      = time.monotonic()
receiving    = False

def send(line):
    uart.write(line.encode("utf-8"))
    print(line, end="")

def decode_obd(data_bytes):
    """Parse OBD-II mode 01 response. Returns dict or None."""
    if len(data_bytes) < 3:
        return None
    if data_bytes[0] != 0x41:   # mode 01 response byte
        return None
    pid = data_bytes[1]
    if pid in OBD_PIDS:
        name, unit, formula = OBD_PIDS[pid]
        try:
            val = formula(data_bytes)
            return {"name": name, "value": val, "unit": unit, "pid": pid}
        except Exception:
            return None
    return None

def format_frame(frame):
    """
    Produce a JSON-like single-line string for Node-RED ingestion.
    Format: {"id":"07E8","ch":"obd_response","pid":12,"name":"rpm","value":1250,"unit":"rpm"}\n
    For unknown/raw frames: {"id":"0245","ch":"engine_raw","raw":"A1B2C3D4E5F60708"}\n
    """
    fid  = frame.id
    data = list(frame.data)
    hex_data = "".join("{:02X}".format(b) for b in data)
    ch   = TOYOTA_IDS.get(fid, "unknown")

    # Attempt OBD decode on response frames
    if fid == 0x7E8 and len(data) >= 3:
        decoded = decode_obd(data[1:])  # skip length byte at data[0]
        if decoded:
            return '{{"id":"{:04X}","ch":"{}","pid":{},"name":"{}","value":{},"unit":"{}"}}\n'.format(
                fid, ch, decoded["pid"], decoded["name"], decoded["value"], decoded["unit"])

    # Raw frame
    return '{{"id":"{:04X}","ch":"{}","raw":"{}"}}\n'.format(fid, ch, hex_data)

# ── Startup ───────────────────────────────────────────────────────────────────
send('{"status":"READY","baud":500000,"mode":"LISTEN"}\n')

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    got_frame = False

    for _ in range(16):
        frame = listener.receive()
        if frame is None:
            break
        frame_count += 1
        got_frame = True
        send(format_frame(frame))

    # LED: green if receiving, red if not
    if got_frame:
        receiving = True
        pixel[0] = GREEN
    else:
        if receiving:
            pixel[0] = RED
            receiving = False

    # Heartbeat every 10s
    now = time.monotonic()
    if now - last_hb >= 10.0:
        send('{{"status":"HB","frames":{}}}\n'.format(frame_count))
        last_hb = now
        frame_count = 0
