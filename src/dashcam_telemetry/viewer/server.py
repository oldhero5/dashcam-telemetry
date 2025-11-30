"""Secure local HTTP server for video/map viewer."""

from __future__ import annotations

import http.server
import shutil
import socketserver
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dashcam_telemetry.viewer.templates import generate_viewer_html

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


class SecureHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with security restrictions.

    Security measures:
    - Only serves files from a specific allowed directory
    - Prevents directory traversal attacks
    - Adds security headers (CSP, X-Frame-Options)
    """

    allowed_dir: Path

    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        self.allowed_dir = Path(directory).resolve() if directory else Path.cwd()
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path: str) -> str:
        """Translate URL path to filesystem path with security checks."""
        result = super().translate_path(path)
        result_path = Path(result).resolve()

        # Prevent directory traversal
        try:
            result_path.relative_to(self.allowed_dir)
        except ValueError:
            # Path is outside allowed directory
            return str(self.allowed_dir / "404.html")

        return str(result_path)

    def end_headers(self) -> None:
        """Add security headers to response."""
        # Content Security Policy - restrict resource loading
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org; "
            "connect-src 'self'; "
            "frame-ancestors 'none';",
        )
        # Prevent clickjacking
        self.send_header("X-Frame-Options", "DENY")
        # Prevent MIME sniffing
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress logging for cleaner output."""
        pass


def find_available_port(start_port: int = 8765, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            # Pass None as handler to just test if port is available
            with socketserver.TCPServer(
                ("127.0.0.1", port),
                None,  # type: ignore[arg-type]
            ) as test:
                test.server_close()
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"No available port found in range {start_port}-{start_port + max_attempts}"
    )


def launch_viewer(video_path: str, track: GPSTrack) -> None:
    """Launch synchronized video/map viewer in browser.

    Security measures:
    - Binds to localhost only (127.0.0.1)
    - Uses random available port
    - Serves from isolated temp directory
    - Auto-cleanup on exit

    Args:
        video_path: Path to the video file
        track: GPSTrack with GPS points to display
    """
    video_file = Path(video_path).resolve()

    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_file}")

    print(f"Preparing viewer for: {video_file.name}")
    print(f"GPS points: {len(track)}")

    # Create temp directory for serving
    temp_dir = tempfile.mkdtemp(prefix="dashcam_viewer_")
    temp_path = Path(temp_dir)

    try:
        # Symlink or copy video to temp directory
        video_dest = temp_path / video_file.name
        try:
            video_dest.symlink_to(video_file)
        except OSError:
            print("Creating video copy (this may take a moment)...")
            shutil.copy2(video_file, video_dest)

        # Generate HTML viewer
        html_content = generate_viewer_html(
            video_filename=video_file.name,
            track=track,
        )
        html_path = temp_path / "viewer.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Find available port
        port = find_available_port()

        # Create server bound to localhost only
        def handler(*args: Any, **kwargs: Any) -> SecureHandler:
            return SecureHandler(*args, directory=temp_dir, **kwargs)

        server = socketserver.TCPServer(("127.0.0.1", port), handler)

        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        url = f"http://127.0.0.1:{port}/viewer.html"
        print(f"\nViewer running at: {url}")
        print("\nControls:")
        print("  Space       - Play/Pause")
        print("  Left/Right  - Skip 10 seconds")
        print("  Click map   - Jump to GPS point")
        print("\nPress Ctrl+C to stop")

        webbrowser.open(url)

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            server.shutdown()

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
