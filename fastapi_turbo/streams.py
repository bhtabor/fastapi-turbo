"""Turbo Stream action builders.

Each named builder encodes its action's requirements in its
*signature* (content builders take ``html`` positionally; ``remove``
has no content parameter; ``refresh`` takes neither content nor
selector), while the generic :func:`stream` is permissive and imposes
no per-action rules.

Custom actions (client-side ``Turbo.StreamActions`` registrations) go
through :func:`stream` with any action name::

    stream("highlight", target="item-7")
    # <turbo-stream action="highlight" target="item-7"><template></template></turbo-stream>

``remove`` and ``refresh`` never carry a ``<template>`` (content
passed for them is silently ignored); every other action — including
custom ones — always carries one, even when empty.

Trust contract for the ``html`` argument
----------------------------------------

The ``html`` you pass is interpolated **verbatim** into the
``<template>`` envelope. The browser-side Turbo parser requires raw
markup, so callers own the safety of that string:

- Jinja2 output with autoescape on (the default in
  :class:`Jinja2Templates` and required by
  :class:`TurboTemplates`) is safe.
- Static, hand-written HTML is safe.
- A user-controlled string interpolated without escaping is **not**
  safe — ``streams.append(user_input, target="chat")`` is an XSS.

Attribute values (``action=``, ``target=``, ``targets=``,
``request-id=``, ``method=``) are escaped automatically.
"""

from __future__ import annotations

from markupsafe import Markup, escape

__all__ = [
    "TEMPLATELESS_ACTIONS",
    "after",
    "append",
    "before",
    "prepend",
    "refresh",
    "remove",
    "replace",
    "stream",
    "update",
]

# Actions that never carry a <template> element.
TEMPLATELESS_ACTIONS = ("remove", "refresh")


def stream(
    action: str,
    *,
    target: str | None = None,
    targets: str | None = None,
    html: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
) -> Markup:
    """Render one ``<turbo-stream>`` element for any action.

    The permissive core: any action name (built-in or custom), any
    combination of attributes — the named builders are the typed,
    self-documenting way to emit the built-ins. ``remove`` and
    ``refresh`` ignore ``html``; every other action gets a
    ``<template>`` element even when ``html`` is ``None``.
    """
    if target is not None and targets is not None:
        raise ValueError("pass either target= or targets=, not both")

    attrs = f'action="{escape(action)}"'
    if target is not None:
        attrs += f' target="{escape(target)}"'
    if targets is not None:
        attrs += f' targets="{escape(targets)}"'
    if method is not None:
        attrs += f' method="{escape(method)}"'
    if request_id is not None:
        attrs += f' request-id="{escape(request_id)}"'

    if action in TEMPLATELESS_ACTIONS:
        content = ""
    else:
        content = f"<template>{html if html is not None else ''}</template>"
    return Markup(f"<turbo-stream {attrs}>{content}</turbo-stream>")


def _require_selector(action: str, target: str | None, targets: str | None) -> None:
    if target is None and targets is None:
        raise ValueError(f"action={action!r} requires target= or targets=")


def after(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately after the targeted element(s)."""
    _require_selector("after", target, targets)
    return stream("after", target=target, targets=targets, html=html)


def append(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the last child of the targeted element(s)."""
    _require_selector("append", target, targets)
    return stream("append", target=target, targets=targets, html=html)


def before(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` immediately before the targeted element(s)."""
    _require_selector("before", target, targets)
    return stream("before", target=target, targets=targets, html=html)


def prepend(html: str, *, target: str | None = None, targets: str | None = None) -> Markup:
    """Insert ``html`` as the first child of the targeted element(s)."""
    _require_selector("prepend", target, targets)
    return stream("prepend", target=target, targets=targets, html=html)


def refresh(*, request_id: str | None = None) -> Markup:
    """Trigger a Turbo 8 page refresh, optionally tagged with ``request_id``.

    Turbo ignores refreshes whose ``request-id`` matches one of its own
    recent form submissions — pass the incoming ``X-Turbo-Request-ID``
    header through when broadcasting so the actor doesn't double-apply.
    """
    return stream("refresh", request_id=request_id)


def remove(*, target: str | None = None, targets: str | None = None) -> Markup:
    """Remove the targeted element(s)."""
    _require_selector("remove", target, targets)
    return stream("remove", target=target, targets=targets)


def replace(
    html: str,
    *,
    target: str | None = None,
    targets: str | None = None,
    method: str | None = None,
) -> Markup:
    """Replace the targeted element(s) — including the element itself — with ``html``.

    Pass ``method="morph"`` to have Turbo 8 morph the element instead of
    swapping it (preserves focus, scroll, and unchanged subtrees).
    """
    _require_selector("replace", target, targets)
    return stream("replace", target=target, targets=targets, html=html, method=method)


def update(
    html: str,
    *,
    target: str | None = None,
    targets: str | None = None,
    method: str | None = None,
) -> Markup:
    """Replace the *contents* of the targeted element(s) with ``html``.

    Pass ``method="morph"`` to have Turbo 8 morph the contents instead
    of swapping them.
    """
    _require_selector("update", target, targets)
    return stream("update", target=target, targets=targets, html=html, method=method)
