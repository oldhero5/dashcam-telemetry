# dashcam-telemetry

Extract GPS and sensor telemetry from dashcam videos.

[![PyPI version](https://badge.fury.io/py/dashcam-telemetry.svg)](https://badge.fury.io/py/dashcam-telemetry)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Extract GPS data** from dashcam MP4 videos
- **Multiple export formats**: GPX, GeoJSON, KML, CSV
- **Auto-detection** of dashcam format
- **Synchronized video/map viewer** for verification
- **Python API** for integration into other projects

## Supported Dashcams

| Brand | Format | Status |
|-------|--------|--------|
| REDTIGER | YOUQINGGPS |  Supported |
| WolfBox | YOUQINGGPS |  Supported |
| Other YOUQING-based | YOUQINGGPS |  Supported |

## Installation

```bash
pip install dashcam-telemetry
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add dashcam-telemetry
```

## Quick Start

### Command Line

```bash
# Extract GPS to GPX (default)
dashcam-telemetry extract video.mp4 -o track.gpx

# Extract to GeoJSON
dashcam-telemetry extract video.mp4 --format geojson -o track.json

# Show file info
dashcam-telemetry info video.mp4

# Batch processing
dashcam-telemetry extract *.mp4 --output-dir ./tracks/

# Launch synchronized video/map viewer
dashcam-telemetry view video.mp4
```

### Python API

```python
from dashcam_telemetry import extract_telemetry

# Extract GPS data
track = extract_telemetry("dashcam_video.mp4")
print(f"Found {len(track)} GPS points")

# Export to various formats
track.to_gpx("output.gpx")
track.to_geojson("output.json")
track.to_kml("output.kml")
track.to_csv("output.csv")

# Access individual points
for point in track:
    print(f"{point.timestamp}: {point.latitude}, {point.longitude}")

# Get track metadata
print(f"Duration: {track.duration} seconds")
print(f"Bounds: {track.bounds}")
```

### With pandas

```bash
pip install dashcam-telemetry[pandas]
```

```python
from dashcam_telemetry import extract_telemetry

track = extract_telemetry("video.mp4")
df = track.to_dataframe()

# Now you can use pandas for analysis
print(df.describe())
df.to_parquet("telemetry.parquet")
```

## Export Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| **GPX** | `.gpx` | Strava, Garmin, Komoot, most GPS apps |
| **GeoJSON** | `.json` | Leaflet, Mapbox, PostGIS, web mapping |
| **KML** | `.kml` | Google Earth, Google Maps |
| **CSV** | `.csv` | Spreadsheets, data analysis |

## CLI Reference

```
dashcam-telemetry <command> [options]

Commands:
  extract    Extract GPS data from video files
  info       Show information about a video file
  formats    List supported formats
  view       Launch synchronized video/map viewer

Extract options:
  -o, --output      Output file path
  -f, --format      Output format: gpx, geojson, kml, csv (default: gpx)
  --output-dir      Output directory for batch mode
  -v, --verbose     Verbose output
  --skip-invalid    Skip invalid GPS points
```

## Data Model

```python
@dataclass
class GPSPoint:
    latitude: float       # Decimal degrees
    longitude: float      # Decimal degrees
    timestamp: datetime   # UTC timestamp
    speed: float          # km/h
    heading: float        # Degrees from north
    altitude: float       # Meters (optional)
    fix_quality: int      # 0=invalid, 1=GPS, 2=DGPS
    gsensor_x: float      # Accelerometer X (optional)
    gsensor_y: float      # Accelerometer Y (optional)
    gsensor_z: float      # Accelerometer Z (optional)

@dataclass
class GPSTrack:
    points: list[GPSPoint]
    source_file: str
    device_info: dict
```

## Development

```bash
# Clone repository
git clone https://github.com/oldhero5/dashcam-telemetry
cd dashcam-telemetry

# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Type check
uv run mypy src/
```

## Adding New Parsers

To add support for a new dashcam format:

1. Create a new parser in `src/dashcam_telemetry/parsers/`
2. Inherit from `BaseParser`
3. Implement `can_parse()` and `parse()` methods
4. Register in `parsers/__init__.py`

```python
from dashcam_telemetry.parsers.base import BaseParser
from dashcam_telemetry.models import GPSTrack

class MyDashcamParser(BaseParser):
    @property
    def name(self) -> str:
        return "MyDashcam"

    @property
    def formats(self) -> list[str]:
        return ["MyDashcam", "BrandX"]

    def can_parse(self, filepath: Path) -> bool:
        # Check if file contains your format's markers
        ...

    def parse(self, filepath: Path) -> GPSTrack:
        # Extract GPS data
        ...
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

- Inspired by [gopro2gpx](https://github.com/juanmcasillas/gopro2gpx)