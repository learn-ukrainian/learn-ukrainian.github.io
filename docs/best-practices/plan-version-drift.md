# Plan-Version Drift Prevention

## What it is

Plan-version drift occurs when writer artifacts (skeleton, write, exercises) are generated from plan version N, then the plan is edited to version N+1 (e.g. via `add_dialogue_situations.py` or manual edits), but the writer artifacts are not regenerated. The reviewer reads the current plan; the writer built against the old one. Result: low plan-adherence scores, review degradation loops.

**Observed symptoms (A1 sweep 2026-04-14):**
- Plan adherence mean 6.26/10 across 19 failing modules
- Reviewer cites off-scenario dialogues ("room furniture" when plan says "pet shop")
- Fix loop degrades content (8.8 → 8.0 → 7.2) because fixes target the wrong scenario

## Prevention mechanisms (shipped 2026-04-15, #1230)

### 1. Plan-hash invalidation (`scripts/build/io_utils.py` + `v6_build.py`)
Every write-phase completion now records `plan_hash` (SHA256 of plan YAML bytes) in `state.json`. Before review/publish/audit, the pipeline recomputes the hash and aborts if it mismatches:

```
WARN: Plan version changed since write phase — marking skeleton/write/exercises/annotate/verify as stale
```

`--resume` treats stale phases as re-run-required, even if their state is `complete`.

### 2. Plan contradiction validator (`scripts/build/phases/plan_validator.py`)
Pre-build gate: `validate_plan_consistency(plan, slug)` checks that `dialogue_situations` settings/exclusions are consistent with `content_outline` bullets. Blocks the build before any content is generated.

### 3. Writer prompt precedence (`v6_build.py` prompt template)
Writer prompt now states: "If the skeleton, examples, or any earlier prompt text conflicts with the current plan YAML, **the plan wins**." Prevents skeleton drift from silently overriding plan intent during the write phase.

### 4. `add_dialogue_situations.py` fix
The script now rewrites `content_outline` dialogue bullets to match the injected `dialogue_situations`, not just appends the new field. Keeps plan internally consistent after injection.

## Migration

For existing modules built before the hash system:

```bash
# Dry run — see what would change
.venv/bin/python scripts/migrate/migrate_v6_plan_hashes.py

# Apply
.venv/bin/python scripts/migrate/migrate_v6_plan_hashes.py --apply
```

Phase records without `plan_hash` are treated as unknown (conservative: may trigger staleness on next plan edit).

## Rule of thumb

**Never edit a plan after the write phase without re-running from skeleton.** Use `v6_build.py {level} {num} --step skeleton` to force a clean rebuild. The hash system will catch violations automatically, but prevention is cheaper than recovery.
