"""Core functions for downloading, assembling, and saving NEA Geofly aerial images.

This module contains the main logic for retrieving metadata, downloading image tiles,
assembling the tiles into a complete image, and saving metadata and KML files.
"""

from __future__ import annotations

import asyncio
import os
import re
from io import BytesIO
from string import Formatter
from collections.abc import Callable
from math import ceil, degrees
from typing import Any
from urllib.parse import quote

import httpx
from httpx_retries import Retry, RetryTransport
from rich.progress import Progress, TaskID
from rich.table import Table

from PIL import Image

from app_console import console
from exif_writer import get_exif_bytes, write_iptc
from kmlgenerator import generator
from metainfos import Metainfos

REQUEST_TIMEOUT = 8
DOWNLOAD_CONCURRENCY = 20
DEFAULT_FILENAME_PATTERN = "{name}_{date}_{location}_{id}_{zoom}"


def create_http_client() -> httpx.Client:
    """Create an HTTP/2 client that retries transient request failures three times."""
    transport = RetryTransport(
        transport=httpx.HTTPTransport(http2=True),
        retry=Retry(total=3, status_forcelist={0, 429, 500, 502, 503, 504}),
    )
    return httpx.Client(transport=transport)


def create_async_http_client() -> httpx.AsyncClient:
    """Create a concurrent HTTP/2 client with three retries for transient failures."""

    async def validate_response(response: httpx.Response) -> None:
        """Read the full response so mid-body protocol errors can be retried."""
        await response.aread()

    transport = RetryTransport(
        transport=httpx.AsyncHTTPTransport(
            http2=True,
            limits=httpx.Limits(max_connections=DOWNLOAD_CONCURRENCY),
        ),
        retry=Retry(
            total=3,
            status_forcelist={0, 429, 500, 502, 503, 504},
            validate_response=validate_response,
        ),
    )
    return httpx.AsyncClient(transport=transport)


