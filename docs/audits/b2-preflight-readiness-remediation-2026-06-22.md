# B2 Preflight Readiness Remediation

Date: 2026-06-22
Scope: blockers from the B2 preflight readiness report prepared in PR #3713
Verdict: conditional pass after this remediation PR merges

## Blockers Cleared

- `reflexive-passive` no longer teaches a named personal agent in the instrumental case with passive `-ся` as normative. The plan now teaches those forms as errors to recognize and rewrite actively, aligned with `wiki/grammar/b2/reflexive-passive.md`.
- The explicit English scaffolding fragments found in `advanced-case-semantics`, `pronoun-system-advanced`, and `reflexive-passive` have been localized where they were likely to be copied into module content.
- `docs/prompts/orchestrators/b2/production-build-orchestrator.md` now requires a `Plan Scaffolding Filter` in every module-tailored mini-prompt, so remaining legacy English planning notes are treated as internal metadata and not copied into B2 modules.
- The production prompt now requires a `Discovery Authority Check`, so empty discovery YAML stubs are treated as query-keyword hints only. The authoritative teaching brief is the locked wiki article plus the source registry for each slug.

## Production Gate

B2 module production may proceed after this remediation PR merges, using `docs/prompts/orchestrators/b2/production-build-orchestrator.md` prompt version 0.3 or later.

Carry forward these non-negotiable checks into the first production batch:

- Cite this remediation report as the B2 preflight report used.
- Include the `Plan Scaffolding Filter` and `Discovery Authority Check` in every module-tailored mini-prompt.
- Stop if a target wiki article or source registry is missing, source-empty, or contains unresolved verification markers.
- Keep generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/` artifacts out of the PR.

## Validation

- `.venv/bin/python scripts/validate_plans.py b2` → all 93 B2 plans OK.
- `git diff --check` → clean.
- Forbidden generated artifact scan → clean.
- Protected config diff for `.python-version`, `.yamllint`, and `.markdownlint.json` → clean.

swarm_used: false
swarm_label: solo
swarm_note: solo run; no swarm used
