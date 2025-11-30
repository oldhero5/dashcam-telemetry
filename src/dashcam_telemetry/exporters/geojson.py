"""GeoJSON exporter for GPS tracks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from geojson import Feature, FeatureCollection, LineString, Point

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


def export_geojson(track: GPSTrack, output_path: Path) -> None:
    """Export GPS track to GeoJSON format.

    GeoJSON is ideal for web mapping applications (Leaflet, Mapbox, OpenLayers)
    and can be directly imported into PostGIS databases.

    The output includes:
    - A LineString feature for the track route
    - Point features for each GPS reading with properties

    Args:
        track: GPSTrack to export
        output_path: Path to output file
    """
    features: list[Feature] = []

    # Create LineString for the route
    if track.points:
        coordinates = [[point.longitude, point.latitude] for point in track.points]

        route_properties: dict[str, Any] = {
            "type": "route",
            "name": Path(track.source_file).stem if track.source_file else "track",
            "point_count": len(track.points),
        }

        if track.duration is not None:
            route_properties["duration_seconds"] = track.duration

        if track.bounds:
            min_lat, min_lon, max_lat, max_lon = track.bounds
            route_properties["bounds"] = {
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon,
            }

        if track.device_info:
            route_properties["device"] = track.device_info

        route_feature = Feature(
            geometry=LineString(coordinates),
            properties=route_properties,
        )
        features.append(route_feature)

    # Create Point features for each GPS reading
    for i, point in enumerate(track.points):
        point_properties: dict[str, Any] = {
            "type": "point",
            "index": i,
            "speed_kmh": point.speed,
            "heading": point.heading,
            "fix_quality": point.fix_quality,
        }

        if point.timestamp:
            point_properties["timestamp"] = point.timestamp.isoformat()

        if point.altitude is not None:
            point_properties["altitude_m"] = point.altitude

        if point.gsensor_x is not None:
            point_properties["gsensor"] = {
                "x": point.gsensor_x,
                "y": point.gsensor_y,
                "z": point.gsensor_z,
            }

        point_feature = Feature(
            geometry=Point((point.longitude, point.latitude)),
            properties=point_properties,
        )
        features.append(point_feature)

    # Create FeatureCollection
    collection = FeatureCollection(features)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2)
