"""EXIF and IPTC metadata embedding for assembled images."""

from datetime import datetime
from importlib import import_module
from typing import Any, Optional

import piexif

from metainfos import Metainfos


def _load_optional_dependency(module_name: str) -> Optional[Any]:
    """Load an optional metadata module when it is installed."""
    try:
        return import_module(module_name)
    except ImportError:
        return None


_iptcinfo3 = _load_optional_dependency("iptcinfo3")



def get_exif_bytes(metainfos: Metainfos) -> Optional[bytes]:
    """Generate EXIF metadata bytes from Metainfos.

    Args:
        metainfos: Metadata object containing image properties.

    Returns:
        EXIF bytes suitable for passing to PIL Image.save(), or None if no metadata.
    """
    exif_dict = _build_exif_dict(metainfos)

    if not exif_dict or not any(exif_dict.values()):
        return None

    return piexif.dump(exif_dict)


def _build_exif_dict(metainfos: Metainfos) -> dict:
    """Build an EXIF dictionary from Metainfos.

    Args:
        metainfos: Metadata object containing image properties.

    Returns:
        Dictionary suitable for piexif.dump().
    """
    exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "Interop": {}}

    _add_basic_exif_tags(exif, metainfos)
    _add_gps_tags(exif, metainfos)

    return exif


def _add_basic_exif_tags(exif: dict, metainfos: Metainfos) -> None:
    """Add basic EXIF tags to the EXIF dictionary.

    Args:
        exif: EXIF dictionary to populate.
        metainfos: Metadata object containing image properties.
    """
    exif_0th = exif["0th"]
    exif = exif["Exif"]

    # Image dimensions
    exif_0th[piexif.ImageIFD.ImageWidth] = metainfos.image_width
    exif_0th[piexif.ImageIFD.ImageLength] = metainfos.image_height

    # Title and Description
    image_desc = (
        f"NEA Aerial Image | ID: {metainfos.image_id} | "
        f"Name: {metainfos.image_name} | "
        f"Location: {metainfos.image_location} | "
        f"Date: {metainfos.image_date}"
    )
    exif_0th[piexif.ImageIFD.ImageDescription] = image_desc.encode("utf-8")
    exif_0th[piexif.ImageIFD.Software] = b"nea-geofly-mapper"

    # Copyright
    if metainfos.image_origin:
        exif_0th[piexif.ImageIFD.Copyright] = str(metainfos.image_origin).encode("utf-8")

    # Date and time from image_date
    date_exif = _parse_date_to_exif(metainfos.image_date)

    if date_exif:
        exif_0th[piexif.ImageIFD.DateTime] = date_exif
        exif[piexif.ExifIFD.DateTimeOriginal] = date_exif
        exif[piexif.ExifIFD.DateTimeDigitized] = date_exif

    # Make and Model can include survey/flight info
    if metainfos.image_tile_base_id:
        exif_0th[piexif.ImageIFD.Make] = "NEA GeoFly Mapper"

    #  Orientation is set to 0 (normal) as we don't have rotation info.
    exif_0th[piexif.ImageIFD.Orientation] = 0

    # Spectral info
    if metainfos.image_spectral:
        exif[piexif.ExifIFD.UserComment] = (
            f"Spectral: {metainfos.image_spectral}".encode("utf-8")
        )



def _add_gps_tags(exif_dict: dict, metainfos: Metainfos) -> None:
    """Add GPS tags with center coordinates.

    Args:
        exif_dict: EXIF dictionary to populate.
        metainfos: Metadata object containing image properties.
    """
    gps = exif_dict["GPS"]
    exif = piexif.GPSIFD

    try:
        lon, lat = metainfos.center_coords_wgs84g()

        lat_ref, lad_rad = _to_exif_dms(lat, ("S", "N"))
        lon_ref, lon_rad = _to_exif_dms(lon, ("W", "E"))

        # Set GPS coordinates
        gps[exif.GPSLatitudeRef] = lat_ref
        gps[exif.GPSLatitude] = lad_rad
        gps[exif.GPSLongitudeRef] = lon_ref
        gps[exif.GPSLongitude] = lon_rad

    except (AttributeError, IndexError, ValueError, TypeError):
        pass



