"""CLI arguments parser."""

import argparse as ap
from argparse import Namespace
from textwrap import dedent
from importlib.metadata import version, PackageNotFoundError
import core

def get_version():
    """Returns the application version from metadata or 'unknown' if not found."""
    try:
        return version("nea-geofly-mapper")
    except PackageNotFoundError:
        return "unknown"


def cli_args(argv) -> Namespace:
    """Parse CLI arguments.

    Args:
        argv: Optional argument list passed to ``argparse``.

    Returns:
        Parsed command-line arguments.
    """
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
        "-o",
        "--output-dir",
        type=str,
        default=".",
        help="Destination directory for downloaded files.",
    )
    parser.add_argument(
        "-n",
        "--filename-pattern",
        type=str,
        default=core.DEFAULT_FILENAME_PATTERN,
        help=(
            "Custom file-name pattern using str.format placeholders like "
            "{name}, {date}, {location}, {id}, {width}, {height}, {origin}, {spectral} and {zoom}."
        ),
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloading and saving the stitched image file.",
    )
    parser.add_argument(
        "--no-kml",
        action="store_true",
        help="Skip generating and saving the KML file.",
    )
    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="Skip generating and saving the metadata text file.",
    )

    setup_group = parser.add_argument_group("Setup")
    setup_group.add_argument(
        "-b", "--bookmarklet",
        action="store_true",
        help="Setup Bookmarklet",
    )

    version_group = parser.add_argument_group("Version")
    version_group.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {app_version}",
        help="Show the application version and exit."
    )


    args = parser.parse_args(argv)
    return args
