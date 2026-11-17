# Plan-Version Drift Prevention

> **Status:** historical. The V6 code this page describes (`v6_build.py`, its plan-hash helpers and the one-shot plan-hash migration) has been removed; the rule of thumb still applies to any build that reads a plan.

## What it is

Plan-version drift occurs when writer artifacts (skeleton, write, exercises) are generated from plan version N, then the plan is edited to version N+1 (e.g. via `add_dialogue_situations.py` or manual edits), but the writer artifacts are not regenerated. The reviewer reads the current plan; the writer built against the old one. Result: low plan-adherence scores, review degradation loops.

**Observed symptoms (A1 sweep 2026-04-14):**
- Plan adherence mean 6.26/10 across 19 failing modules
- Reviewer cites off-scenario dialogues ("room furniture" when plan says "pet shop")
- Fix loop degrades content (8.8 → 8.0 → 7.2) because fixes target the wrong scenario

## Prevention mechanisms (shipped 2026-04-15, #1230)

### 1. Plan-hash invalidation (V6 build)
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

## Rule of thumb

**Never edit a plan after the write phase without re-running from skeleton.** Prevention is cheaper than recovery.
