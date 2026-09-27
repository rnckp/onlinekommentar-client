# Notes

- The public API docs at `https://onlinekommentar.ch/en/apis` document example ID `40eb831a-088b-4b27-9fe2-31f049c790a5`, but a live `GET /api/commentaries/{id}` check on 2026-05-23 returned 404. Tests use mocked API responses, and the example notebook fetches a commentary ID from a live search result before calling `get_commentary()`.
- `GET /api/commentaries/{id}` may return a single-resource payload wrapped as `{"data": {...}}`; `Commentary.from_json()` intentionally accepts both wrapped detail responses and direct commentary dictionaries.
- The distribution is named `onlinekommentar-client`, while its import package is `onlinekommentar`. The uv build backend needs an explicit `module-name` for the `src/onlinekommentar` layout. Tests deliberately avoid `pythonpath` overrides. If an editable install is stale, use `uv sync --reinstall-package onlinekommentar-client`.
- OAI-PMH resumption token requests must be sent with only `verb` and `resumptionToken`; the client intentionally omits `metadataPrefix`, date filters, and set filters when helper methods continue paginated harvests.
- Config validation rejects hostless base URLs and non-finite numeric values so invalid URLs, `nan` timeouts, and infinite rate limits fail before request execution.
- API/config models use Pydantic with input values hidden in formatted validation errors. This changes positional/dataclass construction and error text; `from_json()`, field names, raw payload access, and numeric-ID normalization remain supported.
- `quote(..., safe="")` does not escape dot segments. Empty, `.` and `..` commentary IDs must be rejected before HTTPX normalizes the request path. Base URLs must also reject query/fragment components to keep endpoint concatenation valid.
- This repository is a synchronous client library. Application-level Docker, logging configuration, health endpoints, and telemetry are intentionally left to consuming applications.
