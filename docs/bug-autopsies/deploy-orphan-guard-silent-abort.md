# Bug Autopsy: agents:deploy silently aborts on an orphan guard → stale agent definitions

## Symptom

On 2026-06-12 the SessionStart hook flagged `DEPLOY DRIFT: 2 file(s) differ between
agents_extensions/shared/ and .claude/` and told me to run `npm run agents:deploy`. I ran it.
**It produced no output and changed nothing** — `git status` stayed clean and the drift persisted.
Running it a second time: same silent no-op.

The two drifted files were the **#3039 reviewer-seat policy** edits
(`agents/curriculum-orchestrator.md`, `skills/batch-review/SKILL.md`) made in `agents_extensions/shared/`
(the source) but never propagated to the `.claude/` deploy target. The deploy target — what the running
orchestrator agent + `batch-review` skill actually read — was stale. And it wasn't only those 2 files:
once the deploy finally ran, it resynced **197 files to `.claude/`** (plus 31 to `.agent/`, 27/13 to the
gemini/codex targets). Every `agents_extensions/shared/` edit since the guard first tripped had been
silently failing to deploy.

## Root cause

`scripts/deploy_prompts.sh` runs a preflight **orphan-path guard** (`check_orphans`) before the rsync.
The guard protects gitignored local runtime files in the deploy targets (`.agent/wake`, `prompts/`,
thread-handoff files, …) from `rsync --delete`. It aborts the **entire deploy** (`exit 1`) on the **first**
undeclared orphan it finds in any destination.

A stray batch of consumed scratch — six `a2-*` review/dispatch artifacts
(`a2-7-gemini-review-v2.md`, `a2-7-worker-prompt.md`, `a2-8-*`, `a2-9-gemini-review-result.md`) — had been
written into the **`.agent/` deploy-target root** by the 2026-06-11 gemini A2 review flow. None matched a
declared `ORPHAN_PATHS_AGENT` pattern (`wake cache prompts tmp *-thread-bootstrap.md *-thread-handoff.md
*-thread-lease.json`), so the guard saw them as undeclared orphans and aborted **every** deploy — including
the legitimate `.claude/` sync the SessionStart hook was asking for.

Two compounding traps made it invisible:
1. **The guard is global, the remedy is silent.** `check_orphans` returns on the first undeclared orphan,
   so the deploy never reaches the `rsync` of the *unrelated, legitimately-drifted* `.claude/` files. The
   SessionStart hook recommends `npm run agents:deploy` as the fix, but that fix can't succeed while any
   orphan sits in *any* target.
2. **`npm run --silent` swallows the abort message.** The deploy script *does* print
   `❌ Deploy aborted: undeclared orphan paths would be deleted` — but only when run directly. Through
   `npm run agents:deploy --silent` (and even plain `npm run agents:deploy | tail`) the abort line was not
   surfaced, so the operator sees a no-op and assumes the drift is resolved.

Scratch in a deploy-target root is the upstream cause: `.agent/` is synced from `agents_extensions/shared/`,
so anything written to `.agent/<name>.md` that isn't a declared runtime orphan is a deploy landmine.

## Fix

Removed the six consumed `a2-*` scratch files from `.agent/` (gitignored, all their review findings already
actioned on `main` — verified M56 `next:` pointer + metalanguage nav bridges present; the a2-9 "stray file
blocker" was a false positive about a legit folk-track handoff). Re-ran `bash scripts/deploy_prompts.sh`
directly: preflight passed, rsync synced 197 files to `.claude/` (+ `.agent`/`.codex`/gemini). Confirmed
drift cleared (the SessionStart hook's exact `diff -rq … --exclude=…` returns empty) and the #3039
reviewer-seat policy is now present in `.claude/agents/curriculum-orchestrator.md` and
`.claude/skills/batch-review/SKILL.md`.

Out of scope (left as follow-ups, not blocking): hardening the remedy so the abort can't be silent — e.g.
the SessionStart drift remedy could run the deploy preflight and surface the orphan, or `deploy_prompts.sh`
could print the orphan list to stderr so `--silent` can't hide it.

## Prevention

- **Never run scratch/review output into a deploy-target root** (`.agent/`, `.claude/`, `.codex/`,
  `.gemini/`). Use `.agent/tmp/` (a declared, `--delete`-preserved orphan) or `batch_state/` instead.
  Anything else in those roots is a deploy landmine.
- **When `agents:deploy` looks like a no-op, run the script directly** (`bash scripts/deploy_prompts.sh`)
  and check the exit code — do **not** trust `npm run … --silent`, which hides the orphan-guard abort.
- **Diagnose drift with the script's own comparison**, not by trusting that the remedy ran: the complete
  undeclared-orphan list is
  `diff -rq --exclude=.DS_Store agents_extensions/shared .agent | awk '/^Only in .agent/{…}'` minus the
  declared `ORPHAN_PATHS_*` patterns. `check_orphans` only shows the *first* offender per run, so one run
  under-reports the blockers.

## Links

- Issue: #3039 (reviewer-seat policy — the edits that couldn't deploy) and the deploy-drift SessionStart flag.
- Fix: `ff0dee1a97` (#3039 — the source edits stranded by the silent deploy abort; the deploy itself was
  unblocked this session by clearing the `.agent/` scratch — `.agent/`/`.claude/` are gitignored, no deploy SHA).
- Related: `scripts/deploy_prompts.sh` (`check_orphans`, `ORPHAN_PATHS_AGENT`);
  `agents_extensions/shared/hooks/session-setup.sh` § 7 (the drift check).
- MEMORY #M-8 (orchestrator-active through dispatch lifecycle).
