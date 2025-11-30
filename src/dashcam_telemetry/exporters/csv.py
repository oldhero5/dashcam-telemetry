"""CSV exporter for GPS tracks."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


# CSV column definitions
CSV_COLUMNS = [
    "timestamp",
    "latitude",
    "longitude",
    "altitude",
    "speed_kmh",
    "heading",
    "fix_quality",
    "satellites",
    "gsensor_x",
    "gsensor_y",
    "gsensor_z",
]


def export_csv(track: GPSTrack, output_path: Path) -> None:
    """Export GPS track to CSV format.

    CSV format is ideal for spreadsheet analysis and data science workflows.
    Compatible with Excel, Google Sheets, pandas, and database imports.

    Args:
        track: GPSTrack to export
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for point in track.points:
            row = {
                "timestamp": (point.timestamp.isoformat() if point.timestamp else ""),
                "latitude": point.latitude,
                "longitude": point.longitude,
                "altitude": point.altitude if point.altitude is not None else "",
                "speed_kmh": point.speed,
                "heading": point.heading,
                "fix_quality": point.fix_quality,
                "satellites": point.satellites,
                "gsensor_x": (point.gsensor_x if point.gsensor_x is not None else ""),
                "gsensor_y": (point.gsensor_y if point.gsensor_y is not None else ""),
                "gsensor_z": (point.gsensor_z if point.gsensor_z is not None else ""),
            }
            writer.writerow(row)
