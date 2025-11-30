"""KML (Keyhole Markup Language) exporter for Google Earth."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import simplekml

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


def export_kml(track: GPSTrack, output_path: Path) -> None:
    """Export GPS track to KML format.

    KML is the native format for Google Earth and Google Maps,
    providing rich visualization options including styling,
    icons, and descriptions.

    Args:
        track: GPSTrack to export
        output_path: Path to output file
    """
    kml = simplekml.Kml()

    # Set document name
    name = Path(track.source_file).stem if track.source_file else "Dashcam Track"
    kml.document.name = name

    # Create folder for the track
    folder = kml.newfolder(name=name)

    # Add track as LineString
    if track.points:
        coords = [
            (point.longitude, point.latitude, point.altitude or 0)
            for point in track.points
        ]

        linestring = folder.newlinestring(name="Route")
        linestring.coords = coords
        linestring.description = f"GPS track with {len(track.points)} points"

        # Style the line
        linestring.style.linestyle.color = simplekml.Color.red
        linestring.style.linestyle.width = 3

        # Add altitude mode
        if any(p.altitude is not None for p in track.points):
            linestring.altitudemode = simplekml.AltitudeMode.absolute
        else:
            linestring.altitudemode = simplekml.AltitudeMode.clamptoground

    # Add start and end markers
    if track.points:
        # Start point
        start = track.points[0]
        start_point = folder.newpoint(name="Start")
        start_point.coords = [(start.longitude, start.latitude)]
        start_point.style.iconstyle.icon.href = (
            "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png"
        )
        if start.timestamp:
            start_point.description = f"Start: {start.timestamp.isoformat()}"

        # End point
        end = track.points[-1]
        end_point = folder.newpoint(name="End")
        end_point.coords = [(end.longitude, end.latitude)]
        end_point.style.iconstyle.icon.href = (
            "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
        )
        if end.timestamp:
            end_point.description = f"End: {end.timestamp.isoformat()}"

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    kml.save(str(output_path))
