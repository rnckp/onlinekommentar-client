# Onlinekommentar API compatibility notes

These notes describe the requests and response handling implemented by this independent client. They
are not an official service specification. Start with the [README](../README.md) for installation
and the [client guide](client-guide.md) for Python examples and configuration.

## Evidence and verification limits

Local tests use synthetic HTTP responses and execute the example notebook with an offline transport.
They check request construction, response validation, pagination, retries, and OAI-PMH handling
without establishing current upstream availability or compatibility. There is no vendored upstream
schema or opt-in live test suite.

[NOTES.md](../NOTES.md#historical-upstream-observations) records bounded checks reported on
2026-10-13. The responses were not retained, so those observations cannot be independently verified
from this repository. Complete harvesting and every filter combination remain unverified. The
service's [official API documentation](https://onlinekommentar.ch/en/apis) is the reference for the
upstream API.

## Endpoint inventory

Paths are relative to the configured `base_url`, which defaults to `https://onlinekommentar.ch`. All
requests use GET.

| Path | Client methods | Parameters |
| --- | --- | --- |
| `/api/commentaries` | `list_commentaries()`, `list_commentaries_raw()`, `iter_commentaries()` | `language`, `search`, `legislative_act`, `sort`, `page` |
| `/api/commentaries/{id}` | `get_commentary()`, `get_commentary_raw()` | Commentary ID in the path |
| `/oai` | `oai()` and the six named verb helpers | `verb`, plus the verb-specific arguments below |

The JSON list methods forward supplied filters without validating their values; omitted or empty
language uses the configured default. Omitted sort and page values are not sent. Detail IDs are
URL-quoted; blank IDs and dot segments are rejected before the request.

### OAI-PMH arguments

| Helper | Verb | Optional arguments | Required arguments |
| --- | --- | --- | --- |
| `identify()` | `Identify` | — | — |
| `list_metadata_formats()` | `ListMetadataFormats` | `identifier` | — |
| `list_sets()` | `ListSets` | `resumption_token` | — |
| `list_identifiers()` | `ListIdentifiers` | `metadata_prefix`, `from_date`, `until`, `set_spec`, `resumption_token` | — |
| `list_records()` | `ListRecords` | `metadata_prefix`, `from_date`, `until`, `set_spec`, `resumption_token` | — |
| `get_record()` | `GetRecord` | `metadata_prefix` | `identifier` |

Python names map to protocol parameters `metadataPrefix`, `from`, `until`, `set`, and
`resumptionToken`. Initial identifier/record requests default to `oai_dc`. Continuation tokens
cannot be combined with an explicit metadata prefix or filters. OAI-PMH requests use an XML Accept
header and return response text.

## Client compatibility behavior

- Typed JSON helpers validate selected fields and retain unknown fields in `raw`.
  Raw helpers return decoded JSON objects without model validation. Detail models
  accept a direct commentary object or a `data` wrapper.
- Each list request fetches one page. The iterator increments page numbers on
  the configured server and stops when the response has no next-page URL. It
  does not follow response URLs. Its default cap is ten pages; reaching the cap
  with more pages remaining raises `PaginationLimitError` after any prior yields.
- HTTP and transport failures propagate. Retries are disabled by default;
  optional retries cover selected transient failures. See the
  [client guide](client-guide.md#configuration) for timing and retry rules.
- OAI-PMH HTTP success can still contain protocol errors. The optional
  `parse_oai_response()` parser raises `OAIProtocolError` with error codes. It
  rejects malformed XML, DTD/entity declarations, and unexpected roots without
  validating the full protocol schema or metadata contents.
- The client does not silently replace a failed OAI-PMH verb with another verb.
  Callers may explicitly read identifiers from ListRecords headers if needed.

## Scope and contract tests

This package wraps the two public JSON routes and six OAI-PMH verbs. Website scraping and private
routes are outside its scope. Tests in `tests/test_client.py`, `tests/test_models.py`,
`tests/test_oai.py`, and `tests/test_notebook.py` check the local contracts. Run them with `uv run
pytest` from the repository root.

Follow-up upstream checks are in [PLAN.md](../PLAN.md); contributor setup and validation commands
are in [CONTRIBUTING.md](../CONTRIBUTING.md).
