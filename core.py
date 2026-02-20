import os
import re
import sys
from collections.abc import Callable
from math import ceil
from urllib.parse import quote, urlencode

import requests
from PIL import Image

REQUEST_TIMEOUT = 8


def get_features(id: str | int) -> dict:
    params = {
        "bild_id": str(id),
    }

    response = requests.get(
        f"https://nea.geofly.eu/api.php/getFeature?{urlencode(params)}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    return response.json()


def construct_all_meta(
    feature: dict,
    for_zoom_level: int,
):
    """Use 1 specific feature from json["data"]["images"]["features"] (list) for parameter 'feature'"""
    min_zoom = int(feature["properties"]["image_minzoom"])
    max_zoom = int(feature["properties"]["image_maxzoom"])
    if for_zoom_level < min_zoom or for_zoom_level > max_zoom:
        raise ValueError(f"Invalid zoom level. max = {max_zoom}; min = {min_zoom}")

    image_tile_base_id = feature["properties"]["bildflugnummer"]

    divisor = 2 ** (max_zoom - for_zoom_level)

    total_width = int(feature["properties"]["image_width"] / divisor)
    total_height = int(feature["properties"]["image_height"] / divisor)
    imagepath = str(feature["properties"]["imagepath"])
    TILE_WIDTH, TILE_HEIGHT = (256, 256)
    result: list[tuple[int, int, str]] = []
    for y in range(ceil(total_height / TILE_HEIGHT)):
        for x in range(ceil(total_width / TILE_WIDTH)):
            url = f"https://nea.geofly.eu/tiles/{quote(str(image_tile_base_id))}/{quote(imagepath)}/{quote(str(for_zoom_level))}/{x}/{y}.jpg"
            result.append((x * TILE_WIDTH, y * TILE_HEIGHT, url))

    return ((total_width, total_height), result)


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


def get_image_name_from_feature(feature: dict):
    name = feature["properties"]["bilddateiname"]
    matches = re.findall(r"\d+", name)

    return "_".join(matches[1:4])


def clean_filename(filename: str):
    return re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "-", filename)


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

    image_location = feature["properties"]["gemeinde"]
    image_name = get_image_name_from_feature(feature)
    image_date = feature["properties"]["bildflugdatum"]

    print(f">> Image name: {image_name}")
    print(f">> Image location: {image_location}")
    print(f">> Image date: {image_date}")

    print()

    zoom = zoom_level_callback(
        int(feature["properties"]["image_minzoom"]),
        int(feature["properties"]["image_maxzoom"]),
    )

    (image_width, image_height), tile_list = construct_all_meta(feature, zoom)
    print()
    print(f">> Final image size: {image_width}x{image_height}")
    print(f">> Tilecount: {len(tile_list)}")
    print()
    if prompt_interrupt:
        try:
            input(
                "Press Enter to download or Ctrl+C to exit now or anytime during download."
            )
        except KeyboardInterrupt:
            print()
            print("Exited.")
            return

        print()

    img = download_all(((image_width, image_height), tile_list))
    output_name = f"{image_name}_{image_date}_{image_location}_{image_id}_{zoom}"
    output_name = clean_filename(output_name)

    path = output_name
    i = 2
    while os.path.exists(path + ".jpg"):
        path = f"{output_name} ({i})"
        i += 1
    path += ".jpg"

    img.convert("RGB").save(path, quality=95)

    print(f"\nSaved to {path}")
    print("Done")
