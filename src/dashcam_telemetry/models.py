"""Data models for GPS telemetry data."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class GPSPoint:
    """A single GPS data point with optional sensor data.

    Attributes:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        timestamp: UTC timestamp of the reading
        speed: Speed in km/h
        heading: Heading in degrees from north (0-360)
        altitude: Altitude in meters (if available)
        fix_quality: GPS fix quality (0=invalid, 1=GPS, 2=DGPS)
        satellites: Number of satellites used
        gsensor_x: G-sensor X axis acceleration
        gsensor_y: G-sensor Y axis acceleration
        gsensor_z: G-sensor Z axis acceleration
    """

    latitude: float
    longitude: float
    timestamp: datetime | None = None
    speed: float = 0.0
    heading: float = 0.0
    altitude: float | None = None
    fix_quality: int = 1
    satellites: int = 0
    gsensor_x: float | None = None
    gsensor_y: float | None = None
    gsensor_z: float | None = None

    def is_valid(self) -> bool:
        """Check if this is a valid GPS point."""
        return (
            -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
            and self.fix_quality > 0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "speed": self.speed,
            "heading": self.heading,
            "altitude": self.altitude,
            "fix_quality": self.fix_quality,
            "satellites": self.satellites,
            "gsensor_x": self.gsensor_x,
            "gsensor_y": self.gsensor_y,
            "gsensor_z": self.gsensor_z,
        }


@dataclass
class GPSTrack:
    """A collection of GPS points forming a track.

    Attributes:
        points: List of GPS points in chronological order
        source_file: Path to the source video file
        device_info: Optional device metadata
    """

    points: list[GPSPoint] = field(default_factory=list)
    source_file: str = ""
    device_info: dict | None = None

    def __len__(self) -> int:
        """Return number of points in track."""
        return len(self.points)

    def __iter__(self) -> Iterator[GPSPoint]:
        """Iterate over points."""
        return iter(self.points)

    def __getitem__(self, index: int) -> GPSPoint:
        """Get point by index."""
        return self.points[index]

    @property
    def duration(self) -> float | None:
        """Track duration in seconds, or None if timestamps unavailable."""
        if len(self.points) < 2:
            return None
        first = self.points[0].timestamp
        last = self.points[-1].timestamp
        if first is None or last is None:
            return None
        return (last - first).total_seconds()

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:
        """Return (min_lat, min_lon, max_lat, max_lon) bounding box."""
        if not self.points:
            return None
        lats = [p.latitude for p in self.points]
        lons = [p.longitude for p in self.points]
        return (min(lats), min(lons), max(lats), max(lons))

    def filter_valid(self) -> GPSTrack:
        """Return new track with only valid points."""
        return GPSTrack(
            points=[p for p in self.points if p.is_valid()],
            source_file=self.source_file,
            device_info=self.device_info,
        )

    def to_gpx(self, path: str | Path) -> None:
        """Export track to GPX format.

        Args:
            path: Output file path
        """
        from dashcam_telemetry.exporters.gpx import export_gpx

        export_gpx(self, Path(path))

    def to_geojson(self, path: str | Path) -> None:
        """Export track to GeoJSON format.

        Args:
            path: Output file path
        """
        from dashcam_telemetry.exporters.geojson import export_geojson

        export_geojson(self, Path(path))

    def to_kml(self, path: str | Path) -> None:
        """Export track to KML format.

        Args:
            path: Output file path
        """
        from dashcam_telemetry.exporters.kml import export_kml

        export_kml(self, Path(path))

    def to_csv(self, path: str | Path) -> None:
        """Export track to CSV format.

        Args:
            path: Output file path
        """
        from dashcam_telemetry.exporters.csv import export_csv

        export_csv(self, Path(path))

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert track to pandas DataFrame.

        Requires pandas to be installed: pip install dashcam-telemetry[pandas]

        Returns:
            DataFrame with columns for each GPS point attribute
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install dashcam-telemetry[pandas]"
            ) from e

        return pd.DataFrame([p.to_dict() for p in self.points])
