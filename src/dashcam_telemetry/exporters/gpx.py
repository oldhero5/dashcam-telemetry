"""GPX (GPS Exchange Format) exporter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import gpxpy
import gpxpy.gpx

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


def export_gpx(track: GPSTrack, output_path: Path) -> None:
    """Export GPS track to GPX format.

    GPX is the universal standard for GPS data interchange,
    supported by Strava, Garmin, Komoot, and most mapping apps.

    Args:
        track: GPSTrack to export
        output_path: Path to output file
    """
    gpx = gpxpy.gpx.GPX()

    # Set metadata
    gpx.name = Path(track.source_file).stem if track.source_file else "Dashcam Track"
    gpx.description = "GPS track extracted from dashcam video"

    if track.device_info:
        gpx.creator = track.device_info.get("format", "dashcam-telemetry")

    # Create track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Add points
    for point in track.points:
        gpx_point = gpxpy.gpx.GPXTrackPoint(
            latitude=point.latitude,
            longitude=point.longitude,
            elevation=point.altitude,
            time=point.timestamp,
        )

        # Add speed as extension if available
        if point.speed > 0:
            # Convert km/h to m/s for GPX standard
            gpx_point.speed = point.speed / 3.6

        # Add course/heading if available
        if point.heading > 0:
            gpx_point.course = point.heading  # type: ignore[assignment]

        gpx_segment.points.append(gpx_point)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())
