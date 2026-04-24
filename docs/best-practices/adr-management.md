# ADR Management

Sister doc to [`decision-journal.md`](decision-journal.md). Decision journal is 90-day expiring policies; this is permanent architectural choices. Both are automated so they don't rot.

## The split — one more time

| Question | Where it goes |
|---|---|
| "Why does the code look this way?" — permanent structural choice | **ADR** in `docs/architecture/adr/` |
| "What is our current policy on X?" — might change in 90 days | **Decision** in `docs/decisions/decisions.yaml` |
| "Why did this specific bug happen and how do we stop a repeat?" | **Autopsy** in `docs/bug-autopsies/` |

If you're unsure, default to decision journal. Decisions can be **promoted** to ADRs after two expiry cycles of staying active (see [Promotion](#promotion)). ADRs cannot be trivially deleted.

## The threshold

Write an ADR if **a new engineer would need to know this to understand why the codebase looks the way it does**. Not "is this interesting?" — "would they be confused without it?"

Signals you need an ADR:
- A PR reviewer keeps asking "why isn't this simpler?" and the answer is long
- A new hire re-proposes the design you rejected 2 months ago
- The alternative would be obvious to try and fail at
- A non-trivial chunk of code only makes sense in the context of a constraint not visible from the code itself

## Lifecycle

```
[ write ADR-N ] ──► Accepted
                      │
                      ├──► Superseded by ADR-M   (write ADR-M that references N; N stays in repo with updated status)
                      └──► Deprecated            (architecture retired; kept for historical reference)
```

**Never delete** an ADR. Never reuse a number, even for a superseded one. The file is permanent record; status changes are appended.

### Proposed → Accepted

ADRs may be filed as `Proposed` while design discussion is active. A `Proposed` ADR that sits longer than **14 days** without reaching `Accepted` is stale — either finalize it or close it out with a one-line explanation.

### Accepted → Superseded

When a new ADR supersedes an old one:

1. Write the new ADR with `Status: Accepted` and `Related: supersedes ADR-N` in the header
2. Update ADR-N's `Status` to `Superseded by ADR-M` (add a line to its History section)
3. Run `.venv/bin/python scripts/audit/check_adrs.py --rebuild-index` to refresh the README table

### Accepted → Deprecated

When an architecture is retired without a replacement (e.g., the subsystem is removed entirely):

1. Update the ADR's `Status` to `Deprecated`
2. Add a History entry explaining what replaced it (usually a link to the removal PR)
3. Rebuild the index

## File format

Use `adr-template.md`. Every ADR MUST have:

- **Numbered header**: `# ADR-NNN: {short noun-phrase title}`
- **Status line**: `**Status**: Accepted | Proposed | Superseded by ADR-MMM | Deprecated`
- **Date**: `**Date**: YYYY-MM-DD`
- **Deciders**: humans AND any agents that contributed (Claude, Codex, Gemini) — cite bridge threads
- **Related**: GH issues, prior ADRs, key commits
- **Context / Decision / Alternatives / Consequences / Verification** sections

**One page is better than five.** If an ADR hits >200 lines, ask whether it's really one decision or three.

## Numbering

Strictly sequential: ADR-001, ADR-002, ..., ADR-N where N is the largest existing number + 1. Never reuse. `check_adrs.py --check` enforces no gaps and no duplicates.

The only time gaps are acceptable: an ADR was written and rejected before merge — then the number exists in git history as an abandoned PR. The check reports gaps as WARN not ERROR to tolerate this, but if it happens more than once a year, we're doing something wrong.

## Promotion (decision → ADR)

A decision in `decisions.yaml` that survives **two full expiry cycles** (default 180 days total) of `active` status is effectively permanent. `check_adrs.py --check-promotions` flags these as ADR candidates. Process:

1. Write an ADR that subsumes the decision (scope + rationale)
2. Update the decision's status to `superseded` with `superseded_by: "ADR-N"` in `decisions.yaml`
3. The decision stays in the journal (archive layer) but the ADR is now the canonical record

No auto-promotion — the promotion itself is an architectural judgment call. But the nag fires.

## Automation (the part that makes this stick)

Script: `scripts/audit/check_adrs.py`. Modes:

### `--check` (default; runs in SessionStart hook)

Reports:
- **Numbering**: gaps, duplicates, non-sequential files
- **Required fields**: every ADR has Status / Date / Deciders / Related sections
- **Stale Proposed**: any ADR with `Status: Proposed` older than 14 days
- **Broken supersede chains**: `Status: Superseded by ADR-M` where M doesn't exist, or where M doesn't reference N back
- **Index drift**: `README.md` `<!-- ADR-INDEX-START -->` block doesn't match the actual ADR files (missing entries, stale titles, stale status)
- **Orphaned references**: code comments mentioning "ADR-N" where N doesn't exist (grep over `scripts/`, `docs/`, `curriculum/`)

Exit codes:
- `0` — clean
- `1` — warnings (stale Proposed, index drift) — report but don't block
- `2` — errors (broken chain, missing fields, numbering gap) — CI/pre-commit should block

### `--rebuild-index`

Regenerates the `<!-- ADR-INDEX-START --> ... <!-- ADR-INDEX-END -->` block in `docs/architecture/adr/README.md` from the actual ADR files (parses `# ADR-NNN:` heading + `**Status**:` line). Sorts by number. Writes in place.

### `--check-promotions`

Reads `docs/decisions/decisions.yaml`. Reports any `active` decision whose age (today - date) exceeds **180 days**. These are ADR promotion candidates.

### `--json`

Machine-readable output for Monitor API consumption.

## SessionStart integration

`claude_extensions/hooks/session-setup.sh` calls `check_adrs.py --quiet` and folds the result into the `ISSUES` / `INFO` arrays that already surface decision-journal staleness:

- Errors → `ISSUES` (blocking feel — surfaces in red at session start)
- Warnings → `INFO` (yellow nag)
- Clean → silent

This runs in ~100ms against a typical ADR count (<20 files), so it costs nothing per session.

## Pre-commit hook

`.pre-commit-config.yaml` has a `check-adrs` hook:

- **On `docs/architecture/adr/*.md` staged** → run `--check`, block on errors
- **On `docs/architecture/adr/README.md` staged** → run `--rebuild-index` and verify the working tree matches (i.e., the author ran rebuild; otherwise re-stage after it)

This prevents drift at commit time rather than catching it in a later session.

## Anti-patterns

- **Editing an old ADR to reflect a new decision** — No. Write a new ADR that supersedes it. The old ADR is permanent.
- **"Can I just delete this, nobody cares anymore"** — No. Deprecate with a history note. Someone in 2027 will need to know.
- **Writing an ADR that says "we'll figure this out later"** — That's a `Proposed` ADR with a 14-day clock. If you're not ready, don't write it yet.
- **Scattering architectural rationale across commit messages, PR descriptions, and Slack** — Those vanish. ADRs are durable. Write the ADR, reference it from the PR.

## Rule of thumb

If you've written the same architectural explanation more than twice — once in a PR body, once in a comment, once on chat — the third time is an ADR. The next person asking the same question reads the ADR, not you.

---

*Codified 2026-04-24 after user flagged that the ADR process lacked automation. Accompanying automation: `scripts/audit/check_adrs.py`. Wired into SessionStart via `claude_extensions/hooks/session-setup.sh`.*