def get_features(image_id: int) -> dict:
    """Fetch raw JSON from the NEA for the given image id.

    Args:
        image_id: Numeric NEA image identifier.

    Returns:
        Parsed JSON response as a dict.
    """
    with create_http_client() as client:
        response = client.get(
            "https://nea.geofly.eu/api.php/getFeature",
            params={"bild_id": str(image_id)},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        return response.json()


def construct_all_meta(metainfos: Metainfos, for_zoom_level: int):
    """Compute overall image dimensions and the list of tile URLs for a certain zoom level.

    Args:
        metainfos: Metadata for the image.
        for_zoom_level: Desired zoom level.

    Returns:
        A tuple of (width, height) and a list of (x_offset, y_offset, url).
    """
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
    """Download all tiles and assemble them into a single image.

    Args:
        meta: Tuple of ((width, height), tile_list) where tile_list items are
              (x_offset, y_offset, url).

    Returns:
        A Image containing the stitched tiles.
    """
    image_size, tile_list = meta
    img = Image.new("RGBA", image_size, 0)

    with Progress() as progress:
        task_id = progress.add_task("Downloading...", total=100)
        try:
            asyncio.run(download_tiles(tile_list, img, progress, task_id))
        except KeyboardInterrupt:
            progress.remove_task(task_id)
            console.print("\n :stop_button: Interrupting download.")
    return img


async def download_tiles(
    tile_list: list[tuple[int, int, str]],
    image: Image.Image,
    progress: Progress,
    task_id: TaskID,
) -> None:
    """Download and paste image tiles concurrently, up to the configured limit."""
    if not tile_list:
        progress.update(task_id, completed=100)
        return

    queue: asyncio.Queue[tuple[int, int, int, str]] = asyncio.Queue()
    for index, (x, y, url) in enumerate(tile_list):
        queue.put_nowait((index, x, y, url))

    async with create_async_http_client() as client:
        async def worker() -> None:
            """Download queued tiles and paste each successful response."""
            while not queue.empty():
                _index, _x, _y, _url = await queue.get()
                try:
                    response = await client.get(_url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    with Image.open(BytesIO(response.content)) as tile:
                        image.paste(tile, box=(_x, _y))
                except httpx.HTTPError as error:
                    console.print(f"Downloading Tile #{_index + 1} failed: {error}")
                finally:
                    progress.update(
                        task_id,
                        advance=100 / len(tile_list),
                        description=f"Downloaded Tile #{_index + 1} of {len(tile_list)}",
                    )
                    queue.task_done()

        await asyncio.gather(*(worker() for _ in range(min(DOWNLOAD_CONCURRENCY, len(tile_list)))))


def align_to_true_north(img: Image.Image, metainfos: Metainfos) -> Image.Image:
    """Rotate image so it is aligned to true north.

    Args:
        img: image
        metainfos: Metadata providing ``image_orientation``.

    Returns:
        Image.Image: A new, aligned to true north oriented image (expanded to fit all corners).
    """
    if not metainfos.image_orientation:
        return img

    # ``PIL.Image.rotate`` rotates counter-clockwise for positive angles,
    # so the clockwise orientation angle must be negated.
    return img.rotate(
        -degrees(metainfos.image_orientation), expand=True, resample=Image.Resampling.BICUBIC
    )


def clean_filename(filename: str):
    """Replace characters that are invalid in filesystem names."""
    return re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "-", filename)


def filename_pattern_fields(metainfos: Metainfos, zoom: int) -> dict[str, Any]:
    """Build the placeholder mapping for custom file-name patterns.

    Args:
        metainfos: Metadata for the selected image.
        zoom: Effective zoom level.

    Returns:
        Mapping of supported pattern placeholders to their values.
    """
    return {
        "id": metainfos.image_id,
        "name": metainfos.image_name,
        "date": metainfos.image_date,
        "location": metainfos.image_location,
        "width": metainfos.image_width,
        "height": metainfos.image_height,
        "origin": metainfos.image_origin,
        "spectral": metainfos.image_spectral,
        "zoom": zoom,
    }


def render_filename_pattern(metainfos: Metainfos, zoom: int, filename_pattern: str) -> str:
    """Render a file-name pattern to a sanitized base name.

    Args:
        metainfos: Metadata for the selected image.
        zoom: Effective zoom level.
        filename_pattern: ``str.format`` pattern for the output base name.

    Returns:
        Sanitized file-name stem.

    Raises:
        ValueError: If the pattern is invalid, uses unknown placeholders, or renders an empty name.
    """
    fields = filename_pattern_fields(metainfos, zoom)
    formatter = Formatter()
    available_fields = ", ".join(sorted(fields))

    for _, field_name, _, _ in formatter.parse(filename_pattern):
        if field_name is None:
            continue
        if field_name not in fields:
            raise ValueError(
                f"Unknown filename pattern field '{field_name}'. Available fields: {available_fields}"
            )

    try:
        output_name = filename_pattern.format(**fields)
    except KeyError as error:
        raise ValueError(
            f"Unknown filename pattern field '{error.args[0]}'. Available fields: {available_fields}"
        ) from error
    except ValueError as error:
        raise ValueError(f"Invalid filename pattern: {error}") from error

    output_name = clean_filename(output_name).strip()
    if not output_name:
        raise ValueError("Filename pattern must render a non-empty file name.")

    return output_name


def determine_outputname(
    m: Metainfos,
    zoom: int,
    output_directory: str = ".",
    filename_pattern: str = DEFAULT_FILENAME_PATTERN,
) -> str:
    """Build a unique output path without file extension.

    Args:
        m: Metadata for the selected image.
        zoom: Effective zoom level.
        output_directory: Directory where output files should be stored.
        filename_pattern: ``str.format`` pattern for the output base name.

    Returns:
        Output path without a file extension.
    """
    output_name = render_filename_pattern(m, zoom, filename_pattern)

    path = os.path.join(output_directory, output_name)
    i = 2
    while any(os.path.exists(path + extension) for extension in (".jpg", ".txt", ".kml")):
        path = os.path.join(output_directory, f"{output_name} ({i})")
        i += 1
    return path

def main(
    image_id: int,
    zoom_level_callback: Callable[[int, int], int],
    prompt_interrupt: bool = True,
    output_directory: str = ".",
    filename_pattern: str = DEFAULT_FILENAME_PATTERN,
    no_download: bool = False,
    no_kml: bool = False,
    no_txt: bool = False,
    rotate: bool = False,
): # pylint: disable=R0913,R0914,R0917
    """Download one image and write the image, metadata, and KML files.

    Args:
        image_id: NEA image identifier.
        zoom_level_callback: Callback resolving the effective zoom level.
        prompt_interrupt: Whether to pause for confirmation before download.
        output_directory: Destination directory for generated files.
        filename_pattern: ``str.format`` pattern for the output base name.
        no_download: Whether to skip downloading and saving the stitched image.
        no_kml: Whether to skip generating and saving the KML file.
        no_txt: Whether to skip generating and saving the metadata text file.
        rotate: Whether to rotate and align to true north if possible.
    """
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

    if prompt_interrupt and not no_download:
        try:
            input("Press Enter to download or Ctrl+C to exit now or anytime during download.")
        except KeyboardInterrupt:
            console.print()
            console.print("Exited.")
            return
        console.print()

    os.makedirs(output_directory, exist_ok=True)
    path = determine_outputname(metainfos, zoom, output_directory, filename_pattern)
    image_path = f"{path}.jpg"
    text_path = f"{path}.txt"
    kml_path = f"{path}.kml"

    if not no_download:
        img = download_all(((image_width, image_height), tile_list))
        if rotate:
            img = align_to_true_north(img, metainfos)
        exif_bytes = get_exif_bytes(metainfos)
        convert = img.convert("RGB")
        save_options: dict[str, Any] = {"quality": 95}
        if exif_bytes is not None:
            save_options["exif"] = exif_bytes
        convert.save(image_path, **save_options)

        # write IPTC metadata
        write_iptc(image_path, metainfos)

    if not no_txt:
        with open(text_path, "w", encoding="utf-8") as fp:
            fp.write(metainfos.info_text())
            fp.write("\n")
            fp.write(f"zoom_level={zoom}\n")

    if not no_kml:
        kml = generator(metainfos)
        with open(kml_path, "w", encoding="utf-8") as f:
            f.write(kml.to_string(prettyprint=True))

    if not no_download:
        console.print(f"\n:floppy_disk:  Saved to [i]{image_path}[/i]")
        return

    console.print(f"\n:floppy_disk:  Saved to [i]{image_path}[/i]")


def info_summary(
    image_height: int | Any,
    image_width: int | Any,
    metainfos: Metainfos,
    tile_list: list[tuple[int, int, str]],
    zoom: int
):
    """
    Create a summary table of image metadata and download parameters.

    Args:
        image_height (int | Any): The height of the image in pixels.
        image_width (int | Any): The width of the image in pixels.
        metainfos (Metainfos): Metadata object containing image properties.
        tile_list (list[tuple[int, int, str]]): List of tile coordinates and URLs.
        zoom (int): The selected zoom level.

    Returns:
        Table: A Rich Table object with the summary information.
    """
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
