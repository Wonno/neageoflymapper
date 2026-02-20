import argparse as ap
from textwrap import dedent

try:
    import core
except TypeError:
    import core_legacy as core


def prompt_zoom_level(min: int, max: int) -> int:
    zoom = None
    while zoom is None:
        zoom = input(f"Enter Zoom-Level ({min}-{max}): ")
        try:
            zoom = int(zoom)
            if zoom < min or zoom > max:
                raise ValueError()

            return zoom
        except ValueError:
            print("Wrong zoom-level.")
            zoom = None


def fixed_zoom_level(level: int):
    def zoom_level_callback(min: int, max: int):
        if level < min or level > max:
            raise ValueError(
                f"The specified zoom level is not supported by this image. Min: {min}, Max: {max}"
            )

        return level

    return zoom_level_callback


if __name__ == "__main__":
    parser = ap.ArgumentParser(
        formatter_class=ap.RawDescriptionHelpFormatter,
        description=dedent(
            """
        Downloads an Image by ID from https://nea.geofly.eu.
        If not arguments are set, values will be prompted for interactively.
        """
        ),
    )
    parser.add_argument("-i", "--id", type=int, required=False, help="Image ID.")
    parser.add_argument("-z", "--zoom", type=int, required=False, help="Zoom level.")
    args = parser.parse_args()

    print("# NEA Viewer - Imagemapper")
    print()

    image_id = None
    while image_id is None:
        image_id = args.id or input("Enter ID: ")
        try:
            image_id = int(image_id)
            core.main(
                image_id,
                fixed_zoom_level(args.zoom) if args.zoom else prompt_zoom_level,
                prompt_interrupt=not (args.id and args.zoom),
            )

            break
        except ValueError:
            if args.id:
                break
            print("Try again.")
            image_id = None
