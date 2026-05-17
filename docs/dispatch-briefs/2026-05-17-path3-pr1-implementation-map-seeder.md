# Dispatch brief — Path 3 PR1: `implementation_map.json` deterministic seeder

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Scope:** PR1 of 4 in Path 3 architecture per
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`. Sidecar file +
deterministic seeder + contract tests. NO downstream behavioral changes
(those are PR2/3). NO activity-stub generation (deferred to PR5 per card line 141).

---

## Why

The V7 single-pass writer asymptotes at ~44% on strict 18-obligation manifests
(m20 builds #16–#21 evidence in afternoon handoff). The architectural fix is
to seed a deterministic skeleton BEFORE the writer runs so the writer's job
becomes "fill slots" rather than "invent coverage structure." This PR creates
that sidecar.

Decision Card is approved (user sign-off recorded in
`docs/session-state/2026-05-17-afternoon-path3-decision-card-handoff.md`
under `afternoon_bar_status`). Card forbids "silently starting PR1"; that gate
is satisfied — start now.

---

## What you build

### 1. New module: `scripts/build/phases/implementation_map.py`

Three responsibilities only. No imports of `linear_pipeline` (one-way
dependency: pipeline imports this, not reverse).

```python
"""Deterministic implementation_map seeder for V7 Path 3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, TypedDict

IMPLEMENTATION_MAP_SCHEMA: dict[str, Any] = { ... }  # see schema below
TREATMENT_TEMPLATES: dict[str, dict[str, Any]] = { ... }  # per-type expected output shape

class ImplementationMapEntry(TypedDict):
    obligation_id: str
    obligation_type: Literal[
        "sequence_step", "l2_error", "phonetic_rule", "decolonization_ban"
    ]
    artifact: Literal["module.md", "activities.yaml"]
    location_hint: str
    treatment_template: dict[str, Any]
    manifest_payload: dict[str, Any]   # verbatim copy of source row

def seed_implementation_map(
    manifest: dict[str, Any], *, plan: dict[str, Any] | None = None
) -> dict[str, Any]: ...

def write_implementation_map(payload: dict[str, Any], path: Path) -> None: ...

def read_implementation_map(path: Path) -> dict[str, Any]: ...

def validate_implementation_map(payload: dict[str, Any]) -> None: ...
```

#### Artifact-assignment rules (deterministic; per Decision Card Phase 0)

| `obligation_type` | extra check | `artifact` |
|---|---|---|
| `l2_error` | `treatment == "contrast_pair"` | `activities.yaml` |
| `l2_error` | `treatment == "prose_explanation"` (or anything else) | `module.md` |
| `sequence_step` | — | `module.md` |
| `phonetic_rule` | — | `module.md` |
| `decolonization_ban` | — | `module.md` |

#### `treatment_template` per type (the expected output shape the writer fills)

The template documents what the gate expects the writer to put in
the chosen artifact for THIS obligation. Used by PR2's gate output and PR3's
batched reviewer. Keep it minimal here — just structural promise, not prose.

```python
TREATMENT_TEMPLATES = {
    "l2_error.contrast_pair": {
        "shape": "activities.yaml entry with fields {sentence, error, correction}",
        "expected_error_value": "<from manifest_payload.incorrect>",
        "expected_correction_value": "<from manifest_payload.correct>",
    },
    "l2_error.prose_explanation": {
        "shape": "module.md prose paragraph that names manifest_payload.incorrect verbatim, contrasts with manifest_payload.correct, and explains manifest_payload.why",
    },
    "sequence_step": {
        "shape": "module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num",
        "required_claim": "<from manifest_payload.required_claim>",
    },
    "phonetic_rule": {
        "shape": "module.md prose that states the rule mapping manifest_payload.written → manifest_payload.spoken with an explicit IPA bracket or equivalent",
    },
    "decolonization_ban": {
        "shape": "module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)",
    },
}
```

The `manifest_payload` field on each entry carries the verbatim manifest row
so downstream consumers (PR2 gate, PR3 reviewer) don't need to re-join with
the manifest. This is the "first-class mutable sidecar" Codex called out in
the cross-agent votes.

#### `location_hint` derivation

If `plan` is provided AND contains sections with stable identifiers
(`plan["sections"][i]["heading"]` or similar), pick the section whose
heading most closely matches the obligation's manifest text. **First pass:
keep this simple.** Use a substring-match heuristic:

1. For `sequence_step`: location_hint = `f"§{manifest_payload['heading']}"` (the
   step's own heading is the strongest hint).
2. For `l2_error` / `phonetic_rule` / `decolonization_ban`: location_hint =
   the first plan section heading whose text contains any keyword from the
   obligation's `id` or its `incorrect`/`written`/`rule` field, falling back
   to `"(any prose section)"` if no plan or no match.

Do NOT do anything fancier — the writer can override location during fill-in;
this is a hint, not a constraint. PR3's reviewer reads `manifest_payload.id`
when applying fixes, not `location_hint`.

If `plan is None`, `location_hint = "(any prose section)"` for the prose
artifacts and `"activities.yaml"` for contrast_pair.

#### Output shape

```json
{
  "schema_version": 1,
  "slug": "<from manifest.slug>",
  "wiki_path": "<from manifest.wiki_path>",
  "manifest_obligation_count": <int>,
  "entries": [
    {
      "obligation_id": "step-1",
      "obligation_type": "sequence_step",
      "artifact": "module.md",
      "location_hint": "§Привітання",
      "treatment_template": { "shape": "...", "required_claim": "..." },
      "manifest_payload": { "id": "step-1", "heading": "Привітання", "step_num": 1, "required_claim": "...", "source_lines": "..." }
    },
    ...
  ]
}
```

Entries appear in **manifest order** (the same order `validate_obligations`
in `scripts/audit/wiki_coverage_gate.py` returns: sequence_steps → l2_errors
→ phonetic_rules → decolonization_bans). This is deterministic and matches
existing gate expectations.

### 2. Pipeline wiring (LIGHT — write-only, no behavior change)

In `scripts/build/v7_build.py` (NOT `linear_pipeline.py` — pipeline is
write-once for this PR), after the wiki manifest is extracted and BEFORE the
writer phase runs, call:

```python
from scripts.build.phases.implementation_map import (
    seed_implementation_map, write_implementation_map,
)

impl_map = seed_implementation_map(wiki_manifest, plan=plan_data)
write_implementation_map(impl_map, module_dir / "implementation_map.json")
```

Emit a JSONL event:
`{"event": "implementation_map_seeded", "slug": <slug>, "entry_count": <int>, "path": "<module_dir>/implementation_map.json"}`

That's it for wiring. Do NOT pass `impl_map` to the writer. Do NOT change
prompts. Do NOT change gates. Writer still emits its own
`<implementation_map>` blocks inline as today — PR2/3 will start consuming
the sidecar.

### 3. Contract tests: `tests/build/test_implementation_map.py`

Mandatory test cases:

1. **One entry per manifest obligation**: build a fixture manifest with 4
   sequence_steps + 3 l2_errors (2 contrast_pair + 1 prose_explanation) + 2
   phonetic_rules + 5 decolonization_bans → seeded map MUST have exactly 14
   entries, in manifest order.
2. **Artifact mapping is correct per the table**: assert each entry's
   `artifact` field matches the rule for its type+treatment.
3. **manifest_payload round-trips**: each entry's `manifest_payload` equals
   the original manifest dict for that obligation (deep equality).
4. **JSON schema validates seeded output**: `validate_implementation_map`
   accepts the seeder output without raising.
5. **Round-trip identity**: `read_implementation_map(write_implementation_map(x))`
   equals `x` (deep equality, including key order doesn't matter but values do).
6. **Empty manifest**: a manifest with zero obligations in all 4 groups
   produces an empty `entries` array but still validates and writes.
7. **`location_hint` fallback**: when `plan=None`, sequence_step entries use
   `f"§{heading}"` from manifest_payload; other prose obligations use
   `"(any prose section)"`; contrast_pair uses `"activities.yaml"`.
8. **Determinism**: calling the seeder twice on the same input produces
   byte-identical JSON (sort_keys, indent=2; verify in the test).
9. **m20 real-world fixture**: extract the actual manifest from
   `wiki/pedagogy/a1/my-morning.md` via `wiki_manifest.extract_manifest`,
   seed the map, assert entry count equals the gate's obligation count for
   that wiki (18 per afternoon handoff evidence — verify exact count from
   the fixture; if my-morning.md has changed and the count differs, use
   whatever the deterministic extractor returns and assert ≥10 and that
   the count equals `len(validate_obligations(manifest))`).

Use existing pytest patterns from `tests/build/test_linear_pipeline.py` for
fixture loading.

### 4. Schema JSON (optional, recommended)

If schema validation needs a referenceable JSON file, write it to
`scripts/build/phases/implementation_map.schema.json` and reference it from
`IMPLEMENTATION_MAP_SCHEMA`. Otherwise inline the dict is fine.

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| New module created | `git diff --stat origin/main` showing the new `scripts/build/phases/implementation_map.py` row |
| Tests pass | `.venv/bin/pytest tests/build/test_implementation_map.py -v` final line raw (`N passed in M.MMs`) |
| Full pytest still green | `.venv/bin/pytest tests/build/ -q` final summary line raw (NO `-x` — must surface every downstream failure, not just the first; per #1942) |
| Ruff clean | `.venv/bin/ruff check scripts/build/phases/implementation_map.py tests/build/test_implementation_map.py` raw output (must be `All checks passed!`) |
| m20 real-world seed works | one-shot: `.venv/bin/python -c "from scripts.build.phases.wiki_manifest import extract_manifest; from scripts.build.phases.implementation_map import seed_implementation_map; m = extract_manifest('wiki/pedagogy/a1/my-morning.md'); s = seed_implementation_map(m); print(f'entries={len(s[\"entries\"])} types={sorted({e[\"obligation_type\"] for e in s[\"entries\"]})}')"` raw output |
| Pipeline wiring runs | dry-run of the new emit by importing v7_build and confirming `implementation_map_seeded` event appears (quote the new event in JSONL) — OR if dry-run too painful, quote `git diff scripts/build/v7_build.py` to prove the 5-line wiring landed |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

**No claim allowed without its raw output line.** Per #M-4: a model can claim "we're done" with no evidence and the evaluator has nothing to disprove. Forbid that pattern.

---

## Worktree setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/path3-pr1-impl-map-seeder -b feat/path3-pr1-implementation-map-seeder origin/main
cd .worktrees/path3-pr1-impl-map-seeder
```

`delegate.py dispatch` handles the worktree creation when given
`--worktree`. The path above is the canonical shape.

---

## Verification (must run all BEFORE pushing)

`delegate.py dispatch` symlinks `.venv` into the worktree, so the
`.venv/bin/...` invocations below resolve from inside the worktree.

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/build/test_implementation_map.py -v
.venv/bin/pytest tests/build/ -q
.venv/bin/ruff check scripts/build/phases/implementation_map.py tests/build/test_implementation_map.py
.venv/bin/python -m pre_commit run --files scripts/build/phases/implementation_map.py tests/build/test_implementation_map.py scripts/build/v7_build.py
git diff --stat origin/main
git diff --name-only origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.
Per #1942: do NOT pass `-x` to pytest in dispatched verification — must
surface every downstream failure, not just the first.

---

## Commit + PR

```bash
git add scripts/build/phases/implementation_map.py \
        tests/build/test_implementation_map.py \
        scripts/build/v7_build.py
# also: scripts/build/phases/implementation_map.schema.json if you broke schema out
git commit -m "$(cat <<'EOF'
feat(build): Path 3 PR1 — deterministic implementation_map.json seeder

Path 3 architecture (docs/decisions/2026-05-17-path3-per-obligation-review-loop.md)
splits coverage enforcement out of the writer prompt and into a deterministic
sidecar + per-obligation review loop. This PR ships the sidecar.

PR1 scope (this PR):
* New module scripts/build/phases/implementation_map.py with schema,
  deterministic seeder seed_implementation_map(manifest, plan=None),
  read/write/validate utilities, and TREATMENT_TEMPLATES per obligation type.
* Light wiring in scripts/build/v7_build.py: after wiki manifest extraction
  and before writer phase, seed the map and write it to module_dir as
  implementation_map.json. Emits "implementation_map_seeded" JSONL event.
  No prompt or gate changes (those are PR2/PR3).
* Contract tests covering: 1-row-per-obligation, deterministic artifact
  assignment per type+treatment, manifest_payload round-trip, JSON schema
  validation, write→read identity, empty-manifest, plan=None location_hint
  fallback, byte-determinism, and an m20 wiki real-world smoke.

Out of scope:
* Activity-stub generation (deferred to PR5 per Decision Card line 141).
* Any change to writer prompt, wiki_coverage_gate, or reviewer behavior
  (those are PR2/PR3/PR4).
* External resources are NOT seeded (wiki_coverage_gate's
  validate_obligations excludes them today; keep PR1 aligned with the
  current gate scope).

Cross-agent vote convergence: Codex (first-class mutable sidecar),
Gemini (Allocation-First), Grok (strict ADR-007 fixes-only), Claude
(separate pipeline stage). Refined Path 3 = 4-vote consensus.

Verification:
* tests/build/test_implementation_map.py: <quote pytest final line>
* tests/build/ green: <quote pytest final line>
* ruff: <quote raw>
* m20 real-world seed entry count: <quote stdout>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Codex <noreply@anthropic.com>
EOF
)"
git push -u origin feat/path3-pr1-implementation-map-seeder
gh pr create --title "feat(build): Path 3 PR1 — deterministic implementation_map.json seeder" --body "$(cat <<'EOF'
## Summary

First of 4 Path 3 PRs per Decision Card `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`.

Adds a deterministic per-obligation sidecar `implementation_map.json` written to module_dir before the writer runs. Seeder reads the wiki Obligations Manifest (already extracted deterministically by `scripts/build/phases/wiki_manifest.py`) and produces one entry per obligation with:
* `obligation_id`, `obligation_type`, deterministically-picked `artifact` (module.md vs activities.yaml per type+treatment),
* `location_hint` (best-effort plan section match; safe fallback when no plan),
* `treatment_template` (per-type expected output shape — consumed by PR2/PR3 reviewer),
* verbatim `manifest_payload` (first-class mutable sidecar per Codex's vote).

NO downstream behavioral change in this PR. Writer prompt unchanged. wiki_coverage_gate unchanged. Reviewer unchanged. PR2 will extend wiki_coverage_gate to emit `<fix_proposals>` against this sidecar; PR3 wires the batched correction loop; PR4 adds the Goodhart sentinel.

## Verifiable claims (per #M-4)

* New module + tests landed: <quote git diff --stat>
* `tests/build/test_implementation_map.py`: <quote pytest final line raw>
* Full `tests/build/`: <quote pytest final line raw>
* `ruff check`: <quote raw "All checks passed!" line>
* m20 (`wiki/pedagogy/a1/my-morning.md`) real-world seed produces N entries: <quote stdout>
* Determinism: byte-equal JSON across two seeder runs on same input (asserted in test 8)

## Test plan

* [x] One entry per manifest obligation, in manifest order
* [x] Artifact mapping correct per type+treatment table (5 cases)
* [x] manifest_payload round-trips verbatim
* [x] Schema validates seeded output
* [x] write→read identity
* [x] Empty manifest produces empty entries, still validates
* [x] location_hint fallback when plan=None
* [x] Byte-determinism across two seeder runs
* [x] m20 real-world smoke

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

NO `--auto-merge`. Leave the PR open; orchestrator merges after review.

---

## Out of scope (do NOT include)

* Activity-stub generation in `activities.yaml` (PR5, per card line 141).
* Any change to `linear-write.md` / writer prompt.
* Any change to `wiki_coverage_gate.py` (PR2's job).
* Any change to reviewer prompts or `_apply_writer_correction` (PR3's job).
* Seeding external_resources (`wiki_coverage_gate.validate_obligations` excludes
  them today; aligning with current gate scope avoids divergence).
* Trying to be clever about location_hint matching. The hint is best-effort.
  PR3's reviewer uses `obligation_id`, not `location_hint`, when applying
  fixes.

---

## Anti-fabrication preamble

If anything in this brief surprises you — the wiki_manifest dataclass shape
is different from what you expected, a test fixture doesn't load, the m20
manifest extraction errors — STOP and quote the surprise verbatim before
patching. Don't paper over.

If the `validate_obligations` in `wiki_coverage_gate.py` includes obligations
beyond the 4 groups listed above by the time you read this, mirror its scope
EXACTLY in the seeder (single source of truth: the gate). Quote both the
`validate_obligations` group tuple and your seeder's group tuple in the PR
description to prove they match.

If a test feels redundant or impossible to write deterministically, name the
specific test and the specific blocker — do not silently drop tests from the
list.
