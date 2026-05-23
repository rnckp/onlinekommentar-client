# Notes

- The public API docs at `https://onlinekommentar.ch/en/apis` document example ID `40eb831a-088b-4b27-9fe2-31f049c790a5`, but a live `GET /api/commentaries/{id}` check on 2026-05-23 returned 404. Tests use mocked API responses, and the example notebook fetches a commentary ID from a live search result before calling `get_commentary()`.
- `GET /api/commentaries/{id}` may return a single-resource payload wrapped as `{"data": {...}}`; `Commentary.from_json()` intentionally accepts both wrapped detail responses and direct commentary dictionaries.
- If `.venv/bin/python` cannot import `onlinekommentar` while `uv run python` from the repo root can, the editable install may be stale from an earlier `uv sync` run before the package directory existed. `uv sync --reinstall-package onlinekommentar` regenerates the editable finder with the correct package mapping.
- OAI-PMH resumption token requests must be sent with only `verb` and `resumptionToken`; the client intentionally omits `metadataPrefix`, date filters, and set filters when helper methods continue paginated harvests.
- Config validation rejects hostless base URLs and non-finite numeric values so invalid URLs, `nan` timeouts, and infinite rate limits fail before request execution.
