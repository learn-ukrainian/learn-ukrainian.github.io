---
title: clawpatch — supervised evaluation brief
date: 2026-05-17
author: claude (orchestrator)
status: PROPOSED — awaiting user green light before any install/run
trigger: "user 2026-05-17: 'i wuld like to introduce this tool under supervision'"
target: openclaw/clawpatch + openclaw/acpx (provider bridge)
---

# clawpatch — supervised evaluation brief

> **User direction (2026-05-17):** *"i wuld like to introduce this tool under supervision … it can use any of our agents or agent combinations."*

This brief is research-only. No `pnpm add -g`, no `clawpatch init`, no
`.clawpatch/` directory creation until the user signs off on the evaluation
plan in §4.

## 1. What clawpatch is

`clawpatch` ([github.com/openclaw/clawpatch](https://github.com/openclaw/clawpatch))
is an automated code-review CLI that maps a repository into semantic feature
slices, sends each slice to a coding-agent provider for review, persists the
findings, and offers an explicit `fix` command that runs a single-finding
patch loop. Tagline: *"Review code. Patch bugs. Land PRs."*

**Maturity:**

- Created 2026-05-15 (2 days old).
- 364 stars, 43 forks at brief time — viral early adoption.
- Status per README: *"early CLI. Review/report/state are implemented;
  patching exists behind `clawpatch fix --finding <id>` and still requires
  manual review of the resulting worktree changes."*
- TypeScript codebase (~1.1 MB), distributed via `pnpm add -g`.

**Workflow:**

```bash
clawpatch init                                # write .clawpatch/, detect project
clawpatch map                                 # write feature records
clawpatch review --limit 3 --jobs 3           # review pending or selected features
clawpatch report                              # print findings as markdown
clawpatch next                                # next actionable finding
clawpatch show --finding <id>                 # inspect with evidence + validation
clawpatch triage --finding <id> --status false-positive --note "..."
clawpatch fix --finding <id>                  # patch loop, does NOT commit/push
clawpatch revalidate --finding <id>           # re-check after fix
```

**Critically:** `fix` does NOT commit, push, or open PRs. It runs configured
validation commands and records a patch attempt under `.clawpatch/`. The
operator still drives commit + push + PR through their existing flow — which
matches our `delegate.py dispatch` + worktree + manual-merge pattern.

## 2. Provider compatibility — fits our agent roster

clawpatch's supported providers:

| clawpatch provider | What it maps to in our stack | Notes |
|---|---|---|
| `codex` | Local Codex CLI (we have it; v0.130.0) | Direct call, no bridge |
| `acpx` | `openclaw/acpx` (2673★, updated 2026-05-17) — Agent Client Protocol bridge | Wraps **Codex / Claude / Pi / Gemini** as a single ACP-compatible interface; this is the path to Claude + Gemini integration |
| `grok` | Local Grok Build CLI via Hermes (we have it; PR #2033) | Direct call |
| `opencode` | OpenCode CLI (not currently in our stack) | Skip |
| `mock` / `mock-fail` | Deterministic test providers | For e2e contract tests |

**The user's key insight ("can use any of our agents or agent combinations")
maps directly:**

- Single-agent review: `clawpatch review --provider codex`
  → same as our current Codex adversarial dispatch.
- Cross-agent review: rotate `--provider codex`, `--provider acpx --model gemini`,
  `--provider grok` per feature slice
  → matches our "no LLM reviews its own work" SELF_REVIEW_DETECTED rule.
- Different agent for review vs fix: `clawpatch review --provider codex` then
  `clawpatch fix --finding X --provider acpx --model claude-opus-4-7`
  → bug-finding stays cheap (Codex), fix stays high-judgment (Claude).

## 3. Where it slots in (potential)

The repo features clawpatch claims to map for Python projects:

> Python project metadata, console scripts, bounded source groups, pytest
> suites, and Flask/FastAPI routes

Mapped against our codebase:

- `scripts/*` (~150 .py files) — could become semantic feature slices
  per directory (`scripts/audit/`, `scripts/build/`, `scripts/wiki/`, etc.)
- `tests/*` (~200 test files) — pytest suites would map naturally
- `curriculum/*.yaml` plans — NOT a Python feature; would need custom heuristic
  (clawpatch supports `--source heuristic|auto|agent` so custom slicers may work)
- V7 pipeline (`scripts/build/linear_pipeline.py`) — large file, currently
  ~5000 LOC, monolithic — would likely be reviewed as one slice

**Overlap with existing tools:**

| Existing surface | clawpatch overlap |
|---|---|
| `Skill code-review` (in-session) | Same goal: find bugs. clawpatch persists findings between sessions. |
| `Skill simplify` (in-session) | Different focus (refactor); not directly replaced. |
| Codex adversarial-review dispatch (`delegate.py --agent codex --mode read-only`) | Same goal, but clawpatch adds finding tracking + triage workflow. |
| Audit batch-review skill | clawpatch is finer-grained (per-feature, not per-module). |

**Where clawpatch ADDS value over what we have:**

1. **Persistent finding database** — we currently lose adversarial-review
   findings after each session unless we manually file GH issues. clawpatch's
   `.clawpatch/features/*.json` + `.clawpatch/findings/*.json` survive.
2. **Triage workflow** — false-positive marking with notes. Today we triage
   by closing issues; that's heavier-weight.
3. **Revalidate after fix** — built-in. Today we manually re-run pytest or
   re-dispatch.
4. **Provider rotation in one command** — vs juggling multiple dispatch
   templates.

## 4. Proposed evaluation plan — SUPERVISED

**Step 0 (before any install): user signs off on this brief.**

### Step 1 — install scoped, NOT global

Default README install is `pnpm add -g`. For evaluation, prefer the
non-global path so the tool is isolated:

```bash
# From a scratch directory OUTSIDE the project:
mkdir -p ~/sandbox/clawpatch-trial
cd ~/sandbox/clawpatch-trial
pnpm init -y
pnpm add clawpatch
# Use as `npx clawpatch ...` or `./node_modules/.bin/clawpatch ...`
```

This way `pnpm uninstall clawpatch` cleanly reverses if we decide against it.

### Step 2 — `clawpatch init` on a worktree clone

Create a throwaway worktree of `learn-ukrainian` so the `.clawpatch/`
directory doesn't pollute the main repo until we want it:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git worktree add .worktrees/clawpatch-trial main
cd .worktrees/clawpatch-trial
~/sandbox/clawpatch-trial/node_modules/.bin/clawpatch init
~/sandbox/clawpatch-trial/node_modules/.bin/clawpatch doctor   # check provider
```

### Step 3 — narrow scope first: `clawpatch map` then review a SMALL slice

Map the full repo (read-only), then review only the `scripts/audit/`
directory (~25 files, our most active code area, well-tested):

```bash
clawpatch map
clawpatch review --limit 3 --jobs 1 --provider codex \
  --feature audit  # if features are named by directory; else find the slice id
```

Single-job to avoid 3 concurrent Codex calls (our DISPATCH CAP is 2 Codex
in flight; clawpatch should respect that).

### Step 4 — read the findings, manually triage 3

```bash
clawpatch report                        # markdown table of findings
clawpatch show --finding <id>           # full evidence for each
```

For each finding, decide:

- Real bug → would we ship the same fix via our existing flow?
- False positive → `clawpatch triage --finding <id> --status false-positive`
- Real but stylistic → triage as `wontfix` or low-priority

### Step 5 — try ONE `fix` with `--dry-run`

```bash
clawpatch fix --finding <id> --dry-run
```

The README says `fix` does NOT commit. With `--dry-run` it should also not
modify the working tree. Inspect what it would do.

### Step 6 — decide

Open a Decision Card under `docs/decisions/pending/2026-05-XX-clawpatch-adoption.md`
with evidence from steps 3-5:

- Finding signal-to-noise ratio (real bugs / false positives ratio)
- Provider routing quality (did the right agent get the right slice?)
- Integration friction (`.clawpatch/` directory churn, lock files,
  pnpm dependency, etc.)
- Cost (Codex usage during evaluation)
- Net leverage vs existing tools

## 5. Risks to call out before install

1. **2-day-old tool.** Expect API churn, undocumented edge cases. Pin a
   specific version: `pnpm add clawpatch@<exact-version>`.
2. **Adds pnpm dependency.** We currently use npm for the `starlight/`
   frontend; adding pnpm just for clawpatch creates a tool-doubling risk.
   Alternative: `npx clawpatch@<version>` (no install, but slower per-run).
3. **`.clawpatch/` directory** would need a `.gitignore` decision. Default
   is project-local state; we'd commit some of it (config) but not the
   findings DB (regenerable).
4. **Provider-side credentials.** clawpatch uses our existing Codex CLI
   credentials directly. If clawpatch's Codex invocation pattern differs
   from `delegate.py`'s, it could trigger different rate-limit behavior
   on the OpenAI side.
5. **No commit-side automation.** This is a strength (safety) but also
   means clawpatch is one more step in our flow, not a flow shortcut.
6. **No SDK integration with our Monitor API.** clawpatch doesn't know
   about our `localhost:8765/api/state/*` endpoints; findings would live
   in `.clawpatch/`, not in our standard observability surface.

## 6. What to commit to the repo (none yet)

Nothing — this brief is the only artifact at this stage. After evaluation
(if positive), we'd add:

- `docs/decisions/2026-05-XX-clawpatch-adoption.md` (the Decision Card)
- `.gitignore` entry for `.clawpatch/findings/` if findings are session-local
- Possibly a `scripts/run_clawpatch.sh` wrapper that pins the version + runs
  the standard map/review/report sequence

## 7. Open questions for the user

1. **Eval target — scripts/audit/ or scripts/build/?** scripts/audit/
   recommended (smaller, well-tested, recent activity). scripts/build/ is
   the high-value target but its monolithic 5000-LOC `linear_pipeline.py`
   might trip clawpatch's slicer.
2. **Provider for evaluation — Codex or rotate?** Single-provider (Codex)
   keeps the eval clean. Rotation is the eventual production pattern but
   adds variability to the eval signal.
3. **Eval budget cap?** Codex weekly burn matters. Recommend cap at
   3 findings per slice × 1 slice = 3 Codex calls for the eval.

---

## TL;DR for the orchestrator returning to this brief

If the user comes back and just says "go ahead":

1. Run §1 commands.
2. Run §4 steps 1-5 in order, no improvisation.
3. Write up findings in §6 Decision Card.
4. Bring back for "ship the integration?" decision.

If the user says "skip eval, just install":

- Pin the version: `pnpm add -g clawpatch@<latest at time of read>`.
- Run `clawpatch init` at repo root.
- Add `.clawpatch/findings/` to `.gitignore`.
- Commit a `.clawpatch/config.json` baseline + the gitignore change.
- Then run the §4 steps 3-5 evaluation anyway to validate the choice.

If the user says "drop it":

- Delete this brief.
- File no follow-ups.
