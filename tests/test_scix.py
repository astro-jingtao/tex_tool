import io
import os
import urllib.error

import pytest

from tex_tool.bib.scix import ADS_API_BASE, export_bibtex


class TestExportBibtexOffline:
    def _patch_urlopen(self, monkeypatch, response=None, error=None):
        captured = {}

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def read(self):
                return self._payload

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.get_full_url()
            captured["auth"] = request.get_header("Authorization")
            if error is not None:
                raise error
            return FakeResponse(response)

        monkeypatch.setattr(
            "tex_tool.bib.scix.urllib.request.urlopen", fake_urlopen
        )
        return captured

    def test_request_shape_and_body(self, monkeypatch) -> None:
        captured = self._patch_urlopen(monkeypatch, response=b"@ARTICLE{2024X,\n}\n")

        text = export_bibtex("2024X", "tok", base_url="https://example.test")

        assert text.startswith("@ARTICLE{2024X")
        assert captured["url"] == "https://example.test/v1/export/bibtex/2024X"
        assert captured["auth"] == "Bearer tok"

    def test_trailing_slash_tolerated(self, monkeypatch) -> None:
        captured = self._patch_urlopen(monkeypatch, response=b"@article{x,\n}\n")

        export_bibtex("x", "tok", base_url="https://example.test/")

        assert captured["url"] == "https://example.test/v1/export/bibtex/x"

    def test_http_error_translated(self, monkeypatch) -> None:
        error = urllib.error.HTTPError(
            "https://example.test/v1/export/bibtex/nope",
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"error": "Record not found"}'),
        )
        self._patch_urlopen(monkeypatch, error=error)

        with pytest.raises(RuntimeError, match="404"):
            export_bibtex("nope", "tok", base_url="https://example.test")

    def test_url_error_mentions_ads_fallback(self, monkeypatch) -> None:
        self._patch_urlopen(monkeypatch, error=urllib.error.URLError("refused"))

        with pytest.raises(RuntimeError, match=ADS_API_BASE):
            export_bibtex("x", "tok")


@pytest.mark.skipif(
    not os.environ.get("SCIX_TOKEN"),
    reason="SCIX_TOKEN not set; live API test skipped",
)
class TestExportBibtexLive:
    def test_fetches_a_known_bibcode(self) -> None:
        text = export_bibtex("2015RaSc...50..916A", os.environ["SCIX_TOKEN"])
        assert text.lstrip().startswith("@")
        assert "2015RaSc...50..916A" in text
