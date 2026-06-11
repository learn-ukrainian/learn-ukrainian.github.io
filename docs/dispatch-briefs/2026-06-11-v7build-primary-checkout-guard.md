# Dispatch brief — Fix #2884: v7_build persist can commit to MAIN (primary-checkout guard)

**Owner lane:** infra/build safety. **Issue:** #2884 [infra][HIGH]. **Agent:** codex (gpt-5.5, xhigh).
**Mode:** danger + worktree. **No auto-merge.** **/code-review** after (touches pipeline logic).

## Incident (already forensically established in #2884)
A folk `kalendarna-obriadovist-zvychai` build ran in the **primary checkout** and its
`_persist_build_artifacts` (result=failed) ran `git add -A && git commit` there → commit
`a2792f2a42` on local main, sweeping up unrelated files (`docs/dispatch-briefs/2026-06-09-worktree-reaper.md`
+ `start-claude.sh`). Local main diverged, ff blocked. Recovery needed reflog salvage
(`salvage/main-pollution-a2792`). Recurrence risk is LIVE (folk runs kalendarna builds).

## Root cause + the trap you MUST respect (added by Claude 2026-06-11)
`scripts/build/v7_build.py::_persist_build_artifacts` (L428) does
`git -C <worktree.path> add -A` then `commit` (L464-487) with **no guard** that `<worktree.path>`
is a real worktree and not the primary checkout.

**CRITICAL TRAP — do NOT "just require --worktree":**
- `main()` (L1049): `if args.worktree is not None: return _run_in_worktree(...)`.
- `_run_in_worktree` (L501) sets up the worktree, then **re-invokes the child**
  `scripts/build/v7_build.py` with `--worktree` **stripped** (`_strip_worktree_args`, L525) and
  `cwd=worktree.path`. So the **child legitimately runs WITHOUT `--worktree`, in-place inside the
  worktree.** A blanket "require --worktree / error when args.worktree is None" would **break the
  child**.
- Therefore the correct invariant is **NOT** "require --worktree". It is:
  **"NEVER run `git add`/`commit` when the target dir's git top-level is the PRIMARY CHECKOUT."**
  In-place builds are fine *inside* `.worktrees/…`; they are the bug *in the primary checkout*.

## Helpers that already exist (reuse, do not reinvent)
- `scripts/orchestration/reap_worktrees.py`:
  - `primary_checkout_root(repo_root: Path) -> Path` (L101) — resolves the primary checkout that
    owns the shared `.git`, even when called from inside a worktree (reads the `.git` gitdir file).
  - `_is_under_worktrees(repo_root, path) -> bool` (L191) — True iff path resolves under `.worktrees/`.
    (Private — promote to a public name like `is_under_worktrees` if you import it, and update the
    one internal caller.)
- `scripts/build/run_archive.py`: child invocations carry env key `V7_RUN_ARCHIVE_CONTEXT`
  (`ENV_KEY`, L17; set via `archive.env()` at v7_build.py L532). Presence ⇒ this process is a
  worktree-child; absence ⇒ top-level. Use this to distinguish top-level from child in the main()
  guard (fix 2) so you don't false-positive on the child.

## Three fixes (defense in depth — all three, with tests)
**Fix 1 — primary-checkout commit guard (LOAD-BEARING).**
In `_persist_build_artifacts`, before staging, resolve the git top-level of `worktree.path`
(`git -C <path> rev-parse --show-toplevel`) and compare to
`reap_worktrees.primary_checkout_root(worktree.repo_root)`. If they are the same path → **hard
error** (raise / nonzero), do NOT commit. This must be a real refusal, not a warning. (Persist's
*own* errors are currently swallowed as best-effort — this guard must NOT be swallowed into a
silent "return False"; committing to main is worse than crashing. Make the guard a distinct
exception that propagates, or print a loud error and return a sentinel the caller treats as fatal.)
Belt-and-suspenders: also assert the path is a separate worktree (top-level != primary), which
covers explicit `--worktree /custom/path` outside `.worktrees/` correctly (still a real worktree).

