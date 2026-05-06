# Codex dispatch brief — #1703 V7 bakeoff CLI gaps + harness

> **Issue:** #1703
> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/1703-bakeoff-v7-cli-and-harness/`
> **Branch name:** `codex/1703-bakeoff-v7-cli-and-harness`
> **Mode:** danger (autonomous), --hard-timeout 5400 (90 min)
> **Effort:** xhigh (substantive multi-file refactor + new modules)

## Goal

Make the A1/20 three-writer bakeoff actually runnable. Today nothing works
end-to-end: brief uses CLI flags that don't exist, V7 lacks the codex-tools
writer, V7 has no review-only mode, V7 has no telemetry file sink, and the
aggregator's expected file layout doesn't match what any current command
produces. See #1703 for the full 8-blocker inventory.

This dispatch ships **A → D** below in one branch + one PR. Section E
(brief update) goes in the same PR.

## Worktree setup

`delegate.py dispatch --worktree .worktrees/dispatch/codex/1703-bakeoff-v7-cli-and-harness --base main`
auto-creates the worktree branched from `origin/main`. You will start
already inside it. Do NOT run `git worktree add` yourself.

First action on entry: verify the worktree is on `origin/main`, not
behind:

```bash
git log --oneline HEAD..origin/main  # must be empty
```

If non-empty, `git rebase origin/main && git push --force-with-lease`
before doing any other work.

## Sequenced work

### A. Add `codex-tools` writer to V7

Files: `scripts/build/linear_pipeline.py`, `scripts/build/v7_build.py`, plus
test in `tests/test_linear_pipeline_*.py`.

1. Read `scripts/build/linear_pipeline.py` `WRITER_CHOICES` and
   `WRITER_DEFAULTS`. Mirror the `gemini-tools` entry to add `codex-tools`:
   - Same prompt template (the writer prompt is agent-agnostic)
   - Tool config: use the existing Codex MCP shell-out config from
     `scripts/agent_runtime/adapters/codex.py`
   - Default model: read from `scripts/agent_runtime/registry.py` Codex
     family — pick the same default the V6 `--writer codex-tools` uses
2. Update `scripts/build/v7_build.py` `WRITER_CHOICES` constant to include
   `codex-tools` (the alias `codex` should normalize to `codex-tools`,
   matching how `claude` → `claude-tools` works today).
3. Add a parametrized test case for `codex-tools` to whichever existing
   test verifies writer dispatch. If none exists, add one in a new file
   `tests/test_v7_writer_dispatch.py` that asserts each writer choice
   resolves to a real adapter without calling out to LLMs.

Acceptance:
- `v7_build.py --writer codex-tools a1 my-morning --dry-run` exits 0 and
  prints the same dry-run footer as `--writer gemini-tools` does.
- New parametrized test passes for all 3 writer-tools entries.

### B. Add V7 review-only mode

New file: `scripts/build/v7_review.py`. Mirror the structure of `v7_build.py`.

CLI:

```
v7_review.py LEVEL SLUG \
    --content PATH \
    --reviewer {claude-tools|gemini-tools|codex-tools} \
    [--telemetry-out PATH]
