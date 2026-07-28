# fastapi-turbo

[![PyPI](https://img.shields.io/pypi/v/fastapi-turbo?cacheSeconds=300)](https://pypi.org/project/fastapi-turbo/)
[![Python](https://img.shields.io/pypi/pyversions/fastapi-turbo?cacheSeconds=300)](https://pypi.org/project/fastapi-turbo/)
[![CI](https://github.com/bhtabor/fastapi-turbo/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bhtabor/fastapi-turbo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/fastapi-turbo?cacheSeconds=300)](LICENSE)

`fastapi-turbo` brings [Hotwire Turbo](https://turbo.hotwired.dev/) to FastAPI. Render targeted DOM updates with `<turbo-stream>` responses, serve partials for `<turbo-frame>` requests, and validate forms in place — all from your existing FastAPI handlers, with no JSON layer or client-side framework. Ships with pytest helpers and a `Protocol`-based design so you can swap template engines or session backends.

Inspired by [fastapi-hotwire](https://github.com/socialpyre/fastapi-hotwire).

## Install

```bash
pip install fastapi-turbo
# or
uv add fastapi-turbo
```

For the Pydantic-backed validation-error stream:

```bash
pip install "fastapi-turbo[forms]"
```

## Quickstart

```python
from fastapi import FastAPI, Form, Request
from fastapi_turbo import TurboStreamResponse, TurboTemplates, streams

app = FastAPI()
templates = TurboTemplates(directory="templates")
todos: list[dict] = []


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"todos": todos})


@app.post("/todos")
def create(request: Request, text: str = Form(...)):
    todo = {"id": len(todos) + 1, "text": text}
    todos.append(todo)
    return templates.render_stream(
        request,
        "_todo_row.html",
        action="append",
        target="todos",
        todo=todo,
    )


@app.post("/todos/{todo_id}/delete")
def delete(todo_id: int):
    todos[:] = [t for t in todos if t["id"] != todo_id]
    return TurboStreamResponse(streams.remove(target=f"todo-{todo_id}"))
```

`_todo_row.html` is an ordinary partial template, `{% include %}`-ed by the page and rendered alone for streams. A complete runnable version lives in [`examples/minimal/`](examples/minimal).

## What\'s in the box

| Module | What it does |
| --- | --- |
| [`TurboStreamResponse`](#turbostreamresponse) | A `Response` subclass with `Content-Type: text/vnd.turbo-stream.html`. |
| [`streams`](#streams) | Builders for `<turbo-stream>` actions — the eight built-ins, `method="morph"`, and custom actions via `streams.stream(...)`. |
| [`TurboContext`](#turbocontext) | A FastAPI dependency that summarizes how the current request relates to Turbo (frame request? stream-capable?), plus `accepts_turbo_stream(request)` for imperative checks. |
| [`TurboTemplates`](#turbotemplates) | A `Jinja2Templates` wrapper that adds `render_fragment(...)` and `render_stream(...)`, plus an automatic `turbo_script` template global. |
| [`turbo_script`](#turbo_script) | One line in `<head>` loads Turbo from the CDN (or your own URL) and exposes `window.Turbo`. |
| [`forms`](#forms) | A Pydantic `ValidationError` → turbo-stream renderer for in-place form validation. |
| [`testing`](#testing) | pytest assertions and request helpers (`assert_turbo_stream`, `parse_streams`, `assert_turbo_frame`, `turbo_frame_request`, `turbo_stream_request`). |

## TurboStreamResponse

```python
from fastapi_turbo import TurboStreamResponse, streams


@app.post("/items")
def create():
    return TurboStreamResponse(
        [
            streams.append(item_html, target="items"),
            streams.update(counter_html, target="item-count"),
        ]
    )
```

Pass a single string, a list of strings, or `None`. The class also works as `response_class=TurboStreamResponse` so OpenAPI documents the media type.

## streams

Each builder returns a `markupsafe.Markup` so it composes safely with Jinja templates:

```python
from fastapi_turbo import streams

streams.append("<li>...</li>", target="items")
streams.replace(form_html, target="contact-form", method="morph")  # Turbo 8 morphing
streams.remove(target="item-42")
streams.refresh(request_id=request.headers.get("x-turbo-request-id"))
```

The named builders encode each action's requirements in their signatures (`remove` takes no content, `refresh` takes neither content nor selector), while the generic `streams.stream(action, ...)` is permissive and works for **custom actions** too:

```python
streams.stream("highlight", target="item-7")
# <turbo-stream action="highlight" target="item-7"><template></template></turbo-stream>
# pairs with:
#   Turbo.StreamActions.highlight = function () {
#     this.targetElements.forEach((el) => el.classList.add("highlight"));
#   };
```

The `html` argument is interpolated **verbatim** into the `<template>` envelope. It must be safe HTML (Jinja autoescaped output is safe). Attribute values (`action=`, `target=`, `targets=`, `method=`, `request-id=`) are HTML-escaped automatically.

## TurboContext

```python
from typing import Annotated
from fastapi import Depends
from fastapi_turbo import TurboContext, turbo_context


@app.post("/items")
async def create(turbo: Annotated[TurboContext, Depends(turbo_context)]):
    if turbo.is_frame_request:
        return frame_response(...)
    if turbo.accepts_stream:
        return stream_response(...)
    return full_page_response(...)
```

Fields: `is_frame_request`, `frame_request_id`, `accepts_stream`.

`accepts_stream` is capability detection with real Accept-header parsing: it's true only when the client *explicitly* lists `text/vnd.turbo-stream.html` with a non-zero q-value. `Accept: */*` API clients stay on the HTML path, and `;q=0` is honored as an opt-out. The standalone `accepts_turbo_stream(request)` function exposes the same check for imperative use.

## TurboTemplates

```python
from fastapi_turbo import TurboTemplates

templates = TurboTemplates(directory="templates")


@app.get("/items/{id}")
def item_frame(request: Request, id: int):
    # Render a partial that carries the matching <turbo-frame> — useful
    # for responding to a <turbo-frame src="..."> request.
    return templates.render_fragment(request, "partials/item.html", item=load(id))


@app.post("/items")
def create(request: Request, text: str = Form(...)):
    item = save(text)
    # Render a partial as a turbo-stream that appends to #items.
    return templates.render_stream(
        request,
        "partials/item.html",
        action="append",
        target="items",
        item=item,
    )
```

## turbo_script

```html
<head>
  {{ turbo_script() }}
</head>
```

Renders a `<script type="module">` that imports Turbo (pinned to the version this library is tested against) and exposes `window.Turbo` for custom stream-action registrations. `TurboTemplates` registers it as a Jinja global automatically; pass `version=` to pin differently or `url=` to load a self-hosted/vendored build:

```python
turbo_script(version="8.0.23")
turbo_script(url="/static/vendor/turbo.js")
```

### Fragments: files, not blocks

`fastapi-turbo` renders whole template files; how you carve fragments out of your pages is your business. Partial files are the recommended default — they can be shared between full-page `{% include %}`s and stream/frame responses. If you prefer keeping fragments inside one page template with `{% block %}`, render the block to a string with [jinja2-fragments](https://github.com/sponsfreixes/jinja2-fragments) and hand it to the stream builders:

```python
from jinja2_fragments import render_block

html = render_block(templates.env, "items.html", "item_row", item=item)
return TurboStreamResponse(streams.append(html, target="items"))
```

(Heads-up: `jinja2-fragments` passes context as `**kwargs`, so context keys that collide with its positional parameter names — e.g. `environment` — need renaming.)

## forms

```python
from fastapi_turbo.forms import validation_error_stream

# Render Pydantic validation errors as a turbo-stream that replaces
# only the form\'s partial — no full-page reload, no scroll loss.
try:
    Contact.model_validate(form_data)
except ValidationError as exc:
    return validation_error_stream(
        exc,
        templates=templates,
        template="partials/contact_form.html",
        target="contact-form",
        request=request,
    )
```

## testing

```python
from fastapi_turbo.testing import (
    assert_turbo_stream,
    parse_streams,
    assert_turbo_frame,
    turbo_frame_request,
    turbo_stream_request,
)


def test_create_appends_a_row(client):
    resp = client.post("/todos", data={"text": "ship"})
    assert_turbo_stream(resp)
    actions = parse_streams(resp)
    assert actions[0].action == "append"
    assert actions[0].target == "todos"
```

## Pluggability

`fastapi_turbo.protocols` defines the integration seams:

- `TemplateRenderer` — anything implementing `render(name, context) -> str`.
- `SessionLike` — any `MutableMapping[str, Any]` that hangs off `request.session` (Starlette `SessionMiddleware`, `starsessions`, an in-memory `dict`).

You don\'t need to use the bundled Jinja2 / Starlette code paths to use this library.

## Examples

A full runnable example lives under [`examples/`](examples):

- [`examples/minimal/`](examples/minimal) — A todo list with turbo-stream append + remove. The simplest possible integration.

The example's own README has the exact `uv run --with ...` command — the packages needed beyond `fastapi-turbo` itself (an ASGI server, `python-multipart` for form parsing, etc.).

## Roadmap

- Turbo Stream broadcasts over SSE — signed stream topics, a pluggable broker, and the Turbo 8 `refresh` + `request-id` dedup pattern.

## Non-goals

`fastapi-turbo` deliberately does **not**:

- Bundle a Stimulus JavaScript distribution — load Stimulus the way you load any other JS.
- Dictate your fragment strategy — partial files, Jinja blocks, or hand-built strings all feed the same stream builders.
- Inject logging / observability / tracing — those are application concerns, not library concerns.
- Replace `request.url_for(...)` with anything more magical.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome — please file an issue first for anything bigger than a typo so we can align on scope.

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md) Code of Conduct.

## License

[MIT](LICENSE) `fastapi-turbo` began as a rename-and-refocus of [fastapi-hotwire](https://github.com/socialpyre/fastapi-hotwire).
