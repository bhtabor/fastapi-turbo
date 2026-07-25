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
