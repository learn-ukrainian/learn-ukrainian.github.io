# GPT-6 Luna @ high — closeout contract (append to bounded atlas/practice briefs)

Paste under **Done when** / **Agent** in `gpt-6-luna --effort high` dispatches.
Measured failure modes (2026-08-01 drive): exit -9 after commit, no PR, publish without
pointer commit, empty runtime log, zombie write-ownership.

## Role
You are a bounded worker, not the driver. Deliver a pushed branch for independent
cross-family review (or an explicit blocker with tool proof). The accountable
orchestrator owns CF, PR creation, CI, and merge.

## Mandatory terminal sequence (in order)
1. **Implement** only owned paths; no drive-by refactors.
2. **Verify** with explicit commands (quote exit code + last lines):
   - targeted pytest / ruff on touched files
3. **If deck emit changed:**
   - bump `PRACTICE_DECK_BUILDER_VERSION` when required
   - `make practice-deck-publish` (or project publish entrypoint)
   - **commit** `site/src/data/lexicon-practice-deck.pointer.json` in the same branch
4. **Commit** with `X-Agent: <agent>/<task-id>` trailer (every commit).
5. **Push** branch: `git push -u origin HEAD`.
6. **Hand off** the exact head, before/after tool evidence, test results, and
   measured residual to the orchestrator for branch CF before PR creation.
7. **Print final ledger** (exact lines the orchestrator greps):

```
CLOSEOUT
branch: <name>
sha: <full>
pr: NONE (orchestrator opens after branch CF)
pointer_committed: yes|no|n/a
publish_ran: yes|no|n/a
deck_version: <id or n/a>
tests: <cmd> → exit <n>
blocker: <none or one line + tool proof>
```

## Hard rules against last-night failure modes
- **Do not exit after commit without push and handoff.** If publish or push fails,
  set `blocker:` with tool proof; never claim the branch is reviewable remotely.
- Prefer **one focused commit** (or: code commit + pointer commit) over a long uncommitted
  working tree that dies at hard_timeout.
- **Publish early enough** to leave ≥10 minutes for commit/push/PR before any timeout.
- Do **not** expand multi-MB files (e.g. full `lexicon-sentence-inventory.json`) if a
  residual sidecar exists — CF sealed evidence has a ~2MB cap.
- Do **not** invent acceptance thresholds or mark epic goals done with residual still in scope.
- Do **not** self-merge or self-CF (orchestrator owns cross-family review).

## Time / size hygiene
- Hard timeout is real. Sequence: implement → test → publish → commit → push → handoff.
- If approaching timeout: stop new features and report measured residual to the orchestrator.
- Keep PR evidence under size limits: tables + samples, not full regenerated corpora in body.

## Success definition
Orchestrator can run independent branch CF on the pushed exact head without reconstructing work from a local worktree.
