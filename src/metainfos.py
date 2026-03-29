"""Metadata model and coordinate conversion helpers for aerial image features."""

# pylint: disable=too-many-instance-attributes

import re
from dataclasses import dataclass
from textwrap import dedent

from coords import to_epsg31468, to_epsg3857, to_epsg4326


@dataclass
class Metainfos:
    """Holds metadata for a single aerial image feature.

    Attributes:
        image_id (int): Unique identifier of the image.
        center_crs (str): CRS name of the center coordinate.
        center_coords (tuple): Center coordinate in the source CRS.
        corner_crs (str): CRS name of the corner coordinates.
        corner_coords (tuple): Corner coordinates in the source CRS (up to 4 corners).
        image_location (str): Municipality name where the image was taken.
        image_name (str): Derived short name of the image.
        image_date (str): Date of the aerial survey flight.
        image_tile_base_id (str): Flight number / tile base identifier.
        image_width (int): Width of the image in pixels.
        image_height (int): Height of the image in pixels.
        image_path (str): Server-side path to the image file.
        zoom_min (int): Minimum zoom level for the image.
        zoom_max (int): Maximum zoom level for the image.
        image_origin (str): Origin of the image.
        image_available (str): Image availability
        image_spectral (str): Spectral attribute of the image
    """

    image_id: int

    center_crs: str
    center_coords: tuple
    corner_crs: str
    corner_coords: tuple

    image_location: str
    image_name: str
    image_date: str
    image_tile_base_id: str
    image_width: int
    image_height: int
    image_path: str
    image_origin = None
    image_available = None
    image_spectral = None

    zoom_min: int
    zoom_max: int

    def __init__(self, image_id, feature: dict):
        """Initialise Metainfos from feature dictionary.

        Args:
            image_id (int): Unique identifier for the image.
            feature (dict): feature dict as returned by the NRW WFS endpoint.
        """

        self.image_id = image_id
        self.center_crs = feature["quickview"]["center"]["crs"]["properties"]["name"]
        self.center_coords = feature["quickview"]["center"]["coordinates"]

        self.corner_crs = feature["geometry"]["crs"]["properties"]["name"]
        self.corner_coords = feature["geometry"]["coordinates"][0]

        self.image_location = feature["properties"]["gemeinde"]
        self.image_date = feature["properties"]["bildflugdatum"]
        self.image_tile_base_id = feature["properties"]["bildflugnummer"]
        self.image_name = self.__get_image_name_from_feature(feature)

        self.image_width = int(feature["properties"]["image_width"])
        self.image_height = int(feature["properties"]["image_height"])
        self.image_path = str(feature["properties"]["imagepath"])
        self.image_spectral = feature["properties"]["spektralekanaele"]
        self.image_available = feature["properties"]["image_available"]
        self.image_origin = feature["properties"]["herkunft_der_luftbilder"]

        self.zoom_min = int(feature["properties"]["image_minzoom"])
        self.zoom_max = int(feature["properties"]["image_maxzoom"])

    # noinspection PyMethodMayBeStatic
    def __get_image_name_from_feature(self, feature: dict):
        """Extract a short image name from the feature's file name property.

        Parses all numeric groups from *bilddateiname* and joins groups 2–4
        (index 1–3) with underscores.

        Args:
            feature (dict): feature dict.

        Returns:
            str: Short image name composed of extracted numeric parts.
        """
        name = feature["properties"]["bilddateiname"]
        matches = re.findall(r"\d+", name)
        return "_".join(matches[1:4])

    def __corner(self, fun):
        """Apply a coordinate-transformation function to all four corner coordinates.

        Args:
            fun (callable): Transformation function with signature
                ``fun(crs: str, coord) -> tuple``.

        Returns:
            list[tuple]: Transformed corner coordinates.
        """
        return [fun(self.corner_crs, coord) for coord in self.corner_coords[:4]]

    def corner_coords_gk4(self):
        """Return the four corner coordinates in GK4 (EPSG:31468).

        Returns:
            list[tuple]: Corner coordinates as (x, y) pairs in EPSG:31468.
        """
        return self.__corner(to_epsg31468)

    def corner_coords_wgs84(self):
        """Return the four corner coordinates in Web Mercator (EPSG:3857).

        Returns:
            list[tuple]: Corner coordinates as (x, y) pairs in EPSG:3857.
        """
        return self.__corner(to_epsg3857)

    def corner_coords_wgs84g(self):
        """Return the four corner coordinates in WGS84 geographic (EPSG:4326).

        Returns:
            list[tuple]: Corner coordinates as (lat, lon) pairs in EPSG:4326.
        """
        return self.__corner(to_epsg4326)

    def __center(self, fun):
        """Apply a coordinate-transformation function to the center coordinate.

        Args:
            fun (callable): Transformation function with signature
                ``fun(crs: str, coord) -> tuple``.

        Returns:
            tuple: Transformed center coordinate.
        """
        return fun(self.center_crs, self.center_coords)

    def center_coords_gk4(self):
        """Return the center coordinate in GK4 (EPSG:31468).

        Returns:
            tuple: Center coordinate as (x, y) in EPSG:31468.
        """
        return self.__center(to_epsg31468)

    def center_coords_wgs84(self):
        """Return the center coordinate in Web Mercator (EPSG:3857).

        Returns:
            tuple: Center coordinate as (x, y) in EPSG:3857.
        """
        return self.__center(to_epsg3857)

    def center_coords_wgs84g(self):
        """Return the center coordinate in WGS84 geographic (EPSG:4326).

        Returns:
            tuple: Center coordinate as (lat, lon) in EPSG:4326.
        """
        return self.__center(to_epsg4326)

    def info_text(self) -> str:
        """Build a human-readable summary string of the image metadata.

        The summary includes the image ID, name, location, date, center
        coordinates in three CRS systems, corner coordinates in three CRS
        systems, and image dimensions.

        Returns:
            str: Multi-line metadata summary (leading/trailing whitespace stripped).
        """
        lat, lon = self.center_coords_wgs84g()
        merkator_x, merkator_y = self.center_coords_wgs84()
        gauss_kruger_4_x, gauss_kruger_4_y = self.center_coords_gk4()
        corners_gps = str.join(", ", [f"{y} {x}" for x, y in self.corner_coords_wgs84g()])
        corners_merkator = str.join(", ", [f"{x} {y}" for x, y in self.corner_coords_wgs84()])
        corners_gauss_kruger_4 = str.join(", ", [f"{x} {y}" for x, y in self.corner_coords_gk4()])
        return dedent(
            f"""
            id={self.image_id}
            name={self.image_name}
            location={self.image_location}
            date={self.image_date}
            geo_center(WGS84/EPSG:4326; lat, lon)={lat}, {lon}
            geo_center(WGS84 Pseudo/EPSG:3857)={merkator_x}, {merkator_y}
            geo_center(GK4/EPSG:31468)={gauss_kruger_4_x}, {gauss_kruger_4_y}
            geo_corners(WGS84/EPSG:4326; lat, lon)=({corners_gps})
            geo_corners(WGS84 Pseudo/EPSG:3857)=({corners_merkator})
            geo_corners(GK4/EPSG:31468)=({corners_gauss_kruger_4})
            width={self.image_width}
            height={self.image_height}
            """
        ).strip()
