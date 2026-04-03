// TachyonCAN - Node-RED Live Data Function
// Replace your existing sim engine function with this
// Input: msg.payload = JSON string from serial port
// Output: msg.payload = normalized channel object matching dashboard expectations
//
// Wire up:
//   [Serial In /dev/ttyHS2 115200 \n] -> [this function] -> [existing dashboard nodes]
//
// Serial In node config:
//   Port: /dev/ttyHS2
//   Baud: 115200
//   Delimiter: \n
//   Output: String

// Parse incoming line
let raw = msg.payload;
let obj;

try {
    obj = JSON.parse(raw);
} catch(e) {
    // Skip unparseable lines
    return null;
}

// Skip status/heartbeat messages from data flow
// (they are still logged by the serial validator)
if (obj.status) return null;

// ── Decoded OBD frame ─────────────────────────────────────────────────────────
if (obj.name && obj.value !== undefined) {
    // Map incoming channel name to dashboard payload
    // Extend this map to match your existing dashboard variable names
    const channelMap = {
        rpm:              "rpm",
        vehicle_speed:    "speed",
        coolant_temp:     "coolant",
        intake_air_temp:  "iat",
        throttle_pos:     "throttle",
        engine_load:      "load",
        map_kpa:          "map",
        maf_g_per_sec:    "maf",
        stft_b1:          "stft",
        ltft_b1:          "ltft",
        oil_temp:         "oil_temp",
        fuel_level:       "fuel",
        fuel_flow:        "fuel_flow",
        baro_kpa:         "baro",
        ambient_air_temp: "ambient",
        run_time:         "run_time",
    };

    const dashKey = channelMap[obj.name];
    if (!dashKey) return null;

    // Emit single-channel update
    msg.payload = {
        channel:   dashKey,
        value:     obj.value,
        unit:      obj.unit,
        pid:       obj.pid,
        timestamp: Date.now()
    };
    msg.topic = dashKey;
    return msg;
}

// ── Raw frame (unknown/broadcast) ─────────────────────────────────────────────
if (obj.raw) {
    // Forward raw frames to a debug output - don't push to dashboard
    msg.payload = obj;
    msg.topic   = "raw";
    // Only pass through if you have a raw debug node wired up
    // return msg;
    return null;
}

return null;
