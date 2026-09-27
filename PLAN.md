# Deferred review items

- Add CI for Python 3.13 and 3.14, Ruff, pytest, distribution builds, and dependency
  vulnerability scanning. There was no existing workflow. Select and verify external
  actions before pinning them to full commit SHAs; dependency/service approval is
  required for new tooling. Dependabot configuration is present, but repository-side
  enablement and successful update runs have not been verified.
- The OAI pagination helpers currently discard an explicitly supplied metadata prefix
  when a resumption token is present. Their default `oai_dc` cannot be distinguished
  from an explicit argument. A future API adjustment can use a sentinel and reject
  conflicting explicit prefixes consistently with the generic `oai()` method.
- Live API/schema compatibility was not checked during this review; all HTTP tests
  use MockTransport. Validate against the upstream service before a release,
  especially the stricter response schemas.
