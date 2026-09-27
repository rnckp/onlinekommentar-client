# Deferred review items

- Add CI for Python 3.13 and 3.14, Ruff, pytest, distribution builds, and dependency
  vulnerability scanning. No workflow is present. Select and verify external
  actions before pinning them to full commit SHAs; dependency/service approval is
  required for new tooling. Verify repository-side Dependabot enablement and
  successful update runs; the configuration alone does not establish either.
- Recheck OAI-PMH identifiers and continuation against the live service before relying
  on complete harvesting. Earlier notes report that on 2026-09-27,
  `ListIdentifiers&metadataPrefix=oai_dc` returned HTTP 500 with JSON and XML Accept
  headers. Initial ListRecords/GetRecord requests reportedly worked for `oai_dc`
  and `oai_openaire`, but continuation returned `badResumptionToken`. A no-cache
  response reportedly carried a 2026-09-17 date and a token expiring that day.
  No response captures are retained in the repository, so these observations cannot
  be independently verified here and do not establish current service status or
  the cause of the failures. Tests reproduce HTTP and XML error cases synthetically.
- Resolve the hook setup prerequisite in [AGENTS.md](AGENTS.md): it requires
  `uv run pre-commit install`, but neither `pre-commit` nor a hook configuration is
  declared. Adding the dependency requires approval; this is not a working setup
  command for the current repository.
