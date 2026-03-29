"""Core functions for downloading, assembling, and saving NEA Geofly aerial images.

This module contains the main logic for retrieving metadata, downloading image tiles,
assembling the tiles into a complete image, and saving metadata and KML files.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from math import ceil
from typing import Any
from urllib.parse import quote, urlencode

from requests import RequestException
from rich.progress import Progress
from rich.table import Table

import requests
from PIL import Image

from app_console import console
from kmlgenerator import generator
from metainfos import Metainfos

REQUEST_TIMEOUT = 8


def get_features(image_id: int) -> dict:
    params = {
        "bild_id": str(image_id),
    }

    response = requests.get(
        f"https://nea.geofly.eu/api.php/getFeature?{urlencode(params)}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    return response.json()


def construct_all_meta(metainfos: Metainfos, for_zoom_level: int):
    if for_zoom_level < metainfos.zoom_min or for_zoom_level > metainfos.zoom_max:
        raise ValueError(f"Invalid zoom level. max = {metainfos.zoom_max}; min = {metainfos.zoom_min}")

    divisor = 2 ** (metainfos.zoom_max - for_zoom_level)

    total_width = metainfos.image_width // divisor
    total_height = metainfos.image_height // divisor

    tile_width, tile_height = (256, 256)
    result: list[tuple[int, int, str]] = []
    for y in range(ceil(total_height / tile_height)):
        for x in range(ceil(total_width / tile_width)):
            url = (f"https://nea.geofly.eu/tiles/"
                   f"{quote(str(metainfos.image_tile_base_id))}/"
                   f"{quote(str(metainfos.image_path))}/"
                   f"{quote(str(for_zoom_level))}/{x}/{y}.jpg")
            result.append((x * tile_width, y * tile_height, url))

    return (total_width, total_height), result


def download_all(meta: tuple[tuple[int, int], list]) -> Image.Image:
    image_size, tile_list = meta
    img = Image.new("RGBA", image_size, 0)

    with Progress() as p:
        t = p.add_task("Downloading...", total=100)
        while not p.finished:
            try:
                for i, (x, y, url) in enumerate(tile_list):
                    p.update(t, completed=(i + 1) / len(tile_list) * 100,
                             description=f"Downloading Tile #{i + 1} of {len(tile_list)} [{url}]")
                    try:
                        with requests.get(
                            url, stream=True, timeout=REQUEST_TIMEOUT
                        ) as tile_response:
                            tile_response.raise_for_status()
                            with Image.open(tile_response.raw) as tile:
                                img.paste(tile, box=(x, y))
                    except RequestException as e:
                        console.print(f"Downloading Tile #{i + 1} failed: {e}")
            except KeyboardInterrupt:
                p.remove_task(t)
                console.print("\n :stop_button: Interrupting download.")
    return img


def clean_filename(filename: str):
    return re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "-", filename)


def determine_outputname(m: Metainfos, zoom: int) -> str:
    output_name = f"{m.image_name}_{m.image_date}_{m.image_location}_{m.image_id}_{zoom}"
    output_name = clean_filename(output_name)

    path = output_name
    i = 2
    while os.path.exists(path + ".jpg"):
        path = f"{output_name} ({i})"
        i += 1
    return path


def main(
    image_id: int,
    zoom_level_callback: Callable[[int, int], int],
    prompt_interrupt: bool = True,
):
    console.print(f"Fetching info for {image_id}...")
    console.print()

    features = get_features(image_id)
    if features["data"]["images"]["features"] is None:
        console.print("Wrong Image ID; Not Found")
        raise ValueError()

    feature = features["data"]["images"]["features"][0]
    metainfos = Metainfos(image_id, feature)

    zoom = zoom_level_callback(metainfos.zoom_min, metainfos.zoom_max)
    (image_width, image_height), tile_list = construct_all_meta(metainfos, zoom)

    console.print(info_summary(image_height, image_width, metainfos, tile_list, zoom))

    if not metainfos.image_available:
        return

    if prompt_interrupt:
        try:
            input("Press Enter to download or Ctrl+C to exit now or anytime during download.")
        except KeyboardInterrupt:
            console.print()
            console.print("Exited.")
            return
        console.print()

    path = determine_outputname(metainfos, zoom)
    image_path = f"{path}.jpg"

    img = download_all(((image_width, image_height), tile_list))
    img.convert("RGB").save(image_path, quality=95)

    with open(f"{path}.txt", "w", encoding="utf-8") as fp:
        fp.write(metainfos.info_text())
        fp.write("\n")
        fp.write(f"zoom_level={zoom}\n")

    kml = generator(metainfos)
    with open(f"{path}.kml", "w", encoding="utf-8") as f:
        f.write(kml.to_string(prettyprint=True))

    console.print(f"\n:floppy_disk:  Saved to [i]{image_path}[/i]")


def info_summary(image_height: int | Any, image_width: int | Any, metainfos: Metainfos,
                 tile_list: list[tuple[int, int, str]], zoom: int):
    table = Table(show_header=False)
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("Image name", f"{metainfos.image_name}")
    table.add_row("Image location", f"{metainfos.image_location}")
    table.add_row("Image date", f"{metainfos.image_date}")
    table.add_row("Spectral channel", f"{metainfos.image_spectral}")
    table.add_row("Available", "yes" if metainfos.image_available else "no")
    table.add_row("Origin", f"{metainfos.image_origin}")
    if metainfos.image_available:
        table.add_row("Zoom", f"{zoom} ({metainfos.zoom_min}-{metainfos.zoom_max})")
        table.add_row("Image dimension", f"{image_width}x{image_height}")
        table.add_row("Tilecount", f"{len(tile_list)}")
    return table