**Fix 2 — top-level must not build in the primary checkout without a worktree.**
In `main()`, when `args.worktree is None` AND `V7_RUN_ARCHIVE_CONTEXT` is NOT set (i.e. this is a
top-level invocation, not the child) AND cwd's git top-level == primary checkout → **hard error**
with a clear message: "Refusing to run v7_build in the primary checkout; pass --worktree (artifacts
are committed and must land in an isolated worktree). See #2884." Do not auto-create silently — an
explicit error is more predictable. The child path (env set) and any real-worktree cwd are unaffected.

**Fix 3 — scope the persist stage to artifact paths, never `git add -A`.**
Replace `git add -A` (L465) with an explicit add of the build-artifact globs/paths that
`_persist_build_artifacts` is meant to capture (writer_prompt.md, writer_output.raw.md,
hermes.write.jsonl, writer_tool_calls.json, knowledge_packet.md, implementation_map.json, the
`module.md`+yaml siblings under `curriculum/l2-uk-en/<level>/<slug>/…`, the run-archive dir, and the
assembled MDX under `starlight/…` if present). Use `git -C <path> add -- <paths>` with the set that
exists; tolerate missing paths (don't fail if a phase didn't produce one). This ensures that even
inside a worktree the commit can never sweep unrelated/un-ignored files.

## Tests (new — `tests/test_v7_build_persist_guard.py`)
Use `tmp_path` + a real `git init` scratch repo + a `.worktrees/` worktree to assert:
1. **Refuses primary checkout:** calling the persist on a path whose git top-level == primary
   checkout raises / returns fatal and creates **no commit**. (Reproduces the a2792 incident.)
2. **Allows real worktree child:** persist on a path under `.worktrees/…` commits successfully.
3. **Scoped add:** an unrelated untracked file in the worktree is NOT included in the persist commit
   (only artifact paths are). Assert via `git show --stat`.
4. **main() top-level guard:** top-level invocation (no `V7_RUN_ARCHIVE_CONTEXT`, no `--worktree`,
   cwd == primary) exits nonzero with the guard message; child invocation (env set) does not trip it.

## #M-4 — verifiable claims (quote raw output)
| Claim | Check |
|---|---|
| Guard refuses primary checkout | new test 1 output: `1 passed` line + assert no commit |
| Child still works | new test 2 output |
| Scoped add | new test 3 `git show --stat` lacks the unrelated file |
| Full suite | `.venv/bin/pytest tests/test_v7_build_persist_guard.py` final summary line raw |
| No regression | `.venv/bin/pytest tests/ -k "v7_build or worktree or reap" ` final summary raw |
| Lint | `.venv/bin/ruff check scripts/build/v7_build.py tests/test_v7_build_persist_guard.py` final line |

## Numbered steps
1. `git worktree add` off `origin/main` (dispatch enforces).
2. Implement fixes 1–3 in `scripts/build/v7_build.py` (+ promote `_is_under_worktrees` if imported).
3. Add `tests/test_v7_build_persist_guard.py` (4 cases above).
4. `.venv/bin/pytest tests/test_v7_build_persist_guard.py` and the `-k` regression slice; paste raw.
5. `.venv/bin/ruff check` the edited files; paste raw.
6. Commit (conventional): `fix(v7): guard persist against primary-checkout commits + scope add [#2884]`.
7. `git push -u origin <branch>`.
8. `gh pr create` — body: the trap explanation + raw test/lint evidence + "Closes #2884". **NO auto-merge.**

## Gotchas
- GitHub graphql intermittently 401s — if `gh pr create` flakes use REST `gh api -X POST repos/.../pulls`.
  Only required check = `Test (pytest)`.
- Do NOT touch `codex/2888-a2-*` worktrees/PRs (A2 beta lane) or
  `.worktrees/dispatch/codex/word-atlas-wiktionary-etym` (a concurrent Codex dispatch).
- `_persist_build_artifacts` keeps `--no-verify` + `--allow-empty` semantics; only the *staging* and
  the *guard* change. Keep its #M-10 forensic purpose intact (artifacts must still survive worktree removal).
