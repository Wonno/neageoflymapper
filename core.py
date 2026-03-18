from __future__ import annotations

import os
import re
import sys
from collections.abc import Callable
from math import ceil
from urllib.parse import quote, urlencode

import requests
from PIL import Image

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

    TILE_WIDTH, TILE_HEIGHT = (256, 256)
    result: list[tuple[int, int, str]] = []
    for y in range(ceil(total_height / TILE_HEIGHT)):
        for x in range(ceil(total_width / TILE_WIDTH)):
            url = f"https://nea.geofly.eu/tiles/{quote(str(metainfos.image_tile_base_id))}/{quote(str(metainfos.image_path))}/{quote(str(for_zoom_level))}/{x}/{y}.jpg"
            result.append((x * TILE_WIDTH, y * TILE_HEIGHT, url))

    return (total_width, total_height), result


def download_all(meta: tuple[tuple[int, int], list]) -> Image:
    image_size, tile_list = meta
    img = Image.new("RGBA", image_size, 0)

    try:
        for i, (x, y, url) in enumerate(tile_list):
            print(
                f"Downloading Tile #{i+1} of {len(tile_list)} [{url}]", file=sys.stderr
            )
            try:
                with requests.get(
                    url, stream=True, timeout=REQUEST_TIMEOUT
                ) as tile_response:
                    tile_response.raise_for_status()
                    with Image.open(tile_response.raw) as tile:
                        img.paste(tile, box=(x, y))
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Tile #{i+1} failed: {e}")
    except KeyboardInterrupt:
        print("Interrupting download.")

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
    print(f"Fetching info for {image_id}...")
    print()

    features = get_features(image_id)
    if features["data"]["images"]["features"] is None:
        print("Wrong Image ID; Not Found")
        raise ValueError()

    feature = features["data"]["images"]["features"][0]
    metainfos = Metainfos(image_id,feature)

    print(f">> Image name: {metainfos.image_name}")
    print(f">> Image location: {metainfos.image_location}")
    print(f">> Image date: {metainfos.image_date}")

    zoom = zoom_level_callback(metainfos.zoom_min, metainfos.zoom_max)
    (image_width, image_height), tile_list = construct_all_meta(metainfos, zoom)

    print(f">> Final image size: {image_width}x{image_height}")
    print(f">> Tile count: {len(tile_list)}")
    print()

    if prompt_interrupt:
        try:
            input("Press Enter to download or Ctrl+C to exit now or anytime during download.")
        except KeyboardInterrupt:
            print()
            print("Exited.")
            return
        print()

    path = determine_outputname(metainfos, zoom)
    image_path = f"{path}.jpg"

    img = download_all(((image_width, image_height), tile_list))
    img.convert("RGB").save(image_path, quality=95)

    with open(f"{path}.txt", "w", encoding="utf-8") as fp:
        fp.write(metainfos.info_text())
        fp.write("\n")
        fp.write( f"zoom_level={zoom}\n")

    kml =generator(metainfos)
    with open(  f"{path}.kml", "w", encoding="utf-8") as f:
        f.write(kml.to_string(prettyprint=True))

    print(f"\nSaved to {image_path}")
    print("Done")
