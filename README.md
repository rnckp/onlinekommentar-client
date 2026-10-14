# Onlinekommentar Python Client

An independent, synchronous Python client for legal commentaries through the public
[Onlinekommentar](https://onlinekommentar.ch) JSON and OAI-PMH APIs.

This project is unofficial and is not affiliated with Onlinekommentar.

The service's [official API documentation](https://onlinekommentar.ch/en/apis) is the reference for
the upstream API. This repository documents the client behavior and the limits of its local checks.

## Installation

Requires Python 3.12 or newer and `uv`. From a local checkout, install the package and its declared
development dependencies:

```bash
cd onlinekommentar-client
uv sync
```

## Quick start

Save this example in a Python file and run it with `uv run <file>.py` from the repository root. It
makes live requests.

```python
from onlinekommentar import OnlinekommentarClient

with OnlinekommentarClient() as client:
    results = client.list_commentaries(language="de", search="Datenschutz", page=1)
    for commentary in results.commentaries[:5]:
        print(commentary.title, commentary.html_link)

    if results.commentaries:
        commentary = client.get_commentary(results.commentaries[0].commentary_id)
        print(commentary.title)
```

For more examples, see the [client guide](docs/client-guide.md) and [example
notebook](examples/onlinekommentar_demo.ipynb). Notebook API cells also make live requests; response
examples do not guarantee current service availability.

## Usage

Use a context manager or call `close()` to release the HTTP client. Instances are intended for
sequential use, with request spacing per instance. HTTP and transport errors propagate to callers.

The client covers `GET /api/commentaries`, `GET /api/commentaries/{id}`, and `GET /oai` with all six
OAI-PMH verbs. It does not scrape website pages or wrap private routes.

List calls return one page. `iter_commentaries()` offers bounded pagination with a default cap of
ten pages and raises `PaginationLimitError` if more remain. OAI-PMH methods return XML text;
`parse_oai_response()` provides optional protocol-error checks. JSON responses have typed models and
raw helpers.

See the [client guide](docs/client-guide.md) for method examples, response behavior, and error
handling.

## Configuration

The client loads `config.yaml` from the working directory, or a file selected with `config_path`.
Settings can be at the root or under `onlinekommentar:`. Use `discover_config=False` to disable
implicit file lookup. The defaults are a 30-second HTTPX timeout and a 0.2-second interval between
request starts. Constructor settings override a validated file; every request accepts
`request_timeout`. Retries are disabled by default and can be enabled explicitly.

See [configuration details](docs/client-guide.md#configuration) for validation, overrides, and
file-discovery behavior. The checkout includes [config.yaml](config.yaml); the working directory
controls implicit configuration and relative output paths.

## Scope and compatibility

This is a client library. It does not provide an application server or async client. Local tests use
offline fixtures or synthetic responses. They check the implemented contracts without establishing
current upstream availability or complete data coverage.

See the [API compatibility notes](docs/api-compatibility.md) for evidence and verification limits,
[NOTES.md](NOTES.md) for implementation decisions and historical observations, and
[PLAN.md](PLAN.md) for open tasks.

## Development

Run the local checks from the repository root:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, hooks, builds, CI, and optional checks. Agent
guidance is in [AGENTS.md](AGENTS.md).

## Responsible use

Keep request rates modest, retain source attribution and applicable reuse terms, and avoid sending
confidential or personal data to public endpoints. Consider contributing to
[Onlinekommentar](https://onlinekommentar.ch/en/ueber-onlinekommentar).

## License

This client code is licensed under the [MIT License](LICENSE). The license does not cover data, API
content, or other source materials returned by the service. Consult
[Onlinekommentar](https://onlinekommentar.ch) and the original sources for their reuse terms.
