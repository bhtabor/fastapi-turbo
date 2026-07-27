"""fastapi-turbo — Hotwire Turbo integration for FastAPI.

Public API:

- :class:`TurboStreamResponse` — ``Response`` with the Turbo Stream media type.
- :mod:`streams` — pure-function builders for ``<turbo-stream>`` actions.
- :class:`TurboContext` + :func:`turbo_context` — request-shape dependency
  (:func:`accepts_turbo_stream` for imperative checks).
- :class:`TurboTemplates` — ``Jinja2Templates`` with fragment + stream helpers.
- :func:`turbo_script` — one-line ``<head>`` tag that loads Turbo.
- :mod:`forms` — Pydantic validation-error → Turbo Stream helper.
- :mod:`testing` — pytest assertions and request helpers for Turbo endpoints.

Inspired by `fastapi-hotwire <https://github.com/socialpyre/fastapi-hotwire>`_.
"""

from __future__ import annotations

from . import forms, streams, testing
from .deps import TurboContext, accepts_turbo_stream, turbo_context
from .protocols import SessionLike, TemplateRenderer
from .responses import TURBO_STREAM_MEDIA_TYPE, TurboStreamResponse, append_vary
from .script import DEFAULT_TURBO_VERSION, turbo_script
from .templates import TurboTemplates

__all__ = [
    "DEFAULT_TURBO_VERSION",
    "TURBO_STREAM_MEDIA_TYPE",
    "SessionLike",
    "TemplateRenderer",
    "TurboContext",
    "TurboStreamResponse",
    "TurboTemplates",
    "accepts_turbo_stream",
    "append_vary",
    "forms",
    "streams",
    "testing",
    "turbo_context",
    "turbo_script",
]
