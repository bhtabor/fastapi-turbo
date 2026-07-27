"""The ``turbo_script()`` template helper.

One line in your layout's ``<head>`` loads Turbo::

    {{ turbo_script() }}

:class:`~fastapi_turbo.templates.TurboTemplates` registers it as a
Jinja global automatically; it's also importable for use with a plain
``Jinja2Templates`` (``templates.env.globals["turbo_script"] = turbo_script``).
"""

from __future__ import annotations

from markupsafe import Markup, escape

__all__ = ["DEFAULT_TURBO_VERSION", "turbo_script"]

# The Turbo release this library is developed and tested against.
DEFAULT_TURBO_VERSION = "8.0.23"

_CDN_URL = "https://cdn.jsdelivr.net/npm/@hotwired/turbo@{version}/dist/turbo.es2017-esm.js"


def turbo_script(version: str = DEFAULT_TURBO_VERSION, url: str | None = None) -> Markup:
    """A ``<script type="module">`` tag that loads Turbo and exposes ``window.Turbo``.

    ``window.Turbo`` is set so application scripts can register custom
    stream actions (``Turbo.StreamActions.x = …``) or call
    ``Turbo.visit(...)`` without importing the module themselves.

    Carries ``data-turbo-track="reload"`` unconditionally: if the pinned
    version or a self-hosted ``url`` ever changes, a page navigated to
    via Turbo Drive must reload fully rather than keep running a stale
    Turbo runtime after a body-only swap.

    :param version: the Turbo version to load from the default CDN.
    :param url: full script URL override (self-hosted or vendored
        build); when given, ``version`` is ignored.
    """
    src = url if url is not None else _CDN_URL.format(version=version)
    return Markup(
        f'<script type="module" data-turbo-track="reload">'
        f'import * as Turbo from "{escape(src)}"; window.Turbo = Turbo;'
        f"</script>"
    )
