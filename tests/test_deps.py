"""Tests for ``fastapi_turbo.deps``."""

from __future__ import annotations

from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_turbo import TurboContext, turbo_context


@pytest.fixture
def client():
    app = FastAPI()

    @app.get("/")
    async def root(turbo: Annotated[TurboContext, Depends(turbo_context)]):
        return {
            "is_frame_request": turbo.is_frame_request,
            "frame_request_id": turbo.frame_request_id,
            "accepts_stream": turbo.accepts_stream,
        }

    return TestClient(app)


def test_no_turbo_headers(client):
    body = client.get("/").json()
    assert body == {
        "is_frame_request": False,
        "frame_request_id": None,
        "accepts_stream": False,
    }


def test_turbo_frame_header_marks_frame_request(client):
    body = client.get("/", headers={"Turbo-Frame": "sidebar"}).json()
    assert body["is_frame_request"] is True
    assert body["frame_request_id"] == "sidebar"


def test_accepts_stream_via_accept_header(client):
    body = client.get("/", headers={"Accept": "text/vnd.turbo-stream.html"}).json()
    assert body["accepts_stream"] is True


def test_accepts_stream_in_mixed_accept_list(client):
    body = client.get("/", headers={"Accept": "text/html, text/vnd.turbo-stream.html;q=0.9"}).json()
    assert body["accepts_stream"] is True


def test_html_only_accept_does_not_accept_stream(client):
    body = client.get("/", headers={"Accept": "text/html"}).json()
    assert body["accepts_stream"] is False


def test_accept_q_zero_is_explicit_opt_out(client):
    body = client.get("/", headers={"Accept": "text/vnd.turbo-stream.html;q=0, text/html"}).json()
    assert body["accepts_stream"] is False


def test_accept_wildcard_only_does_not_accept_stream(client):
    body = client.get("/", headers={"Accept": "*/*"}).json()
    assert body["accepts_stream"] is False


def test_accept_media_type_is_case_insensitive(client):
    body = client.get("/", headers={"Accept": "TEXT/VND.Turbo-Stream.HTML"}).json()
    assert body["accepts_stream"] is True
