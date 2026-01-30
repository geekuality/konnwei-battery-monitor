"""Constants for the Konnwei Battery Monitor integration."""

DOMAIN = "konnwei_battery_monitor"

# BLE identifiers
MAC_PREFIX = "B3:00"
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_WRITE_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# Commands (pre-calculated packets for common operations)
CMD_STATUS_POLL = bytes.fromhex("40400A000B0BA9B20D0A")
CMD_DEVICE_INFO = bytes.fromhex("40400A00030133D30D0A")

# Configuration keys
CONF_BATTERY_TYPE = "battery_type"
CONF_VOLTAGE_MIN = "voltage_min"
CONF_VOLTAGE_MAX = "voltage_max"
CONF_POLL_INTERVAL = "poll_interval"

# Battery presets: (min_voltage, max_voltage)
BATTERY_PRESETS = {
    "12v_lead_acid": {"min": 10.5, "max": 12.8, "name": "12V Lead Acid"},
    "12v_agm": {"min": 10.5, "max": 12.9, "name": "12V AGM"},
    "12v_lifepo4": {"min": 10.0, "max": 14.6, "name": "12V LiFePO4 (4S)"},
    "12v_lithium": {"min": 9.0, "max": 12.6, "name": "12V Li-Ion (3S)"},
    "24v_lead_acid": {"min": 21.0, "max": 25.6, "name": "24V Lead Acid"},
    "24v_lifepo4": {"min": 20.0, "max": 29.2, "name": "24V LiFePO4 (8S)"},
    "6v_lead_acid": {"min": 5.25, "max": 6.4, "name": "6V Lead Acid"},
    "custom": {"min": None, "max": None, "name": "Custom"},
}

# Poll interval settings
DEFAULT_POLL_INTERVAL = 600  # 10 minutes in seconds
MIN_POLL_INTERVAL = 60  # 1 minute minimum
MAX_POLL_INTERVAL = 3600  # 1 hour maximum

# Response timeouts
BLE_RESPONSE_TIMEOUT = 10.0  # seconds

# Voltage limits for validation
MAX_VOLTAGE_LIMIT = 60.0  # Maximum reasonable voltage (V)
MIN_VOLTAGE_LIMIT = 1.0  # Minimum reasonable voltage (V)
