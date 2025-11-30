"""Tests for data models."""

import pytest
from datetime import datetime

from dashcam_telemetry.models import GPSPoint, GPSTrack


class TestGPSPoint:
    """Tests for GPSPoint model."""

    def test_create_point(self):
        """Test creating a GPS point."""
        point = GPSPoint(latitude=38.678898, longitude=-77.271553)
        assert point.latitude == 38.678898
        assert point.longitude == -77.271553
        assert point.speed == 0.0
        assert point.timestamp is None

    def test_point_with_all_fields(self):
        """Test creating a GPS point with all fields."""
        point = GPSPoint(
            latitude=38.678898,
            longitude=-77.271553,
            timestamp=datetime(2024, 4, 20, 14, 24, 12),
            speed=45.5,
            heading=180.0,
            altitude=100.0,
            fix_quality=2,
            satellites=12,
            gsensor_x=0.1,
            gsensor_y=0.2,
            gsensor_z=9.8,
        )
        assert point.altitude == 100.0
        assert point.satellites == 12
        assert point.gsensor_z == 9.8

    def test_is_valid(self, sample_point):
        """Test point validity check."""
        assert sample_point.is_valid()

    def test_invalid_latitude(self):
        """Test that invalid latitude is detected."""
        point = GPSPoint(latitude=100.0, longitude=0.0)
        assert not point.is_valid()

    def test_invalid_longitude(self):
        """Test that invalid longitude is detected."""
        point = GPSPoint(latitude=0.0, longitude=200.0)
        assert not point.is_valid()

    def test_invalid_fix_quality(self):
        """Test that invalid fix quality is detected."""
        point = GPSPoint(latitude=38.0, longitude=-77.0, fix_quality=0)
        assert not point.is_valid()

    def test_to_dict(self, sample_point):
        """Test conversion to dictionary."""
        d = sample_point.to_dict()
        assert d["latitude"] == sample_point.latitude
        assert d["longitude"] == sample_point.longitude
        assert d["speed"] == sample_point.speed
        assert "timestamp" in d


class TestGPSTrack:
    """Tests for GPSTrack model."""

    def test_create_empty_track(self):
        """Test creating an empty track."""
        track = GPSTrack()
        assert len(track) == 0
        assert track.duration is None
        assert track.bounds is None

    def test_track_length(self, sample_track):
        """Test track length."""
        assert len(sample_track) == 3

    def test_track_iteration(self, sample_track):
        """Test iterating over track points."""
        points = list(sample_track)
        assert len(points) == 3
        assert all(isinstance(p, GPSPoint) for p in points)

    def test_track_indexing(self, sample_track):
        """Test indexing track points."""
        assert sample_track[0].latitude == 38.678898
        assert sample_track[-1].latitude == 38.679000

    def test_duration(self, sample_track):
        """Test track duration calculation."""
        assert sample_track.duration == 2.0  # 2 seconds

    def test_bounds(self, sample_track):
        """Test bounding box calculation."""
        bounds = sample_track.bounds
        assert bounds is not None
        min_lat, min_lon, max_lat, max_lon = bounds
        assert min_lat == 38.678898
        assert max_lat == 38.679000
        assert min_lon == -77.271650
        assert max_lon == -77.271553

    def test_filter_valid(self):
        """Test filtering invalid points."""
        points = [
            GPSPoint(latitude=38.0, longitude=-77.0, fix_quality=1),
            GPSPoint(latitude=0.0, longitude=0.0, fix_quality=0),  # Invalid
            GPSPoint(latitude=39.0, longitude=-78.0, fix_quality=1),
        ]
        track = GPSTrack(points=points)
        filtered = track.filter_valid()
        assert len(filtered) == 2
