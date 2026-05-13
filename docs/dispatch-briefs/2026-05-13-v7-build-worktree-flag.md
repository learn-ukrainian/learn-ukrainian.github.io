---
date: 2026-05-13
agent: codex
mode: danger
worktree: true
effort: high
task_id: v7-build-worktree-flag-2026-05-13
hard_timeout: 3600
silence_timeout: 1500
references:
  - scripts/build/v7_build.py  # target
  - AGENTS.md  # pre-submit checklist (lines 11-26 verbatim)
  - claude_extensions/agents/curriculum-maintainer.md  # encoded rule; this is the implementation
  - PR #1949  # safety net (gitignore + rule encoded); land BEFORE this dispatch is reviewed
---

# Dispatch — Add `--worktree` flag to `scripts/build/v7_build.py`

## Goal

Add an ergonomic `--worktree [PATH]` flag to `scripts/build/v7_build.py` so a V7 module build runs in an isolated git worktree instead of polluting the main project tree. PR #1949 already (a) gitignored the build telemetry artifacts and (b) encoded the discipline rule in the agent definition. This PR is the **mechanical implementation** of the rule.

This is mechanical, single-file Python work (~80-150 LOC + tests + 1 doc update). Pattern matches `scripts/delegate.py --worktree` which already does the same thing for agent dispatches — study it for parameter handling, default-path derivation, branch naming, and error handling.

## Background

Today `v7_build.py` writes module outputs (`activities.yaml`, `module.md`, `resources.yaml`, `vocabulary.yaml` + the assembled MDX at `starlight/src/content/docs/{level}/{slug}.mdx` + 5 telemetry files) directly into the current working tree. If invoked from the main project dir, the user must stash/commit/discard before any subsequent `git pull` or merge. The 2026-05-13 stash-and-lose incident (dropped stash@{0} containing the validated `a1/my-morning` build output) is the recurrence-prevention motivation.

The script already has `--out PATH` (custom output dir) — that's NOT the same thing. `--out` redirects the output path but doesn't create or manage a worktree. `--worktree` should be a higher-level orchestration flag: "create a worktree, set up git, run me inside it, exit with a summary."

## Design (read before coding)

### Interface

```
v7_build.py LEVEL SLUG [--worktree [PATH]] [other existing flags]
```

- `--worktree` with no value: auto-derive both path and branch.
  - Path:   `.worktrees/builds/{level}-{slug}-{YYYYMMDD-HHMMSS}/`
  - Branch: `build/{level}/{slug}-{YYYYMMDD-HHMMSS}`
