"""Base parser interface for dashcam formats."""

from abc import ABC, abstractmethod
from pathlib import Path

from dashcam_telemetry.models import GPSTrack


class BaseParser(ABC):
    """Abstract base class for dashcam GPS parsers.

    Subclasses must implement can_parse() and parse() methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this parser."""

    @property
    @abstractmethod
    def formats(self) -> list[str]:
        """List of format identifiers this parser handles."""

    @abstractmethod
    def can_parse(self, filepath: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            filepath: Path to the video file

        Returns:
            True if this parser supports the file format
        """

    @abstractmethod
    def parse(self, filepath: Path) -> GPSTrack:
        """Extract GPS data from the file.

        Args:
            filepath: Path to the video file

        Returns:
            GPSTrack containing extracted GPS points

        Raises:
            ParseError: If parsing fails
        """


class ParseError(Exception):
    """Raised when GPS parsing fails."""


class UnsupportedFormatError(Exception):
    """Raised when no parser supports the file format."""
