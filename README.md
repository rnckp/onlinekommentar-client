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
defaults to the server. List filters are forwarded without local value validation.

Raw JSON helpers are available when you need fields that are not modeled yet:

```python
raw_page = client.list_commentaries_raw(language="de", search="Datenschutz")
raw_commentary = client.get_commentary_raw("commentary-id-from-response")
```

### OAI-PMH

The public OAI-PMH endpoint returns XML. The client provides small helpers and returns the XML text unchanged.

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

For explicit protocol calls or a per-call timeout, use the generic helper:

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

### Configuration

Settings are loaded from `config.yaml` in the working directory, or from an explicit
`config_path`. No configuration file is shipped. Non-`None` constructor arguments
for the four settings below override file values, after the file has been validated.
The example shows the package defaults:

```yaml
onlinekommentar:
  base_url: "https://onlinekommentar.ch"
  timeout: 30.0
  rate_limit_delay: 0.2
  default_language: "en"
```

```python
with OnlinekommentarClient(timeout=10.0, rate_limit_delay=0.5, default_language="de") as client:
    results = client.list_commentaries()
```

Settings may be at the YAML root or under `onlinekommentar`; when that section is
present, other root sections are ignored. Missing files use defaults. Existing files
must contain a mapping (`{}` is valid); empty files, unknown client settings, and
invalid values are rejected. Base URLs may include a path prefix, but cannot contain
credentials, queries, or fragments. `timeout` must be finite and positive;
`rate_limit_delay` must be finite and nonnegative. Durations are in seconds.

`request_timeout` overrides the HTTPX timeout on `list_commentaries()`,
`list_commentaries_raw()` and `oai()` only. Detail methods and named OAI helpers use
the constructor timeout. This is an HTTPX timeout for connect/read/write/pool
operations, not a total deadline for a call or harvest.

### Typed Models

```python
from onlinekommentar import (
    Commentary,
    CommentarySearchResult,
    LegislativeAct,
    Person,
)
```

The client models stable high-use shapes and preserves unknown fields in each model's `raw` attribute. Raw JSON helpers are available for consumers that need exact API payloads.

Models and configuration are validated Pydantic models. Construct them with keyword
arguments; they are not dataclasses. API response models provide `from_json()` to
validate dictionaries. Invalid payloads raise `pydantic.ValidationError`
(a `ValueError` subclass), with structured field errors. Malformed collections and
pagination values are rejected rather than silently discarded or coerced. Integer
identifiers are accepted and normalized to strings. Models prevent field
reassignment, but their lists and raw dictionaries remain mutable.

Use a separate client per thread: the synchronous rate limiter spaces request starts
on one client and is intended for sequential requests. The client adds no automatic
retries or pagination. Close it with a context manager or `close()`.
HTTP failures and timeouts propagate as HTTPX exceptions. OAI-PMH responses remain raw
XML, so callers must inspect any protocol-level `<error>` elements themselves.

## Scope

The client implements requests to these routes:

- `GET /api/commentaries`
- `GET /api/commentaries/{id}`
- `GET /oai` with OAI-PMH verbs `Identify`, `ListMetadataFormats`, `ListSets`, `ListIdentifiers`, `ListRecords`, and `GetRecord`

The client does not scrape website pages and does not cover private or undocumented routes.

Tests use synthetic HTTP responses; they do not establish current upstream API
availability or compatibility. Historical upstream observations awaiting rechecking
are tracked in [PLAN.md](PLAN.md).

## Fair Use

This independent client accesses public Onlinekommentar endpoints.

> [!IMPORTANT]
> Please be kind to the server, keep rate limiting enabled for batch work, mention Onlinekommentar as the data source when appropriate, and avoid sending confidential or personal data to public endpoints. **Also consider contributing to [Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar).**

## Development

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest -v
uv build
```

The package lives in `src/onlinekommentar` and uses the `uv_build` backend. Tests
import the installed package; run `uv sync` after cloning or changing build metadata.
`pyproject.toml` declares Python >=3.13; there is no CI version matrix. Weekly uv
dependency updates are configured in `.github/dependabot.yml`, but successful
repository-side runs are not established by these files. No CI workflow is present.

`client.py` handles synchronous HTTP requests and rate limiting, `config.py` loads
and validates settings, and `models.py` validates JSON responses. The package has
no CLI or application server. Design constraints are recorded in [NOTES.md](NOTES.md);
remaining infrastructure and upstream checks are in [PLAN.md](PLAN.md).

## License

This Python client is licensed under the MIT License.

The MIT License applies only to this client code. It does not apply to Onlinekommentar data, API content, or other source materials returned by the service. For data and content licensing details, consult [Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar) and the respective original data sources.
