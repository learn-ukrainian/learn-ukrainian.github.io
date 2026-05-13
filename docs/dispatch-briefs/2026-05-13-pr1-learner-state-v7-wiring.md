# Dispatch Brief — PR1: Wire `scripts/pipeline/learner_state.py` into V7

> **Status:** PENDING DISPATCH. Authority: `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` (ACCEPTED). Scope is PR1 of the 2-PR split (PR2 is a separate dispatch).

## Mission

V7 pipeline is not student-aware. The v6 `learner_state.py` module exists, works, and produces the right prompt-injection text, but it is unwired in V7. This PR restores the wiring with minimal scope: path fix + writer-prompt placeholder + new deterministic audit gate. Do NOT change `IMMERSION_POLICIES`, do NOT add `plan.targets` schema — those are PR2.

## Determined verifiable claims this PR will produce

| Claim | Deterministic tool | Output format (raw evidence required, never paraphrased) |
|---|---|---|
| `learner_state.py:_load_vocab` reads V7 layout | `grep -n "vocabulary.yaml" scripts/pipeline/learner_state.py` | raw line containing `f"{slug}/vocabulary.yaml"` or equivalent V7 path |
| `{LEARNER_STATE}` placeholder is in writer prompt | `grep -n "{LEARNER_STATE}" scripts/build/phases/linear-write.md` | raw line showing the placeholder, AND surrounding context proving placement is after `## Module Context` and before `## Immersion Rule` |
| Substitution wired in prompt builder | `grep -n "LEARNER_STATE\|learner_state" scripts/build/prompt_builder.py` | raw lines showing import + substitution dict entry |
| Audit gate registered | `grep -rn "learner_state" scripts/audit/__init__.py scripts/audit/registry*.py scripts/audit/audit_module.py` | raw line showing the check imported/registered |
| Tests pass | `.venv/bin/pytest tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py -v` | the `passed in M.MMs` summary line raw |
| Full suite pytest unchanged on touched modules | `.venv/bin/pytest tests/ -x --ignore=tests/e2e 2>&1 \| tail -5` | the final summary line raw (no new failures) |
| Lint clean | `.venv/bin/ruff check scripts/pipeline/learner_state.py scripts/build/prompt_builder.py scripts/audit/checks/learner_state.py tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py` | `All checks passed!` raw |

If you cannot produce raw output for any claim above, the PR is not done. **No paraphrased claims** — every assertion in the PR body must be backed by a `<command + cwd + raw-output>` triple per `#M-4` deterministic-over-hallucination.

## Numbered steps (MANDATORY — do not skip or merge steps)

### Step 1 — Worktree setup

```bash
git worktree add -b codex/pr1-learner-state-v7-wiring-2026-05-13 \
  .worktrees/dispatch/codex/pr1-learner-state-v7-wiring-2026-05-13 \
  origin/main
cd .worktrees/dispatch/codex/pr1-learner-state-v7-wiring-2026-05-13
```

NEVER `git checkout -b` in the main project directory (see prior session incident in `docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md`).

### Step 2 — File-level work

#### 2a. `scripts/pipeline/learner_state.py` — path fix only

The module-level `CURRICULUM_ROOT` constant is correct as-is. Update `_load_vocab(track: str, slug: str)` to read the V7 layout:

- Current (v6): `CURRICULUM_ROOT / track / "vocabulary" / f"{slug}.yaml"`
- Target (V7): `CURRICULUM_ROOT / track / slug / "vocabulary.yaml"`

V7 stores vocab inline in the module folder; the `track` argument is conceptually the `level` (`a1`/`a2`/...) since V7 organizes by level. Keep the function signature unchanged — call sites in `format_learner_state` / `build_learner_state` already pass the right value.

**Do NOT add v6 fallback path support.** V7 is the only live pipeline. If a downstream call breaks because of an empty-string track, fix the caller, not the loader.

