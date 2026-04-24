# Git Hygiene

Sister doc to [`gitflow.md`](gitflow.md). `gitflow.md` is about how we
branch, PR, and merge. This doc is about **keeping the working tree
clean between sessions** — which is what we historically failed at.

## Principle

> **Every session ends with zero dirty files** — `git status` prints
> nothing to the right of `On branch main`.

Exceptions are explicit and narrow. Everything else is debt that
accumulates across sessions, silently drifts past merged PRs, and
eventually produces surprises like "why is this build crashing on an
import that's clearly in main?"

## Why this is a rule, not a suggestion

Real incident 2026-04-24: a pilot build of `a1/sounds-letters-and-hello`
was blocked because the working tree was missing
`scripts/common/text_utils.py` — a file added to main by PR #1513 the
day before. The working tree had 489 dirty entries (modified + deleted
+ untracked). A mix of:

- 43 `.worktree-briefs/*.md` — consumed dispatch prompts that had
  already produced merged PRs (pure noise)
- 99 `curriculum/l2-uk-en/a1/colors/**` — stale output from pre-ADR-007
  pilot runs
- 16 files modified to pre-merge state (pre-#1498, pre-#1513, pre-#1515,
  pre-ADR-007) — drift from never-reset local state
- 3 tests deleted in the working tree that had been ADDED by recent
  PRs (never materialized in the checkout)

Every one of these was resolvable in under a minute at the time of the
relevant PR merge. Together, they cost ~90 min of triage at pilot-fire
time, with real risk of destroying user WIP if the cleanup was done
carelessly.

**Lesson: dirty state accumulates like technical debt. Cheap to fix
each day, expensive to fix cumulatively.**

## What counts as dirty

```
git status --short | grep -vE '^(<exemption patterns>)' | wc -l
```

Any non-zero output outside the [exemption paths](#exemption-paths) is
a hygiene violation.

Dirty file classes:

| Marker | Meaning | Default action |
|---|---|---|
| ` M` | Modified in working tree | Commit, restore to HEAD, or stash |
| `MM` / `M ` | Modified + staged (partial) | Finish staging and commit |
| ` D` | Deleted in working tree | Either commit the deletion or restore |
| `??` | Untracked | Either commit, delete, or gitignore |

## Exemption paths

These paths are **expected to be dirty** during active work and don't
count toward the "end session clean" rule. They're either output from
running builds or local-only state:

- `wiki/**` — wiki builder runs in parallel and emits new/modified
  files constantly. Snapshot-commit periodically (`feat(wiki): snapshot
  built wikis — batch YYYY-MM-DD`), don't restore.
- `data/corpus_audit/draft_tickets/*.md` — local-only audit drafts
  (already unignored/allowed per existing `.gitignore` rule)
- `.venv/`, `node_modules/`, `starlight/dist/`, etc. — gitignored build
  artifacts. If any of these show up in `git status`, something is
  miswired.

Exemptions are **additive** — new exemptions go in this list with
a justification, not as silent practice.

## Non-exempt categories (the ones that bite us)

### `.worktree-briefs/` (was not gitignored pre-2026-04-24)

One-shot dispatch prompts consumed by `delegate.py dispatch`. Each
brief is generated, passed to a Codex/Claude/Gemini subprocess, and
produces a PR. After the PR merges, the brief has zero archival value.
Now gitignored (commit 3aa5880304). If you ever see one tracked, delete
it.

### `orchestration/{module}/` output

Build artifacts (dispatch metadata, chunk caches, correction attempts)
are rebuilt on every v6 run. If the module slug is committed in a
published state, its orchestration dir can be regenerated on demand.
Reset to the unbuilt state when retiring a pilot or bad build.

### Drift from merged PRs

This is the most dangerous. Files you didn't touch, but that HEAD
moved ahead on. Working tree "rejects" the new state by holding the
old one. Spot the pattern:

- Working tree has functions/classes that no longer exist on main
  (tests for KILLed infrastructure, pre-refactor helpers, etc.)
- Working tree is missing files that main added (new shared modules,
  new tests, new pre-commit hooks)
- Line counts differ from HEAD despite no intentional edits

Detection is trivial:

```bash
# Is the working-tree version of a file behind main?
git diff HEAD -- <file> | head
# If output looks like "remove lines main already removed", restore:
git checkout HEAD -- <file>
```

## Decision flow for a dirty file

```
Is the file under an exemption path (wiki/**, etc.)?
├── YES → leave it (or snapshot-commit if session end)
└── NO:
    Does `git diff HEAD -- <file>` show you're behind main?
    ├── YES → `git checkout HEAD -- <file>` (restore)
    └── NO:
        Is this intentional WIP?
        ├── YES → commit (even as WIP branch) or stash with a named label
        └── NO → delete / revert / restore
```

## Session-end protocol

Before closing a session:

```bash
# 1. Inventory
git status --short | awk '{print $1}' | sort | uniq -c

# 2. Classify
git status --short | grep -vE '^(.M|.D|.\?) (wiki/|data/corpus_audit/draft_tickets/)'

# 3. Resolve all non-exempt entries per the decision flow above.
# 4. Confirm clean:
test -z "$(git status --short | grep -vE '^(.M|.D|.\?) wiki/')" \
    && echo "clean" || echo "DIRTY — do not close session"
```

Or use the session-start hygiene hook (next section) to catch it
on the *next* session if you forget.

## Session-start hygiene hook

Lives at `scripts/claude/session-start-hygiene.sh`, wired via
`.claude/settings.json` as a `SessionStart` hook. Runs on every fresh
Claude session, prints a colored warning if the dirty-file count
outside exemption paths exceeds a threshold (default: 20).

Non-blocking. Meant to be a nag, not a gate — sometimes a session
legitimately inherits dirty state from an interrupted previous session
and wants to resume it. The warning makes sure you don't work *past*
the problem without noticing.

See `scripts/claude/session-start-hygiene.sh --help` for overrides.

## Monitor API surface

`GET /api/git/hygiene` (planned, GH #TBD) returns a structured view:

```json
{
  "dirty_total": 487,
  "exempt": { "wiki": 269, "draft_tickets": 4 },
  "buckets": {
    "stale_behind_main": 16,
    "real_wip": 1,
    "untracked_unexempted": 34,
    "intentional_deletions": 99
  },
  "suggestions": [
    { "action": "restore", "files": [...] },
    { "action": "gitignore", "pattern": ".worktree-briefs/" }
  ]
}
```

Consumed by the Operator dashboard to show a red/green hygiene badge
per workstation. Planned, not shipped.

## Rule of thumb

If you find yourself thinking "the dirty files are fine, I'll deal
with them later" — you've already lost the discipline. The cleanup is
cheap *now*, it is never cheaper tomorrow. Every dirty file multiplies
across every session that reads state.

---

*Codified 2026-04-24 after the #1517 / #1518 pilot block and the
accompanying 489-file cleanup. First incident of this class; last one
that should ever need a doc like this.*
