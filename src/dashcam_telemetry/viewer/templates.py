"""HTML/JavaScript templates for the video viewer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dashcam_telemetry.models import GPSTrack


def generate_viewer_html(video_filename: str, track: GPSTrack) -> str:
    """Generate HTML page with synchronized video and map.

    Args:
        video_filename: Name of the video file (must be in same directory)
        track: GPSTrack with GPS points

    Returns:
        Complete HTML page as string
    """
    # Calculate map center
    if track.points:
        center_lat = sum(p.latitude for p in track.points) / len(track.points)
        center_lon = sum(p.longitude for p in track.points) / len(track.points)
    else:
        center_lat, center_lon = 0.0, 0.0

    # Convert points to JSON-serializable format
    gps_points = [
        {
            "latitude": p.latitude,
            "longitude": p.longitude,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "speed": p.speed,
        }
        for p in track.points
    ]

    route_coords = [[p.latitude, p.longitude] for p in track.points]

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>GPS Viewer - {video_filename}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            overflow: hidden;
        }}
        .container {{ display: flex; height: 100vh; }}
        .video-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #000;
            min-width: 0;
        }}
        .map-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        video {{
            width: 100%;
            flex: 1;
            background: #000;
            object-fit: contain;
        }}
        #map {{ flex: 1; background: #2a2a3e; }}
        .info-bar {{
            background: #16213e;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            border-top: 1px solid #0f3460;
        }}
        .info-bar .coords {{ font-family: monospace; color: #00ff88; }}
        .info-bar .time {{ color: #ff6b6b; }}
        .controls {{
            background: #16213e;
            padding: 8px 15px;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .controls button {{
            background: #0f3460;
            border: none;
            color: #fff;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .controls button:hover {{ background: #1a4980; }}
        .controls input[type="range"] {{
            flex: 1;
            height: 6px;
            -webkit-appearance: none;
            background: #0f3460;
            border-radius: 3px;
        }}
        .controls input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: #e94560;
            border-radius: 50%;
            cursor: pointer;
        }}
        .title-bar {{
            background: #0f3460;
            padding: 10px 15px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
        }}
        .point-count {{ color: #888; font-weight: normal; }}
        .marker-icon {{
            background: #e94560;
            border: 3px solid #fff;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="video-panel">
            <div class="title-bar">
                <span>{video_filename}</span>
                <span class="point-count">{len(track)} GPS points</span>
            </div>
            <video id="video" controls>
                <source src="{video_filename}" type="video/mp4">
            </video>
            <div class="controls">
                <button onclick="skipBack()">-10s</button>
                <button onclick="togglePlay()" id="playBtn">Play</button>
                <button onclick="skipForward()">+10s</button>
                <input type="range" id="seekBar" min="0" max="100" value="0" oninput="seekVideo(this.value)">
                <span id="timeDisplay">0:00 / 0:00</span>
            </div>
            <div class="info-bar">
                <span class="coords" id="coordsDisplay">--</span>
                <span class="time" id="gpsTimeDisplay">--</span>
            </div>
        </div>
        <div class="map-panel">
            <div class="title-bar">
                <span>GPS Route</span>
                <span class="point-count" id="pointIndex">Point 0 / {len(track)}</span>
            </div>
            <div id="map"></div>
            <div class="info-bar">
                <span>Lat: <span class="coords" id="latDisplay">--</span></span>
                <span>Lon: <span class="coords" id="lonDisplay">--</span></span>
                <span>Speed: <span class="coords" id="speedDisplay">--</span></span>
            </div>
        </div>
    </div>
    <script>
        const gpsPoints = {json.dumps(gps_points)};
        const routeCoords = {json.dumps(route_coords)};

        const map = L.map('map').setView([{center_lat}, {center_lon}], 15);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);

        const routeLine = L.polyline(routeCoords, {{
            color: '#e94560', weight: 4, opacity: 0.8
        }}).addTo(map);

        if (routeCoords.length > 0) {{
            map.fitBounds(routeLine.getBounds(), {{ padding: [30, 30] }});
        }}

        const traveledLine = L.polyline([], {{
            color: '#00ff88', weight: 6, opacity: 0.9
        }}).addTo(map);

        const markerIcon = L.divIcon({{
            className: 'marker-icon',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        }});

        let currentMarker = null;
        if (gpsPoints.length > 0) {{
            currentMarker = L.marker([gpsPoints[0].latitude, gpsPoints[0].longitude], {{
                icon: markerIcon
            }}).addTo(map);
        }}

        const video = document.getElementById('video');
        const seekBar = document.getElementById('seekBar');
        const playBtn = document.getElementById('playBtn');

        function formatTime(s) {{
            const m = Math.floor(s / 60);
            const sec = Math.floor(s % 60);
            return `${{m}}:${{sec.toString().padStart(2, '0')}}`;
        }}

        function getGPSPointForTime(currentTime, duration) {{
            if (gpsPoints.length === 0 || duration === 0) return null;
            const progress = currentTime / duration;
            const index = Math.min(Math.floor(progress * gpsPoints.length), gpsPoints.length - 1);
            return {{ point: gpsPoints[index], index }};
        }}

        function updatePosition() {{
            const duration = video.duration || 1;
            const currentTime = video.currentTime;
            seekBar.value = (currentTime / duration) * 100;
            document.getElementById('timeDisplay').textContent = `${{formatTime(currentTime)}} / ${{formatTime(duration)}}`;

            const result = getGPSPointForTime(currentTime, duration);
            if (result) {{
                const {{ point, index }} = result;
                if (currentMarker) currentMarker.setLatLng([point.latitude, point.longitude]);
                traveledLine.setLatLngs(routeCoords.slice(0, index + 1));
                document.getElementById('coordsDisplay').textContent = `${{point.latitude.toFixed(6)}}, ${{point.longitude.toFixed(6)}}`;
                document.getElementById('latDisplay').textContent = point.latitude.toFixed(6);
                document.getElementById('lonDisplay').textContent = point.longitude.toFixed(6);
                document.getElementById('speedDisplay').textContent = `${{point.speed.toFixed(1)}} km/h`;
                document.getElementById('gpsTimeDisplay').textContent = point.timestamp || '--';
                document.getElementById('pointIndex').textContent = `Point ${{index + 1}} / ${{gpsPoints.length}}`;
            }}
        }}

        video.addEventListener('timeupdate', updatePosition);
        video.addEventListener('loadedmetadata', updatePosition);
        video.addEventListener('play', () => {{ playBtn.textContent = 'Pause'; }});
        video.addEventListener('pause', () => {{ playBtn.textContent = 'Play'; }});

        function togglePlay() {{ video.paused ? video.play() : video.pause(); }}
        function seekVideo(val) {{ video.currentTime = (val / 100) * video.duration; }}
        function skipBack() {{ video.currentTime = Math.max(0, video.currentTime - 10); }}
        function skipForward() {{ video.currentTime = Math.min(video.duration, video.currentTime + 10); }}

        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{ e.preventDefault(); togglePlay(); }}
            else if (e.code === 'ArrowLeft') skipBack();
            else if (e.code === 'ArrowRight') skipForward();
        }});

        map.on('click', (e) => {{
            let minDist = Infinity, closestIdx = 0;
            gpsPoints.forEach((p, i) => {{
                const d = Math.pow(p.latitude - e.latlng.lat, 2) + Math.pow(p.longitude - e.latlng.lng, 2);
                if (d < minDist) {{ minDist = d; closestIdx = i; }}
            }});
            video.currentTime = (closestIdx / gpsPoints.length) * video.duration;
        }});
    </script>
</body>
</html>"""
