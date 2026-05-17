# Dispatch brief — clawpatch supervised evaluation (execution)

> User signed off mid-session (2026-05-17 afternoon): "crabpatch needs attention. you can handle 3 parallel things?" — interpret as GO on the supervised evaluation per `docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md` §4.

## What you're doing

Run the §4 evaluation plan from `docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md` end-to-end. Write findings into a Decision Card at `docs/decisions/pending/2026-05-17-clawpatch-adoption.md`.

This is a HEAVY task. ~30-60 min realistically. Don't rush. Don't improvise — follow the §4 steps verbatim.

## Reads-required-first (in order)

1. **`docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md`** — the canonical brief. Read in full before acting.
2. **`docs/best-practices/agent-cooperation.md`** § "Three-agent model" to understand where clawpatch's persistent finding DB might slot in.
3. **`memory/MEMORY.md`** §M-7 and §M-9 — local fanout and pytest-before-push rules apply to your worktree work.
4. **The clawpatch README** at https://github.com/openclaw/clawpatch — use `WebFetch` to read the current README, not memory.
5. **The acpx README** at https://github.com/openclaw/acpx — same, current state of the provider bridge.

## Execution plan (verbatim from brief §4)

### Step 1 — SKIP install (user already installed globally)

User installed clawpatch globally via npm — verified at `/opt/homebrew/bin/clawpatch` → `../lib/node_modules/clawpatch/dist/cli.js`, version **0.2.0** (`npm list -g clawpatch`). Use the binary as `clawpatch` directly. Quote `clawpatch --version` raw output to confirm the pinned version in your writeup.

### Step 2 — `clawpatch init` on a worktree clone

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/clawpatch-trial -b eval/clawpatch-trial origin/main
cd .worktrees/clawpatch-trial
clawpatch init
clawpatch doctor
```

Quote `clawpatch doctor` raw output. If `doctor` reports no usable provider (e.g., Codex CLI unfindable from this shell), STOP and report — don't paper over.

### Step 3 — narrow scope: map then review `scripts/audit/`

```bash
# venv symlinked into worktree by delegate.py
clawpatch map
clawpatch review --limit 3 --jobs 1 --provider codex \
  --feature audit  # or whatever slice id matches scripts/audit/
