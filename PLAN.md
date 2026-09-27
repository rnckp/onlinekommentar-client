# Deferred review items

- Add CI for Python 3.13 and 3.14, Ruff, pytest, distribution builds, and dependency
  vulnerability scanning. There was no existing workflow. Select and verify external
  actions before pinning them to full commit SHAs; dependency/service approval is
  required for new tooling. Dependabot configuration is present, but repository-side
  enablement and successful update runs have not been verified.
- Recheck upstream OAI failures before releasing harvesting functionality. On
  2026-09-27, `ListIdentifiers&metadataPrefix=oai_dc` returned HTTP 500 with both
  JSON and XML Accept headers. Initial ListRecords/GetRecord requests worked for
  both formats, but continuation returned `badResumptionToken`; a no-cache request
  still received a response dated 2026-09-17 with a token expiring that same day.
  The cause of stale responses is unconfirmed. Do not hide these failures or
  treat them as successful completion. Other sampled live routes parsed correctly;
  this was a smoke check, not a complete crawl of every record/filter combination.
