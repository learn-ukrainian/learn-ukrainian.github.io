# #1452 P1-A — Alignment manifest hash contract

## Why

EPIC #1451's highest-leverage architectural move. The alignment pipeline today has NO runtime contract coupling its layers. Plans change, prompts change, tokenizer changes, sources.db changes — and downstream sidecars get consumed silently, stale. Every recent alignment incident (#1403, #1431, #1448) is an instance of this missing invariant. Full analysis: `docs/architecture/2026-04-23-alignment-pipeline-audit.md` §3.A1, §3.A2 and `docs/bug-autopsies/alignment-contracts.md` §1.

Codex's own #1450 adversarial take identified this as "the biggest live risk" and proposed the manifest as the single-highest-leverage structural change.

## What to build

A new module `scripts/build/alignment_manifest.py` that composes a deterministic hash from the full set of inputs that should invalidate any cached build artifact. The hash + its components get STAMPED into every generated sidecar as an `alignment_manifest` block. A companion checker function validates a stamped artifact against the CURRENT manifest and returns `(fresh, mismatch_reasons)`.

This PR is ONLY the manifest module + its unit tests. The enforcement (refuse-to-reuse-stale-artifacts) is the next PR, #1453 (P1-B), dispatched in parallel — it will consume this module's public API.

## Contents the manifest MUST hash

Each item as a separate field in the manifest dict, so callers can see WHICH component changed:

| Key | Source of hash |
|---|---|
| `plan_hash` | SHA-256 of the canonical-ordered YAML bytes of `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (the plan this build is for) |
| `sources_hash` | SHA-256 of a manifest of `data/sources.db` — one row per indexed table: `{table_name, row_count, max_rowid}`. DO NOT hash the full DB file (too slow and too volatile on writes). |
| `template_hashes` | Dict of `{phase_name: sha256(template_bytes)}` for each writer/reviewer phase template. Minimal scope: everything under `.claude/phases/claude/`, `.gemini/phases/gemini/`, and the v6 chunk/review prompt templates referenced from `scripts/build/v6_build.py` and `scripts/build/phases/*.py`. Use a deterministic traversal. |
| `canonical_anchor_hash` | SHA-256 of `data/canonical_anchors.yaml` bytes (landed in #1447). |
| `tokenizer_version` | A string constant module-level in `scripts/build/phases/wiki_compressor.py`. Add it (e.g. `TOKENIZER_VERSION = "2026-04-23"`) if it doesn't exist — bump on tokenizer semantic change. |
| `threshold_snapshot` | Dict of the level-relevant audit + review thresholds from `scripts/audit/config.py` (`LEVEL_CONFIG`) and `scripts/build/v6_build.py` (review target). Tuple-of-tuples form so it hashes deterministically. |
| `decisions_subset` | List of `(decision_id, status)` tuples for every ACTIVE decision in `docs/decisions/decisions.yaml` whose `scope` is `pipeline` or `architecture`. Excludes content-scope decisions that don't affect build output. |

The composite `manifest_hash` is SHA-256 of the JSON-canonicalized dict of all the above.

## Public API

```python
# scripts/build/alignment_manifest.py

def compose_manifest(*, level: str, slug: str) -> dict:
    """Build the full manifest dict (callers can inspect fields or the hash)."""

def manifest_hash(manifest: dict) -> str:
    """Return the SHA-256 hex digest of the canonicalized manifest."""

def stamp_artifact(artifact: dict, manifest: dict) -> dict:
    """Return artifact with `alignment_manifest` block injected (non-destructive)."""

def validate_stamped_artifact(
    artifact: dict,
    current_manifest: dict,
) -> tuple[bool, tuple[str, ...]]:
    """Return (is_fresh, mismatch_reasons). Mismatch reasons are per-field keys
    (e.g. ('plan_hash', 'template_hashes.v6_write')) so callers can log which
    upstream change invalidated the artifact."""
```

Stamping a NEW field into a sidecar: add `alignment_manifest` at top level of the dict. Structure:

```yaml
alignment_manifest:
  composite_hash: <sha256>
  composed_at: <iso8601>
  components:
    plan_hash: <sha256>
    sources_hash: <sha256>
    template_hashes: {...}
    canonical_anchor_hash: <sha256>
    tokenizer_version: "..."
    threshold_snapshot: {...}
    decisions_subset: [...]
```

## Tests (required)

Create `tests/test_alignment_manifest.py`:

1. `test_manifest_is_deterministic` — calling `compose_manifest` twice with the same inputs returns identical hash.
2. `test_plan_change_invalidates_manifest` — mutate the plan YAML, re-compose, hash differs.
3. `test_sources_db_change_invalidates_manifest` — insert a row into a fixture DB, re-compose, hash differs.
4. `test_template_change_invalidates_manifest` — mutate one writer phase template, re-compose, hash differs.
5. `test_canonical_anchor_change_invalidates_manifest` — mutate `canonical_anchors.yaml`, re-compose, hash differs.
6. `test_tokenizer_version_bump_invalidates_manifest` — monkeypatch the version string.
7. `test_threshold_change_invalidates_manifest` — change a threshold.
8. `test_decision_status_change_invalidates_manifest` — flip an active decision to superseded.
9. `test_stamp_roundtrip` — stamp then validate on the same manifest returns `(True, ())`.
10. `test_validate_reports_specific_mismatch` — stamp, mutate plan, validate returns `(False, ("plan_hash",))`.

Use `tmp_path` fixtures, monkeypatch where touching module globals, and a tiny SQLite fixture for `sources_hash`. **Do NOT hit the real `data/sources.db` in tests.**

## Out of scope (later PRs)

- **Integration with `v6_build.py` and `module_memory.py`** → that's #1453 P1-B, dispatched in parallel.
- **Actual refusal-to-reuse-stale behavior** → #1453.
- **Manifest persistence to disk as standalone file** → not needed; stamping into sidecars is the contract.
- **Changing existing sidecar formats** → new `alignment_manifest` field is additive.

## Non-goals (do NOT do)

- Do NOT add the hash to `contract.yaml` / `wiki-excerpts.yaml` / `state.json` / `module-memory.yaml` YET — that's #1453. Stay in the manifest module + tests.
- Do NOT touch the convergence loop or any existing pipeline code path.
- Do NOT optimize `sources_hash` by computing a real content hash — row-count+max-rowid per table is the agreed cheap-but-sufficient proxy.

## Worktree

Already created: `.worktrees/codex-1452-alignment-manifest` on branch `codex/1452-alignment-manifest`, based on `origin/main`. Commit, push, open PR. Do NOT auto-merge.

## PR title

`feat(build): alignment manifest hash contract (#1452 P1-A of #1451)`

## References

- Audit: `docs/architecture/2026-04-23-alignment-pipeline-audit.md`
- EPIC: `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md`
- Autopsy: `docs/bug-autopsies/alignment-contracts.md` §1
