"""Parsers for various dashcam GPS formats."""

from dashcam_telemetry.models import GPSTrack
from dashcam_telemetry.parsers.base import (
    BaseParser,
    ParseError,
    UnsupportedFormatError,
)
from dashcam_telemetry.parsers.youqing import YouqingParser

# Registry of available parsers (order matters - first match wins)
PARSERS: list[BaseParser] = [
    YouqingParser(),
]


def get_parser(filepath: str) -> BaseParser:
    """Get a parser that can handle the given file.

    Args:
        filepath: Path to the video file

    Returns:
        Parser instance that can handle the file

    Raises:
        UnsupportedFormatError: If no parser supports the file
    """
    from pathlib import Path

    path = Path(filepath)
    for parser in PARSERS:
        if parser.can_parse(path):
            return parser
    raise UnsupportedFormatError(f"No parser found for: {filepath}")


def extract_telemetry(filepath: str) -> GPSTrack:
    """Extract GPS telemetry from a dashcam video file.

    Auto-detects the file format and uses the appropriate parser.

    Args:
        filepath: Path to the video file

    Returns:
        GPSTrack containing extracted GPS points

    Raises:
        UnsupportedFormatError: If no parser supports the file
        ParseError: If parsing fails
    """
    from pathlib import Path

    parser = get_parser(filepath)
    return parser.parse(Path(filepath))


__all__ = [
    "BaseParser",
    "ParseError",
    "UnsupportedFormatError",
    "YouqingParser",
    "PARSERS",
    "get_parser",
    "extract_telemetry",
]
