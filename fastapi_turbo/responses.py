"""Response classes for Turbo-aware endpoints."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.responses import Response

__all__ = ["TURBO_STREAM_MEDIA_TYPE", "TurboStreamResponse", "append_vary"]

# The media type Turbo advertises on form submissions and expects on
# stream responses.
TURBO_STREAM_MEDIA_TYPE = "text/vnd.turbo-stream.html"


def append_vary(headers: MutableHeaders, value: str) -> None:
    """Add ``value`` to the response's ``Vary`` header (idempotent).

    Endpoints that answer differently based on a request header (the
    ``Accept`` negotiation for streams, the ``Turbo-Frame`` header for
    frames) must declare it, or an HTTP cache may serve one variant to
    the other kind of client.
    """
    existing = headers.get("vary")
    if existing is None:
        headers["vary"] = value
        return
    tokens = {token.strip().lower() for token in existing.split(",")}
    if value.lower() not in tokens:
        headers["vary"] = f"{existing}, {value}"


class TurboStreamResponse(Response):
    """HTTP response carrying one or more Turbo Stream actions.

    Sets ``Content-Type: text/vnd.turbo-stream.html`` so Turbo on the
    client recognizes the body as stream actions to apply rather than
    HTML to render. ``content`` accepts a single string of stream HTML
    or an iterable of strings (e.g. the return values from
    ``fastapi_turbo.streams.*``), which are joined verbatim — no
    separator, no extra escaping, since each builder already produces
    well-formed ``<turbo-stream>`` markup.

    Declares ``Vary: Accept``: this response is the stream
    representation of its URL. An HTML client hitting the same URL
    receives a different body, so a cache must keep the two variants
    separate.

    Use as ``response_class=TurboStreamResponse`` on a route to have
    OpenAPI document the response media type, or instantiate directly.
    """

    media_type = TURBO_STREAM_MEDIA_TYPE

    def __init__(
        self,
        content: str | bytes | Iterable[str] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: Any = None,
    ) -> None:
        if content is not None and not isinstance(content, (str, bytes)):
            content = "".join(content)
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
        append_vary(self.headers, "Accept")
