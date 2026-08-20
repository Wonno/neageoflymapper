"""Integration test to verify EXIF data is written to actual JPEG files."""

import tempfile
from pathlib import Path
from types import SimpleNamespace

import piexif
from PIL import Image

from exif_writer import get_exif_bytes


def test_exif_data_written_to_jpeg_file():
    """Integration test: verify EXIF data is actually written to a JPEG file."""
    # Create a test image and metadata
    img = Image.new("RGB", (100, 100), color="red")
    metainfos = SimpleNamespace(
        image_id=999,
        image_name="integration_test",
        image_date="2024-12-20",
        image_location="Test Location",
        image_tile_base_id="TEST-001",
        image_width=100,
        image_height=100,
        image_origin="Test Origin",
        image_spectral="RGB",
        center_crs="EPSG:4326",
        center_coords=(13.4, 52.5),  # (lon, lat) - always_xy=True order
        center_coords_wgs84g=lambda: (13.4, 52.5),
    )

    # Get EXIF bytes
    exif_bytes = get_exif_bytes(metainfos)

    # Save to temporary file with EXIF
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        img.save(tmp_path, quality=95, exif=exif_bytes)

        # Verify file exists and has content
        assert Path(tmp_path).exists()
        assert Path(tmp_path).stat().st_size > 0

        # Read back and verify EXIF data is present
        saved_img = Image.open(tmp_path)
        assert "exif" in saved_img.info
        assert len(saved_img.info["exif"]) > 0

        # Parse EXIF and verify content
        exif_dict = piexif.load(saved_img.info["exif"])
        assert piexif.ImageIFD.Software in exif_dict["0th"]
        software = exif_dict["0th"][piexif.ImageIFD.Software]
        assert software == b"nea-geofly-mapper"

        # Verify description contains metadata
        desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode("utf-8")
        assert "999" in desc  # image_id
        assert "integration_test" in desc  # image_name

            # Verify GPS coordinates
        assert piexif.GPSIFD.GPSLatitude in exif_dict["GPS"]
        assert piexif.GPSIFD.GPSLongitude in exif_dict["GPS"]

    finally:
        # Cleanup - close the image first
        saved_img.close()
        Path(tmp_path).unlink(missing_ok=True)
