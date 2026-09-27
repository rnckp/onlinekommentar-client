# Notes

- `GET /api/commentaries/{id}` may return a single-resource payload wrapped as `{"data": {...}}`; `Commentary.from_json()` intentionally accepts both wrapped detail responses and direct commentary dictionaries.
- The distribution is named `onlinekommentar-client`, while its import package is `onlinekommentar`. The uv build backend needs an explicit `module-name` for the `src/onlinekommentar` layout. Tests deliberately avoid `pythonpath` overrides. If an editable install is stale, use `uv sync --reinstall-package onlinekommentar-client`.
- Pydantic hides input values in formatted validation errors, but structured `ValidationError.errors()` output can still contain inputs. Avoid logging raw error details or API payloads. Model lists and `raw` dictionaries remain mutable despite frozen model fields. See [README.md](README.md) for the public model contract.
- `quote(..., safe="")` does not escape dot segments. Empty, `.` and `..` commentary IDs must be rejected before HTTPX normalizes the request path. Base URLs must also reject query/fragment components to keep endpoint concatenation valid.
- This repository is a synchronous client library. Application-level Docker, logging configuration, health endpoints, and telemetry are intentionally left to consuming applications.
- OAI list helpers use `metadata_prefix=None` to distinguish omission from an explicit format. This lets initial requests default to `oai_dc` while continuation requests reject explicit formats. Preserve this distinction when changing the signatures; see the token rules in [README.md](README.md).
