"""Parser for YOUQINGGPS format dashcam videos.

This format is used by many Chinese dashcam manufacturers including:
- REDTIGER
- WolfBox
- Various OEM brands using the YOUQING chipset

The GPS data is stored in plaintext (no encryption) within 'free' atoms
marked with 'GPS ' followed by 'YOUQINGGPS' brand identifier.
"""

from __future__ import annotations

import struct
from datetime import datetime
from pathlib import Path

from dashcam_telemetry.models import GPSPoint, GPSTrack
from dashcam_telemetry.parsers.base import BaseParser, ParseError
from dashcam_telemetry.utils.nmea import nmea_to_decimal


# Magic bytes to identify YOUQINGGPS format
MARKER_FREE_GPS = b"freeGPS "
MARKER_YOUQING = b"YOUQINGGPS"


class YouqingParser(BaseParser):
    """Parser for YOUQINGGPS format MP4 files.

    GPS data structure (256-byte chunks):
        [0:4]   'free' - MP4 atom type
        [4:8]   'GPS ' - GPS marker
        [8:12]  payload size (LE uint32)
        [12:22] 'YOUQINGGPS' - brand identifier
        [22:24] padding
        [24:28] unknown
        [28:32] unknown
        [32:36] zeros
        [36:40] latitude (LE float, NMEA format DDMM.MMMM)
        [40:44] longitude (LE float, NMEA format DDDMM.MMMM)
        [44:48] year (LE int32, offset from 2000)
        [48:52] hour (LE int32)
        [52:56] minute (LE int32)
        [56:60] day (LE int32)
        [60:64] month (LE int32)
        [64:68] second (LE int32)
        [68:71] status (ASCII: A=Active, N/S, E/W)
        [108:112] speed (LE float, optional)
    """

    @property
    def name(self) -> str:
        return "YOUQINGGPS"

    @property
    def formats(self) -> list[str]:
        return ["YOUQINGGPS", "REDTIGER", "WolfBox"]

    def can_parse(self, filepath: Path) -> bool:
        """Check if file contains YOUQINGGPS format GPS data."""
        try:
            with open(filepath, "rb") as f:
                # Read first 10MB to check for marker
                chunk = f.read(10 * 1024 * 1024)
                pos = chunk.find(MARKER_FREE_GPS)
                if pos < 0:
                    return False
                # Verify YOUQINGGPS brand marker
                return chunk[pos + 12 : pos + 22] == MARKER_YOUQING
        except (OSError, IOError):
            return False

    def parse(self, filepath: Path) -> GPSTrack:
        """Extract GPS data from YOUQINGGPS format file.

        Args:
            filepath: Path to MP4 file

        Returns:
            GPSTrack with extracted points

        Raises:
            ParseError: If file cannot be parsed
        """
        try:
            with open(filepath, "rb") as f:
                content = f.read()
        except (OSError, IOError) as e:
            raise ParseError(f"Failed to read file: {e}") from e

        points: list[GPSPoint] = []
        offset = 0

        while True:
            pos = content.find(MARKER_FREE_GPS, offset)
            if pos < 0:
                break

            chunk = content[pos : pos + 256]

            # Verify YOUQINGGPS brand
            if chunk[12:22] != MARKER_YOUQING:
                offset = pos + 8
                continue

            try:
                point = self._parse_chunk(chunk)
                if point is not None:
                    points.append(point)
            except Exception:
                # Skip malformed chunks
                pass

            offset = pos + 8

        return GPSTrack(
            points=points,
            source_file=str(filepath),
            device_info={"format": "YOUQINGGPS"},
        )

    def _parse_chunk(self, chunk: bytes) -> GPSPoint | None:
        """Parse a single GPS chunk.

        Args:
            chunk: 256-byte GPS data chunk

        Returns:
            GPSPoint or None if chunk is invalid
        """
        if len(chunk) < 72:
            return None

        # Extract coordinates (NMEA format floats)
        lat_nmea = struct.unpack("<f", chunk[36:40])[0]
        lon_nmea = struct.unpack("<f", chunk[40:44])[0]

        # Skip invalid coordinates
        if lat_nmea == 0 or lon_nmea == 0:
            return None

        # Extract timestamp components
        year = struct.unpack("<I", chunk[44:48])[0]
        hour = struct.unpack("<I", chunk[48:52])[0]
        minute = struct.unpack("<I", chunk[52:56])[0]
        day = struct.unpack("<I", chunk[56:60])[0]
        month = struct.unpack("<I", chunk[60:64])[0]
        second = struct.unpack("<I", chunk[64:68])[0]

        # Extract status (A=Active, N/S, E/W)
        try:
            status = chunk[68:71].decode("ascii", errors="replace")
        except Exception:
            status = "ANE"

        # Convert NMEA to decimal degrees
        lat = nmea_to_decimal(lat_nmea)
        lon = nmea_to_decimal(lon_nmea)

        # Apply N/S E/W indicators
        ns = status[1] if len(status) > 1 else "N"
        ew = status[2] if len(status) > 2 else "E"

        if ns == "S":
            lat = -lat
        if ew == "W":
            lon = -lon

        # Parse speed if available
        speed = 0.0
        if len(chunk) >= 112:
            try:
                raw_speed = struct.unpack("<f", chunk[108:112])[0]
                # Sanity check speed value
                if 0 <= raw_speed < 500:
                    speed = raw_speed
            except Exception:
                pass

        # Build timestamp
        try:
            year_full = 2000 + year if year < 100 else year
            # Handle hour overflow (some devices report 24+)
            hour_clamped = hour % 24
            timestamp = datetime(
                year_full, month, day, hour_clamped, minute, second
            )
        except ValueError:
            timestamp = None

        # Determine fix quality from status
        fix_quality = 1 if status.startswith("A") else 0

        return GPSPoint(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp,
            speed=speed,
            heading=0.0,  # Not available in this format
            fix_quality=fix_quality,
        )