```

Behavior:
1. Load plan and knowledge packet for `LEVEL/SLUG` exactly as `v7_build.py`
   does (reuse `linear_pipeline.writer_context()` and the existing plan
   loader — extract a shared helper if needed; do not duplicate logic).
2. Read the markdown at `--content`. If it has a YAML front-matter block
   with `writer:` field, refuse with exit 1 if `writer == reviewer`
   (no self-review).
3. Run the per-dim review phase by calling
   `linear_pipeline.render_review_prompt()` + the existing review dispatch
   path. Iterate over all 9 dimensions (whatever the current set is — read
   the source of truth, don't hardcode).
4. Aggregate via `linear_pipeline.aggregate_llm_review()`.
5. Emit `reviewer_dim_evidence` per dim + `phase_review_summary` at the end.
6. If `--telemetry-out PATH`: write events to that file (append mode); else
   stdout.
7. Exit 0 if all dims emitted; exit 1 on plan/packet/content/reviewer error.

Tests in `tests/test_v7_review.py`:
- Self-review refusal (writer == reviewer)
- Successful review against a fixture lesson markdown
- `--telemetry-out` file path: assert events land in file, not stdout
- All 9 dim events emitted

`--help` must follow `.claude/rules/cli-help-standard.md` —
description, examples, Outputs, Exit codes, Related.

### C. Add `--telemetry-out PATH` to `v7_build.py`

Same file. New flag. When set, `linear_pipeline.emit_event` (or whatever
sink the V7 builder uses) writes events to the path instead of stdout.

Implementation:
- Wrap or replace `emit_event`. The cleanest pattern is a context manager
  in `linear_pipeline.py` that swaps the sink for the duration of a build.
- Append mode (so phase outputs concatenate if the harness invokes
  multiple times against the same file — used by the resume path in D).
- Without the flag: stdout, no behavior change.

Tests: extend whichever existing v7_build test exercises the writer
dispatch — assert `--telemetry-out /tmp/out.jsonl` produces a non-empty
file with valid JSONL.

### D. Bakeoff harness `scripts/audit/bakeoff_run.py`

New file. Python, not bash. Mirrors the structure and `--help` discipline
of `scripts/audit/bakeoff_aggregate.py`.

CLI:

```
bakeoff_run.py --bakeoff-dir audit/bakeoff-2026-05-05 \
               --level a1 --slug my-morning \
               --writers claude-tools,gemini-tools,codex-tools \
               [--resume] [--skip-aggregate] [--writers-only] [--reviewers-only]
```

**`--writers` order is the execution order.** Default to
`claude-tools,gemini-tools,codex-tools` — Claude first because Anthropic's
2× peak-hours pricing window (14:00–20:00 CET) makes Claude the most
schedule-sensitive writer; running it first lets us fail fast before
peak hits or, if we miss the pre-peak window, the harness can be
invoked with `--writers gemini-tools,codex-tools` during peak and then
re-invoked with `--writers claude-tools --resume` after 20:00 to fill in
the Claude run.

`--writers-only` skips the review phase entirely (used when sequencing
writes around peak hours and reviews can wait). `--reviewers-only`
skips writes (used to re-run reviews if a reviewer prompt was tweaked
without changing writer outputs).

Sequence:
1. **Pre-flight.** Verify plan at `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
   exists. Verify wiki packet for the slug exists. Verify each writer in
   `--writers` resolves via the agent_runtime registry. Fail fast if any
   missing.
2. **Spike.** First writer × `--dry-run`. Catches plan/packet errors
   before burning compute on the real writes.
3. **Writes (3 ×).** For each writer in `--writers`:
   - Skip if `--resume` AND `audit/bakeoff-DATE/<short-name>.write.jsonl`
     exists AND non-empty (`<short-name>` strips the `-tools` suffix:
     `gemini-tools` → `gemini`, `codex-tools` → `gpt55` per aggregator
     naming convention — see `bakeoff_aggregate.py:normalize_agent`).
   - Invoke `v7_build.py LEVEL SLUG --writer X --out audit/bakeoff-DATE/<short>/
     --telemetry-out audit/bakeoff-DATE/<short>.write.jsonl`.
   - Copy the produced lesson markdown (`<slug>.md` or `<slug>.mdx` —
     check what v7_build actually emits) to
     `audit/bakeoff-DATE/<short>.md` so it matches what
     `bakeoff_aggregate.collect_bakeoff_data()` looks for.
4. **Reviews (6 ×).** For each `(writer, reviewer)` pair where writer != reviewer:
   - Skip if `--resume` AND target review file exists.
   - Invoke `v7_review.py LEVEL SLUG --content audit/bakeoff-DATE/<writer-short>.md
     --reviewer Y --telemetry-out audit/bakeoff-DATE/<writer-short>-<reviewer-short>.review.jsonl`.
5. **Aggregate.** Unless `--skip-aggregate`: invoke
   `scripts/audit/bakeoff_aggregate.py --bakeoff-dir audit/bakeoff-DATE
   --writers <comma-list-of-shorts>`.
6. **Summary.** Print to stdout: per-writer pass/fail, per-review pass/fail,
   aggregator exit code.

Tests in `tests/test_bakeoff_run.py`:
- Mock `v7_build.py` and `v7_review.py` with fake commands that emit
  deterministic JSONL (use `subprocess.run` with a fake `python` shim or
  patch the runner). Assert harness invokes them in the right order with
  the right args.
- `--resume` skips already-complete writers
- Pre-flight failure modes (missing plan / missing packet / unknown
  writer) all exit 1 with clear messages
