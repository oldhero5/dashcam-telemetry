"""Tests for export formats."""

import json
import tempfile
from pathlib import Path

import pytest

from dashcam_telemetry.models import GPSTrack


class TestGPXExporter:
    """Tests for GPX export."""

    def test_export_gpx(self, sample_track):
        """Test exporting to GPX format."""
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as f:
            output_path = Path(f.name)

        try:
            sample_track.to_gpx(output_path)
            content = output_path.read_text()

            assert '<?xml version="1.0"' in content
            assert "<gpx" in content
            assert "<trkpt" in content
            assert "38.678898" in content
        finally:
            output_path.unlink(missing_ok=True)


class TestGeoJSONExporter:
    """Tests for GeoJSON export."""

    def test_export_geojson(self, sample_track):
        """Test exporting to GeoJSON format."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            sample_track.to_geojson(output_path)
            content = output_path.read_text()
            data = json.loads(content)

            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) > 0

            # Check for LineString (route)
            route = next(
                (f for f in data["features"] if f["geometry"]["type"] == "LineString"),
                None,
            )
            assert route is not None
        finally:
            output_path.unlink(missing_ok=True)


class TestKMLExporter:
    """Tests for KML export."""

    def test_export_kml(self, sample_track):
        """Test exporting to KML format."""
        with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as f:
            output_path = Path(f.name)

        try:
            sample_track.to_kml(output_path)
            content = output_path.read_text()

            assert '<?xml version="1.0"' in content
            assert "<kml" in content
            assert "<coordinates>" in content
        finally:
            output_path.unlink(missing_ok=True)


class TestCSVExporter:
    """Tests for CSV export."""

    def test_export_csv(self, sample_track):
        """Test exporting to CSV format."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            sample_track.to_csv(output_path)
            content = output_path.read_text()
            lines = content.strip().split("\n")

            # Check header
            assert "latitude" in lines[0]
            assert "longitude" in lines[0]
            assert "timestamp" in lines[0]

            # Check data rows
            assert len(lines) == 4  # Header + 3 points
        finally:
            output_path.unlink(missing_ok=True)
