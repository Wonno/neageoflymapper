"""CLI entry point for downloading NEA Geofly images by ID and zoom level."""

import argparse as ap
from argparse import Namespace
from textwrap import dedent
from importlib.metadata import version, PackageNotFoundError

from app_console import console

import core


def get_version():
    """Returns the application version from metadata or 'unknown' if not found."""
    try:
        return version("nea-geofly-mapper")
    except PackageNotFoundError:
        return "unknown"


def prompt_zoom_level(minimum: int, maximum: int) -> int | None:
    """Prompt interactively for a zoom level within the provided range.

    Args:
        minimum: Lowest supported zoom level for the current image.
        maximum: Highest supported zoom level for the current image.

    Returns:
        The validated zoom level entered by the user.
    """
    zoom = None
    while zoom is None:
        zoom = input(f"Enter Zoom-Level ({minimum}-{maximum}): ")
        try:
            zoom = int(zoom)
            if zoom < minimum or zoom > maximum:
                raise ValueError()

            return zoom
        except ValueError:
            console.print("Wrong zoom-level.")
            zoom = None
    return zoom


def fixed_zoom_level(zoom_level: str):
    """Build a zoom-level resolver that always returns a fixed level.

    The fixed level may be ``"min"``, ``"max"``, or a numeric zoom string.

    Args:
        zoom_level: User-provided fixed zoom value.

    Returns:
        A callback that maps image min/max limits to a valid zoom level.
    """

    def zoom_level_callback(minimum: int, maximum: int):
        """Resolve the effective zoom level for one image's limits.

        Args:
            minimum: Image-specific minimum zoom level.
            maximum: Image-specific maximum zoom level.

        Returns:
            The effective zoom level.

        Raises:
            ValueError: If the configured level is invalid or out of range.
        """
        if zoom_level.lower() == "max":
            level = maximum
            console.print(f"Using max zoom level: {level}")
        elif zoom_level.lower() == "min":
            level = minimum
            console.print(f"Using min zoom level: {level}")
        else:
            try:
                level = int(zoom_level)
            except ValueError as ve:
                raise ValueError(f"Invalid zoom level '{zoom_level}'.") from ve

        if level < minimum or level > maximum:
            raise ValueError(
                f"The specified zoom level is not supported by this image. Min: {minimum}, Max: {maximum}"
            )

        return level

    return zoom_level_callback


def main(argv=None):
    """Run the command-line interface.

    Args:
        argv: Optional argument list passed to ``argparse``.
    """
    args = cli_args(argv)

    console.print("NEA Geofly - Imagemapper", style="bold green italic")

    index = 0
    try:
        while True:
            try:
                image_id = input("Enter ID: ") if args.id is None else args.id[index]
                index += 1
                image_id = int(image_id)
                core.main(
                    image_id,
                    fixed_zoom_level(args.zoom) if args.zoom else prompt_zoom_level,
                    prompt_interrupt=not (args.id and args.zoom),
                )
            except ValueError as e:
                console.print(str(e))
                console.print("Try again.", style="bold red")

            if args.id and index >= len(args.id):
                break
    except KeyboardInterrupt:
        console.print("\n :stop_button: Exiting.")


def cli_args(argv) -> Namespace:
    app_version = get_version()

    parser = ap.ArgumentParser(
        formatter_class=ap.RawDescriptionHelpFormatter,
        epilog=f"Version: {app_version}",
        description=dedent(
            """
            Downloads an Image by ID from https://nea.geofly.eu.
            If not arguments are set, values will be prompted for interactively.
            """
        ),
    )
    parser.add_argument("-i", "--id", type=int, nargs="+", help="Image ID(s).")
    parser.add_argument(
        "-z",
        "--zoom",
        type=str,
        required=False,
        help="Zoom level. You can specify 'max' or 'min' to use the highest/lowest zoom level for any image.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {app_version}",
        help="Show the application version and exit."
    )
    args = parser.parse_args(argv)
    return args


if __name__ == "__main__":
    main()
