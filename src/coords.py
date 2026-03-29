"""Coordinate transformation utilities for nea-geofly-mapper.

This module provides functions to convert between different coordinate reference
systems (CRS) and Gauss-Kruger zones using the pyproj library.
"""
from __future__ import annotations
from pyproj import Transformer


def epsg_to_zone(name: str):
    """Convert an EPSG string to a Gauss-Kruger zone number.

    Args:
        name (str): EPSG string (e.g., 'EPSG:31468').

    Returns:
        int: Gauss-Kruger zone number.
    """
    assert name.startswith("EPSG:")

    return int(name[5:]) - 31464


def zone_to_epsg(zone: int):
    """Convert a Gauss-Kruger zone number to an EPSG string.

    Args:
        zone (int): Gauss-Kruger zone number (2-5).

    Returns:
        str: EPSG string (e.g., 'EPSG:31468').
    """
    assert 2 <= zone <= 5

    return f"EPSG:{zone + 31464}"


def to_epsg3857(crs: str, coords: tuple[int, int]):
    """Transform coordinates to Web Mercator (EPSG:3857).

    Args:
        crs (str): Source CRS name.
        coords (tuple): Coordinates in source CRS.

    Returns:
        tuple: Transformed coordinates in EPSG:3857.
    """
    out_crs = "EPSG:3857"
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)


def to_epsg4326(crs: str, coords: tuple[int, int]):
    """Transform coordinates to WGS84 geographic (EPSG:4326).

    Args:
        crs (str): Source CRS name.
        coords (tuple): Coordinates in source CRS.

    Returns:
        tuple: Transformed coordinates in EPSG:4326.
    """
    out_crs = "EPSG:4326"
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)


def to_epsg31468(crs: str, coords: tuple[int, int]):
    """Transform coordinates to Gauss-Kruger zone 4 (EPSG:31468).

    Args:
        crs (str): Source CRS name.
        coords (tuple): Coordinates in source CRS.

    Returns:
        tuple: Transformed coordinates in EPSG:31468.
    """
    out_crs = zone_to_epsg(4)
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)
