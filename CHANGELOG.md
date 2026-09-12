# CHANGELOG

## Unreleased — v0.1.0

Initial release of `fastapi-turbo`, a rename and refocus of
[fastapi-hotwire](https://github.com/socialpyre/fastapi-hotwire) v0.3.0.

- Renamed: package `fastapi_hotwire` → `fastapi_turbo`, `HotwireTemplates` → `TurboTemplates`.
- Removed: Jinja block rendering (`blocks.py`, `BlockRenderer`, `render_block*`).
  Fragments are whole template files; see the README for the `jinja2-fragments`
  recipe if you prefer blocks.
- Changed: `render_stream(...)` and the new `render_fragment(...)` /
  `render_string(...)` render template files; `forms.validation_error_stream`
  lost its `block=` parameter.
- Added: `streams.stream(action, ...)` — a permissive generic entry point:
  any action (including custom client-side `Turbo.StreamActions`),
  `remove`/`refresh` silently ignore content, all other actions always carry
  a `<template>`. Named builders encode built-in requirements in their
  signatures; `replace`/`update` accept `method="morph"`.
- Added: `turbo_script()` template helper (auto-registered Jinja global) that
  loads Turbo and exposes `window.Turbo`.
- Added: `accepts_turbo_stream(request)` and `TURBO_STREAM_MEDIA_TYPE` public
  exports.
- Changed: `TurboContext.accepts_stream` uses real Accept-header parsing
  (explicit media type with non-zero q) instead of a substring check —
  `Accept: */*` no longer counts, `;q=0` is honored.
- Added: cache correctness for header-varied responses — `TurboStreamResponse`
  sets `Vary: Accept`, `render_fragment` sets `Vary: Turbo-Frame`, and the
  merging `append_vary(headers, value)` helper is exported.
- Removed: `TurboContext.is_visit` (previously derived from
  `Sec-Fetch-Mode`) and the session-backed `flash` module (`flash`,
  `get_flashed`, `FlashMessage`, the automatic `flashes` context
  processor, `examples/flash`). `TurboTemplates` no longer touches
  `request.session`; apps needing flash messaging own that plumbing.