`_load_grammar(track, slug)` reads `plans/{track}/{slug}.yaml`. Verify this matches V7 layout by checking `curriculum/l2-uk-en/plans/a1/my-morning.yaml` exists (the example plan from PR0 verification). If yes, no change needed to `_load_grammar`. If no, fix it the same way.

Also verify `_load_plan_title(track, slug)` follows the same plans/ path. Same one-line check.

#### 2b. `scripts/build/phases/linear-write.md` — placeholder insertion

Add `{LEARNER_STATE}` immediately after the `## Module Context` block (current line ~228) and before `## Immersion Rule` (current line ~230). Insertion shape:

```markdown
## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Topic: {TOPIC_TITLE}
- Phase: {PHASE}
- Word target: {WORD_TARGET}

## Learner State

{LEARNER_STATE}

## Immersion Rule
```

Add a short 2-line directive paragraph IMMEDIATELY before the placeholder, integrated with the `Tone and immersion (mandatory)` section's voice (assertive, no hedging):

> Words and grammar listed in **Cumulative vocabulary** / **Grammar already taught** are the floor of what this module's prose may assume. Do not re-explain already-taught grammar; do not introduce vocabulary that is not in the cumulative list or in this module's declared `vocabulary.yaml` (any unknown UK lemma in body prose without inline gloss is a HARD audit failure from m04 onward; WARN m01–m03).

#### 2c. `scripts/build/linear_pipeline.py:writer_context()` — substitution wiring (NARROW SCOPE)

