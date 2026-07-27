"""Tests for ``fastapi_turbo.script``."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from markupsafe import Markup

from fastapi_turbo import DEFAULT_TURBO_VERSION, TurboTemplates, turbo_script


def test_default_loads_pinned_version_from_cdn():
    out = turbo_script()
    assert isinstance(out, Markup)
    assert f"@hotwired/turbo@{DEFAULT_TURBO_VERSION}/" in out
    assert 'type="module"' in out
    assert "window.Turbo = Turbo;" in out


def test_carries_turbo_track_reload():
    assert 'data-turbo-track="reload"' in turbo_script()
    assert 'data-turbo-track="reload"' in turbo_script(url="/static/vendor/turbo.js")


def test_version_override():
    out = turbo_script(version="9.0.0")
    assert "@hotwired/turbo@9.0.0/" in out


def test_url_override_wins_over_version():
    out = turbo_script(version="9.0.0", url="/static/vendor/turbo.js")
    assert '"/static/vendor/turbo.js"' in out
    assert "9.0.0" not in out


def test_url_is_escaped():
    out = turbo_script(url='x"></script><script>alert(1)</script>')
    assert "</script><script>" not in out


def test_registered_as_jinja_global(tmp_path: Path):
    (tmp_path / "layout.html").write_text("<head>{{ turbo_script() }}</head>")
    templates = TurboTemplates(directory=str(tmp_path))
    app = FastAPI()

    @app.get("/")
    def root(request: Request):
        return templates.TemplateResponse(request, "layout.html", {})

    body = TestClient(app).get("/").text
    assert "window.Turbo = Turbo;" in body
    assert f"@hotwired/turbo@{DEFAULT_TURBO_VERSION}/" in body
