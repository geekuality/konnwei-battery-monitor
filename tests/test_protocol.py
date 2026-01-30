"""Unit tests for protocol module."""

# Import directly from protocol module (conftest.py adds it to path)
import protocol
import pytest


class TestCRC16X25:
    """Test CRC-16/X.25 calculation."""

    def test_crc_known_value_status_poll(self):
        """Test CRC calculation matches known value for status poll command."""
        # From protocol spec: 0B0B command packet
        packet = bytes.fromhex("40400A000B0B")
        crc = protocol.crc16_x25(packet)
        assert crc == 0xB2A9

    def test_crc_known_value_device_info(self):
        """Test CRC calculation matches known value for device info command."""
        # From protocol spec: 0301 command packet
        packet = bytes.fromhex("40400A000301")
        crc = protocol.crc16_x25(packet)
        assert crc == 0xD333

    def test_crc_empty_data(self):
        """Test CRC calculation with empty data."""
        crc = protocol.crc16_x25(b"")
        # Empty data: CRC starts at 0xFFFF, no data to process, then XOR with 0xFFFF = 0x0000
        assert crc == 0x0000

    def test_crc_single_byte(self):
        """Test CRC calculation with single byte."""
        crc = protocol.crc16_x25(b"\x00")
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF


class TestValidatePacket:
    """Test packet validation."""

    def test_validate_valid_packet(self):
        """Test validation of valid packet using residue method."""
        # Valid status poll response
        packet = bytes.fromhex("24240E004B0BEE04020108B40D0A")
        assert protocol.validate_packet(packet) is True

    def test_validate_valid_device_info_packet(self):
        """Test validation of valid device info packet."""
        # Valid device info response from BK300
        packet = bytes.fromhex(
            "24243600"
            "4301"
            "424B3330300000000000"
            "312E3100000000000000"
            "312E302E330000000000"
            "392E392E390000000000"
            "00040004"
            "33E6"
            "0D0A"
        )
        assert protocol.validate_packet(packet) is True

    def test_validate_packet_too_short(self):
        """Test validation rejects packet that's too short."""
        packet = bytes.fromhex("2424")
        assert protocol.validate_packet(packet) is False

    def test_validate_packet_invalid_footer(self):
        """Test validation rejects packet with invalid footer."""
        packet = bytes.fromhex("24240E004B0BEE04020108B40000")
        assert protocol.validate_packet(packet) is False

    def test_validate_packet_invalid_crc(self):
        """Test validation rejects packet with invalid CRC using residue."""
        # Corrupt the CRC bytes - residue will not be 0x0F47
        packet = bytes.fromhex("24240E004B0BEE04020100000D0A")
        assert protocol.validate_packet(packet) is False

    def test_validate_residue_constant(self):
        """Test that CRC over valid packet produces magic residue 0x0F47."""
        # Valid status poll response
        packet = bytes.fromhex("24240E004B0BEE04020108B40D0A")
        # Calculate CRC over everything except footer (including embedded CRC)
        residue = protocol.crc16_x25(packet[:-2])
        assert residue == 0x0F47


class TestBuildPacket:
    """Test packet building."""

    def test_build_packet_no_data(self):
        """Test building packet without data payload."""
        packet = protocol.build_packet(b"\x0B\x0B")
        expected = bytes.fromhex("40400A000B0BA9B20D0A")
        assert packet == expected

    def test_build_packet_with_data(self):
        """Test building packet with data payload."""
        packet = protocol.build_packet(b"\x05\x01", b"\x14\x00")
        expected = bytes.fromhex("40400C00050114000AD60D0A")
        assert packet == expected

    def test_build_packet_structure(self):
        """Test packet has correct structure."""
        packet = protocol.build_packet(b"\x0B\x0B")
        # Header
        assert packet[0:2] == b"\x40\x40"
        # Footer
        assert packet[-2:] == b"\x0D\x0A"
        # Length
        assert packet[2:4] == b"\x0A\x00"  # 10 bytes in little-endian


