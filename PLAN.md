# Deferred review items

- After pushing the branch, verify successful hosted CI runs for Python 3.13 and
  3.14 and repository-side Dependabot enablement/update runs. The workflow and
  dependency/action monitoring configuration are present; local validation cannot
  establish hosted settings or run status.
- Investigate the upstream ListIdentifiers HTTP 500 confirmed on 2026-10-13 with
  both JSON and XML Accept headers. Initial ListRecords/GetRecord and one fresh
  continuation page worked in both formats; historical badResumptionToken failures
  were not reproduced. Complete harvesting remains unverified. See [NOTES.md](NOTES.md).
