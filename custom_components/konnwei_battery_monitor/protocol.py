"""BLE protocol implementation for Konnwei Battery Monitor."""

import struct
from typing import Optional


def crc16_x25(data: bytes) -> int:
    """Calculate CRC-16/X.25 checksum.

    Args:
        data: Bytes to calculate CRC over

    Returns:
        CRC-16 value as integer
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc ^ 0xFFFF


def validate_packet(data: bytes) -> bool:
    """Validate packet CRC using residue method.

    For CRC-16/X.25, when CRC is calculated over data including the CRC bytes,
    the result should be the magic residue constant 0x0F47.

    Note: The CRC-16/X.25 specification lists the residue as 0xF0B8, which is the
    value before the final XOR operation. Our implementation uses the complete CRC
    function (including the final XOR with 0xFFFF), resulting in residue 0x0F47.
    These values are related as bitwise inverses: ~0x0F47 = 0xF0B8.

    Args:
        data: Complete packet including CRC and footer

    Returns:
        True if CRC is valid
    """
    if len(data) < 10:
        return False

    # Footer must be 0x0D0A
    if data[-2:] != b"\x0d\x0a":
        return False

    # Calculate CRC over everything except footer (including the embedded CRC)
    # For a valid packet, this should equal the magic residue 0x0F47
    residue = crc16_x25(data[:-2])

    return residue == 0x0F47


def build_packet(command: bytes, data: bytes = b"") -> bytes:
    """Build a command packet.

    Args:
        command: 2-byte command code
        data: Optional command payload

    Returns:
        Complete packet with header, length, CRC, and footer
    """
    header = b"\x40\x40"
    footer = b"\x0d\x0a"
    length = 10 + len(data)
    length_bytes = struct.pack("<H", length)

    payload = header + length_bytes + command + data
    crc = crc16_x25(payload)
    crc_bytes = struct.pack("<H", crc)

    return payload + crc_bytes + footer


def parse_status_response(data: bytes) -> Optional[dict]:
    """Parse 4B0B status poll response.

    Expected format:
    - Header (2 bytes): 0x2424
    - Length (2 bytes LE): 0x000E (14 bytes)
    - Command (2 bytes): 0x4B0B
    - Voltage (2 bytes LE): uint16 / 100 = Volts
    - Battery status (1 byte): 0x00=low, 0x02=OK
    - Charging indicator (1 byte): 0x00=not charging, 0x01=charging
    - CRC (2 bytes LE)
    - Footer (2 bytes): 0x0D0A

    Args:
        data: Raw response bytes from device

    Returns:
        Dict with voltage, battery_ok, and charging fields, or None if invalid
    """
    if len(data) < 14:
        return None

    if data[0:2] != b"\x24\x24":
        return None

    if data[4:6] != b"\x4b\x0b":
        return None

    # Validate CRC
    if not validate_packet(data):
        return None

    voltage_raw = struct.unpack("<H", data[6:8])[0]
    voltage = voltage_raw / 100.0

    battery_status = data[8]
    battery_ok = battery_status == 0x02

    charging = data[9] == 0x01

    return {
        "voltage": voltage,
        "battery_ok": battery_ok,
        "charging": charging,
    }


def parse_device_info_response(data: bytes) -> Optional[dict]:
    """Parse 4301 device info response.

    Expected format:
    - Header (2 bytes): 0x2424
    - Length (2 bytes LE): 0x0036 (54 bytes)
    - Command (2 bytes): 0x4301
    - Device name (10 bytes): null-padded ASCII
    - Hardware version (10 bytes): null-padded ASCII
    - Firmware version (10 bytes): null-padded ASCII
    - Flash version (10 bytes): null-padded ASCII
    - Capabilities (4 bytes): purpose unknown
    - CRC (2 bytes LE)
    - Footer (2 bytes): 0x0D0A

    Args:
        data: Raw response bytes from device

    Returns:
        Dict with model, hw_version, and fw_version fields, or None if invalid
    """
    if len(data) < 54:
        return None

    if data[0:2] != b"\x24\x24":
        return None

    if data[4:6] != b"\x43\x01":
        return None

    # Validate CRC
    if not validate_packet(data):
        return None

    model = data[6:16].rstrip(b"\x00").decode("ascii", errors="ignore")
    hw_version = data[16:26].rstrip(b"\x00").decode("ascii", errors="ignore")
    fw_version = data[26:36].rstrip(b"\x00").decode("ascii", errors="ignore")

    return {
        "model": model,
        "hw_version": hw_version,
        "fw_version": fw_version,
    }
