"""
TachyonCAN - Feather RP2040 CAN
Passive CAN bus sniffer @ 500kbps
Target: 2024 Toyota Tacoma OBD-II port
Output: Raw frames over UART to Tachyon (via ISO7721)

Wiring:
  CAN TX -> Feather CAN TX
  CAN RX -> Feather CAN RX
  UART TX -> Feather TX (to ISO7721 input)
"""

import board
import canio
import busio
import digitalio
import time

# ── UART to Tachyon (via ISO7721) ─────────────────────────────────────────────
# TX only for now — we are not receiving commands from Tachyon yet
uart = busio.UART(
    tx=board.TX,
    rx=board.RX,
    baudrate=115200,
    timeout=0
)

# ── CAN Bus @ 500kbps, listen-only ────────────────────────────────────────────
can = canio.CAN(
    rx=board.CAN_RX,
    tx=board.CAN_TX,
    baudrate=500_000,
    auto_restart=True
)

# Listen-only: no filters = accept all frames (11-bit and 29-bit)
listener = can.listen(matches=[], timeout=0.1)

# ── Status LED (Feather onboard LED) ──────────────────────────────────────────
# Feather RP2040 CAN has a single red LED on board.LED (digitalio)
# OFF = idle, ON = frame activity
import digitalio
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False  # Start idle/off

# ── Frame counter ──────────────────────────────────────────────────────────────
frame_count = 0
last_report = time.monotonic()

def format_frame(frame):
    """
    Format a CAN frame as a compact CSV string for UART transmission.
    Format: ID,EXT,DLC,DATA_HEX\n
    Example: 07E8,0,8,0141000000000000\n
    """
    ext = 1 if frame.extended else 0
    data_hex = "".join("{:02X}".format(b) for b in frame.data)
    return "{:04X},{},{},{}\n".format(frame.id, ext, len(frame.data), data_hex)

def uart_send(line):
    """Send a UTF-8 encoded line over UART."""
    uart.write(line.encode("utf-8"))

# ── Startup message ────────────────────────────────────────────────────────────
uart_send("TachyonCAN READY 500kbps LISTEN-ONLY\n")
print("TachyonCAN READY - listening at 500kbps")

# ── Main loop ──────────────────────────────────────────────────────────────────
while True:
    # Read available frames (non-blocking, up to 8 at a time)
    for _ in range(8):
        frame = listener.receive()
        if frame is None:
            break

        frame_count += 1
        line = format_frame(frame)

        # Send to Tachyon over UART
        uart_send(line)

        # Also echo to USB serial for dev/debug
        print(line, end="")

        # Flash LED on frame activity
        led.value = True

    # Heartbeat report every 5 seconds
    now = time.monotonic()
    if now - last_report >= 5.0:
        report = "HEARTBEAT frames={}\n".format(frame_count)
        uart_send(report)
        print(report, end="")
        last_report = now
        frame_count = 0

    # Return LED to idle after activity
    led.value = False
