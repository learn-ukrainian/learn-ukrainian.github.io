## CI Health Baseline

Last verified: 2026-04-22

Issue: #1405

Scope of the 2026-04-22 repair pass:

- `Validate YAML Files / Curriculum Plans`: install `jsonschema` in the workflow so `validate_plan_config.py` imports cleanly.
- `CI / Secret Scanning (gitleaks)`: migrate the GitHub Actions job to TruffleHog while preserving the existing allowlist intent for public Algolia keys and lockfiles.
- `CI / Quality Gates (radon)`: evaluate only changed `scripts/**/*.py` files so historic complexity debt on untouched files does not block unrelated PRs.
- `CI / No new root scripts`: diff only true `scripts/*.py` root files, not nested `scripts/**`.
- `CI / Test (pytest)`: create a repo-local `.venv` in CI and install from `requirements-lock.txt` so tests run against the interpreter layout the repo expects.

Verification notes:

- Use a smoke PR after workflow edits to confirm the GitHub-required `CI` checks are green on a normal branch.
- `Validate YAML Files` still contains the repo-wide `Activities & Vocab` yamllint gate, which currently reports unrelated curriculum YAML failures outside #1405. Re-run that workflow with `workflow_dispatch` when validating the `jsonschema` fix so the `Curriculum Plans` job can be checked independently from the outstanding content debt.
- If `CI / Secret Scanning (gitleaks)` goes red again, verify the pinned TruffleHog action SHA and `.trufflehogignore` patterns before changing policy.