- `--worktree PATH`: use PATH for the worktree location.
  - Branch is still auto-derived (matches PATH's basename if possible, else `build/{level}/{slug}-{YYYYMMDD-HHMMSS}`).
  - PATH may be absolute or relative-to-repo-root.

The TIMESTAMP suffix is mandatory (not optional) — it makes parallel builds of the SAME module trivially safe. UTC, second-precision.

### Behavior

1. Pre-check: cwd must be inside the repo. If not, error + exit 2.
2. Generate the path + branch per the rules above.
3. Resolve the base commit (default `origin/main`; respect `--base` if added later, but don't add `--base` in this PR).
4. `git fetch origin` (with `--max-time` equivalent — if it times out, log + still proceed against local main as a fallback, mirroring `delegate.py` behavior).
5. `git worktree add -b {branch} {path} {base}` (or `--detach` then `--track` if branch already exists — investigate `delegate.py`'s approach).
6. `os.chdir(path)` (or pass it through to subprocess calls via `cwd=` — pick whichever is consistent with the existing flow; the existing module_dir handling in `v7_build.py` suggests `cwd=` is the idiom here).
7. Run the existing build flow exactly as before — PROJECT_ROOT auto-resolves to the worktree root, so `_default_module_dir` lands at `{worktree}/curriculum/l2-uk-en/{level}/{slug}/` which is what we want.
8. On completion (success OR failure), print a final summary to stdout:
   ```
   BUILD_WORKTREE=<absolute-path>
   BUILD_BRANCH=<branch-name>
   BUILD_BASE=<base-sha-shortname>
   BUILD_RESULT=<success|failed|...>
   Next steps if successful:
     cd <path>
     git status                              # review the diff
     git add curriculum/l2-uk-en/{level}/{slug}/*.yaml starlight/src/content/docs/{level}/{slug}.mdx
     git commit -m "..."
     git push -u origin <branch>
     gh pr create --title "..." --body "..."
   Next steps if you want to discard:
     git worktree remove <path>
     git branch -D <branch>
   ```
9. Exit with the underlying build's exit code (don't mask a build failure with `0` just because the worktree was created).

### Error handling

- If the worktree path already exists (e.g. a previous failed build at the same timestamp — unlikely with second precision but possible): error + exit 3 with a clear message ("Worktree path {path} exists; remove with `git worktree remove {path}` or pass a different `--worktree PATH`").
- If `git worktree add` fails (branch already exists, permission error, etc.): propagate stderr verbatim + exit 4.
- If the build crashes mid-run: DON'T auto-remove the worktree. The user may want to inspect partial state to debug. Print the BUILD_RESULT=failed summary and exit non-zero.

### What NOT to do

- ❌ Don't add `--no-worktree` as an opt-out flag yet. The default stays "no worktree" for backward compat (the agent rule says "must use worktree" but the script default doesn't enforce that yet — this PR is opt-in plumbing).
- ❌ Don't modify `--out` behavior. `--worktree` and `--out` are orthogonal: `--worktree` creates the worktree; the existing `--out` (if also passed) overrides the output dir WITHIN the worktree. Document that `--worktree --out` is a power-user combo.
- ❌ Don't add a separate `scripts/build/build-in-worktree.sh` wrapper. We're putting it in the Python script directly — one entry point.
- ❌ Don't auto-cleanup successful worktrees. The user reviews + commits + opens a PR + then manually `git worktree remove`. Auto-cleanup would defeat the purpose (losing the build output).
- ❌ Don't try to be clever about reusing existing worktrees. Each invocation = fresh worktree. Simpler mental model.

## Inputs available

| Resource | Path |
|---|---|
| Target | `scripts/build/v7_build.py` (study lines 54-60 `_default_module_dir` + `_resolve_output_dir`, lines 130-200 build flow, line 381 `writer_cwd`) |
| Pattern precedent | `scripts/delegate.py --worktree` impl + `scripts/agent_runtime/` worktree handling |
| Existing agent rule | `claude_extensions/agents/curriculum-maintainer.md:164` ("V7 builds MUST run in a worktree") — encoded in PR #1949 |
| Gitignore for telemetry | `.gitignore:264-268` (V7 build telemetry block, encoded in PR #1949) |
| Test fixture pattern | Existing tests in `tests/test_v7_build.py` (or wherever v7_build is tested — find via `grep -rn v7_build tests/`) |

## Deliverables

1. **`scripts/build/v7_build.py`** — `--worktree [PATH]` flag + `_setup_worktree()` helper + summary printer + error handling per the design above.
2. **`tests/test_v7_build_worktree.py`** (or extend existing) — parametrized tests:
   - `--worktree` without PATH: derives path/branch from level+slug+timestamp; calls `git worktree add` with expected args.
   - `--worktree PATH`: uses PATH; branch still auto-derived.
   - Path collision: errors cleanly with exit 3.
   - Worktree-add failure: propagates stderr.
   - Build success: prints `BUILD_RESULT=success` summary; preserves worktree.
   - Build failure: prints `BUILD_RESULT=failed`; does NOT auto-remove worktree; exits non-zero.
   - Mock `subprocess.run` for the `git worktree add` call; mock the build subprocess so the test doesn't actually run a real build.
3. **`CLAUDE.md`** — update the "Build pipeline (V7 only)" row in the Power Features / Reference Docs table (or wherever the current build-invocation example lives) to show `--worktree` as the recommended invocation pattern. One-line edit.
4. **Conventional commit + PR** — title `feat(v7_build): --worktree flag for isolated module builds`.

## #M-4 verifiable claims (paste raw output, never "I checked X")

| Claim | Required tool evidence |
|---|---|
| "Help text shows --worktree" | `.venv/bin/python scripts/build/v7_build.py --help` raw output, with the `--worktree` block visible |
| "Tests pass" | `.venv/bin/python -m pytest tests/test_v7_build_worktree.py -v` final summary line raw (`N passed in M.MMs`) |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/v7_build.py tests/test_v7_build_worktree.py` "All checks passed!" raw |
| "Worktree path collision errors cleanly" | The test's captured stderr from the collision case, quoted in the commit body |
| "Backward-compat: existing flags still work" | `.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run` — runs to completion without `--worktree` and produces the same dry-run output it did before |

## 8-step process (numbered, no exceptions)

1. **Worktree setup for your own dispatch.** `git fetch origin && git worktree add -b codex/v7-build-worktree-flag-2026-05-13 .worktrees/dispatch/codex/v7-build-worktree-flag-2026-05-13 origin/main` — work inside this worktree exclusively. (Your `delegate.py --mode danger --worktree` invocation already arranges this; document the path in the commit body.)
2. **Read first, code second.** Study `scripts/build/v7_build.py` end-to-end (it's <500 LOC; read it all). Study `scripts/delegate.py --worktree` for pattern. Sketch the changes BEFORE writing.
3. **Implement** per the design above. Single coherent diff to `v7_build.py` + new test file + 1-line CLAUDE.md edit.
4. **Run tests** — `.venv/bin/python -m pytest tests/test_v7_build_worktree.py tests/test_v7_build.py -v` (the latter if it exists — keeps regression coverage).
5. **Ruff** — `.venv/bin/ruff check scripts/build/v7_build.py tests/test_v7_build_worktree.py`.
6. **Manual smoke test** — `.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run --worktree`. Should create `.worktrees/builds/a1-my-morning-{stamp}/`, run dry-run successfully inside it, print summary, exit 0. Then `git worktree remove .worktrees/builds/a1-my-morning-{stamp}/` to clean up after the test.
7. **Commit + push + open PR** — conventional message; reference PR #1949 as the prerequisite.
8. **DO NOT auto-merge.** Orchestrator reviews.

## Pre-submit checklist — `AGENTS.md:11-26` MANDATORY (paste verbatim, verify EVERY box before push)

- [ ] `.python-version` unchanged (must be `3.12.8`)
- [ ] `.yamllint` unchanged
- [ ] `.markdownlint.json` unchanged
- [ ] No `status/*.json` files in the diff
- [ ] No `audit/*-review.md` files in the diff
- [ ] No `review/*-review.md` files in the diff
- [ ] No `sys.executable` anywhere in code (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g., `is True` → `isinstance(..., bool)`)
- [ ] Every changed file is directly related to the `--worktree` flag
- [ ] Total files changed < 20 (this should be ~3-4: v7_build.py, test file, CLAUDE.md, maybe AGENTS.md note)
- [ ] Code runs without `NameError`, `KeyError`, or `ImportError`

## Anti-patterns specific to this work

- ❌ **Don't run a REAL `v7_build` in tests.** Mock `subprocess.run` for the `git worktree add` call AND mock the actual writer subprocess invocation. Tests should run in <5 seconds.
- ❌ **Don't `os.chdir` if the existing code uses `cwd=` parameter passing.** Match the existing idiom. Mixing chdir + cwd= leads to subtle bugs.
- ❌ **Don't bundle this with `--no-worktree` / making worktree default.** Two separate concerns. This PR is opt-in plumbing; defaulting is a follow-up after we've used it on a few real builds.
- ❌ **Don't break the existing `--out PATH` flag.** It must keep working. If `--worktree --out` is both passed, `--out` is interpreted RELATIVE to the worktree root, not the main project root. Document this in `--help`.
- ❌ **Don't bypass blocking CI.** Per #M-0.5: pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint = ALL blocking. Advisory `review/review` (Gemini-Dispatch) is the only non-blocking failure.

## Acceptance

PR merged when:

1. `--worktree` flag works in the manual smoke test (path + branch derived, dry-run completes inside worktree, summary printed, exit 0).
2. All blocking CI checks green.
3. Backward compat: existing `--dry-run`, `--out`, `--writer` flags still work without `--worktree`.
4. CLAUDE.md updated to show worktree pattern as recommended.
5. Worktree on failure is NOT auto-removed (user inspects).
