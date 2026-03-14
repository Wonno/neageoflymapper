from __future__ import annotations

import os
import re
import sys
import traceback
from collections.abc import Callable
from math import ceil
from textwrap import dedent
from urllib.parse import quote, urlencode
from rich.progress import Progress

import requests
from PIL import Image

from coords import to_epsg3857, to_epsg4326, to_epsg31468

REQUEST_TIMEOUT = 8


def get_features(id: int) -> dict:
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

    with Progress() as p:
        t = p.add_task("Downloading...", total=100)
        while not p.finished:
            try:
                for i, (x, y, url) in enumerate(tile_list):
                    p.update(t, advance=i/len(tile_list)*100)
                    print(f"Downloading Tile #{i + 1} of {len(tile_list)} [{url}]", file=sys.stderr)
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
                        print(f"Tile #{i + 1} failed: {e}")
            except KeyboardInterrupt:
                print("Interrupting download.")
    return img


def get_image_name_from_feature(feature: dict):
    name = feature["properties"]["bilddateiname"]
    matches = re.findall(r"\d+", name)

    return "_".join(matches[1:4])


def clean_filename(filename: str):
    return re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "-", filename)


def geo_info(feature: dict):
    center_crs = feature["quickview"]["center"]["crs"]["properties"]["name"]
    center_coords = feature["quickview"]["center"]["coordinates"]

    assert len(center_coords) == 2

    corner_crs = feature["geometry"]["crs"]["properties"]["name"]
    corner_coords = feature["geometry"]["coordinates"][0]

    assert 4 <= len(corner_coords) <= 5

    # remove last entry (equals first)
    if len(corner_coords) == 5:
        corner_coords = corner_coords[:-1]

    corner_coords_gk4 = [to_epsg31468(corner_crs, coord) for coord in corner_coords]
    corner_coords_wgs84 = [to_epsg3857(corner_crs, coord) for coord in corner_coords]
    corner_coords_wgs84g = [to_epsg4326(corner_crs, coord) for coord in corner_coords]

    center_coords_gk4 = to_epsg31468(center_crs, center_coords)
    center_coords_wgs84 = to_epsg3857(center_crs, center_coords)
    center_coords_wgs84g = to_epsg4326(center_crs, center_coords)

    return dedent(
        f"""
        geo_center(WGS84/EPSG:4326; lat, lon)={center_coords_wgs84g[1]}, {center_coords_wgs84g[0]}
        geo_center(WGS84 Pseudo/EPSG:3857)={center_coords_wgs84[0]}, {center_coords_wgs84[1]}
        geo_center(GK4/EPSG:31468)={center_coords_gk4[0]}, {center_coords_gk4[1]}
        geo_corners(WGS84/EPSG:4326; lat, lon)=({str.join(", ", [
            f"{y} {x}" for x, y in corner_coords_wgs84g
        ])})
        geo_corners(WGS84 Pseudo/EPSG:3857)=({str.join(", ", [
            f"{x} {y}" for x, y in corner_coords_wgs84
        ])})
        geo_corners(GK4/EPSG:31468)=({str.join(", ", [
            f"{x} {y}" for x, y in corner_coords_gk4
        ])})
        """
    ).strip()


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

    def image_metadata_text():
        geo_info_text = ""
        try:
            geo_info_text = geo_info(feature)
        except:
            print(
                f"Warning: Could not determine geo info metadata:\n{traceback.format_exc()}",
                file=sys.stderr,
            )

        return (
            dedent(
                f"""
                id={image_id}
                name={image_name}
                location={image_location}
                date={image_date}
                %(geo_info_text)s
                width={image_width}
                height={image_height}
                zoom_level={zoom}
                """
            ).strip()
            % {
                "geo_info_text": geo_info_text,
            }
        )

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

    image_path = f"{path}.jpg"
    metadata_path = f"{path}.txt"

    img.convert("RGB").save(image_path, quality=95)
    with open(metadata_path, "w", encoding="utf-8") as fp:
        fp.write(image_metadata_text())
        fp.write("\n")

    print(f"\nSaved to {image_path}")
    print("Done")
