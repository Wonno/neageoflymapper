"""Tests for kmlgenerator module."""
from unittest.mock import MagicMock
from fastkml import kml, geometry
from pygeoif import geometry as pygeo
from kmlgenerator import generator

def test_generator():
    """Test the generator function with a mocked metainfos object."""
    # Mocking Metainfos object
    metainfos = MagicMock()
    metainfos.image_id = 123
    metainfos.image_name = "test_image"
    metainfos.image_location = "test_location"
    metainfos.image_date = "2023-01-01"

    # Mock return values for methods
    # center_coords_wgs84g should return (lon, lat) based on pyproj's always_xy=True
    metainfos.center_coords_wgs84g.return_value = (7.0, 51.0)
    metainfos.corner_coords_wgs84g.return_value = [
        (6.9, 50.9),
        (7.1, 50.9),
        (7.1, 51.1),
        (6.9, 51.1)
    ]

    # Call the generator
    k = generator(metainfos)

    # Verify KML structure
    assert isinstance(k, kml.KML)

    # Check Document
    features = list(k.features)
    assert len(features) == 1
    doc = features[0]
    assert isinstance(doc, kml.Document)
    assert doc.name == "test_image"

    # Check Placemark
    doc_features = list(doc.features)
    assert len(doc_features) == 1
    pm = doc_features[0]
    assert isinstance(pm, kml.Placemark)
    assert pm.name == "test_image"
    assert pm.id == "test_image"
    assert "id: 123" in pm.description
    assert "name: test_image" in pm.description
    assert "location: test_location" in pm.description
    assert "date: 2023-01-01" in pm.description

    # Check Geometry
    geoms = list(pm.geometry.geoms)
    assert len(geoms) == 2

    # Check Point
    point = geoms[0]
    assert isinstance(point, pygeo.Point)
    assert point.x == 7.0
    assert point.y == 51.0

    # Check LineString
    line = geoms[1]
    assert isinstance(line, pygeo.LineString)
    # Should have 5 points (original 4 + 1 to close loop)
    coords = list(line.coords)
    assert len(coords) == 5
    assert coords[0] == (6.9, 50.9, 0)
    assert coords[-1] == (6.9, 50.9, 0)

    # Also verify kml_geometry (the fastkml wrapper)
    assert isinstance(pm.kml_geometry, geometry.MultiGeometry)
    assert len(pm.kml_geometry.kml_geometries) == 2
