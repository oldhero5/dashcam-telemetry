"""Command-line interface for dashcam-telemetry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dashcam_telemetry.models import GPSTrack
from dashcam_telemetry.parsers import (
    PARSERS,
    ParseError,
    UnsupportedFormatError,
    extract_telemetry,
)

# Supported export formats
EXPORT_FORMATS = ["gpx", "geojson", "kml", "csv"]


def cmd_extract(args: argparse.Namespace) -> int:
    """Extract GPS data from video files."""
    input_files = args.input
    output_format = args.format
    output_path = args.output
    output_dir = args.output_dir
    verbose = args.verbose
    skip_invalid = args.skip_invalid

    # Process each input file
    for input_file in input_files:
        input_path = Path(input_file)

        if not input_path.exists():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            continue

        if verbose:
            print(f"Processing: {input_file}")

        try:
            track = extract_telemetry(str(input_path))
        except UnsupportedFormatError as e:
            print(f"Error: {e}", file=sys.stderr)
            continue
        except ParseError as e:
            print(f"Error parsing {input_file}: {e}", file=sys.stderr)
            continue

        if skip_invalid:
            track = track.filter_valid()

        if verbose:
            print(f"  Found {len(track)} GPS points")
            if track.duration:
                print(f"  Duration: {track.duration:.1f} seconds")

        # Determine output path
        if output_path:
            out_path = Path(output_path)
        elif output_dir:
            out_path = Path(output_dir) / f"{input_path.stem}.{output_format}"
        else:
            out_path = input_path.with_suffix(f".{output_format}")

        # Export
        export_track(track, out_path, output_format)

        if verbose:
            print(f"  Exported to: {out_path}")

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show information about a video file."""
    input_file = args.input
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        return 1

    print(f"File: {input_file}")
    print(f"Size: {input_path.stat().st_size:,} bytes")
    print()

    # Try to detect format
    detected_parser = None
    for parser in PARSERS:
        if parser.can_parse(input_path):
            detected_parser = parser
            break

    if detected_parser:
        print(f"Format: {detected_parser.name}")
        print(f"Supported formats: {', '.join(detected_parser.formats)}")
        print()

        # Parse and show stats
        try:
            track = detected_parser.parse(input_path)
            print(f"GPS Points: {len(track)}")

            if track.duration:
                minutes = int(track.duration // 60)
                seconds = int(track.duration % 60)
                print(f"Duration: {minutes}m {seconds}s")

            if track.bounds:
                min_lat, min_lon, max_lat, max_lon = track.bounds
                print(f"Bounds:")
                print(f"  Lat: {min_lat:.6f} to {max_lat:.6f}")
                print(f"  Lon: {min_lon:.6f} to {max_lon:.6f}")

            if track.points:
                first = track.points[0]
                last = track.points[-1]
                print(f"First point: {first.latitude:.6f}, {first.longitude:.6f}")
                print(f"Last point: {last.latitude:.6f}, {last.longitude:.6f}")

                if first.timestamp:
                    print(f"Start time: {first.timestamp.isoformat()}")
                if last.timestamp:
                    print(f"End time: {last.timestamp.isoformat()}")

        except ParseError as e:
            print(f"Error parsing: {e}", file=sys.stderr)
            return 1
    else:
        print("Format: Unknown (not supported)")
        return 1

    return 0


def cmd_formats(args: argparse.Namespace) -> int:
    """List supported formats."""
    print("Supported input formats:")
    print("-" * 40)
    for parser in PARSERS:
        print(f"  {parser.name}")
        for fmt in parser.formats:
            print(f"    - {fmt}")
    print()

    print("Supported export formats:")
    print("-" * 40)
    for fmt in EXPORT_FORMATS:
        desc = {
            "gpx": "GPS Exchange Format (Strava, Garmin, etc.)",
            "geojson": "GeoJSON (Leaflet, Mapbox, PostGIS)",
            "kml": "Keyhole Markup Language (Google Earth)",
            "csv": "Comma-Separated Values (spreadsheets)",
        }
        print(f"  {fmt}: {desc.get(fmt, '')}")

    return 0


def cmd_view(args: argparse.Namespace) -> int:
    """Launch synchronized video/map viewer."""
    try:
        from dashcam_telemetry.viewer import launch_viewer
    except ImportError:
        print(
            "Error: Viewer not available. Install with: pip install dashcam-telemetry[viewer]",
            file=sys.stderr,
        )
        return 1

    input_file = args.input
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        return 1

    try:
        track = extract_telemetry(str(input_path))
    except (UnsupportedFormatError, ParseError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    launch_viewer(str(input_path), track)
    return 0


def export_track(track: GPSTrack, output_path: Path, format: str) -> None:
    """Export track to the specified format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "gpx":
        track.to_gpx(output_path)
    elif format == "geojson":
        track.to_geojson(output_path)
    elif format == "kml":
        track.to_kml(output_path)
    elif format == "csv":
        track.to_csv(output_path)
    else:
        raise ValueError(f"Unknown format: {format}")


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="dashcam-telemetry",
        description="Extract GPS and sensor telemetry from dashcam videos",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract GPS data from video files",
    )
    extract_parser.add_argument(
        "input",
        nargs="+",
        help="Input video file(s)",
    )
    extract_parser.add_argument(
        "-o", "--output",
        help="Output file path (single file mode)",
    )
    extract_parser.add_argument(
        "--output-dir",
        help="Output directory (batch mode)",
    )
    extract_parser.add_argument(
        "-f", "--format",
        choices=EXPORT_FORMATS,
        default="gpx",
        help="Output format (default: gpx)",
    )
    extract_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    extract_parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Skip invalid GPS points",
    )
    extract_parser.set_defaults(func=cmd_extract)

    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show information about a video file",
    )
    info_parser.add_argument(
        "input",
        help="Input video file",
    )
    info_parser.set_defaults(func=cmd_info)

    # Formats command
    formats_parser = subparsers.add_parser(
        "formats",
        help="List supported formats",
    )
    formats_parser.set_defaults(func=cmd_formats)

    # View command
    view_parser = subparsers.add_parser(
        "view",
        help="Launch synchronized video/map viewer",
    )
    view_parser.add_argument(
        "input",
        help="Input video file",
    )
    view_parser.set_defaults(func=cmd_view)

    # Parse arguments
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
