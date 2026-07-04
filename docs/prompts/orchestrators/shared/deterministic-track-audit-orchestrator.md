# Deterministic Track Audit Orchestrator

Prompt version: 0.1
Last reviewed: 2026-07-04

## Source Assumptions

- This workflow is for deterministic structural and hygiene checks across one
  curriculum track or level.
- It is not a replacement for judgement-required pedagogy, source selection,
  cultural framing, or native-review work.
- Old LLM-QG persistence is excluded pending issue #2156. Do not run old
  LLM-QG workers, import old LLM-QG stores, write telemetry, or create
  module-local LLM-QG evidence.

## Goal

Run a reusable manifest-driven audit for a target track, starting with B2, and
produce stable JSON plus a concise summary. A new track should normally require
`--track <id>` and optional config/range choices, not script edits.

## Read First

- `AGENTS.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `scripts/audit/track_deterministic_audit.py`
- `scripts/audit/track_deterministic_audit_config.yaml`
- `curriculum/l2-uk-en/curriculum.yaml`

## Default Command

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --format summary
```

For a smoke slice:

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --range 1-3 --format json --output /tmp/b2-deterministic-smoke.json
```

The default runner is read-only. It checks manifest inventory, required source
and mirror files, activity YAML, vocabulary YAML, resource YAML shape, surface
leakage, internal leakage, MDX index/route health, protected artifact hygiene,
and explicit skipped-check accounting.

## Optional Checks

`generate_mdx.py --validate` rewrites site MDX before validating, so it is not a
default read-only check. Use it only for a controlled smoke slice:

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --range 1-1 --run-mdx-generation-validate
```

Live external URL checks are network-dependent and are also excluded from the
default deterministic profile.

## Output Contract

Each finding includes:

- `track`
- `module_num`
- `slug`
- `category`
- `severity`
- `file`
- `line`
- `message`
- `evidence`
- `auto_fixable`
- `recommended_remediation_batch`

The summary separates blocker/high findings from advisories, deterministic
failures from judgement-required content work, auto-fixable findings from
remediation-only findings, skipped checks, and the LLM-QG exclusion pending
issue #2156.

## B2 First Target

B2 uses folder-layout modules:

```text
curriculum/l2-uk-en/b2/<slug>/module.md
curriculum/l2-uk-en/b2/<slug>/activities.yaml
curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml
curriculum/l2-uk-en/b2/<slug>/resources.yaml
site/src/content/docs/b2/<slug>.mdx
wiki/grammar/b2/<slug>.md
wiki/grammar/b2/<slug>.sources.yaml
```

The runner enumerates modules from `curriculum.yaml` and checks the folder
layout. It does not use legacy flat-file batch runners for B2.

## Forbidden Writes

- `.python-version`
- `.yamllint`
- `.markdownlint.json`
- root `package.json`
- root `package-lock.json`
- `data/telemetry/**`
- generated curriculum `status/`, `audit/`, or `review/` artifacts
- old LLM-QG evidence or telemetry

## Validation Before PR

```bash
git diff --check
.venv/bin/python -m pytest tests/audit/test_track_deterministic_audit.py
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --range 1-3 --format summary --fail-on never
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --format json --output /tmp/b2-deterministic-audit.json --fail-on never
```

Then run the protected artifact/config gate from
`docs/prompts/orchestrators/shared/validation-checklist.md`.
