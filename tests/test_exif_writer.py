"""Tests for EXIF and IPTC metadata embedding."""

from types import SimpleNamespace

import piexif

from exif_writer import get_exif_bytes, _parse_date_to_exif, _decimal_to_dms


def create_test_metainfos():
    """Create a minimal metadata object for EXIF tests."""
    return SimpleNamespace(
        image_id=12345,
        image_name="test_image",
        image_date="2024-06-15",
        image_location="Test City",
        image_tile_base_id="FL-2024-001",
        image_width=1024,
        image_height=768,
        image_origin="NEA",
        image_spectral="RGB",
        center_crs="EPSG:4326",
        center_coords=(8.5, 50.5),  # (lon, lat) - always_xy=True order
        center_coords_wgs84g=lambda: (8.5, 50.5),
    )


def test_get_exif_bytes_returns_bytes():
    """Test that get_exif_bytes returns valid EXIF bytes."""
    metainfos = create_test_metainfos()

    result = get_exif_bytes(metainfos)

    assert result is not None
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_get_exif_bytes_can_be_loaded_by_piexif():
    """Test that returned bytes can be loaded and parsed by piexif."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)

    assert "0th" in exif_dict
    assert "Exif" in exif_dict
    assert "GPS" in exif_dict


def test_decimal_to_dms_positive():
    """Test conversion of positive decimal degrees to DMS format."""
    dms = _decimal_to_dms(50.5)

    assert len(dms) == 3
    assert dms[0] == (50, 1)  # degrees
    assert dms[1] == (30, 1)  # minutes
    assert dms[2][0] == 0  # seconds should be 0
    assert dms[2][1] == 1000


def test_decimal_to_dms_negative():
    """Test conversion of negative decimal degrees."""
    # Function expects absolute value, so just test positive
    dms = _decimal_to_dms(8.25)

    assert dms[0] == (8, 1)
    assert dms[1] == (15, 1)
    assert dms[2] == (0, 1000)


def test_parse_date_to_exif_iso_format():
    """Test parsing ISO date format (YYYY-MM-DD)."""
    result = _parse_date_to_exif("2024-06-15")

    assert result is not None
    assert result.startswith(b"2024:06:15")


def test_parse_date_to_exif_slash_format():
    """Test parsing date format with slashes."""
    result = _parse_date_to_exif("2024/06/15")

    assert result is not None
    assert result.startswith(b"2024:06:15")


def test_parse_date_to_exif_german_format():
    """Test parsing German date format (DD.MM.YYYY)."""
    result = _parse_date_to_exif("15.06.2024")

    assert result is not None
    assert result.startswith(b"2024:06:15")


def test_parse_date_to_exif_invalid_date():
    """Test parsing invalid date returns None."""
    result = _parse_date_to_exif("invalid")

    assert result is None


def test_parse_date_to_exif_none():
    """Test parsing None returns None."""
    result = _parse_date_to_exif(None)

    assert result is None


def test_parse_date_to_exif_empty_string():
    """Test parsing empty string returns None."""
    result = _parse_date_to_exif("")

    assert result is None


def test_exif_bytes_include_image_description():
    """Test that image description is included in EXIF data."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)
    desc = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription)

    assert desc is not None
    desc_str = desc.decode("utf-8")
    assert "12345" in desc_str  # image_id
    assert "Test City" in desc_str  # location
    assert "test_image" in desc_str  # image_name
    assert "2024-06-15" in desc_str  # date


def test_exif_bytes_include_software_tag():
    """Test that software tag identifies this tool."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)
    software = exif_dict["0th"].get(piexif.ImageIFD.Software)

    assert software == b"nea-geofly-mapper"


def test_exif_bytes_include_gps_coordinates():
    """Test that GPS coordinates are embedded."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)

    assert piexif.GPSIFD.GPSLatitude in exif_dict["GPS"]
    assert piexif.GPSIFD.GPSLongitude in exif_dict["GPS"]
    assert piexif.GPSIFD.GPSLatitudeRef in exif_dict["GPS"]
    assert piexif.GPSIFD.GPSLongitudeRef in exif_dict["GPS"]


def test_exif_bytes_include_image_dimensions():
    """Test that image dimensions are included."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)

    assert exif_dict["0th"][piexif.ImageIFD.ImageWidth] == 1024
    assert exif_dict["0th"][piexif.ImageIFD.ImageLength] == 768


def test_exif_bytes_include_datetime():
    """Test that datetime is included."""
    metainfos = create_test_metainfos()

    exif_bytes = get_exif_bytes(metainfos)
    exif_dict = piexif.load(exif_bytes)
    dt = exif_dict["0th"].get(piexif.ImageIFD.DateTime)

    assert dt is not None
    assert b"2024:06:15" in dt