The substitution dict for the writer prompt is `writer_context(...)` in `scripts/build/linear_pipeline.py` (the dict passed to `render_phase_prompt(...)` for `linear-write.md`). Around line 1908 (the existing `"IMMERSION_RULE": get_immersion_rule(level.lower(), sequence)` entry — there's a second similar dict around line 2338, update both if both feed the writer prompt) add:

```python
from scripts.pipeline.learner_state import build_learner_state, format_learner_state  # at top of file
...
"LEARNER_STATE": format_learner_state(build_learner_state(level.lower(), sequence)),
```

**Scope boundary inside `linear_pipeline.py`:** you may touch ONLY the two `writer_context` dict entries (one per phase) and the top-of-file import. You may NOT touch `IMMERSION_POLICIES` consumers, `_advisory_immersion_pct`, `_l2_exposure_floor_gate`, `_long_uk_ceiling_gate`, `_component_density_gate`, `_split_immersion_sentences`, or any other function. If you encounter an apparent need to touch a third place, emit `GOAL_ABORT` rather than expand scope.

(There is no `prompt_builder.py` separate from `linear_pipeline.py` in V7. The earlier brief revision referencing it was wrong — `writer_context` in `linear_pipeline.py` is the real wiring point.)

#### 2d. `scripts/audit/checks/learner_state.py` — new audit gate

Two checks in one module. Match the existing audit-check shape (import + class/function naming convention from sibling files in `scripts/audit/checks/`).

**Check 1 — `unknown_vocabulary`:**

For a given module, extract all UK lemmas appearing in body prose (use the existing UK-word extractor that immersion gates use — there is one in `linear_pipeline.py`; do not duplicate the regex). For each lemma:

- Pass if lemma is in `build_learner_state(level, sequence).cumulative_vocabulary`.
- Pass if lemma is declared in this module's `vocabulary.yaml` (parse the `items` list, extract `lemma` field).
- Otherwise: violation.

Threshold:
- Module 1–3 inclusive: severity **WARN** (warm-up grace).
- Module 4+: severity **HARD** (forces plan accuracy).

Reuse `max_unsupported_uk_words` from the existing structural band (`scripts/config.py:get_immersion_structural`) as the tolerance — i.e. a module is flagged only if it has MORE THAN `max_unsupported_uk_words` violations. Do not introduce a new threshold knob.

**Check 2 — `known_grammar_re_explanation`:**

For each grammar topic string in `build_learner_state(level, sequence).known_grammar`, check whether `module.md` re-explains it. Heuristic: a top-level (`##` or `###`) section header whose lowercase substring contains a substring of the lowercase topic. This is intentionally conservative — false negatives are acceptable, false positives are not.

Threshold:
- Level `a1` / `a2`: severity **WARN**.
- Level `b1+`: severity **HARD**.

#### 2e. Audit registry entry

Register both checks in the audit-pipeline registry (locate the actual registry — likely `scripts/audit/__init__.py`, `scripts/audit/audit_module.py`, or a dedicated `scripts/audit/registry.py`). Add the new check to whatever data structure exists; do not invent a new registration mechanism.

### Step 3 — Tests (MANDATORY per `#M-7`)

Two new test files; existing tests must continue to pass.

#### 3a. `tests/test_learner_state_v7_layout.py`

- Setup: temp dir with V7 layout (`curriculum/l2-uk-en/a1/module-a/vocabulary.yaml` + `vocabulary.yaml` containing `items: [{lemma: тест}]`).
- Assert: `_load_vocab("a1", "module-a")` returns `["тест"]`.
- Assert: missing file returns empty list (no exception).
- Assert: `build_learner_state("a1", 3)` accumulates vocab from modules 1 + 2 (not 3 — only modules BEFORE the target).
- Assert: `format_learner_state(...)` output contains the `**Rule:**` footer string when state is non-empty.

#### 3b. `tests/test_audit_learner_state.py`

- Setup: temp module with a known violation (`module.md` containing UK lemma `xyz` not in cumulative vocab + not in declared `vocabulary.yaml`).
- Assert: `unknown_vocabulary` check returns the violation lemma.
- Assert: severity is `WARN` at sequence 2, `HARD` at sequence 5.
- Assert: `known_grammar_re_explanation` returns violations when section header matches a `known_grammar` topic.
- Assert: severity is `WARN` at level `a1`, `HARD` at level `b1`.

### Step 4 — Test suite + ruff

```bash
.venv/bin/pytest tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py -v
.venv/bin/pytest tests/ -x --ignore=tests/e2e 2>&1 | tail -10
.venv/bin/ruff check scripts/pipeline/learner_state.py scripts/build/prompt_builder.py scripts/audit/checks/learner_state.py tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py
```

If any of these fail, fix and re-run. Do not skip. Do not weaken assertions. Do not add `@pytest.mark.skip`. (Pre-submit checklist below restates these prohibitions.)

### Step 5 — Conventional commit

```bash
git add scripts/pipeline/learner_state.py scripts/build/phases/linear-write.md scripts/build/prompt_builder.py scripts/audit/checks/learner_state.py tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py
# plus the registry file you updated in step 2e
git status --short  # verify ONLY these files staged
git commit -m "$(cat <<'CMSG'
feat(learner-state): wire scripts/pipeline/learner_state.py into V7 + new audit gate

Restores v6 student-aware lesson building capability into V7. Path fix for
V7 module layout. New {LEARNER_STATE} placeholder in writer prompt with
HARD-from-m04 rule. New audit check scripts/audit/checks/learner_state.py
with unknown_vocabulary (WARN m01-m03 / HARD m04+) and known_grammar_re_explanation
(WARN a1/a2 / HARD b1+).

Scope: PR1 of the 2-PR split ratified in
docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md.
Does NOT touch IMMERSION_POLICIES, does NOT add plan.targets schema — those
are PR2.

Co-Authored-By: Codex <noreply@openai.com>
CMSG
)"
```

### Step 6 — Push

```bash
git push -u origin codex/pr1-learner-state-v7-wiring-2026-05-13
```

### Step 7 — Open PR

```bash
gh pr create \
  --title "feat(learner-state): wire scripts/pipeline/learner_state.py into V7 + new audit gate" \
  --body-file - <<'EOF'
## Summary

PR1 of the 2-PR split ratified in `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`.

Restores v6 `learner_state.py` student-aware lesson building into V7:

- Path fix: `_load_vocab` now reads V7 layout `curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml`.
- Writer prompt: new `{LEARNER_STATE}` placeholder injected after `## Module Context`, before `## Immersion Rule`.
- Audit: new `scripts/audit/checks/learner_state.py` with `unknown_vocabulary` (WARN m01-m03, HARD m04+) and `known_grammar_re_explanation` (WARN a1/a2, HARD b1+).

## Test plan

- [x] `tests/test_learner_state_v7_layout.py` — V7-layout loader unit tests
- [x] `tests/test_audit_learner_state.py` — both audit checks unit tests
- [x] Full `tests/` suite passes (no new failures)
- [x] `ruff check` clean on all touched files
- [x] No regression on existing immersion / VESUM / wiki-coverage gates

## Out of scope (PR2 will land separately)

- `IMMERSION_POLICIES` static-bands replacement with cumulative-vocab derivation
- `plan.targets` schema extension
- Pattern-frequency model
- Recycle-cadence gate

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

### Step 8 — NO AUTO-MERGE

Do not pass `--allow-merge`, do not call `gh pr merge`, do not enable auto-merge. PR review + merge is the orchestrator's job, not the dispatched worker's. Per `AGENT_NO_MERGE=1` default.

## Pre-submit checklist (MANDATORY — per `AGENTS.md:11-26`)

Verify EVERY item before pushing. Missing one = PR rejected.

- [ ] `.python-version` unchanged (must be `3.12.8`)
- [ ] `.yamllint` and `.markdownlint.json` unchanged (zero modifications)
- [ ] No `status/*.json`, `audit/*-review.md`, or `review/*-review.md` files in the diff
- [ ] No `sys.executable` anywhere in code — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g. `is True` → `isinstance(..., bool)`)
- [ ] Every changed file directly related to this PR
- [ ] Total files changed < 20 (this PR's surgical surface should be ~6 files)
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`

## Scope boundaries (HARD limits)

You may touch ONLY:

- `scripts/pipeline/learner_state.py`
- `scripts/build/phases/linear-write.md`
- `scripts/build/linear_pipeline.py` — **STRICTLY** the two `writer_context` dict entries (add `"LEARNER_STATE": ...`) + top-of-file import. NOTHING else in this file.
- `scripts/audit/checks/learner_state.py` (new file)
- The audit registry file (whichever module registers checks)
- `tests/test_learner_state_v7_layout.py` (new file)
- `tests/test_audit_learner_state.py` (new file)

You may NOT touch:

- `scripts/config.py` (PR2)
- Any other section of `scripts/build/linear_pipeline.py` besides the two `writer_context` dicts (no IMMERSION_POLICIES, no `_advisory_immersion_pct`, no structural gates — those are PR2)
- Plan YAMLs in `curriculum/l2-uk-en/plans/` (PR2 will introduce `plan.targets`)
- Any wiki / immersion gate code (out of scope)
- Decolonization rules / decision cards

If a task in the brief seems to require touching something outside this list, stop and emit `GOAL_ABORT` with `reason="scope-boundary"` rather than improvising.

## Verification deliverable

In the PR body's Test Plan section, include a verbatim block per the verifiable-claims table at the top of this brief. Each row is one command, one output, one raw quote. Example shape:

```
$ grep -n "vocabulary.yaml" scripts/pipeline/learner_state.py
28:    path = CURRICULUM_ROOT / track / slug / "vocabulary.yaml"

$ .venv/bin/pytest tests/test_learner_state_v7_layout.py tests/test_audit_learner_state.py -v 2>&1 | tail -3
============================== 9 passed in 0.42s ==============================
```

A PR description with paraphrased claims ("I added the placeholder", "tests pass") and no raw output is treated as hallucinated and will be sent back for re-verification.

---

*Authority: `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` § "PR1 — Restore learner-state V7 wiring".*
*Per `#M-4` (deterministic-over-hallucination) and `#DISPATCH-BRIEF-CHECKLIST`.*
