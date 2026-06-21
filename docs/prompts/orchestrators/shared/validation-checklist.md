# Shared Validation Checklist

Prompt suite component version: 0.2
Last reviewed: 2026-06-21

Use this as a menu, not a blind script. First inspect the current local repo to confirm each command still applies.

## Always Run For Any PR

```bash
git status --short --branch
git diff --check
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
printf '%s\n' "$CHANGED_FILES"
if ! git diff --quiet -- .python-version .yamllint .markdownlint.json || ! git diff --cached --quiet -- .python-version .yamllint .markdownlint.json; then
  echo "Protected config changed" >&2
  exit 1
fi
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg '(^|/)status/.*\.json$|(^|/)audit/.*-review\.md$|(^|/)review/.*-review\.md$|^docs/.*-STATUS\.md$|^data/telemetry/'; then
  echo "Forbidden generated artifact in diff" >&2
  exit 1
fi
CHANGED_CODE_FILES="$(printf '%s\n' "$CHANGED_FILES" | awk '/^(scripts|site|curriculum|tests)\\// {print}')"
if [ -n "$CHANGED_CODE_FILES" ]; then
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    if rg -n 'sys\.executable' "$file"; then
      echo "New or modified code path contains sys.executable" >&2
      exit 1
    fi
  done <<EOF
$CHANGED_CODE_FILES
EOF
fi
```

For docs-only prompt infrastructure, add a scoped path gate:

```bash
CHANGED_FILES="$( { git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$CHANGED_FILES" ] && printf '%s\n' "$CHANGED_FILES" | rg -v '^docs/prompts/orchestrators/'; then
  echo "Unexpected file outside docs/prompts/orchestrators/" >&2
  exit 1
fi
```

## Markdown Sanity

If markdownlint is available locally, run it without changing configuration:

```bash
npx markdownlint-cli2 "docs/prompts/orchestrators/**/*.md"
```

If the command is unavailable, do not edit `.markdownlint.json`; report that markdownlint was not available and rely on manual Markdown inspection plus `git diff --check`.

## Module Source Validation

Adapt these commands for the target level or track and module number. Use `.venv/bin/python`, not `python3`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en <track-or-level> <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/<track-or-level>/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en <track-or-level> <module_num> --validate
```

For folder-layout modules, the source files are normally:

- `curriculum/l2-uk-en/<track-or-level>/<slug>/module.md`
- `curriculum/l2-uk-en/<track-or-level>/<slug>/activities.yaml`
- `curriculum/l2-uk-en/<track-or-level>/<slug>/vocabulary.yaml`
- `curriculum/l2-uk-en/<track-or-level>/<slug>/resources.yaml` when present
- generated site MDX at `site/src/content/docs/<track-or-level>/<slug>.mdx`

Use `scripts/audit/check_mdx_generation_drift.py` when you need a drift-only check after generation, not as a default duplicate regeneration after `generate_mdx.py --validate`.

## Deterministic Audit Validation

For built module sources, run the deterministic audit without `--fix` before relying on subjective review:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/<track-or-level>/<slug>/module.md
```

Do not run `scripts/audit_module.py` on raw plans or wiki articles. For pre-production tracks with no built `module.md`, run plan/wiki/source coverage checks instead and record that the deterministic module audit was not applicable.

## Seminar And Sensitive Track Validation

For seminar or sensitive tracks such as HIST, BIO, ISTORIO, LIT, OES, RUTH, or folk/epic work, add track-specific checks before reuse:

- verify source attribution and quote provenance with the repo-supported source tools or scripts available in the current checkout
- check factual claims against the track's approved source, reading, dossier, wiki, or bibliography files
- check decolonization, Russian-shadow, imperial framing, and inherited-bias risks using the current track rubric
- verify that wiki/source paths match the track, such as historiography, literature, periods, figures, dossiers, readings, or other non-CEFR layouts
- consult existing seminar audit precedents under `docs/audits/` before choosing report naming and scope

## Audit Or Review Validation

Read-only audit prompts should not run full builds. They may run deterministic listing, parsing, lint, and diff checks that do not write generated artifacts. If an audit command writes `status/`, `audit/`, `review/`, or telemetry artifacts, remove those from the worktree before finalizing unless the prompt explicitly scoped a durable `docs/audits/` report.

## Prompt Suite Structural Validation

For this prompt suite, rerun a structural check before PR updates:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path

root = Path("docs/prompts/orchestrators")
prompts = sorted(p for p in root.glob("*/*-orchestrator.md") if "shared" not in p.parts)
required = [
    "Prompt version:",
    "## Source Assumptions",
    "## Goal",
    "## WORKTREE_ROOT Setup",
    "## Read First",
    "## Allowed Writes",
    "## Forbidden Writes",
    "## Helpers And Headroom",
    "## Validation Commands",
    "## Expected Final Response",
]
shared = [
    "docs/prompts/orchestrators/shared/repo-rules.md",
    "docs/prompts/orchestrators/shared/validation-checklist.md",
]
errors = []
for path in prompts:
    text = path.read_text(encoding="utf-8")
    for marker in required + shared:
        if marker not in text:
            errors.append(f"{path}: missing {marker}")
    if not text.endswith("\n"):
        errors.append(f"{path}: missing final newline")
    if "\t" in text:
        errors.append(f"{path}: contains tab")
for path in sorted(root.rglob("*.md")):
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        errors.append(f"{path}: missing final newline")
    if "\t" in text:
        errors.append(f"{path}: contains tab")
print(f"checked {len(prompts)} orchestrator prompts")
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
PY
```

## Commit Validation

Before pushing a module-build or remediation PR:

```bash
.venv/bin/python scripts/audit/lint_agent_trailer.py
git status --short
```
