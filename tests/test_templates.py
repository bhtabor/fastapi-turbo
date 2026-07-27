"""Tests for ``fastapi_turbo.templates``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from fastapi_turbo import TurboContext, TurboTemplates, turbo_context
from fastapi_turbo.testing import assert_turbo_stream, parse_streams


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    (tmp_path / "row.html").write_text('<li id="item-{{ item.id }}">{{ item.name }}</li>')
    return tmp_path


def test_frame_request_serves_partial_else_full_page(templates_dir: Path):
    templates = TurboTemplates(directory=str(templates_dir))
    (templates_dir / "page.html").write_text("<main>{{ item.name }}</main>")
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/items/{item_id}")
    def item(
        request: Request,
        turbo: Annotated[TurboContext, Depends(turbo_context)],
        item_id: int,
    ):
        item = {"id": item_id, "name": "lucky"}
        name = "row.html" if turbo.is_frame_request else "page.html"
        return templates.TemplateResponse(request, name, {"item": item})

    client = TestClient(app)
    full = client.get("/items/7")
    assert full.text == "<main>lucky</main>"

    frame = client.get("/items/7", headers={"Turbo-Frame": "item-7"})
    assert frame.text == '<li id="item-7">lucky</li>'


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


def test_render_stream_requires_selector_for_selector_actions(templates_dir: Path):
    templates = TurboTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_stream(
            request,
            "row.html",
            action="append",
            item={"id": 7, "name": "lucky"},
        )

    with pytest.raises(ValueError, match="requires target= or targets="):
        TestClient(app).get("/")


def test_render_stream_refresh_does_not_require_selector(templates_dir: Path):
    templates = TurboTemplates(directory=str(templates_dir))
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test")

    @app.get("/")
    def root(request: Request):
        return templates.render_stream(request, "row.html", action="refresh")

    resp = TestClient(app).get("/")
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert len(actions) == 1
    assert actions[0].action == "refresh"
    assert actions[0].target is None


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