def _decimal_to_dms(decimal: float) -> tuple:
    """Convert decimal degrees to degrees, minutes, seconds format for EXIF.

    Args:
        decimal: Decimal degree value.

    Returns:
        Tuple of ((degrees, 1), (minutes, 1), (seconds * 1000, 1000))
    """
    degrees_int = int(decimal)
    minutes_float = (decimal - int(decimal)) * 60
    minutes_int = int(minutes_float)
    seconds = (minutes_float - int(minutes_float)) * 60
    seconds_micro = int(seconds * 1000)

    return (degrees_int, 1), (minutes_int, 1), (seconds_micro, 1000)


def _parse_date_to_exif(date_string: Optional[str]) -> Optional[bytes]:
    """Parse a date string and convert to EXIF DateTime format.

    EXIF DateTime format is 'YYYY:MM:DD HH:MM:SS'.

    Args:
        date_string: Date string in ISO, slash-separated, or German format.

    Returns:
        Bytes in EXIF DateTime format, or None if parsing fails.
    """
    if not date_string:
        return None

    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            date_obj = datetime.strptime(date_string.strip(), date_format)
            exif_datetime = date_obj.strftime("%Y:%m:%d 00:00:00")
            return exif_datetime.encode("utf-8")
        except ValueError:
            continue

    return None


def _to_deg(value, loc):
    """Convert decimal degrees to degrees, minutes, seconds."""
    if value < 0:
        loc_value = loc[0]
    else:
        loc_value = loc[1]

    abs_value = abs(value)
    deg = int(abs_value)
    mnt = int((abs_value - deg) * 60)
    sec = round(float((abs_value - deg - mnt/60) * 3600)*1000)

    return loc_value, deg, mnt, sec

def _to_exif_dms(value, loc):
    """Convert decimal degrees to EXIF DMS format.

    Args:
        value: Decimal degree value.
        loc: Tuple of ('S', 'N') or ('W', 'E') for latitude or longitude.

    Returns:
        Tuple of (ref, (deg, 1), (min, 1), (sec * 1000, 1000))
    """
    ref, deg, mnt, sec = _to_deg(value, loc)
    return ref, ((deg, 1), (mnt, 1), (sec, 1000))


def write_iptc(image_path: str, metainfos: Metainfos) -> None:
    """Write basic IPTC fields into the saved JPEG using iptcinfo3.

    The function is tolerant when iptcinfo3 is not available or when writing
    fails; it should not interrupt the main flow.
    """
    if _iptcinfo3 is None:
        return

    info = _iptcinfo3.IPTCInfo(image_path, force=True)

    info["country/primary location name"] = "Deutschland"
    info["province/state"] = "Bayern"

    image_desc = (
        f"NEA Aerial Image | ID: {metainfos.image_id} | "
        f"Name: {metainfos.image_name} | "
        f"Location: {metainfos.image_location} | "
        f"Date: {metainfos.image_date}"
    )

    # Common IPTC fields
    if metainfos.image_name:
        info["object name"] = str(metainfos.image_name)
    info["caption/abstract"] = image_desc

    if metainfos.image_location:
        info["city"] = str(metainfos.image_location)

    if metainfos.image_origin:
        info["copyright notice"] = str(metainfos.image_origin)

    # Date created: IPTC prefers YYYYMMDD
    if metainfos.image_date:
        d = datetime.strptime(metainfos.image_date.strip(), "%d.%m.%Y")
        info["date created"] = d.strftime("%Y%m%d")

    # Save changes; iptcinfo3 writes back into the JPEG APP13 segment
    info.save()
