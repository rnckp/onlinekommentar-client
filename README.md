# Onlinekommentar Python Client

**Python client for accessing the public [Onlinekommentar](https://onlinekommentar.ch) APIs more easily.**

This project is not official, associated with, or affiliated with Onlinekommentar. It was developed independently as a convenience wrapper around the publicly documented Onlinekommentar APIs.

**Note:** The official [Onlinekommentar website](https://onlinekommentar.ch) and [API documentation](https://onlinekommentar.ch/en/apis) are the actual and authoritative reference for the APIs.

## Installation

```bash
uv sync
```

## Quick Start

For a tour of the public APIs, see also [examples/onlinekommentar_demo.ipynb](examples/onlinekommentar_demo.ipynb).

```python
from onlinekommentar import OnlinekommentarClient

with OnlinekommentarClient() as client:
    # List recent published commentaries
    results = client.list_commentaries(language="en", page=1)

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

```python
results = client.list_commentaries(
    language="en",  # "en", "de", "fr", "it"; defaults to configured language
    search="data protection",
    legislative_act="2cdeaaed-30b6-416e-a6ca-7eaef78dfd69",
    sort="-date",  # "title", "-title", "date", "-date"
    page=1,
    request_timeout=60.0,  # optional per-call timeout
)

commentary = client.get_commentary("c9f28a48-39a2-42c4-baa8-7024899156b1")
```

`list_commentaries()` returns a `CommentarySearchResult` with parsed `Commentary` items. `get_commentary()` returns a single `Commentary`.

Raw JSON helpers are available when you need fields that are not modeled yet:

```python
raw_page = client.list_commentaries_raw(language="de", search="Datenschutz")
raw_commentary = client.get_commentary_raw("c9f28a48-39a2-42c4-baa8-7024899156b1")
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
    set_spec="legal_domain:civil-procedure",
)

records = client.list_records(metadata_prefix="oai_openaire")

record = client.get_record(
    identifier="oai:onlinekommentar.ch:commentary:40eb831a-088b-4b27-9fe2-31f049c790a5",
    metadata_prefix="oai_dc",
)
```

For unsupported or advanced OAI-PMH combinations, use the generic helper:

```python
xml = client.oai(
    verb="ListRecords",
    resumption_token="token-from-previous-response",
)
```

### Configuration

Runtime defaults are loaded from `config.yaml` when present. Constructor arguments such as `base_url`, `timeout`, `rate_limit_delay`, and `default_language` override configured defaults.

```yaml
onlinekommentar:
  base_url: "https://onlinekommentar.ch"
  timeout: 30.0
  rate_limit_delay: 0.2
  default_language: "en"
```

```python
client = OnlinekommentarClient(timeout=10.0, rate_limit_delay=0.5, default_language="de")
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

The client models stable high-use shapes and preserves unknown fields in each model's `raw` attribute. Raw JSON helpers are available for consumers that need exact API payloads.

Models and configuration are validated Pydantic models. Construct them with keyword
arguments; dataclass utilities and positional construction are no longer supported.
`from_json()` remains available. Invalid payloads raise `pydantic.ValidationError`
(a `ValueError` subclass), with structured field errors. Malformed collections and
pagination values are rejected rather than silently discarded or coerced. Integer
identifiers are still accepted and normalized to strings. Models prevent field
reassignment, but their lists and raw dictionaries remain mutable.

Missing configuration files use defaults. Existing files must contain a YAML mapping
(`{}` is valid); empty files, unknown settings, and invalid values are rejected.
Base URLs may include a path prefix, but cannot contain credentials, queries, or fragments.

Use a separate client per thread: the rate limiter is intended for sequential requests.
HTTP failures and timeouts propagate as HTTPX exceptions. OAI-PMH responses remain raw
XML, so callers must inspect any protocol-level `<error>` elements themselves.

## Scope

This package covers the public routes documented on the Onlinekommentar API page:

- `GET /api/commentaries`
- `GET /api/commentaries/{id}`
- `GET /oai` with OAI-PMH verbs `Identify`, `ListMetadataFormats`, `ListSets`, `ListIdentifiers`, `ListRecords`, and `GetRecord`

The client does not scrape website pages and does not cover private or undocumented routes.

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
Python 3.13 and newer are supported. Dependency updates are monitored by Dependabot.

## License

This Python client is licensed under the MIT License.

The MIT License applies only to this client code. It does not apply to Onlinekommentar data, API content, or other source materials returned by the service. For data and content licensing details, consult [Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar) and the respective original data sources.
