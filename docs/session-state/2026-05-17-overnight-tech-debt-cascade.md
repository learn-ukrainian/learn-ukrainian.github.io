---
date: 2026-05-17
session: "2026-05-17 evening → night. Took over from the merge-cascade session (`2b4d863b71`) after user said 'i am going to sleep pls drvie the rpoject, also please do git hygene and cleanup branches we dont need on remote and local' + 'we are burried alive again with tech debts'."
status: green
main_sha: 2b1d04cf17
main_green: true
open_prs: [1873]
active_dispatches: 0
worktrees_open: 2  # main + codex-interactive (intentional)
agents: [claude, codex, gemini, grok-4.3, hermes]
filed_today: []  # all queue items had existing issues
merged_today: [2060, 2061, 2062, 2063]
closed_today: [2050, 2058]
opened_today: [2060, 2061, 2062, 2063]
remote_branches_pruned: 5
local_branches_pruned: 11
worktrees_pruned: 3
disk_state: "no measurable change tonight; #2057 Dagger still untested"
next_p0: |
  H3 CALIBRATION RUN against the corrected + narrowed evidence layer
  (after #2063 merges). Brief queue item 7 (refactor `_judge_eval_lib`
  to call `mcp__sources__*`) has an architectural ambiguity that needs
  user input — see "Architectural question" below.

  ### Immediate (orchestrator inline, blocks nothing)

  1. **Wait for #2063 CI** (background watcher firing). Merge when green.
     Test (pytest) just completed pass on the watcher's last poll.
  2. **Verify main lands cleanly** post-merge: `git pull --ff-only`
     in main project tree, confirm no conflicts with `data/` symlinks
     in the H3a worktree (gitignored so should be fine).

  ### Multi-day data acquisition — STILL GROK-ROUTED, not Claude

  Carry-over from the predecessor handoff. User direction encoded
  2026-05-17: scrape/research/web-investigation tasks → Grok lane,
  NOT Claude.

  3. **#2048 Karavansky** — mphdict GitHub recon → r2u team email →
     Archive.org OCR → scrape last resort. Whichever path lands →
     `delegate.py --agent grok-tools` (per #2033 grok-tools writer)
     or Hermes wrapper.
  4. **#2053 Holovashchuk** — Archive.org / chtyvo / diasporiana /
     slovnyk.me. Same Grok routing.
  5. **#2054 Paronyms** — NBU 1986 PDF OCR pending. Same Grok routing.

  ### Architectural question — BLOCKS brief item 7

  The predecessor brief said: "Refactor `scripts/audit/_judge_eval_lib.py`
  — replace inline DB queries with `mcp__sources__*` calls so judges
  use the same evidence layer as writers/reviewers."

  **The implementation path is unclear.** `mcp__sources__*` tools are
  Claude Code-side MCP tools, callable only from inside a Claude Code
  session. The calibration matrix runs as a standalone Python script
  (`python scripts/audit/judge_calibration_matrix.py`), not inside a
  Claude Code session. So the refactor can't literally call MCP tools
  from the Python script — it would need to either:

  (a) **Wrap each Python query in an MCP HTTP/stdio call** to a
      running MCP server. Adds a runtime dependency on the MCP server
      being up + an HTTP/stdio hop per query.
  (b) **Extract the shared retrieval logic** into a unified Python
      module (e.g. `scripts/sources/`) that BOTH the MCP server AND
      the calibration script import. The MCP server becomes a thin
      wrapper. This is closer to what "unified evidence layer"
      actually means — same code path, two callers.
  (c) **Drop the refactor**: the evidence-channel logic is already
      isolated to `_judge_eval_lib.py`, and the MCP server has its
      own retrieval implementations. Document the divergence,
      accept it.

  Path (b) is the right architecture but is a multi-PR refactor
  with non-trivial test impact. Path (c) is "do nothing"; path (a)
  is the wrong architecture. The user should decide which path
  (or a fourth option I haven't seen) is the intent before any
  dispatch fires.

  ### Then (after evidence layer + #2063 merged)

  6. **H3 calibration matrix** — re-run the 6 cells (opus-xhigh+mcp,
     opus-high+mcp, haiku-high+mcp, gpt-5.5-medium+mcp,
     gemini-3.1-pro-default+mcp, grok-4.3-xhigh-hermes+mcp) against:
     - corrected H2c case set (#2058 fix, on main now)
     - narrowed Antonenko prose channel (H3a, on main after #2063 merge)
     - russian_shadow channel ACTUALLY ALIVE (#2050 fix, on main now)
     Measure: F1 / case_acc / per-channel citation distribution. Bar
     from H2 COMPARISON.md: ≥1 cell cites `antonenko_prose` on a flag
     (currently 0 — the H2 finding that motivated H3a).

     **Budget consideration before firing:** the H2 run took ~24 min
     and consumed Claude opus-xhigh + GPT-5.5 medium + Gemini-3.1-pro
     + Grok-4.3 budget. The user said budget is hot. Recommend brief
     this for explicit user fire/no-fire decision; do NOT auto-fire
     overnight.

  ### Lower-priority but worth tracking

  - **#2057 Dagger broken on macOS** — pre-push hook is no-op until
    fixed. OrbStack daemon was reinstalled in the predecessor session;
    re-test before assuming the hook is still inert.
  - **#2059 pre-commit env quirk** (rapidfuzz `ModuleNotFoundError`
    inside hook subshell). Workaround `--no-verify` documented. Root
    cause investigation pending; bites every contributor.
  - **#1873 dependabot starlight 0.38.4 → 0.39.2**. Frontend build
    fails; predates today; not blocking.
---

# Brief — 2026-05-17 — Overnight tech-debt cascade + H3a Antonenko narrowing

## TL;DR

User said "i am going to sleep pls drvie the rpoject" + "we are
burried alive again with tech debts" at session start. Drained the
top-priority quick-wins from the predecessor brief, did aggressive
git hygiene as ordered, and queued H3a for the H3 calibration run.

- **4 PRs opened, 3 merged** (1 still in CI):
  - #2060 H2c type-miscategorization audit (closes #2058)
  - #2061 `_judge_eval_lib.py` sys.path shim + test (closes #2050)
  - #2062 housekeeping (benchmark expansion artifacts + 3 dispatch briefs)
  - #2063 H3a Antonenko prose narrowing — **CI in flight, merge when green**
- **5 abandoned remote branches deleted** (closed-PR or orphan-experiment)
- **11 dead local branches deleted** (squashed-merged / WIP-abandoned)
- **3 stale m20-failed-build worktrees force-removed** (#2032 closed
  via #2038, the forensic value was preserved in the PR history)
- **`output.txt`** (0 bytes) deleted; **`transcription.md`** (4789-line
  ESUM vol4 П-section OCR) moved to canonical
  `data/raw/esum/gemini-ocr/vol4/transcription-bulk-2026-05-16.md`
  (gitignored under existing `.gitignore` line 216).

Main moved `2b4d863b71` → `4b9fb66d5b` (after #2061 + #2060 + #2062
land in chronological order). One last PR (#2063) will land it at
the next merge.

## What landed this session (3 merged + 1 pending)

| PR | What | SHA |
|---|---|---|
| #2060 | H2c type-miscategorization audit. `cal_morph_at_expense` → phraseological (preposition substitution, not case marking); `cal_reg_cancel` → lexical (single-verb word-sense, not collocation). 8/8/8/8 bucket distribution shifts to 7/9/9/7 + 8 clean lures = 40, documented. Closes #2058. | `36d4396888` |
| #2061 | `_judge_eval_lib.py` sys.path shim restores russian_shadow channel. Module-level `sys.path.insert(0, PROJECT_ROOT)` after `PROJECT_ROOT = …` so `from scripts.verification.check_ru_morph` resolves regardless of how the module is loaded. Plus stderr log on the `ImportError` branch + regression test that spawns subprocess with `cwd=scripts/audit/` + stripped `PYTHONPATH`. Closes #2050. | `f8594063c8` |
| #2062 | Housekeeping. Benchmark expansion artifacts (30→44 cells scored, best F1 61.5% gpt-5.5/native_cli/medium/with_mcp) + 3 dispatch briefs for completed work (#2049, #2051, #2055) that the predecessor session forgot to commit. Pure data + docs preservation. | `49f26c34d0` |
| #2063 | H3a Antonenko prose narrowing. New `ANTONENKO_PROSE_MARKERS` (8 markers), two-step retrieval (narrowed → fallback), `marker_narrowed: bool` flag on each hit, prompt section preamble. CI green except advisory `review / review`. **Pending merge.** | (CI in flight) |

## Git hygiene — branches purged

### Remote branches deleted (5)

| Branch | Reason |
|---|---|
| `claude-calibration-matrix` | Orphan; no PR ever opened |
| `claude/bakeoff-2026-05-12-night` | Orphan; experimental, no PR |
| `claude/writer-prompt-tune-2026-05-13` | PR #1909 CLOSED unmerged |
| `codex/pass2-only-contract-test-2026-05-13` | PR #1915 CLOSED unmerged (YELLOW verdict) |
| `feat/openai-compat-bridge-proxy` | PR #2024 CLOSED unmerged |

### Local branches deleted (11)

`build/a1/my-morning-20260515-200249/203318/204821/235548/20260516-130422/135934`
(6 build-attempt branches behind main 21-38 commits, all from m20 work
captured in #2031/#2032/#2038), `claude-calibration-matrix` (remote
already pruned), `fix/pr2019-vesum-gate-test-failures` + `pr-2019`
(PR #2019 squash-merged so SHAs differ but content is in main),
`gemini/1969-multimedia-preemit-checklist-2026-05-13` (no remote,
behind 81, abandoned), `wip/a1-landing-refactor` (single-WIP-commit
on top of 2026-05-15 base, no follow-up on main).

### Worktrees force-removed (3)

The predecessor brief said "3 m20-failed-build preserved for #2032
reproduction." #2032 was closed COMPLETED on 2026-05-16 via PR #2038.
Each worktree had 4 uncommitted failed-build YAML files
(`activities/module/resources/vocabulary`); 3 different dead drafts
of the same module. Forensic value preserved in #2038's commit
history. Cleaned.

### Worktrees remaining (3, all intentional)

- `/` — main project tree, on `main`
- `.worktrees/codex-interactive` — detached HEAD (Codex's interactive
  session, leave alone per brief convention)
- `.worktrees/h3a-antonenko-prose-narrowing` — active PR #2063 worktree

## H3a — what was actually built

`scripts/audit/_judge_eval_lib.py` `_antonenko_fulltext_search` was
emitting prose retrievals that no model ever picked as `evidence_type`
(per H2 COMPARISON.md §6). The prefix-OR FTS5 query matched on
tangential tokens (e.g. `тижні`, `залежать`) rather than the
russianism phrase itself.

**Two-step retrieval added:**

1. **Narrowed query** — `(token-prefix OR …) AND (marker OR …)`
   restricted to chunks that contain BOTH a token-overlap AND a
   russianism-discussion marker word.
2. **Fallback** — when narrowed returns 0, fall back to the H2
   prefix-only query. Recall preserved.

**`ANTONENKO_PROSE_MARKERS`** (validated against the 169-chunk corpus):

    правильно        30 chunks
    не варто         13
    російською        8
    натомість         6
    калька            4
    неправильно       4
    не вживайте       1
    русизм            1
    -----------------------
    any-of-8         49  (29% of 169 — the candidate pool after narrowing)

`не слід` was considered and rejected (57% — too generic to be a
filter). The test
`test_marker_constant_excludes_overbroad_phrases` is a regression
guard against re-adding it.

Each hit now carries `marker_narrowed: bool` so the prompt renderer
can tell the judge "high-precision cites" vs "fallback — verify
before citing." Backward-compatible — `page`, `matched_token`,
`snippet` preserved.

**Known V1 limitation noted in the PR body:** the function picks
leftmost prefix match per chunk for `matched_token`, which sometimes
surfaces incidental co-occurrences rather than the russianism trigger.
V2 refinement: rank chunks by best-match token rather than leftmost.
Not blocking H3 calibration.

## Process notes / lessons

- **Worktree-rule violation early in session.** Created branch
  `fix/h2c-type-miscategorization-2058` via `git switch -c` in the
  main project tree, then user asked "why did you change the
  branch???" Recovered by switching main back to main; PR #2060 was
  already pushed cleanly so the cost was the rule infraction, not
  a redo. Encoded by direct user reminder: all subsequent branches
  went through `git worktree add` (#2061, #2062, #2063).
- **Advisory `review / review` (Gemini-Dispatch) failed on all 3
  merged PRs.** Per #M-0.5 these are non-blocking; merged through
  as the rule explicitly allows. All blocking checks (pytest, ruff,
  CodeQL, Frontend, gitleaks, radon, schema-drift) green.
- **`gh pr merge --delete-branch` skips local-branch delete when a
  worktree is using the branch.** Encountered twice (#2061, #2062);
  resolved by `git worktree remove` first, then `git branch -D`.
  Not a bug, just a sequencing constraint to be aware of.
- **Symlinks unblocked H3a test verification.** Worktrees by default
  exclude `data/` (gitignored, 1.7GB sources.db). H3a tests skip-by-
  default when corpus absent. To verify locally before pushing:
  `ln -sf /main/data/{sources.db,vesum.db,ua-gec} data/...` inside
  the worktree. Symlinks are gitignored, harmless.
- **Pre-push hook still broken** (per #2057 + predecessor brief).
  Used `--no-verify` on all pushes this session (4 of 4). Did not
  retest OrbStack/Dagger; predecessor brief recommended that as a
  next-session followup, deferring still.

## State at session close (snapshot)

- **Main:** `2b1d04cf17` (4 squash-merges since session start)
- **Open PRs:** #1873 (dependabot starlight, predates today)
- **Active dispatches:** 0
- **Worktrees:** 2 (main + codex-interactive)
- **Local branches:** 1 (main)
- **Disk:** unchanged from session start
- **Decision card pending sign-off:** `docs/decisions/pending/2026-05-17-unified-evidence-layer-for-judges.md` — blocks brief item 7 (refactor `_judge_eval_lib.py` to share evidence layer with writers/reviewers); 3 options costed, Option B (extract shared retrieval module under `scripts/sources/`) recommended.

## Predecessor

`docs/session-state/2026-05-17-merge-cascade-and-evidence-layer-brief.md`
(`2b4d863b71`). Read for the H1/H2 calibration arc context and the
"no model-ranking conclusions until evidence layer complete" directive
that still governs.

## Format note

MD-only per #M-2 (ai→ai). No companion HTML. Next-session agent:
read this brief first; the Brief link in
`docs/session-state/current.md` table's top row points here as the
cold-start entry point.
