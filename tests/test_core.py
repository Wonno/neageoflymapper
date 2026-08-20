"""Tests for core file-name handling and output options."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import core
from core import determine_outputname, render_filename_pattern


def create_metainfos():
    """Create a minimal metadata object for file-name tests."""
    return SimpleNamespace(
        image_id=123,
        image_name="image_name",
        image_date="2026-04-12",
        image_location="Test City",
        image_tile_base_id="flight-7",
        image_width=4000,
        image_height=3000,
        image_origin="NEA",
        image_spectral="RGB",
    )


def test_render_filename_pattern_uses_placeholders():
    """Test that custom file-name patterns are rendered from metadata."""
    output_name = render_filename_pattern(create_metainfos(), 5, "{date}_{id}_{zoom}")

    assert output_name == "2026-04-12_123_5"


def test_render_filename_pattern_rejects_unknown_placeholder():
    """Test that unknown file-name placeholders raise a clear error."""
    with pytest.raises(ValueError, match="Unknown filename pattern field 'unknown'"):
        render_filename_pattern(create_metainfos(), 5, "{unknown}")


def test_determine_outputname_uses_output_directory_and_pattern(tmp_path):
    """Test that output paths use the selected directory and pattern."""
    path = determine_outputname(
        create_metainfos(),
        5,
        str(tmp_path),
        "{date}_{id}_{zoom}",
    )

    assert Path(path) == tmp_path / "2026-04-12_123_5"


def test_determine_outputname_deduplicates_within_output_directory(tmp_path):
    """Test that de-duplication stays scoped to the selected directory."""
    existing = tmp_path / "2026-04-12_123_5.jpg"
    existing.write_bytes(b"existing")

    path = determine_outputname(
        create_metainfos(),
        5,
        str(tmp_path),
        "{date}_{id}_{zoom}",
    )

    assert Path(path) == tmp_path / "2026-04-12_123_5 (2)"


def test_determine_outputname_deduplicates_with_existing_kml(tmp_path):
    """Test that de-duplication also considers existing KML files."""
    existing = tmp_path / "2026-04-12_123_5.kml"
    existing.write_text("<kml />", encoding="utf-8")

    path = determine_outputname(
        create_metainfos(),
        5,
        str(tmp_path),
        "{date}_{id}_{zoom}",
    )

    assert Path(path) == tmp_path / "2026-04-12_123_5 (2)"


def test_determine_outputname_deduplicates_with_existing_txt(tmp_path):
    """Test that de-duplication also considers existing text metadata files."""
    existing = tmp_path / "2026-04-12_123_5.txt"
    existing.write_text("metadata", encoding="utf-8")

    path = determine_outputname(
        create_metainfos(),
        5,
        str(tmp_path),
        "{date}_{id}_{zoom}",
    )

    assert Path(path) == tmp_path / "2026-04-12_123_5 (2)"


def test_main_saves_image_when_exif_is_unavailable(tmp_path, monkeypatch):
    """Test JPEG saving does not pass None as the EXIF option."""
    metainfos = SimpleNamespace(
        image_available=True,
        zoom_min=1,
        zoom_max=5,
    )
    monkeypatch.setattr(
        core,
        "get_features",
        lambda image_id: {"data": {"images": {"features": [{}]}}},
    )
    monkeypatch.setattr(core, "Metainfos", lambda image_id, feature: metainfos)
    monkeypatch.setattr(core, "construct_all_meta", lambda metadata, zoom: ((1, 1), []))
    monkeypatch.setattr(core, "info_summary", lambda *args: "")
    monkeypatch.setattr(core, "determine_outputname", lambda *args: str(tmp_path / "output"))
    monkeypatch.setattr(core, "download_all", lambda meta: Image.new("RGB", (1, 1)))
    monkeypatch.setattr(core, "get_exif_bytes", lambda metadata: None)
    monkeypatch.setattr(core, "write_iptc", lambda image_path, metadata: None)

    core.main(
        123,
        zoom_level_callback=lambda minimum, maximum: maximum,
        prompt_interrupt=False,
        output_directory=str(tmp_path),
        no_kml=True,
        no_txt=True,
    )

    assert (tmp_path / "output.jpg").is_file()
