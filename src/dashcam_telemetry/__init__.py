"""Dashcam Telemetry - Extract GPS and sensor data from dashcam videos.

Basic usage:
    from dashcam_telemetry import extract_telemetry

    track = extract_telemetry("dashcam_video.mp4")
    track.to_gpx("output.gpx")

For more control:
    from dashcam_telemetry import GPSTrack, GPSPoint
    from dashcam_telemetry.parsers import YouqingParser

    parser = YouqingParser()
    if parser.can_parse(path):
        track = parser.parse(path)
"""

from dashcam_telemetry.models import GPSPoint, GPSTrack
from dashcam_telemetry.parsers import (
    ParseError,
    UnsupportedFormatError,
    extract_telemetry,
)

__version__ = "0.1.0"

__all__ = [
    "GPSPoint",
    "GPSTrack",
    "extract_telemetry",
    "ParseError",
    "UnsupportedFormatError",
    "__version__",
]
