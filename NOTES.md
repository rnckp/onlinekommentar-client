# Implementation notes

Durable decisions, constraints, and historical observations. Public usage is in
the [client guide](docs/client-guide.md); open work is in [PLAN.md](PLAN.md).

- Required CI covers Python 3.12–3.14. A local Python 3.15 smoke test passed on macOS arm64 on 2026-10-14, but the locked `pydantic-core` needed a source build. Keep 3.15 outside required CI until eligible wheels make setup fast and reproducible; a local pass does not establish Linux compatibility.

- `GET /api/commentaries/{id}` may return a single-resource payload wrapped as `{"data": {...}}`; `Commentary.from_json()` intentionally accepts both wrapped detail responses and direct commentary dictionaries.
- The distribution is named `onlinekommentar-client`, while its import package is `onlinekommentar`. The uv build backend needs an explicit `module-name` for the `src/onlinekommentar` layout. Tests deliberately avoid `pythonpath` overrides. If an editable install is stale, use `uv sync --reinstall-package onlinekommentar-client`.
- Pydantic hides input values in formatted validation errors, but structured `ValidationError.errors()` output can still contain inputs. Avoid logging raw error details or API payloads. Model lists and `raw` dictionaries remain mutable despite frozen model fields. See [the client guide](docs/client-guide.md#response-models) for the public model contract.
- `quote(..., safe="")` does not escape dot segments. Empty, `.` and `..` commentary IDs must be rejected before HTTPX normalizes the request path. Base URLs must also reject query/fragment components to keep endpoint concatenation valid.
- This repository is a synchronous client library. Application-level Docker, logging configuration, health endpoints, and telemetry are intentionally left to consuming applications.
- OAI list helpers use `metadata_prefix=None` to distinguish omission from an explicit format. This lets initial requests default to `oai_dc` while continuation requests reject explicit formats. Preserve this distinction when changing the signatures; see the token rules in [the client guide](docs/client-guide.md#oai-pmh).
- The notebook tests require empty saved outputs and unset execution counts before running tutorial cells. The notebook cleanup hook is currently disabled; use the manual cleanup command in [CONTRIBUTING.md](CONTRIBUTING.md#examples). Preserve these assertions to keep live response data out of Git.
- `discover_config=False` disables only implicit working-directory discovery. Explicit config paths still load and validate before constructor overrides. Client tests run from temporary working directories so repository/user config cannot affect their defaults.
- CI pins uv 0.13.0 and builds with `--force-pep517` to use the declared uv_build backend range. Keep this flag when upgrading the CLI, whose bundled build backend may fall outside that range.

## Historical upstream observations

The previous review recorded the following observations on 2026-10-13. Responses
were not retained, so the repository cannot independently substantiate these
results or establish current service availability. Tests use synthetic responses.

- The [official API documentation](https://onlinekommentar.ch/en/apis) was reported
  to list the two implemented JSON routes, five list filters and six OAI-PMH verbs.
  Bounded checks reportedly validated JSON pages 1 and 2, combined filters and a
  wrapped detail response against the client models.
- Identify, ListMetadataFormats and ListSets reportedly succeeded. The advertised
  `oai_dc` and `oai_openaire` formats worked for initial ListRecords, one continuation
  page and GetRecord. A date/set-filtered ListRecords request returned `noRecordsMatch`.
- ListIdentifiers with `metadataPrefix=oai_dc` reportedly returned HTTP 500 with
  both JSON and XML Accept headers. The earlier `badResumptionToken` concern was
  not reproduced with fresh ListRecords tokens.

Complete harvesting and every filter combination remain unverified. Follow-up
checks are tracked in [PLAN.md](PLAN.md).

## 2026-10-26: eMudhra/emSign certificate update

Require certifi >=2026.10.19; only certifi and affected pip changed package versions. Keep the seven-day cooldown. Remove only the incident certifi exception after 2026-10-27 03:24:17 Europe/Zurich, then relock and sync. Build/CI uv pins are 0.13.5; Python image stages patch existing pip with secure uv. Deployment images still require a fresh build (`--pull --no-cache`) and verification before redeployment. Advisory: https://discuss.python.org/t/109576.
