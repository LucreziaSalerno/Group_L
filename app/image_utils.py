from pathlib import Path
from urllib.parse import urlencode

import requests


ESRI_WORLD_IMAGERY_EXPORT = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/export"
)


def sanitize_coordinate(value: float) -> str:
    """Create a filename-safe coordinate string."""
    return f"{value:.4f}".replace("-", "m").replace(".", "_")


def build_image_filename(latitude: float, longitude: float, zoom: int) -> str:
    """Generate a stable image filename from settings."""
    lat = sanitize_coordinate(latitude)
    lon = sanitize_coordinate(longitude)
    return f"lat_{lat}_lon_{lon}_zoom_{zoom}.png"


def compute_bbox(
    latitude: float,
    longitude: float,
    zoom: int,
    base_half_size_degrees: float = 0.8,
) -> str:
    """
    Build a simple bbox around the chosen point.

    This is a lightweight heuristic for a proof-of-concept app.
    Larger zoom => smaller bbox.
    """
    zoom = max(1, zoom)
    half_size = base_half_size_degrees / zoom

    xmin = longitude - half_size
    ymin = latitude - half_size
    xmax = longitude + half_size
    ymax = latitude + half_size

    return f"{xmin},{ymin},{xmax},{ymax}"


def build_esri_export_url(
    latitude: float,
    longitude: float,
    zoom: int,
    width: int,
    height: int,
    base_half_size_degrees: float = 0.8,
) -> str:
    """Build the ESRI World Imagery export URL."""
    params = {
        "bbox": compute_bbox(
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
            base_half_size_degrees=base_half_size_degrees,
        ),
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "png",
        "transparent": "false",
        "f": "image",
    }
    return f"{ESRI_WORLD_IMAGERY_EXPORT}?{urlencode(params)}"


def download_esri_image(
    latitude: float,
    longitude: float,
    zoom: int,
    output_path: Path,
    width: int,
    height: int,
    base_half_size_degrees: float = 0.8,
) -> Path:
    """Download the satellite image and save it locally."""
    url = build_esri_export_url(
        latitude=latitude,
        longitude=longitude,
        zoom=zoom,
        width=width,
        height=height,
        base_half_size_degrees=base_half_size_degrees,
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)

    return output_path
