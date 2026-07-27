"""FastAPI dependencies for reading Turbo-related request signals."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from .responses import TURBO_STREAM_MEDIA_TYPE

__all__ = ["TurboContext", "accepts_turbo_stream", "turbo_context"]


def _explicit_quality(accept: str, media_type: str) -> float:
    """The q-value the Accept header assigns to an *exact* media type.

    Wildcard ranges (``*/*``, ``text/*``) deliberately don't count: for
    Turbo detection, only an explicit mention of the stream media type
    signals a Turbo client. Returns 0.0 when the type isn't listed.
    """
    best = 0.0
    for part in accept.split(","):
        segments = part.split(";")
        if segments[0].strip().lower() != media_type:
            continue
        q = 1.0
        for param in segments[1:]:
            key, _, value = param.partition("=")
            if key.strip().lower() == "q":
                try:
                    q = max(0.0, min(1.0, float(value.strip())))
                except ValueError:
                    q = 0.0
        best = max(best, q)
    return best


def accepts_turbo_stream(request: Request) -> bool:
    """True when the client explicitly accepts Turbo Stream responses.

    Capability detection, not preference negotiation: any request whose
    Accept header explicitly lists ``text/vnd.turbo-stream.html`` with a
    non-zero q-value understands streams — even if it ranks ``text/html``
    higher. Wildcards don't count (``Accept: */*`` API clients stay on
    the HTML path), and ``;q=0`` is an explicit opt-out.
    """
    accept = request.headers.get("accept", "")
    return _explicit_quality(accept, TURBO_STREAM_MEDIA_TYPE) > 0.0


@dataclass(frozen=True, slots=True)
class TurboContext:
    """Read-only summary of how the current request relates to Turbo.

    Attributes:
        is_frame_request: True if the request was issued by a
            ``<turbo-frame>`` (the ``Turbo-Frame`` header is present).
        frame_request_id: The ``id`` of the frame that initiated the
            request, or ``None`` for non-frame requests.
        accepts_stream: True if the client explicitly lists the Turbo
            Stream media type in its Accept header (with non-zero q).
            Turbo advertises this on form submissions; a normal page
            navigation doesn't.
    """

    accepts_stream: bool
    frame_request_id: str | None
    is_frame_request: bool


async def turbo_context(request: Request) -> TurboContext:
    """FastAPI dependency that returns a :class:`TurboContext` for the request.

    Use as::

        from typing import Annotated
        from fastapi import Depends
        from fastapi_turbo import TurboContext, turbo_context

        @app.post("/items")
        async def create(turbo: Annotated[TurboContext, Depends(turbo_context)]):
            if turbo.accepts_stream:
                ...
    """
    frame_request_id = request.headers.get("turbo-frame")
    return TurboContext(
        accepts_stream=accepts_turbo_stream(request),
        frame_request_id=frame_request_id,
        is_frame_request=frame_request_id is not None,
    )
