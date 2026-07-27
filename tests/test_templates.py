"""Tests for ``fastapi_turbo.templates``."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from fastapi_turbo import TurboTemplates
from fastapi_turbo.testing import assert_turbo_stream, parse_streams


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    (tmp_path / "row.html").write_text('<li id="item-{{ item.id }}">{{ item.name }}</li>')
    return tmp_path


def test_render_fragment_renders_partial_template(templates_dir: Path):
    templates = TurboTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_fragment(request, "row.html", item={"id": 1, "name": "x"})

    resp = TestClient(app).get("/")
    assert resp.text == '<li id="item-1">x</li>'
    vary_tokens = {t.strip().lower() for t in resp.headers["vary"].split(",")}
    assert "turbo-frame" in vary_tokens


def test_render_stream_returns_turbo_stream_response(templates_dir: Path):
    templates = TurboTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_stream(
            request,
            "row.html",
            action="append",
            target="items",
            item={"id": 7, "name": "lucky"},
        )

    resp = TestClient(app).get("/")
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert len(actions) == 1
    assert actions[0].action == "append"
    assert actions[0].target == "items"
    assert actions[0].content == '<li id="item-7">lucky</li>'


def test_extra_context_processors_compose(templates_dir: Path):
    def brand_ctx(request: Request) -> dict[str, object]:
        return {"brand": "Hotwire"}

    (templates_dir / "branded.html").write_text("Hello {{ brand }}, {{ message }}.")
    templates = TurboTemplates(
        directory=str(templates_dir),
        context_processors=[brand_ctx],
    )
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.TemplateResponse(request, "branded.html", {"message": "world"})

    body = TestClient(app).get("/").text
    assert body == "Hello Hotwire, world."
