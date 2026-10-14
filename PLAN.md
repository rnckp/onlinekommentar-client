# Deferred review items

- After pushing the CI changes, verify successful hosted `Quality` and `Python
  3.14` checks and the dependency audit. Confirm Dependabot update runs; local
  validation cannot establish hosted run status.
- Recheck the upstream ListIdentifiers failure reported in [NOTES.md](NOTES.md)
  and verify complete OAI-PMH harvesting. Synthetic tests cannot establish current
  service behavior; the recorded checks covered only bounded requests.
