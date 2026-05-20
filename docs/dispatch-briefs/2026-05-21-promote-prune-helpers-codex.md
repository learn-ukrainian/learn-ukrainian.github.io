# Dispatch brief — paired promote-module + prune-forensics helpers

**Agent:** codex
**Model:** gpt-5.5 (default)
**Mode:** workspace-write (with `--worktree` enforced)
**Effort:** xhigh
**Task ID:** `promote-prune-helpers-20260521`

## Why now

Handoff §7 Decision 2 (2026-05-20) locked this scope after the operator's correction *"i think we should copy all forensics, we can always clean them up when the module is finished."* The two tools are paired in **the same PR** so "later = tool call" not "later = never." Without this pair, a green V7 build's artifacts sit on a `build/<level>/<slug>-<stamp>` branch (#M-10 auto-commit) and never reach main's `curriculum/{level}/{slug}/` tree.

Today's smoke builds (lit/natalka-poltavka, hist/trypillian-civilization) produced 5 build worktrees + branches on disk that this helper can be tested against — none reached green, but they exercise the failure paths (partial artifacts, missing module.md, etc.).

## Verifiable claims this work must produce

Per `docs/best-practices/deterministic-over-hallucination.md` and #M-4: every claim below must be tool-backed in your PR body. List the command + raw output for each:

| Claim | Deterministic tool |
|---|---|
| "promote_module.py exists at scripts/sync/" | `ls -la scripts/sync/promote_module.py` |
| "prune_module_forensics.py exists at scripts/sync/" | `ls -la scripts/sync/prune_module_forensics.py` |
| "promote --help renders" | `.venv/bin/python scripts/sync/promote_module.py --help` |
| "prune --help renders" | `.venv/bin/python scripts/sync/prune_module_forensics.py --help` |
| "all new tests pass" | `.venv/bin/python -m pytest tests/sync/test_promote_module.py tests/sync/test_prune_module_forensics.py -v` (final summary line) |
| "full suite green" | `.venv/bin/python -m pytest` (final summary line) |
| "ruff clean" | `.venv/bin/ruff check scripts/sync/promote_module.py scripts/sync/prune_module_forensics.py tests/sync/` |
| "PR opened" | `gh pr view <N> --json url` raw URL |

## Specification — promote_module.py

`scripts/sync/promote_module.py`

### Behavior

After a green V7 build the artifacts live on a `build/<level>/<slug>-<stamp>` branch (created by `v7_build.py::_persist_build_artifacts` per #M-10). This script copies BOTH the lesson source AND the forensics from that branch into the canonical curriculum tree on the current branch (typically main).

### Source set (from build branch, in the build worktree's `curriculum/{level}/{slug}/`)

**Lesson source — REQUIRED. Promotion FAILS if any of these are missing:**

- `module.md`
- `activities.yaml`
- `vocabulary.yaml`
- `resources.yaml`

**Lesson MDX — REQUIRED:**

- `starlight/src/content/docs/{level}/{slug}.mdx`

**Forensics — copied if present; absence is logged but not fatal:**

- `writer_prompt.md`
- `writer_output.raw.md`
- `hermes.write.jsonl`
- `writer_tool_calls.json`
- `python_qg.json`
- `llm_qg.json`
- `knowledge_packet.md`
- `implementation_map.json`

### Destination (on current branch)

- Lesson source → `curriculum/{level}/{slug}/<file>`
- MDX → `starlight/src/content/docs/{level}/{slug}.mdx`
- Forensics → `curriculum/{level}/{slug}/<file>` (sit alongside lesson source until prune)

### CLI surface

```
promote_module.py --build-branch <ref>           # explicit ref, e.g. build/a1/my-morning-20260520-123456
promote_module.py --worktree <path>              # use a worktree dir (HEAD ref read by script)
promote_module.py --latest --level a1 --slug my-morning   # find most-recent build/a1/my-morning-* branch
promote_module.py ... --dry-run                  # show diff, write nothing, exit 0
promote_module.py ... --no-commit                # write files, skip git commit
promote_module.py ... --message "..."            # override default commit message
```

Default commit message: `feat(content): promote {level}/{slug} from {build-branch}`

### Idempotency

- If `curriculum/{level}/{slug}/module.md` already exists with content-hash matching the build branch's version → skip with `OK already-promoted` (exit 0, no commit).
- If lesson source partially matches (e.g. someone hand-edited 2 files) → abort with diff summary, exit non-zero. Add `--force` to override.

### Required artifact contract

If any of the four lesson source files is missing on the build branch → exit 2 with the missing-file list. Do NOT partially promote.

### Implementation notes

- Use `subprocess.run(["git", "-C", main_dir, "show", f"{branch}:{path}"], capture_output=True)` to read files from the build branch — works regardless of whether the build worktree is still on disk. Falls back to reading from disk if the branch ref has been deleted but a worktree still exists.
- The list of "lesson source" and "forensics" file names should live as module-level frozensets at the top of `promote_module.py` so `prune_module_forensics.py` can import them — single source of truth.
- All file writes go through a single `_write_atomically(path, content)` helper so a crash mid-promote can't leave a partial state.
- `--latest` is implemented via `git for-each-ref --sort=-creatordate refs/heads/build/{level}/{slug}-* --format='%(refname:short)'`.

## Specification — prune_module_forensics.py

`scripts/sync/prune_module_forensics.py`

### Behavior

When a module's status flips to `locked` (or on manual operator invocation), remove the in-curriculum forensics that the promote helper copied in. Keeps `module.md`, the three YAMLs, and the MDX. Leaves `_orchestration/runs/{stamp}/` and `_orchestration/{level}/{slug}/runs/` untouched (full history lives in those run archives per #2151 / PR #2162).

### CLI surface

```
prune_module_forensics.py --level a1 --slug my-morning           # one module, requires locked status
prune_module_forensics.py --all                                  # every locked module
prune_module_forensics.py ... --dry-run                          # show plan, exit 0
prune_module_forensics.py ... --no-commit                        # delete, skip git commit
prune_module_forensics.py ... --force                            # bypass status check
```

Default commit message: `chore(content): prune forensics for locked {level}/{slug}`

### Status detection

Read `curriculum/{level}/{slug}/status/{slug}.json` if present. Expected schema (verify against an existing status file in the repo before writing the helper):

```json
{ "status": "locked" | "ready" | "draft" | ..., "..." }
```

If the file is missing OR `status` is not `"locked"` → refuse with a clear message, exit non-zero. `--force` bypasses.

### Idempotency

- If a forensics file isn't present → log "already pruned, skip", continue.
- If NO forensics files were present at all → exit 0 with `OK nothing-to-prune`.

### Required imports

Import the `FORENSICS_FILES` frozenset from `promote_module.py` so a future scope change to "what counts as forensics" needs one edit, not two.

## Specification — tests

`tests/sync/test_promote_module.py` and `tests/sync/test_prune_module_forensics.py`

Cover at minimum:

### promote_module tests

1. `test_promote_copies_lesson_source_and_forensics` — given a fake build branch with all expected files, after promote the curriculum dir and MDX path contain the expected content.
2. `test_promote_fails_if_lesson_source_incomplete` — build branch missing `module.md` → exit 2, no files written.
3. `test_promote_idempotent_on_matching_content` — re-running on already-promoted module exits 0 with no commit.
4. `test_promote_aborts_on_partial_match_without_force` — build branch's `module.md` differs from in-tree → abort, exit non-zero.
5. `test_promote_dry_run_writes_nothing` — `--dry-run` produces no file changes and no commit.
6. `test_promote_resolves_latest_branch` — given multiple `build/a1/foo-*` refs in different stamps, `--latest --level a1 --slug foo` picks the highest stamp.

### prune_module_forensics tests

1. `test_prune_removes_forensics_keeps_lesson_source` — given a curriculum dir with both, prune removes forensics, keeps lesson source + MDX.
2. `test_prune_refuses_when_status_not_locked` — status `draft` → exit non-zero.
3. `test_prune_force_bypasses_status_check` — `--force` works regardless of status.
4. `test_prune_idempotent` — re-run on already-pruned module exits 0.
5. `test_prune_all_skips_non_locked` — `--all` only touches locked modules; draft/ready modules untouched.

### Test fixtures

Use `pytest tmp_path` + a helper that initializes a tiny git repo with one `build/level/slug-stamp` branch containing seeded files. Don't rely on the live repo state.

## Pre-submit checklist (MANDATORY per AGENTS.md:11-26)

1. `git worktree add .worktrees/codex/promote-prune-helpers -b feat/promote-prune-helpers` (from main project dir). The new branch-switch guard hook (PR #2167) will refuse `git checkout -b` in the main worktree — `git worktree add -b` is explicitly allowed.
2. `cd .worktrees/codex/promote-prune-helpers`
3. Write `scripts/sync/promote_module.py`, `scripts/sync/prune_module_forensics.py`, `tests/sync/__init__.py` (if needed), `tests/sync/test_promote_module.py`, `tests/sync/test_prune_module_forensics.py`.
4. `.venv/bin/python -m pytest tests/sync/ -v` → all new tests pass.
5. `.venv/bin/python -m pytest` → full suite green.
6. `.venv/bin/ruff check scripts/sync/promote_module.py scripts/sync/prune_module_forensics.py tests/sync/` → clean.
7. `git add scripts/sync/promote_module.py scripts/sync/prune_module_forensics.py tests/sync/` + targeted commit. Conventional message: `feat(sync): paired promote-module + prune-forensics helpers`.
8. `git push -u origin feat/promote-prune-helpers`.
9. `gh pr create --title "feat(sync): paired promote-module + prune-forensics helpers" --body ...` — DO NOT auto-merge.

## Hard constraints

- ONE PR for both tools. They must be paired per the operator's 2026-05-20 direction.
- Do NOT touch v7_build.py, linear_pipeline.py, or any pipeline code in this PR.
- Do NOT delete the existing `.worktrees/builds/*` test data.
- Do NOT add a "promote on success" hook to v7_build.py (separate decision; out of scope here).
- All new file content goes through the worktree first; never write to the main project dir directly.

## Test data already on disk (for your manual verification)

The five build worktrees + branches from today's smoke builds:

- `build/a2/aspect-concept-20260519-204548` (oldest, partial state)
- `build/hist/trypillian-civilization-20260520-182509` (plan-phase fail; empty artifact set)
- `build/lit/natalka-poltavka-20260520-{182758,182859,183940}` (writer-phase fail; partial artifacts)

None of these are GREEN builds, so `promote_module.py` should REFUSE to promote any of them (missing lesson source). Use this as your "fails-correctly" smoke test against real data. Don't delete these worktrees.

## Coverage signals

After landing, the operator will run the helpers manually against the next real green seminar/CORE build to validate end-to-end. This PR ships the tooling + tests; production validation happens separately.
