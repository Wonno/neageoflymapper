"""Tests for core file-name handling and output options."""

import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
import httpx
from PIL import Image
from _pytest.monkeypatch import MonkeyPatch

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


def test_get_features_uses_http_client(monkeypatch: MonkeyPatch):
    """Test feature requests pass the expected image identifier and timeout."""
    calls = {}

    class FakeResponse:
        """Minimal successful API response."""

        def raise_for_status(self):
            """Represent a successful response."""

        def json(self):
            """Return the response payload."""
            return {"features": []}

    class FakeClient:
        """Capture feature request arguments."""

        def __enter__(self):
            """Return the client context."""
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            """Close the client context."""
            return False

        def get(self, url, *, params, timeout):
            """Capture request arguments and return a successful response."""
            calls["request"] = (url, params, timeout)
            return FakeResponse()

    def create_fake_client():
        """Return the fake HTTP client."""
        return FakeClient()

    monkeypatch.setattr(core, "create_http_client", create_fake_client)

    assert core.get_features(123) == {"features": []}
    assert calls["request"] == (
        "https://nea.geofly.eu/api.php/getFeature",
        {"bild_id": "123"},
        core.REQUEST_TIMEOUT,
    )


@pytest.mark.parametrize("failures", [1, 3])
def test_http_client_retries_server_errors(monkeypatch: MonkeyPatch, failures: int):
    """Test transient server errors are retried up to three times."""
    attempts = 0

    def respond(request):
        """Return temporary server errors before succeeding."""
        nonlocal attempts
        attempts += 1
        status_code = 500 if attempts <= failures else 200
        return httpx.Response(status_code, request=request)

    def mock_transport(*, http2):
        """Create a mock transport and verify HTTP/2 configuration."""
        assert http2 is True
        return httpx.MockTransport(respond)

    monkeypatch.setattr(core.httpx, "HTTPTransport", mock_transport)

    with core.create_http_client() as client:
        response = client.get("https://example.com")

    assert response.status_code == 200
    assert attempts == failures + 1


@pytest.mark.parametrize("failures", [1, 3])
def test_http_client_retries_transport_errors(monkeypatch: MonkeyPatch, failures: int):
    """Test transport errors are retried up to three times."""
    attempts = 0

    def respond(request):
        """Raise temporary transport errors before succeeding."""
        nonlocal attempts
        attempts += 1
        if attempts <= failures:
            raise httpx.ConnectError("temporary network failure", request=request)
        return httpx.Response(200, request=request)

    def mock_transport(*, http2):
        """Create a mock transport and verify HTTP/2 configuration."""
        assert http2 is True
        return httpx.MockTransport(respond)

    monkeypatch.setattr(core.httpx, "HTTPTransport", mock_transport)

    with core.create_http_client() as client:
        response = client.get("https://example.com")

    assert response.status_code == 200
    assert attempts == failures + 1


def test_download_all_fetches_tiles_concurrently(monkeypatch: MonkeyPatch):
    """Test tile downloads use concurrent asynchronous requests."""
    active_requests = 0
    max_active_requests = 0
    tile_bytes = BytesIO()
    Image.new("RGB", (1, 1), color="red").save(tile_bytes, format="PNG")

    async def respond(request):
        """Track simultaneous requests and return a valid image tile."""
        nonlocal active_requests, max_active_requests
        active_requests += 1
        max_active_requests = max(max_active_requests, active_requests)
        await asyncio.sleep(0.01)
        active_requests -= 1
        return httpx.Response(200, content=tile_bytes.getvalue(), request=request)

    def create_mock_client():
        """Create an async client with an in-memory response transport."""
        return httpx.AsyncClient(transport=httpx.MockTransport(respond))

    monkeypatch.setattr(core, "create_async_http_client", create_mock_client)

    image = core.download_all(
        ((3, 1), [(0, 0, "https://example.com/1"), (1, 0, "https://example.com/2"),
                  (2, 0, "https://example.com/3")])
    )

    assert max_active_requests > 1
    assert image.getpixel((0, 0)) == (255, 0, 0, 255)
    assert image.getpixel((1, 0)) == (255, 0, 0, 255)
    assert image.getpixel((2, 0)) == (255, 0, 0, 255)


def test_async_http_client_retries_connection_terminated_response(monkeypatch: MonkeyPatch):
    """Test HTTP/2 connection termination while reading a body is retried."""
    attempts = 0

    class TerminatedStream(httpx.AsyncByteStream):
        """Simulate an HTTP/2 stream terminated before its body arrives."""

        async def __aiter__(self):
            """Raise the transport protocol error seen on connection termination."""
            raise httpx.RemoteProtocolError("ConnectionTerminated error_code:0")
            yield b""

        async def aclose(self):
            """Close the simulated response stream."""

    async def respond(request):
        """Terminate the first response body and succeed on retry."""
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(200, stream=TerminatedStream(), request=request)
        return httpx.Response(200, content=b"complete", request=request)

    def mock_transport(*, http2, limits):
        """Create an async mock transport and verify its HTTP/2 configuration."""
        assert http2 is True
        assert limits.max_connections == core.DOWNLOAD_CONCURRENCY
        return httpx.MockTransport(respond)

    monkeypatch.setattr(core.httpx, "AsyncHTTPTransport", mock_transport)

    async def fetch_response():
        """Fetch using the configured retrying async client."""
        async with core.create_async_http_client() as client:
            return await client.get("https://example.com")

    response = asyncio.run(fetch_response())

    assert response.content == b"complete"
    assert attempts == 2


def test_render_filename_pattern_uses_placeholders():
    """Test that custom file-name patterns are rendered from metadata."""
    output_name = render_filename_pattern(create_metainfos(), 5, "{date}_{id}_{zoom}")

    assert output_name == "2026-04-12_123_5"


def test_render_filename_pattern_rejects_unknown_placeholder():
    """Test that unknown file-name placeholders raise a clear error."""
    with pytest.raises(ValueError, match="Unknown filename pattern field 'unknown'"):
        render_filename_pattern(create_metainfos(), 5, "{unknown}")


def test_determine_outputname_uses_output_directory_and_pattern(tmp_path: Path):
    """Test that output paths use the selected directory and pattern."""
    path = determine_outputname(
        create_metainfos(),
        5,
        str(tmp_path),
        "{date}_{id}_{zoom}",
    )

    assert Path(path) == tmp_path / "2026-04-12_123_5"


def test_determine_outputname_deduplicates_within_output_directory(tmp_path: Path):
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


def test_determine_outputname_deduplicates_with_existing_kml(tmp_path: Path):
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


def test_determine_outputname_deduplicates_with_existing_txt(tmp_path: Path):
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


def test_main_saves_image_when_exif_is_unavailable(tmp_path: Path, monkeypatch: MonkeyPatch):
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
    monkeypatch.setattr(core, "download_all", lambda meta: Image.new("RGB", (42, 42)))
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