- Aggregator invocation gets the right `--writers` list

`--help` per CLI standard.

### E. Update the bakeoff brief

Edit `docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md`:
- Replace the broken Phase 1/2/3 command block with the single
  `bakeoff_run.py` invocation
- Add a "Prerequisites" section linking to PR #1703 (this PR)
- Update the "Implementation deltas" section: remove the old "Claude
  needs to verify telemetry / write aggregator" item (already done via
  #1699/#1700/#1703); replace with "Run `bakeoff_run.py` per below"
- Keep the rubric, success criteria, and timeline sections unchanged

## Constraints

- **No V6 changes.** V6 is legacy (`.claude/rules/pipeline.md`). All work on V7.
- **No bash scripts for orchestration.** Python with structured
  error handling and tests.
- **Reuse existing modules.** Don't reimplement adapters, plan loading,
  prompt rendering, or aggregation. Import from `linear_pipeline` and
  `agent_runtime`.
- **CLI help standard** (`.claude/rules/cli-help-standard.md`) on
  every new entry point: `v7_review.py`, `bakeoff_run.py`. Description /
  Examples / Outputs / Exit codes / Related.
- **Tests are non-negotiable.** Every new module ships with tests.
  No "happy-path-only" — include the failure modes listed in each section.
- **Conventional commit messages**, one PR. Title:
  `feat(bakeoff): V7 codex-tools writer + review-only + telemetry-out + harness (#1703)`.

## Numbered execution steps

1. Verify worktree base: `git log --oneline HEAD..origin/main` must be empty. Rebase if needed.
2. Implement Section A (codex-tools writer). Run `.venv/bin/ruff check scripts/build/`. Run the new writer-dispatch test.
3. Implement Section C (`--telemetry-out` on v7_build.py — do this BEFORE B because B depends on it). Test.
4. Implement Section B (`v7_review.py`). Test.
5. Implement Section D (`bakeoff_run.py`). Test.
6. Implement Section E (brief update). No test.
7. `.venv/bin/ruff check scripts/build/ scripts/audit/ tests/`
8. `.venv/bin/pytest tests/test_v7_writer_dispatch.py tests/test_v7_review.py tests/test_bakeoff_run.py tests/test_linear_pipeline_telemetry.py -v`
9. `git add -A && git commit -m "feat(bakeoff): V7 codex-tools writer + review-only + telemetry-out + harness (#1703)"` (use HEREDOC for body, see CLAUDE.md commit template)
10. `git push -u origin codex/1703-bakeoff-v7-cli-and-harness`
11. `gh pr create --title "feat(bakeoff): V7 codex-tools writer + review-only + telemetry-out + harness (#1703)" --body "<see template below>"` — DO NOT enable auto-merge.

## PR body template

```markdown
## Summary
- Adds `codex-tools` writer to V7 (`v7_build.py` + `linear_pipeline.WRITER_*`)
- New `scripts/build/v7_review.py` — review-only entry point with `--content`/`--reviewer`/`--telemetry-out`
- New `--telemetry-out PATH` flag on `v7_build.py` for file-sink JSONL
- New `scripts/audit/bakeoff_run.py` — Python orchestration harness for the 3-writer × 6-cross-review bakeoff
- Updates `docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md` to use the new harness

## Test plan
- [ ] `pytest tests/test_v7_writer_dispatch.py tests/test_v7_review.py tests/test_bakeoff_run.py tests/test_linear_pipeline_telemetry.py -v` all green
- [ ] `v7_build.py --writer codex-tools a1 my-morning --dry-run` exit 0
- [ ] `v7_review.py a1 my-morning --content fixtures/sample.md --reviewer claude-tools --telemetry-out /tmp/out.jsonl` produces a valid event stream
- [ ] `bakeoff_run.py --bakeoff-dir /tmp/bk-test --level a1 --slug my-morning --writers gemini-tools,claude-tools --skip-aggregate` (without codex to avoid burning the API in CI) writes the expected file layout
- [ ] `ruff check scripts/build/ scripts/audit/ tests/` clean

Closes #1703.
```

## Do NOT

- Do not auto-merge.
- Do not create a feature branch in the main checkout — work in the
  `.worktrees/dispatch/codex/1703-...` worktree.
- Do not extend V6.
- Do not skip tests "for speed."
- Do not propose options in the PR description — ship the proper full fix.
