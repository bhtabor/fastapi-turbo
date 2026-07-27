# Minimal example

A todo list with turbo-stream append + remove — the simplest possible `fastapi-turbo` integration.

## Run

```bash
cd examples/minimal
uv run --with uvicorn --with python-multipart uvicorn app:app --reload
```

Then open http://127.0.0.1:8000.

## What it shows

- `templates.render_stream(...)` to append a new row without a full-page reload.
- `TurboStreamResponse(streams.remove(target=...))` to remove a row by id.
- `_todo_row.html` is a standalone partial, `{% include %}`-ed as the page-level loop body and rendered directly as the stream's content — the same file, no template-level fragment syntax.
