# Konnwei Battery Monitor

Home Assistant custom integration for Konnwei BK-series battery monitors (BK100, BK200, BK300, KW700).

## Features

- Bluetooth Low Energy communication
- Auto-discovery of devices via MAC prefix
- Real-time voltage monitoring
- Battery state of charge calculation
- Charging status detection
- Configurable battery types and voltage ranges
- Adjustable polling interval

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Konnwei Battery Monitor" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/konnwei_battery_monitor` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

The integration will automatically discover Konnwei devices with MAC addresses starting with `B3:00`.

### Setup

1. Go to Configuration → Integrations
2. Click the "+" button
3. Select "Konnwei Battery Monitor"
4. Choose your device from the list
5. Configure battery type and voltage range
6. Set polling interval (default: 10 minutes)

### Battery Types

Preset configurations are available for:
- 12V Lead Acid
- 12V AGM
- 12V LiFePO4 (4S)
- 12V Li-Ion (3S)
- 24V Lead Acid
- 24V LiFePO4 (8S)
- 6V Lead Acid
- Custom (manual voltage range)

## Entities

Each device provides the following entities:

- **Voltage** - Current battery voltage in volts
- **Battery** - State of charge percentage (calculated from voltage)
- **Battery Status** - Binary sensor indicating low battery condition
- **Charging** - Binary sensor indicating charging state
- **Model** - Diagnostic sensor showing device model
- **Firmware** - Diagnostic sensor showing firmware version

## Protocol

The integration implements the Konnwei BLE protocol using CRC-16/X.25 for data integrity.

## Requirements

- Home Assistant 2023.1 or later
- Bluetooth adapter with BLE support
- Konnwei BK-series battery monitor

## Supported Devices

- BK100
- BK200
- BK300
- KW700

All devices use the same BLE protocol and are identified by MAC address prefix `B3:00`.

## Development

### Testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest
pytest tests/
```

### Linting

```bash
ruff check custom_components/
```

## License

MIT License - see LICENSE file for details.

## Contributing

See CONTRIBUTING.md for development guidelines.
