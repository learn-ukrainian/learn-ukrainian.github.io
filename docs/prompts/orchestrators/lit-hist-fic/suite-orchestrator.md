# LIT-HIST-FIC Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- `lit-hist-fic` is an active historical fiction track. It studies novels and stories that shape Ukrainian historical memory.
- Current planning docs include `docs/l2-uk-en/LIT-HIST-FIC-PLAN-GENERATED.md` and active plans under `curriculum/l2-uk-en/plans/lit-hist-fic/`.
- Each module needs primary literary readings plus a source-aware comparison to the historical event or memory problem being fictionalized.

## Goal

Run preflight, production, quality audit, or remediation for scoped `lit-hist-fic` modules while preserving literary analysis and historical-source discipline.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/lit-hist-fic-<stage>-<batch> .worktrees/dispatch/codex/lit-hist-fic-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/lit-hist-fic-<stage>-<batch>
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
export WORKTREE_ROOT="$(pwd)"
git status --short --branch
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/l2-uk-en/LIT-HIST-FIC-PLAN-GENERATED.md`
- `docs/l2-uk-en/templates/lit-module-template.md`
- target `curriculum/l2-uk-en/plans/lit-hist-fic/<slug>.yaml`

## Allowed Writes

- `docs/audits/lit-hist-fic-<scope>-<date>.md`
- scoped files under `curriculum/l2-uk-en/lit-hist-fic/`
- `site/src/content/docs/lit-hist-fic/<slug>.mdx`
- hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- inactive LIT remnants
- non-hostable copyrighted novels or long excerpts
- protected configs, generated status/audit/review artifacts, and `data/telemetry/**`

## Lifecycle Rules

- Preflight: verify text availability, rights, historical event/source anchors, and whether the novel's claims need HIST cross-checks.
- Production: teach how fiction constructs memory; compare with documented history without turning the module into a history lecture.
- Quality audit: check literary quote fidelity, historical framing, rights, and no romantic-nationalist overclaiming.
- Remediation: repair reading, historical-source, and copyright findings first.

## Track-Specific Checks

- Distinguish the novel's imagined scene from the historical record.
- Identify which imperial myth or memory distortion the work challenges, but do not let that become unsourced praise.

## Helpers And Headroom

Use helpers for historical cross-checks and text rights. Compress long outputs with Headroom.

## Validation Commands

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/lit-hist-fic").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("lit-hist-fic plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Add content-generation validation for production/remediation.

## Expected Final Response

```text
LIT-HIST-FIC stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