class TestParseStatusResponse:
    """Test status response parsing."""

    def test_parse_valid_status_response(self):
        """Test parsing valid status response."""
        # Valid response: 12.62V, battery OK, charging
        data = bytes.fromhex("24240E004B0BEE04020108B40D0A")
        result = protocol.parse_status_response(data)

        assert result is not None
        assert result["voltage"] == pytest.approx(12.62, rel=0.01)
        assert result["battery_ok"] is True
        assert result["charging"] is True

    def test_parse_status_response_battery_low(self):
        """Test parsing status response with battery low."""
        # Construct response with battery_status = 0x00 (low), correct CRC
        data = bytes.fromhex("24240E004B0BEE040001B8870D0A")
        result = protocol.parse_status_response(data)

        assert result is not None
        assert result["battery_ok"] is False

    def test_parse_status_response_not_charging(self):
        """Test parsing status response when not charging."""
        # Construct response with charging = 0x00 (not charging), correct CRC
        data = bytes.fromhex("24240E004B0BEE04020081A50D0A")
        result = protocol.parse_status_response(data)

        assert result is not None
        assert result["charging"] is False

    def test_parse_status_response_too_short(self):
        """Test parsing rejects response that's too short."""
        data = bytes.fromhex("24240E004B0B")
        result = protocol.parse_status_response(data)
        assert result is None

    def test_parse_status_response_wrong_header(self):
        """Test parsing rejects response with wrong header."""
        data = bytes.fromhex("00000E004B0BEE04020108B40D0A")
        result = protocol.parse_status_response(data)
        assert result is None

    def test_parse_status_response_wrong_command(self):
        """Test parsing rejects response with wrong command code."""
        data = bytes.fromhex("24240E004301EE04020108B40D0A")
        result = protocol.parse_status_response(data)
        assert result is None

    def test_parse_status_response_invalid_crc(self):
        """Test parsing rejects response with invalid CRC."""
        # Corrupt the CRC
        data = bytes.fromhex("24240E004B0BEE04020100000D0A")
        result = protocol.parse_status_response(data)
        assert result is None


class TestParseDeviceInfoResponse:
    """Test device info response parsing."""

    def test_parse_valid_device_info(self):
        """Test parsing valid device info response."""
        # Valid response from BK300
        data = bytes.fromhex(
            "24243600"
            "4301"
            "424B3330300000000000"
            "312E3100000000000000"
            "312E302E330000000000"
            "392E392E390000000000"
            "00040004"
            "33E6"
            "0D0A"
        )
        result = protocol.parse_device_info_response(data)

        assert result is not None
        assert result["model"] == "BK300"
        assert result["hw_version"] == "1.1"
        assert result["fw_version"] == "1.0.3"

    def test_parse_device_info_too_short(self):
        """Test parsing rejects response that's too short."""
        data = bytes.fromhex("24243600")
        result = protocol.parse_device_info_response(data)
        assert result is None

    def test_parse_device_info_wrong_header(self):
        """Test parsing rejects response with wrong header."""
        data = bytes.fromhex(
            "00003600"
            "4301"
            "424B3330300000000000"
            "312E3100000000000000"
            "312E302E330000000000"
            "392E392E390000000000"
            "00040004"
            "33E6"
            "0D0A"
        )
        result = protocol.parse_device_info_response(data)
        assert result is None

    def test_parse_device_info_wrong_command(self):
        """Test parsing rejects response with wrong command code."""
        data = bytes.fromhex(
            "24243600"
            "4B0B"
            "424B3330300000000000"
            "312E3100000000000000"
            "312E302E330000000000"
            "392E392E390000000000"
            "00040004"
            "33E6"
            "0D0A"
        )
        result = protocol.parse_device_info_response(data)
        assert result is None

    def test_parse_device_info_invalid_crc(self):
        """Test parsing rejects response with invalid CRC."""
        # Corrupt the CRC
        data = bytes.fromhex(
            "24243600"
            "4301"
            "424B3330300000000000"
            "312E3100000000000000"
            "312E302E330000000000"
            "392E392E390000000000"
            "00040004"
            "0000"
            "0D0A"
        )
        result = protocol.parse_device_info_response(data)
        assert result is None

    def test_parse_device_info_null_padding(self):
        """Test parsing handles null-padded strings correctly."""
        # BK100 device with properly null-padded fields (each 10 bytes)
        data = bytes.fromhex(
            "242436004301"  # header + length + command
            "424B3130300000000000"  # "BK100" (5 bytes) + 5 nulls = 10 bytes
            "312E3000000000000000"  # "1.0" (3 bytes) + 7 nulls = 10 bytes
            "312E3000000000000000"  # "1.0" (3 bytes) + 7 nulls = 10 bytes
            "392E392E390000000000"  # "9.9.9" (5 bytes) + 5 nulls = 10 bytes
            "00040004"  # capabilities
            "DAC6"  # CRC
            "0D0A"  # footer
        )
        result = protocol.parse_device_info_response(data)

        assert result is not None
        assert result["model"] == "BK100"
        assert result["hw_version"] == "1.0"
        assert result["fw_version"] == "1.0"
