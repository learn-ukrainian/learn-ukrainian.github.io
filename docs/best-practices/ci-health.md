## CI Health Baseline

Last verified: 2026-04-22

Issue: #1405

Scope of the 2026-04-22 repair pass:

- `Validate YAML Files / Curriculum Plans`: install `jsonschema` in the workflow so `validate_plan_config.py` imports cleanly.
- `CI / Secret Scanning (gitleaks)`: migrate the GitHub Actions job to TruffleHog while preserving the existing allowlist intent for public Algolia keys and lockfiles.
- `CI / Quality Gates (radon)`: evaluate only changed `scripts/**/*.py` files so historic complexity debt on untouched files does not block unrelated PRs.
- `CI / No new root scripts`: diff only true `scripts/*.py` root files, not nested `scripts/**`.
- `CI / Test (pytest)`: create a repo-local `.venv` in CI, install from `requirements-lock.txt`, force CPU `torch` wheels on GitHub-hosted Linux, and exclude non-hermetic integration files that require local corpora, generated review/orchestration artifacts, or sidecar tooling (`vesum.db`, `pdfinfo`, `codex`, `embed-venv`) that the runner does not provide.

Verification notes:

- Use a smoke PR after workflow edits to confirm the GitHub-required `CI` checks are green on a normal branch.
- The required PR checks now scope `Validate YAML Files`, `radon`, and `pytest` toward hermetic validation so unrelated repo debt does not force admin merges on otherwise clean PRs.
- If `CI / Secret Scanning (gitleaks)` goes red again, verify the pinned TruffleHog action SHA and `.trufflehogignore` patterns before changing policy.
