"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime

from dashcam_telemetry.models import GPSPoint, GPSTrack


@pytest.fixture
def sample_point() -> GPSPoint:
    """Create a sample GPS point for testing."""
    return GPSPoint(
        latitude=38.678898,
        longitude=-77.271553,
        timestamp=datetime(2024, 4, 20, 14, 24, 12),
        speed=45.5,
        heading=180.0,
        fix_quality=1,
    )


@pytest.fixture
def sample_track(sample_point: GPSPoint) -> GPSTrack:
    """Create a sample GPS track for testing."""
    points = [
        sample_point,
        GPSPoint(
            latitude=38.678950,
            longitude=-77.271600,
            timestamp=datetime(2024, 4, 20, 14, 24, 13),
            speed=46.0,
            heading=182.0,
            fix_quality=1,
        ),
        GPSPoint(
            latitude=38.679000,
            longitude=-77.271650,
            timestamp=datetime(2024, 4, 20, 14, 24, 14),
            speed=47.0,
            heading=185.0,
            fix_quality=1,
        ),
    ]
    return GPSTrack(
        points=points,
        source_file="test_video.mp4",
        device_info={"format": "test"},
    )
