"""Tests for ``fastapi_turbo.streams``."""

from __future__ import annotations

import pytest
from markupsafe import Markup

from fastapi_turbo import streams


@pytest.mark.parametrize(
    ("action", "fn"),
    [
        ("append", streams.append),
        ("prepend", streams.prepend),
        ("replace", streams.replace),
        ("update", streams.update),
        ("before", streams.before),
        ("after", streams.after),
    ],
)
def test_content_action_with_target(action, fn):
    out = fn("<p>hi</p>", target="messages")
    assert isinstance(out, Markup)
    expected = (
        f'<turbo-stream action="{action}" target="messages">'
        f"<template><p>hi</p></template>"
        f"</turbo-stream>"
    )
    assert out == expected


@pytest.mark.parametrize(
    ("action", "fn"),
    [
        ("append", streams.append),
        ("prepend", streams.prepend),
        ("replace", streams.replace),
        ("update", streams.update),
        ("before", streams.before),
        ("after", streams.after),
    ],
)
def test_content_action_with_targets(action, fn):
    out = fn("<p>hi</p>", targets=".message")
    expected = (
        f'<turbo-stream action="{action}" targets=".message">'
        f"<template><p>hi</p></template>"
        f"</turbo-stream>"
    )
    assert out == expected


def test_remove_action_has_no_template():
    out = streams.remove(target="msg-1")
    assert out == '<turbo-stream action="remove" target="msg-1"></turbo-stream>'


def test_remove_with_targets():
    out = streams.remove(targets=".dismissed")
    assert out == '<turbo-stream action="remove" targets=".dismissed"></turbo-stream>'


def test_refresh_without_request_id():
    assert streams.refresh() == '<turbo-stream action="refresh"></turbo-stream>'


def test_refresh_with_request_id():
    assert (
        streams.refresh(request_id="abc-123")
        == '<turbo-stream action="refresh" request-id="abc-123"></turbo-stream>'
    )


def test_target_and_targets_together_raises():
    with pytest.raises(ValueError, match="either target= or targets="):
        streams.append("x", target="a", targets=".b")


def test_neither_target_nor_targets_raises():
    with pytest.raises(ValueError, match="requires target= or targets="):
        streams.append("x")


def test_remove_neither_target_nor_targets_raises():
    with pytest.raises(ValueError):
        streams.remove()


def test_target_attribute_is_html_escaped():
    out = streams.append("<p/>", target='evil"x')
    # Quote inside target gets escaped so the attribute isn't broken out of.
    assert 'target="evil&#34;x"' in out


def test_content_is_not_escaped():
    raw = '<div data-foo="bar\'s">x & y</div>'
    out = streams.append(raw, target="t")
    assert raw in out


# ---------------------------------------------------------------------------
# stream() — the permissive generic entry point
# ---------------------------------------------------------------------------


def test_named_builders_encode_requirements_in_signatures():
    """Requirements live in signatures: refresh takes no selector or
    content parameters at all; remove takes no content."""
    with pytest.raises(TypeError):
        streams.refresh(target="items")  # ty: ignore[unknown-argument]
    with pytest.raises(TypeError):
        streams.remove("<p>hi</p>", target="row-1")  # ty: ignore[too-many-positional-arguments]


def test_builders_require_a_selector():
    with pytest.raises(ValueError, match="requires target"):
        streams.append("<p>hi</p>")
    with pytest.raises(ValueError, match="requires target"):
        streams.remove()


def test_generic_stream_ignores_html_for_remove_and_refresh():
    """Content passed to remove/refresh is silently dropped."""
    out = streams.stream("remove", target="row-1", html="<p>ignored</p>")
    assert out == '<turbo-stream action="remove" target="row-1"></turbo-stream>'
    out = streams.stream("refresh", html="<p>ignored</p>")
    assert out == '<turbo-stream action="refresh"></turbo-stream>'


def test_generic_stream_is_permissive_about_attribute_combinations():
    """No per-action rules on the generic path — method/request-id pass
    through for any action."""
    out = streams.stream("append", target="items", html="x", method="morph", request_id="r1")
    assert 'method="morph"' in out
    assert 'request-id="r1"' in out


def test_replace_and_update_accept_morph():
    out = streams.replace("<p>hi</p>", target="card", method="morph")
    assert 'action="replace" target="card" method="morph"' in out
    out = streams.update("<p>hi</p>", target="card", method="morph")
    assert 'method="morph"' in out


def test_refresh_renders_without_template():
    assert streams.refresh() == '<turbo-stream action="refresh"></turbo-stream>'
    out = streams.refresh(request_id="req-1")
    assert out == '<turbo-stream action="refresh" request-id="req-1"></turbo-stream>'


def test_custom_action_bare_carries_empty_template():
    """Non-remove/refresh actions always carry a <template>, even empty."""
    out = streams.stream("confetti", target="stage")
    assert (
        out == '<turbo-stream action="confetti" target="stage"><template></template></turbo-stream>'
    )


def test_custom_action_accepts_any_arguments():
    out = streams.stream("log", target="console", html="hello", request_id="r1")
    assert 'action="log"' in out
    assert 'target="console"' in out
    assert 'request-id="r1"' in out
    assert "<template>hello</template>" in out


def test_custom_action_name_is_escaped():
    out = streams.stream('x"><script>')
    assert "<script>" not in out.split(">", 1)[0]
    assert "&#34;" in out or "&quot;" in out


def test_stream_rejects_both_target_and_targets():
    with pytest.raises(ValueError, match="not both"):
        streams.stream("shake", target="a", targets=".b")
