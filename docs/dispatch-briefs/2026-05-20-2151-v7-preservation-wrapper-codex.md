# Dispatch — #2151 V7 preservation wrapper

**Issue:** #2151 — [impl] V7 preservation wrapper not yet shipped — spec landed but copy-on-phase-boundary missing.
**Target:** Codex.
**Mode:** danger (with --worktree).
**Effort:** xhigh.
**Severity:** MED (Tier 1 from WORKSTREAMS).
**Estimated:** ~half-day per the issue.

## TL;DR

PR #2149 shipped `docs/best-practices/pipeline/v7-build-preservation.md` as the canonical spec. The implementation is missing. Build the wrapper that copies orchestration artifacts from the build worktree to `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/` on every phase boundary AND on terminal outcome.

This complements (does NOT replace) the artifact-preservation auto-commit that landed in `feat(v7_build): auto-commit build artifacts to the build branch` (commit `c9a29a2420`, MEMORY #M-10). That commit preserves the end-state on the build branch. THIS wrapper preserves intermediate-state phase snapshots and correction iterations under a stable archive path.

## Spec — read these FIRST

1. `docs/best-practices/pipeline/v7-build-preservation.md` (517 lines, canonical).
2. `docs/architecture/v7-pipeline.md` — phase list authority.
3. Issue #2151 body for the punch list.

## Deliverables (verbatim from issue + spec)

1. **Wrapper module** under `scripts/build/` that, given a level + slug + worktree path:
   - Creates `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/` at run start.
   - Copies orchestration artifacts from the build worktree to the run dir on every phase boundary (see spec §"Phase Boundary Copies").
   - Copies again on terminal outcome (success / fail / crash).
   - Writes `state.json` per the canonical V7 schema (spec §"`state.json` Schema"): `mode`, `track`, `slug`, `run_id`, `parent_run_id`, `started_at`, `finished_at`, `status`, `failed_phase`, `failure_class`, `agent`, `model`, `effort`, `prompt_sha`, `phases`.
   - Writes `commit_diff_summary.json` from `git diff --stat` parsing (~30 LOC per spec).
2. **MDX-on-failure**: ALWAYS assemble the MDX, regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx` (current behavior). Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with frontmatter `build_status: failed` + `failed_phase: <phase>`. NEVER modify the source `module.md` frontmatter.
3. **Correction iterations preserved**: `python_qg_correction_r{N}.json`, `wiki_coverage_correction_r{N}.json`. Currently swallowed — explicit "actual prompt-engineering blind spot" per spec.
4. **Per-dim reviewer prompts** preserved as separate files under the run dir (`llm-qg-{dimension}-prompt.md`), NOT aggregated into `llm_qg.json`.
5. **File naming**: hyphenated to avoid `.gitignore` collision (e.g., `v7-writer-prompt.md` not `writer_prompt.md` — `*_PROMPT.md` is gitignored).
6. **Wire-up in `scripts/build/v7_build.py`**: invoke the wrapper at run start and at every `_phase_done` boundary, with terminal-outcome copy in the `_run_in_worktree` finally block (alongside the existing `_persist_build_artifacts`).

## Verifiable claims this work must produce (per #M-4)

| Claim | Deterministic check | Evidence format |
|---|---|---|
| Wrapper module exists at `scripts/build/run_archive.py` (or similar) | `ls scripts/build/run_archive.py` | raw `ls` output |
| `state.json` schema fields match spec | `jq '.mode, .track, .slug, .run_id, .status' on a real run's state.json` | raw `jq` output |
| Phase-boundary copies fire | Run a build with `--worktree`; assert `_orchestration/.../runs/{stamp}/` has expected files per spec §"Run Directory Contract" | `ls -la` raw output of run dir after a build |
| MDX-on-failure assembles | Force a failed build; assert `{slug}.mdx` exists under `_orchestration/.../runs/{stamp}/` with `build_status: failed` frontmatter | `head -10 {slug}.mdx` raw output |
| Correction iterations preserved | Force a correction-triggering failure; assert `python_qg_correction_r{N}.json` files exist | `ls _orchestration/.../runs/{stamp}/` |
| Tests pass | `.venv/bin/pytest tests/test_run_archive.py` | pytest summary `N passed in M.MMs` |

## Dispatch-brief checklist (MANDATORY per MEMORY)

1. **`git worktree add` setup** — `.venv/bin/python scripts/delegate.py dispatch --worktree` already handles this. Confirm via the agent_runtime guide.
2. **File-level work** — primary new module `scripts/build/run_archive.py` (~150-200 LOC est) + wire-up in `scripts/build/v7_build.py` (~30 LOC new + finally hook).
3. **Test suite** — new `tests/test_run_archive.py` with a contract test: assert run dir contents match §"Run Directory Contract" after a successful build, and again after a forced failure. Use mocks/fakes for the build itself.
4. **Ruff** — `.venv/bin/ruff check scripts/build/ tests/test_run_archive.py`.
5. **Commit** — conventional `feat(v7-preservation): ship run-archive wrapper (closes #2151)`. Reference the spec doc + issue body.
6. **`git push -u origin`** — to a branch like `codex/2151-v7-preservation-wrapper`.
7. **`gh pr create`** — title and body per `AGENTS.md:11-26` pre-submit checklist.
8. **NO auto-merge**.

## Out of scope

- Cleanup cron (spec defers details to month 3).
- Long-lived build branches (spec: "Always merge to main"; "Worktree reaped on completion; branch dies with it"). My #M-10 auto-commit IS a local-only branch retention layer for forensics — DO NOT change that behavior.
- Modifications to the existing `_persist_build_artifacts` end-of-build commit (it's a different concern).

## Hard guardrails

- The underscore prefix on `_orchestration/` is part of the contract (keeps the dir out of `mcp__sources__*` retrieval namespace per claude-headless Q5). Do not rename.
- Do not move the run archive under the published module directory, the wiki source tree, or a non-underscored `orchestration/` path.
- File naming MUST be hyphenated, never underscored, for files matching `*-prompt.md` (`*_PROMPT.md` is gitignored).
- Don't modify source `module.md` frontmatter (gate-consumed, parser risk).

## Cross-links

- Spec: `docs/best-practices/pipeline/v7-build-preservation.md`
- Phase order: `docs/architecture/v7-pipeline.md`
- Worktree isolation predecessor: PR #1952
- Implementation map seeder: PR #2108
- End-state auto-commit (complementary, already shipped): commit `c9a29a2420` (`feat(v7_build): auto-commit build artifacts to the build branch (#M-10)`)
- MEMORY #M-10 (artifact-preservation contract)
