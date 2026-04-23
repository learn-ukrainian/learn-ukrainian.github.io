# Monitor API — lock-state endpoints for all tracks

## Goal

Add Monitor API endpoints that expose wiki + plan lock state, so agents
and the user can query lock progress without grepping file systems.

## Current state of truth (no code change — just reference)

Lock markers live in two files per slug:

1. **Plan YAML** at `curriculum/l2-uk-en/plans/{track}/{slug}.yaml`
   contains `lifecycle: locked` plus `reviewed_at`, `reviewed_by`,
   `review_notes`.
2. **Wiki review file** at `wiki/.reviews/pedagogy/{track}/{slug}-review-LOCKED.md`
   (the `-LOCKED` suffix is the marker).

For now, "locked" = both files present. If plan says locked but no
review-LOCKED.md (or vice versa), surface as `partially_locked` so
drift is visible.

## Endpoints to add

### 1. `GET /api/state/locks/{track}` — per-track detail

Response:
```json
{
  "track": "a1",
  "generated_at": "2026-04-23T...",
  "total_slugs": 55,
  "locked_count": 10,
  "partially_locked_count": 0,
  "unlocked_count": 45,
  "locked": [
    {
      "slug": "at-the-cafe",
      "plan_lifecycle": "locked",
      "reviewed_at": "2026-04-23T...",
      "reviewed_by": "codex-...",
      "has_review_locked_md": true,
      "review_md_path": "wiki/.reviews/pedagogy/a1/at-the-cafe-review-LOCKED.md"
    },
    ...
  ],
  "partially_locked": [
    {
      "slug": "foo",
      "plan_lifecycle": "locked",
      "has_review_locked_md": false,
      "reason": "plan marked locked but no -LOCKED.md review file"
    }
  ],
  "unlocked": ["reading-ukrainian", "special-signs", ...]
}
```

Slug list comes from `curriculum/l2-uk-en/curriculum.yaml`
`levels.{track}.modules`.

### 2. `GET /api/state/locks` — all-tracks summary

Response:
```json
{
  "generated_at": "2026-04-23T...",
  "tracks": {
    "a1": {"total": 55, "locked": 10, "partially_locked": 0, "unlocked": 45},
    "a2": {"total": 69, "locked": 0, ...},
    "b1": {"total": 100, "locked": 0, ...},
    ...
  },
  "totals": {"total": 1776, "locked": 10, "partially_locked": 0, "unlocked": 1766}
}
```

### 3. Add to `GET /api/state/manifest` index

Include `"locks": {"url": "/api/state/locks", "cache": "miss|hit"}` in
the manifest response so agents discover it via the standard bootstrap.

## Implementation notes

1. Put the logic in `scripts/monitor_api/` next to existing track-state
   endpoints. Follow the existing cache pattern (TTL ~60s, mtime-based
   invalidation on `curriculum.yaml` + `curriculum/l2-uk-en/plans/**` +
   `wiki/.reviews/**`).
2. Parse plan YAML with `yaml.safe_load`. Don't blindly assume field
   presence — treat missing `lifecycle` as "unlocked".
3. Glob patterns:
   - plans: `curriculum/l2-uk-en/plans/{track}/*.yaml`
   - reviews: `wiki/.reviews/*/{track}/*-review-LOCKED.md` (pedagogy or
     grammar subdir depending on track — `a1/a2` are pedagogy; `b1+`
     are grammar; seminars under their own names). Use glob with `*`
     on the domain dir, not a hardcoded `pedagogy/`.
4. Handle seminar tracks in `curriculum.yaml` (hist, bio, lit, etc.).
   If a track has no plans yet, return `total: 0, locked: 0`
   gracefully.

## Acceptance criteria

- [ ] `GET /api/state/locks/a1` returns the current 10 locked a1 slugs
      plus 45 unlocked
- [ ] `GET /api/state/locks/b2` returns `total: 114, locked: 0` (no
      errors even though B2 has no lifecycle-marked plans yet)
- [ ] `GET /api/state/locks` returns all 22 tracks aggregated
- [ ] `GET /api/state/manifest` includes `"locks"` entry
- [ ] Pytest coverage for:
  - Pure-locked slug (both markers present)
  - Unlocked slug (neither marker)
  - Partially-locked (plan YAML says locked but review-LOCKED.md absent)
  - Track with zero plans (seminar track, empty response)
- [ ] No regressions on existing manifest / orient endpoints (run full
      `pytest tests/test_monitor_api*` green)
- [ ] `docs/MONITOR-API.md` updated — add the 3 endpoints with
      sample responses

## Worktree

```
git worktree add -b codex/monitor-api-locks .worktrees/codex-monitor-api-locks
cd .worktrees/codex-monitor-api-locks
# work, commit, push, PR

gh pr create --title "feat(monitor-api): lock-state endpoints per track + summary" --body "..."
```

Do NOT auto-merge. User reviews + merges.

## Do NOT

- Do not modify any plan YAML or wiki review file in this PR (read-only
  observability)
- Do not add a /api/state/lock-slugs/{slug}/force-lock write endpoint
  — lock is done by the review-and-lock agent workflow, not via API
- Do not add authentication — the Monitor API is localhost-only today
  (preserve that)

## Hard timeout

3600s (1h). Small task.