```

`--jobs 1` is mandatory — our DISPATCH CAP is 2 Codex in flight and one is already running (inject_activity_ids fix); a Codex parallel-job of 3 would breach the cap and trigger rate limits.

### Step 4 — read findings, triage 3

```bash
# venv symlinked into worktree by delegate.py
clawpatch report
clawpatch show --finding <id>
```

For each of (up to) 3 findings:
- Real bug → record what fix you'd ship
- False positive → `clawpatch triage --finding <id> --status false-positive --note "<why>"`
- Real but stylistic → `clawpatch triage --finding <id> --status wontfix --note "<why>"`

Quote the full `clawpatch report` table in your Decision Card.

### Step 5 — try ONE `fix --dry-run`

Pick the highest-confidence finding from Step 4. Run:

```bash
# venv symlinked into worktree by delegate.py
clawpatch fix --finding <id> --dry-run
```

Quote what it proposes. Inspect the patch shape — does it match what you'd write?

### Step 6 — Decision Card writeup

Create `docs/decisions/pending/2026-05-17-clawpatch-adoption.md` with:

- **Status:** PROPOSED (decision needs user sign-off)
- **Evidence:** raw `clawpatch report` table, raw `clawpatch fix --dry-run` output, install pinned version
- **Finding signal-to-noise:** how many findings were real bugs vs false positives (of those reviewed)
- **Provider routing quality:** did the Codex-via-clawpatch invocation match what `delegate.py dispatch --agent codex` produces, or did clawpatch's prompt template generate different findings?
- **Integration friction:** install size, lock files, pnpm dependency, `.clawpatch/` directory disk footprint
- **Cost:** rough estimate of Codex tokens consumed during this eval (from clawpatch logs)
- **Net leverage vs existing tools:** is the persistent finding DB + triage workflow worth the pnpm dependency + install ceremony?
- **Recommendation (adopt / adopt-with-modifications / drop):** explicit
- **Adoption sequence if positive:** what changes to repo (`scripts/run_clawpatch.sh` wrapper? `.gitignore` entries? CI integration?)

## What NOT to do

- ❌ Do NOT `pnpm add -g` — scoped install only.
- ❌ Do NOT run `clawpatch fix` without `--dry-run`. Patches the worktree only, but stay safe in eval mode.
- ❌ Do NOT run more than `--jobs 1` against Codex provider (DISPATCH CAP).
- ❌ Do NOT modify any file outside `.worktrees/clawpatch-trial/` and the new Decision Card at `docs/decisions/pending/2026-05-17-clawpatch-adoption.md`.
- ❌ Do NOT commit the `.clawpatch/` directory or the trial worktree's changes — eval only, no PR from clawpatch-trial.
- ❌ Do NOT install or invoke clawpatch on the main project tree — only inside `.worktrees/clawpatch-trial/`.

## What TO commit

Only ONE file:
- `docs/decisions/pending/2026-05-17-clawpatch-adoption.md` — the Decision Card with findings.

Commit + push from the main repo (not the trial worktree):

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git checkout -b eval/clawpatch-decision-card
# move/copy the decision card if you wrote it in the trial worktree
git add docs/decisions/pending/2026-05-17-clawpatch-adoption.md
git commit -m "docs(decisions): clawpatch supervised evaluation Decision Card

Evaluation run per docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md §4.

Pinned version: <X.Y.Z>
Eval slice: scripts/audit/
Findings reviewed: <N>
Recommendation: <adopt | adopt-with-mods | drop>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
git push -u origin eval/clawpatch-decision-card
gh pr create --title "docs(decisions): clawpatch supervised evaluation Decision Card" --body "$(cat <<'EOF'
## Summary

Per user direction (2026-05-17): supervised evaluation of \`openclaw/clawpatch\` and \`openclaw/acpx\` as a potential addition to our adversarial-review toolkit.

Brief: \`docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md\` §4

Findings live in \`docs/decisions/pending/2026-05-17-clawpatch-adoption.md\`.

## Test plan

- [x] Pinned version installed scoped (no global pollution)
- [x] \`clawpatch init\` + \`doctor\` ran cleanly in throwaway worktree
- [x] \`clawpatch map\` + \`review\` against scripts/audit/ slice
- [x] 3 findings triaged with notes
- [x] One \`fix --dry-run\` inspected
- [x] Decision Card written with evidence + recommendation

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Cleanup after PR opens

Whether the Decision Card recommends adopt or drop:

```bash
# venv symlinked into worktree by delegate.py
# Remove the trial worktree
git worktree remove --force /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/clawpatch-trial
# Delete the trial branch
git branch -D eval/clawpatch-trial 2>/dev/null

# Remove the scoped install if recommend was DROP; KEEP it if recommend was ADOPT
# (for ADOPT, leave it so the user can verify before we re-install differently)
```

Report cleanup status in your final response — quote `git worktree list` to prove the trial worktree is gone.

## Anti-fabrication reminders (#M-4)

- Quote raw output from `pnpm view clawpatch version`, `clawpatch doctor`, `clawpatch report`, `clawpatch fix --dry-run`, `git worktree list` in the Decision Card.
- If any clawpatch command fails or behaves unexpectedly, capture stderr verbatim — don't paraphrase.
- Cost figures should be sourced from actual telemetry (clawpatch's logs or Codex usage delta), not estimated from intuition.
- The "Recommendation" field MUST be explicit: `adopt` / `adopt-with-modifications` / `drop`. No vibes.

## NO auto-merge

Open the PR with the Decision Card; orchestrator triggers user sign-off discussion.
