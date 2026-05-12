# Codex dispatch brief — yaml_activities parser handles 'unjumble' activity type

> **Issue:** #1923
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/yaml-activities-unjumble-2026-05-14/`
> **Base:** `origin/main` (currently `1d57748f6f`)
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/yaml-activities-unjumble-2026-05-14 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Fix the silent-skip bug in `scripts/yaml_activities.py` where an `unjumble` activity authored as a list (instead of a string) causes `'list' object has no attribute 'split'` and the activity is **silently dropped from the assembled MDX**.

Two structural deliverables:
1. **Make the parser work** for whatever shape the writer is emitting today (most likely a list of tokens, since unjumble activities are intrinsically token-sequence games — the list-shape is probably MORE correct than the legacy string-shape).
2. **Eliminate silent drops** entirely. Any future shape mismatch should either (a) be handled with a clear conversion, OR (b) raise an exception with the failing field name + activity id. **Never silently skip.**

After this PR merges, the assembler on `a1/my-morning` should produce an MDX containing activity 6 (unjumble) rather than skipping it.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Failing activity shape identified" | open `curriculum/l2-uk-en/a1/my-morning/activities.yaml`, locate activity 6 (unjumble), show its `items` / target field structure | quote the relevant YAML block |
| "Parser handles list shape" | new fixture test asserts a list-shape unjumble round-trips through the parser into MDX | quote the test's input + assertion |
| "Silent skip eliminated" | grep for `Skipping activity` in `scripts/yaml_activities.py` shows no path that silently drops; failures raise or warn loudly | quote the before/after of the offending block |
| "Tests pass" | `.venv/bin/pytest tests/test_yaml_activities*.py tests/test_*activity*.py` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/yaml_activities.py` | quote final line |
| "End-to-end repro" | re-run `assemble_mdx` on `curriculum/l2-uk-en/a1/my-morning/` against the assembler in the worktree; show that activity 6 IS now in the output MDX | quote the activity-6 block from the regenerated MDX |

---

## Reproducer

From the previous session, `assemble_mdx` on `curriculum/l2-uk-en/a1/my-morning/` emitted:

```
⚠️ Skipping activity 6 (type='unjumble'): 'list' object has no attribute 'split'
```

Activity 6 in `curriculum/l2-uk-en/a1/my-morning/activities.yaml` (read-only reference in MAIN checkout) is the live failing input.

**Step 1 of investigation:** read activity 6 to see whether the field that the parser calls `.split()` on is a list. Most likely the parser expects a string like `"я вмиваюся вранці"` and calls `.split()` to get tokens; the writer is emitting `["я", "вмиваюся", "вранці"]` (already tokenized).

**Step 2:** locate the offending code in `scripts/yaml_activities.py`:

```bash
grep -n 'split\|unjumble\|Skipping activity' scripts/yaml_activities.py
```

---

## Fix shape

Two acceptable approaches; pick whichever is cleaner given existing schema:

**Approach A — accept both shapes (tolerant parser):**
```python
def _tokens_from_unjumble_target(target) -> list[str]:
    if isinstance(target, list):
        return [str(t) for t in target]
    if isinstance(target, str):
        return target.split()
    raise TypeError(f"unjumble target must be str or list, got {type(target).__name__}")
```

**Approach B — canonicalize at YAML load:**
Add a schema validator (or migrate the YAML so `items` is always a list) and parse uniformly downstream.

**Approach A is recommended** — minimal blast radius, doesn't require migrating existing fixtures.

**Critical: do NOT keep silent-skip as fallback.** If the type is unrecognized, raise. The user explicitly flagged this pattern as a smell:

> "Pattern smell: assembler should not silently drop activities; should emit telemetry as hard signal." (handoff brief)

Replace `print("⚠️ Skipping activity ...")` with `raise` OR `logger.error(...)` + re-raise. Failing loudly is better than producing an incomplete MDX.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/yaml-activities-unjumble-2026-05-14 .worktrees/dispatch/codex/yaml-activities-unjumble-2026-05-14 origin/main
   ```
2. **Inspection** — read activity 6 in MAIN checkout's `curriculum/l2-uk-en/a1/my-morning/activities.yaml`. Quote the exact shape in the PR body.
3. **File-level work** — fix `scripts/yaml_activities.py`. Convert silent-skip paths into either tolerant parsers or loud raises. Aim for minimal LOC.
4. **Test suite** — add fixtures:
   - List-shape unjumble round-trips to expected MDX.
   - String-shape unjumble (legacy) still works.
   - Malformed (e.g. `target: 42`) raises with a clear message.
   Then run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/yaml-activities-unjumble-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_yaml_activities*.py tests/test_*activity*.py -x
   ```
   Quote final summary line raw.
5. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/yaml_activities.py
   ```
   Quote final line raw.
6. **Regression check** — re-run `assemble_mdx` on `a1/my-morning/` from the worktree. Quote the activity-6 block from the regenerated MDX in the PR body. Show that the previous warning no longer appears.
7. **Commit** — conventional message: `fix(yaml_activities): handle list-shape unjumble target + replace silent skip with loud raise`. Reference `Closes #1923`.
8. **Push:** `git push -u origin codex/yaml-activities-unjumble-2026-05-14`.
9. **Open PR** via `gh pr create` with body containing reproducer, fix shape rationale, test summary, ruff summary, `Closes #1923`.
10. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- Silent-skip paths preserved (must be replaced with raise or loud log + re-raise).
- Tests for both string AND list shapes not both passing.
- Ruff failing.
- A behavior change for non-unjumble activity types (gap, multiple-choice, etc.).

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No `status/*.json` / `audit/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] Every changed file directly related to this fix
- [ ] Total files changed < 10

---

## Related

- Predecessor handoff: `docs/session-state/2026-05-13-night-wiki-obligations-e2e-brief.md`
- Live failing input: `curriculum/l2-uk-en/a1/my-morning/activities.yaml` (activity 6, type=unjumble)
- Companion fixes in flight: #1921 / #1922 (linear_pipeline VESUM + parser) — separate dispatch
