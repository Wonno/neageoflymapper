from __future__ import annotations
from pyproj import Transformer


def epsg_to_zone(name: str):
    assert name.startswith("EPSG:")

    return int(name[5:]) - 31464


def zone_to_epsg(zone: int):
    assert 2 <= zone <= 5

    return f"EPSG:{zone + 31464}"


def to_epsg3857(crs: str, coords: tuple[int, int]):
    out_crs = "EPSG:3857"
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)


def to_epsg4326(crs: str, coords: tuple[int, int]):
    out_crs = "EPSG:4326"
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)


def to_epsg31468(crs: str, coords: tuple[int, int]):
    out_crs = zone_to_epsg(4)
    if crs == out_crs:
        return coords

    transformer = Transformer.from_crs(crs, out_crs, always_xy=True)

    return transformer.transform(*coords)
