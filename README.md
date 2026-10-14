# Onlinekommentar Python Client

**Python client for accessing the public [Onlinekommentar](https://onlinekommentar.ch) APIs more easily.**

This project is not official, associated with, or affiliated with Onlinekommentar. It was developed independently as a convenience wrapper around the publicly documented Onlinekommentar APIs.

**Note:** The official [Onlinekommentar website](https://onlinekommentar.ch) and [API documentation](https://onlinekommentar.ch/en/apis) are the actual and authoritative reference for the APIs.

## Installation

Requires Python 3.13 or newer and `uv`. From the repository root, install the
package and declared development dependencies:

```bash
uv sync
```

## Quick Start

For a complete runnable walkthrough, see [examples/onlinekommentar_demo.ipynb](examples/onlinekommentar_demo.ipynb).
It covers configuration, every JSON filter and raw/typed response method, bounded pagination,
all six OAI-PMH verbs, `oai_dc` and `oai_openaire` examples, continuation tokens,
error handling, and an offline HTTPX transport. Run cells in order; API cells make live requests and discover IDs from responses.
Automated tests execute the notebook with synthetic responses, including upstream failure cases.

```python
from onlinekommentar import OnlinekommentarClient

with OnlinekommentarClient() as client:
    # List published commentaries, newest first
    results = client.list_commentaries(language="en", sort="-date", page=1)

    for commentary in results.commentaries[:5]:
        print(commentary.title, commentary.html_link)

    # Search commentaries
    search_results = client.list_commentaries(
        language="de",
        search="universalversammlung",
    )

    # Fetch a specific commentary by API ID
    if search_results.commentaries:
        commentary = client.get_commentary(search_results.commentaries[0].commentary_id)
        print(commentary.title)

    # Access OAI-PMH metadata as XML
    identify_xml = client.identify()
    print(identify_xml[:200])
```

## API Reference

### Commentaries

The following snippets assume an open `client` inside a context manager as above.
Replace placeholder IDs and tokens with values from API responses.

```python
results = client.list_commentaries(
    language="en",  # "en", "de", "fr", "it"; defaults to configured language
    search="data protection",
    legislative_act="act-id-from-response",
    sort="-date",  # "title", "-title", "date", "-date"
    page=1,
    request_timeout=60.0,  # optional per-call timeout
)

commentary = client.get_commentary("commentary-id-from-response")
```

`list_commentaries()` returns a `CommentarySearchResult` with parsed `Commentary`
items. `get_commentary()` returns a single `Commentary`. Each list call fetches one page;
pagination is caller-managed. Omitted `sort` and `page` values are not sent, leaving
defaults to the server. List methods do not validate filter values; an omitted or
empty `language` uses the configured default.

Raw JSON helpers are available when you need fields that are not modeled yet:

```python
raw_page = client.list_commentaries_raw(language="de", search="Datenschutz")
raw_commentary = client.get_commentary_raw("commentary-id-from-response")
```

For bounded pagination, `iter_commentaries()` retains the filters and defaults to
at most ten pages. Set an explicit cap for larger traversals. It increments page
numbers on the configured server rather than following URLs supplied in responses.
Iteration stops when `next_page_url` is absent or empty.
If more pages remain at the cap, it raises `PaginationLimitError`; any items already
yielded are incomplete results. HTTP and validation failures also stop iteration.

```python
from onlinekommentar import PaginationLimitError

try:
    for commentary in client.iter_commentaries(language="de", max_pages=20):
        print(commentary.title)
except PaginationLimitError:
    print("Page limit reached; results are incomplete.")
```

### OAI-PMH

The OAI-PMH helpers return response text without parsing it automatically.
Requests use an XML Accept header.

```python
identify = client.identify()
formats = client.list_metadata_formats()
sets = client.list_sets()

identifiers = client.list_identifiers(
    metadata_prefix="oai_dc",
    from_date="2026-01-01",
    set_spec="set-spec-from-ListSets",
)

records = client.list_records(metadata_prefix="oai_openaire")

# Continue with the token returned in the XML; do not repeat the format or filters.
next_records = client.list_records(resumption_token="token-from-previous-response")

record = client.get_record(
    identifier="identifier-from-OAI-header",
    metadata_prefix="oai_dc",
)
```

For explicit protocol calls, use the generic helper. It accepts `request_timeout`,
as do the named helpers:

```python
xml = client.oai(
    verb="ListRecords",
    resumption_token="token-from-previous-response",
)
```

`get_record()`, `list_records()` and `list_identifiers()` default to `oai_dc` for initial requests.
Passing a resumption token together with an explicit metadata prefix or filters
raises `ValueError`, following the
[OAI-PMH exclusive-argument rules](https://www.openarchives.org/OAI/openarchivesprotocol.html#ProtocolMessages).

Use the optional parser to validate XML and detect protocol errors even when the
HTTP status is 200. Error messages contain standard codes rather than server text.
The parser rejects malformed XML, DTD/entity declarations and unexpected XML roots;
it does not validate the complete OAI-PMH schema or metadata contents.

```python
from onlinekommentar import OAIProtocolError, parse_oai_response

try:
    root = parse_oai_response(client.list_records(request_timeout=60.0))
except OAIProtocolError as error:
    print(error.codes)
```

If identifier listing fails, callers can explicitly read identifiers from
`ListRecords` headers. The client propagates failures without silently changing
the requested verb. Historical upstream observations and their verification limits
are recorded in [NOTES.md](NOTES.md).

### Configuration

Settings are loaded from `config.yaml` in the working directory, or from an explicit
`config_path`. The repository includes [config.yaml](config.yaml) with package
defaults; installed distributions use defaults unless the consuming application
provides a file. The file is validated before non-`None` constructor settings
override its values; overrides cannot repair an invalid file:

```yaml
onlinekommentar:
  base_url: "https://onlinekommentar.ch"
  timeout: 30.0
  rate_limit_delay: 0.2
  default_language: "en"
  max_retries: 0
  retry_backoff: 1.0
  max_retry_delay: 60.0
```

```python
with OnlinekommentarClient(timeout=10.0, rate_limit_delay=0.5, default_language="de") as client:
    results = client.list_commentaries()

# Ignore a consuming application's unrelated working-directory config.yaml.
with OnlinekommentarClient(discover_config=False) as client:
    results = client.list_commentaries()
```

`discover_config=False` disables implicit lookup only; an explicit `config_path`
still loads that file.

Settings may be at the YAML root or under `onlinekommentar`; when that section is
present, other root sections are ignored. Missing files use defaults. Existing files
must contain a mapping (`{}` is valid); empty files, unknown client settings, and
invalid values are rejected. Base URLs may include a path prefix, but cannot contain
credentials, queries, or fragments. `timeout` must be finite and positive;
`rate_limit_delay` must be finite and nonnegative. Durations are in seconds.

Every request method accepts a keyword-only `request_timeout`, validated with the
same finite, positive, non-boolean constraints as the constructor timeout. This is
an HTTPX timeout for connect/read/write/pool operations, not a total deadline for a
call or harvest. The iterator applies it separately to each page request.

Retries are disabled by default. Opt in with `max_retries` (0–10). Transient
transport errors and HTTP 429/502/503/504 use exponential backoff, starting at
`retry_backoff` and capped at `max_retry_delay`. HTTP 500 and XML protocol errors
are not retried. A valid `Retry-After` seconds value or HTTP date takes precedence
when longer; if it exceeds the configured delay budget, the HTTP error propagates
instead of retrying early. Rate limiting also applies to retry attempts.

```python
with OnlinekommentarClient(max_retries=2, retry_backoff=1.0, max_retry_delay=30.0) as client:
    results = client.list_commentaries()
```

### Typed Models

```python
from onlinekommentar import (
    Commentary,
    CommentarySearchResult,
    LegislativeAct,
    Person,
)
```

The response models expose selected fields and preserve unknown fields in each
model's `raw` attribute. Raw JSON helpers return the decoded JSON object without
model validation.

Models and configuration are validated Pydantic models. Construct them with keyword
arguments; they are not dataclasses. API response models provide `from_json()` to
validate dictionaries. Invalid payloads raise `pydantic.ValidationError`
(a `ValueError` subclass), with structured field errors. Malformed collections and
pagination values are rejected rather than silently discarded or coerced. Integer
identifiers are accepted and normalized to strings; floats, booleans, bytes, and
blank identifiers are rejected. Required titles and names cannot be blank. Models
prevent field reassignment, but their lists and raw dictionaries remain mutable.

Use a separate client per thread: the synchronous rate limiter spaces request starts
on one client and is intended for sequential requests. Close it with a context
manager or `close()`.
HTTP failures and timeouts propagate as HTTPX exceptions. OAI-PMH responses remain raw
XML; use `parse_oai_response()` or inspect protocol-level `<error>` elements yourself.

## Scope

The client implements requests to these routes:

- `GET /api/commentaries`
- `GET /api/commentaries/{id}`
- `GET /oai` with OAI-PMH verbs `Identify`, `ListMetadataFormats`, `ListSets`, `ListIdentifiers`, `ListRecords`, and `GetRecord`

The client does not scrape website pages and does not cover private or undocumented routes.

Tests use synthetic HTTP responses; they do not establish current upstream API
availability or compatibility. Dated live checks and remaining upstream issues
are tracked in [NOTES.md](NOTES.md) and [PLAN.md](PLAN.md).

## Fair Use

This independent client accesses public Onlinekommentar endpoints.

> [!IMPORTANT]
> Please be kind to the server, keep rate limiting enabled for batch work, mention Onlinekommentar as the data source when appropriate, and avoid sending confidential or personal data to public endpoints. **Also consider contributing to [Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar).**

## Development

```bash
uv sync
uv run pre-commit install
uv run ruff format .
uv run ruff check .
uv run pytest -v
uv run pre-commit run --all-files
uv build --force-pep517
```

Local hooks run Ruff lint with safe fixes, then formatting, using the version in
`uv.lock`. Run `uv sync` first: hooks use `--no-sync` and do not install dependencies
while committing. Checks operate on staged filenames and include Python notebooks.
File hooks validate YAML/JSON, reject conflict markers, detect private keys, fix
whitespace, and reject newly added files larger than 1 MB. Add narrow exceptions
only for intentional assets. Gitleaks scans staged changes for credentials; its
first run installs a Go-based hook environment, which is reused afterward.
Review and stage any hook fixes before committing again.

The notebook hook clears saved outputs and execution counts; tests enforce that
committed notebooks remain clean. To clear an executed notebook manually, run
`uv run python scripts/clear_notebook_outputs.py examples/onlinekommentar_demo.ipynb`.
The cleanup command returns 1 when it changes files and 0 when no changes are
needed; review and stage the cleared notebook before committing.

The package lives in `src/onlinekommentar` and uses the `uv_build` backend. Tests
import the installed package; run `uv sync` after cloning or changing build metadata.
The build command uses the declared backend through PEP 517 even when the installed
uv CLI is newer than the backend's supported range.

CI runs on pull requests and pushes to `main`. `Quality` checks all tracked files,
runs offline tests on Python 3.13, and builds the distributions. `Python 3.14` runs
compatibility tests without repeating lint or hooks. Both checks are required on
`main`. Redundant CI runs are canceled; jobs have ten-minute timeouts and read-only
permissions. Gitleaks is skipped in CI because its staged-change hook cannot scan
PR history; GitHub secret scanning and push protection cover remote commits.
Local hooks remain useful for catching credentials before they reach GitHub.

Dependency auditing runs separately for dependency changes and weekly, and can
be triggered manually. It is not a required status check because its workflow is
filtered by paths. Review failures before merging dependency updates and respond
to scheduled findings. Dependabot monitors uv, GitHub Actions, and external hooks
weekly, groups routine updates, and applies a seven-day cooldown. Urgent security
fixes may need an explicit exception to uv's seven-day resolution cooldown.

GitHub defaults: PRs into `main`, one approval of the latest reviewable push,
resolved conversations, passing `Quality` and `Python 3.14`, blocked force pushes
and branch deletion, squash merges, and automatic deletion of merged branches.
Administrators can bypass requirements through a PR for exceptional cases; direct
pushes remain blocked. Keep deployment and publishing workflows out until a
release process is needed.
After pushing, verify that the two required checks are reported by hosted CI.

To run the same vulnerability check locally (contacts external package/advisory services):

```bash
uv audit --locked --preview-features audit-command
```

`client.py` handles synchronous HTTP requests and rate limiting, `config.py` loads
and validates settings, `models.py` validates JSON responses, and `oai.py` provides
optional XML validation. The package has
no CLI or application server. Design constraints are recorded in [NOTES.md](NOTES.md);
remaining infrastructure and upstream checks are in [PLAN.md](PLAN.md).

## License

This Python client is licensed under the MIT License.

The MIT License applies only to this client code. It does not apply to Onlinekommentar data, API content, or other source materials returned by the service. For data and content licensing details, consult [Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar) and the respective original data sources.
