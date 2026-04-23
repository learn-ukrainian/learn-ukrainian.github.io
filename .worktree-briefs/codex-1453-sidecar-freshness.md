# #1453 P1-B — Sidecar freshness invariant (refuse stale reuse)

## Why

Closes the two most dangerous silent-drift paths in the build pipeline:

1. **`scripts/build/v6_build.py:3207`** (`_ensure_contract_artifacts`) reloads `contract.yaml` + `wiki-excerpts.yaml` from disk if they exist — **with zero validation** against the current plan, wiki packet, prompt templates, canonical-anchor registry, or tokenizer version. A "consistent" run can be consistent against yesterday's inputs.
2. **`scripts/build/module_memory.py:293-316`** invalidates learned constraints ONLY on `plan_hash` mismatch — `sources_hash` updates silently. Corpus/rule/tokenizer changes land but old writer constraints persist.

Full analysis: `docs/bug-autopsies/alignment-contracts.md` §1 + §2.

## Dependency

**Depends on #1452 P1-A** (alignment manifest module). Dispatched in parallel — when #1452 lands on `main`, rebase this branch on `main` and wire the manifest API into the two fixes below. If `scripts/build/alignment_manifest.py` doesn't yet exist on main when this dispatch runs, implement stub calls (`from build.alignment_manifest import compose_manifest, manifest_hash, stamp_artifact, validate_stamped_artifact`) and skip tests that exercise real mismatch — add a TODO comment + issue reference. Rebase after #1452 lands to un-stub.

## Fix 1 — `_ensure_contract_artifacts` hash check

**File:** `scripts/build/v6_build.py` (function `_ensure_contract_artifacts`, ~line 3196–3239)

**Current behavior:** `if contract_path.exists() and excerpts_path.exists(): return <load them blindly>`

**New behavior:**

```python
def _ensure_contract_artifacts(level, module_num, slug, packet_path=None, *, log_creation=False):
    from build.alignment_manifest import (
        compose_manifest, stamp_artifact, validate_stamped_artifact,
    )

    current_manifest = compose_manifest(level=level, slug=slug)
    contract_path = _contract_path(level, slug)
    excerpts_path = _wiki_excerpts_path(level, slug)

    if contract_path.exists() and excerpts_path.exists():
        contract = _load_yaml_artifact(contract_path)
        excerpts = _load_yaml_artifact(excerpts_path)
        contract_fresh, contract_mismatches = validate_stamped_artifact(contract, current_manifest)
        excerpts_fresh, excerpts_mismatches = validate_stamped_artifact(excerpts, current_manifest)
        if contract_fresh and excerpts_fresh:
            return contract, excerpts
        _log(
            f"  ♻️  Rebuilding contract/excerpts — stale sidecar "
            f"(contract mismatches: {contract_mismatches}, "
            f"excerpts mismatches: {excerpts_mismatches})"
        )
        # Fall through to rebuild.

    # ... existing build logic ...
    contract, excerpts = build_contract(plan, wiki_packet, level=level, slug=slug, module_num=module_num)
    # Stamp with current manifest BEFORE writing:
    contract = stamp_artifact(contract, current_manifest)
    excerpts = stamp_artifact(excerpts, current_manifest)
    _save_yaml_artifact(contract_path, contract)
    _save_yaml_artifact(excerpts_path, excerpts)
    # ... existing log_creation logic ...
    return contract, excerpts
```

Also: when `_save_style_review_advice_to_contract` (line ~3242) mutates `contract.yaml`, it MUST re-stamp with the current manifest — the contract after style-review advice is a new version. Add the re-stamp before writing.

## Fix 2 — `module_memory` full-manifest invalidation

**File:** `scripts/build/module_memory.py` (lines ~78–91 and ~285–320)

**Current:** `_default_memory` stores `plan_hash`, `plan_version`, `sources_hash` as independent fields. The invalidation path at 293–316 only clears `constraints` on `plan_hash` mismatch; `sources_hash` is updated silently.

**New:** replace the trio with a single `alignment_manifest_hash` that's the composite hash from the manifest module. Keep `plan_version` for human-readable tracking. Invalidation predicate: clear `constraints` AND append an invalidation event to `events` on ANY manifest-hash mismatch (not just plan).

Add a back-compat read path: if a pre-existing memory file has `plan_hash` / `sources_hash` but no `alignment_manifest_hash`, treat as stale on first read and invalidate constraints. Log the migration.

```python
def _default_memory(*, alignment_manifest_hash=None, plan_version=None):
    return {
        "alignment_manifest_hash": alignment_manifest_hash or "",
        "plan_version": int(plan_version or 0),
        "constraints": [],
        "history": [],
        "events": [],
    }

# In the load+invalidate path, compose current manifest and compare:
current_hash = manifest_hash(current_manifest)
stored_hash = merged.get("alignment_manifest_hash", "")
if stored_hash and stored_hash != current_hash:
    invalidated = True
    merged["constraints"] = []
    merged["events"].append({
        "type": "alignment_manifest_invalidation",
        "ts": datetime.now(tz=UTC).isoformat(),
        "previous_hash": stored_hash,
        "current_hash": current_hash,
    })
merged["alignment_manifest_hash"] = current_hash
```

## Fix 3 — state.json + module-memory.yaml stamping

Add manifest stamping to:
- `scripts/build/v6_build.py` wherever `state.json` is written for a module (grep for `state.json` in `v6_build.py`).
- `scripts/build/module_memory.py::save_module_memory` — stamp with current manifest before write.

## Tests

Extend existing test suites + add new cases:

1. `tests/test_v6_contract_artifact_freshness.py` (new): build a module with fixtures, assert sidecars carry `alignment_manifest.composite_hash`. Mutate the plan, rerun `_ensure_contract_artifacts`, assert log message + new sidecar hash matches new manifest.
2. `tests/test_module_memory.py` (existing or new): assert full-manifest mismatch invalidates constraints; assert legacy `plan_hash`-only file gets migrated + invalidated on first read.

## Verify

- Full pytest green, touching `.venv/bin/pytest tests/test_v6_*.py tests/test_module_memory*.py tests/test_alignment_manifest.py`.
- Live smoke: after merge, re-running `v6_build.py a1 10 --writer claude-tools` with EXISTING sidecars should reuse them (log: "sidecars fresh"). Mutating the plan manually mid-run and re-firing should emit "Rebuilding contract/excerpts — stale sidecar".

## PR

Title: `feat(build): sidecar freshness invariant — refuse stale reuse (#1453 P1-B of #1451)`

Body: reference #1453 + EPIC #1451 + the manifest module from #1452. Do NOT auto-merge.

## Worktree

Already created: `.worktrees/codex-1453-sidecar-freshness` on branch `codex/1453-sidecar-freshness`, based on `origin/main`.

**If #1452 is not yet on `main` when you start:** stub the imports (see Dependency section). **If #1452 is on `main`:** rebase `origin/main` first, then implement.

## References

- Autopsy: `docs/bug-autopsies/alignment-contracts.md` §1, §2
- EPIC: `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md` Phase 1
- Codex's own adversarial finding (bridge message 429) — this closes finding #1 + #2.
