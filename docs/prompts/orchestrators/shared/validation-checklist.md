# Shared Validation Checklist

Prompt version: 0.1
Last reviewed: 2026-06-21

Use this as a menu, not a blind script. First inspect the current local repo to confirm each command still applies.

## Always Run For Any PR

```bash
git status --short --branch
git diff --check
git diff --name-only
git diff -- .python-version .yamllint .markdownlint.json
git diff --name-only | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^docs/.*-STATUS\.md$|^data/telemetry/' || true
git diff --name-only | rg -v '^docs/prompts/orchestrators/' || true
rg -n 'sys\.executable' scripts site curriculum tests || true
```

For docs-only prompt infrastructure, the expected result is that only `docs/prompts/orchestrators/**` appears in `git diff --name-only`.

## Markdown Sanity

If markdownlint is available locally, run it without changing configuration:

```bash
npx markdownlint-cli2 "docs/prompts/orchestrators/**/*.md"
```

If the command is unavailable, do not edit `.markdownlint.json`; report that markdownlint was not available and rely on manual Markdown inspection plus `git diff --check`.

## Module Source Validation

Adapt these commands for the target level and module number. Use `.venv/bin/python`, not `python3`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en <level> <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/<level>/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en <level> <module_num> --validate
.venv/bin/python scripts/audit/check_mdx_generation_drift.py --files curriculum/l2-uk-en/<level>/<slug>/module.md curriculum/l2-uk-en/<level>/<slug>/activities.yaml curriculum/l2-uk-en/<level>/<slug>/vocabulary.yaml
```

For folder-layout modules, the source files are normally:

- `curriculum/l2-uk-en/<level>/<slug>/module.md`
- `curriculum/l2-uk-en/<level>/<slug>/activities.yaml`
- `curriculum/l2-uk-en/<level>/<slug>/vocabulary.yaml`
- `curriculum/l2-uk-en/<level>/<slug>/resources.yaml` when present
- generated site MDX at `site/src/content/docs/<level>/<slug>.mdx`

## Audit Or Review Validation

Read-only audit prompts should not run full builds. They may run deterministic listing, parsing, lint, and diff checks that do not write generated artifacts. If an audit command writes `status/`, `audit/`, `review/`, or telemetry artifacts, remove those from the worktree before finalizing unless the prompt explicitly scoped a durable `docs/audits/` report.

## Commit Validation

Before pushing a module-build or remediation PR:

```bash
.venv/bin/python scripts/audit/lint_agent_trailer.py
git status --short
```
