# Deferred review items

- After pushing the branch, verify successful hosted CI runs for Python 3.13 and
  3.14 and repository-side Dependabot enablement/update runs. The workflow and
  dependency/action monitoring configuration are present; local validation cannot
  establish hosted settings or run status.
- Recheck the upstream ListIdentifiers failure reported in [NOTES.md](NOTES.md)
  and verify complete OAI-PMH harvesting. Synthetic tests cannot establish current
  service behavior; the recorded checks covered only bounded requests.
