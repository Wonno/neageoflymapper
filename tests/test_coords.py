"""Tests for coords module."""
from unittest.mock import patch, MagicMock
import pytest
from coords import epsg_to_zone, zone_to_epsg, to_epsg3857, to_epsg4326, to_epsg31468

def test_epsg_to_zone():
    """Test conversion from EPSG string to Gauss-Kruger zone."""
    assert epsg_to_zone("EPSG:31466") == 2
    assert epsg_to_zone("EPSG:31467") == 3
    assert epsg_to_zone("EPSG:31468") == 4
    assert epsg_to_zone("EPSG:31469") == 5

def test_epsg_to_zone_invalid():
    """Test epsg_to_zone with invalid input."""
    with pytest.raises(AssertionError):
        epsg_to_zone("INVALID")

def test_zone_to_epsg():
    """Test conversion from Gauss-Kruger zone to EPSG string."""
    assert zone_to_epsg(2) == "EPSG:31466"
    assert zone_to_epsg(3) == "EPSG:31467"
    assert zone_to_epsg(4) == "EPSG:31468"
    assert zone_to_epsg(5) == "EPSG:31469"

def test_zone_to_epsg_invalid():
    """Test zone_to_epsg with invalid input."""
    with pytest.raises(AssertionError):
        zone_to_epsg(1)
    with pytest.raises(AssertionError):
        zone_to_epsg(6)

def test_to_epsg3857_same_crs():
    """Test to_epsg3857 when input CRS is already EPSG:3857."""
    coords = (1000, 2000)
    assert to_epsg3857("EPSG:3857", coords) == coords

@patch("coords.Transformer.from_crs")
def test_to_epsg3857_transform(mock_from_crs):
    """Test to_epsg3857 transformation logic."""
    mock_transformer = MagicMock()
    mock_transformer.transform.return_value = (10.0, 20.0)
    mock_from_crs.return_value = mock_transformer

    result = to_epsg3857("EPSG:4326", (7, 51))

    assert result == (10.0, 20.0)
    mock_from_crs.assert_called_once_with("EPSG:4326", "EPSG:3857", always_xy=True)
    mock_transformer.transform.assert_called_once_with(7, 51)

def test_to_epsg4326_same_crs():
    """Test to_epsg4326 when input CRS is already EPSG:4326."""
    coords = (7, 51)
    assert to_epsg4326("EPSG:4326", coords) == coords

@patch("coords.Transformer.from_crs")
def test_to_epsg4326_transform(mock_from_crs):
    """Test to_epsg4326 transformation logic."""
    mock_transformer = MagicMock()
    mock_transformer.transform.return_value = (7.0, 51.0)
    mock_from_crs.return_value = mock_transformer

    result = to_epsg4326("EPSG:3857", (1000, 2000))

    assert result == (7.0, 51.0)
    mock_from_crs.assert_called_once_with("EPSG:3857", "EPSG:4326", always_xy=True)
    mock_transformer.transform.assert_called_once_with(1000, 2000)

def test_to_epsg31468_same_crs():
    """Test to_epsg31468 when input CRS is already EPSG:31468."""
    coords = (4000, 5000)
    assert to_epsg31468("EPSG:31468", coords) == coords

@patch("coords.Transformer.from_crs")
def test_to_epsg31468_transform(mock_from_crs):
    """Test to_epsg31468 transformation logic."""
    mock_transformer = MagicMock()
    mock_transformer.transform.return_value = (4000, 5000)
    mock_from_crs.return_value = mock_transformer

    result = to_epsg31468("EPSG:4326", (7, 51))

    assert result == (4000, 5000)
    mock_from_crs.assert_called_once_with("EPSG:4326", "EPSG:31468", always_xy=True)
    mock_transformer.transform.assert_called_once_with(7.0, 51.0)
