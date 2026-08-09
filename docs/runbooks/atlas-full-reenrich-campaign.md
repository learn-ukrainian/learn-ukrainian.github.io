# Atlas Full-Reenrich Campaign Runbook (#6466)

This runbook documents the operator and driver procedures for the full-catalog Atlas re-enrichment campaign tooling (#6466).

## Overview & Campaign Architecture

The full-catalog campaign re-enriches all entries in `lexicon-manifest.json` using the VPS runner.
Because the remote VPS repo checkout (`/home/ops/atlas-runner/repo`) is deliberately dirty/stale (large data directories deleted for disk space), execution is isolated to the isolated work directory (`$ATLAS_RE_ENRICH_WORK_DIR`).

### Key Invariants
1. **Entry-count invariance**: Live manifest entry count is strictly unchanged.
2. **Zero non-empty overwrites**: Merging pulled results onto published lineage never overwrites existing non-empty fields.
3. **Pre-flight canary**: Execution hard-aborts with exit code 75 before modifying batch state if control lemmas fail layer filling.
4. **Circuit breaker**: Execution halts with exit code 70 if 50 consecutive entries yield total source/cache misses.
5. **Publish-side CAS**: Re-fetches the live published manifest immediately before publish and re-evaluates all invariants if moved.
6. **Shard-export integrity**: Shards are written as `.tmp` files, hashed (SHA-256), recorded in metadata, and atomically renamed.

---

## Step-by-Step Operator Recipe

### 1. Pre-flight Positive-Control Canary Check

Run the positive-control canary check locally against your target environment:

```bash
.venv/bin/python scripts/lexicon/reenrich_thin_manifest_entries.py \
  --local \
  --canary
```

- Expected outcome: Exit code `0` with `canary_passed: true`.
- Failure outcome: Exit code `75` (`CANARY_FAILURE_EXIT_CODE`) with JSON failure payload on `stderr`. Execution must abort.

---

### 2. Deploy Tooling & Launch Remote VPS Driver

From the Mac worktree, deploy the driver and launcher to the remote VPS and launch the job in `full-catalog` mode:

```bash
# Smoke test (small limit)
ATLAS_RUNNER_HOST=ops@runner-vps scripts/lexicon/runner/launch_reenrich_class_b_remote.sh \
  --target full-catalog \
  --limit 10

# Full campaign launch (detached systemd-run under 1.5G/2.0G memory limits)
ATLAS_RUNNER_HOST=ops@runner-vps scripts/lexicon/runner/launch_reenrich_class_b_remote.sh \
  --target full-catalog \
  --no-poll
```

---

### 3. Target Snapshot & Checkpointing

The driver writes a target snapshot at startup to `$ATLAS_RE_ENRICH_WORK_DIR/target_snapshot.json`:

- `slugs`: Array of target URL slugs.
- `count`: Target count.
- `sha256`: SHA-256 hash of the target slug list.

Manifest checkpoints are saved periodically every 100 entries to `$ATLAS_RE_ENRICH_WORK_DIR/manifest.json`.
Resuming a dead run reuses this snapshot and manifest checkpoint without restarting from zero.

---

### 4. Monitor VPS Execution & Circuit Breaker Probe

Check status and logs on the VPS runner:

```bash
# Check if driver process is active
ssh ops@runner-vps "ps aux | grep reenrich_thin_manifest_entries"

# Inspect live log tail
ssh ops@runner-vps "tail -n 60 /home/ops/atlas-runner/run-class-b-reenrich/reenrich.log"
```

If 50 consecutive entries fail to hit any source/cache, the circuit breaker trips, returning exit code `70` (`CIRCUIT_BREAKER_EXIT_CODE`) and logging `circuit_breaker_tripped: true`.

---

### 5. Pull-Back Results to Worktree

Once complete, pull back the output manifest and run summary:

```bash
ATLAS_RUNNER_HOST=ops@runner-vps scripts/lexicon/runner/launch_reenrich_class_b_remote.sh \
  --pull-only
```

Artifacts pulled into `batch_state/class-b-reenrich-pulled/`:
- `manifest.json`: Donor manifest with re-enriched catalog entries.
- `reenrich-summary.json`: Summary counters, target snapshot hash, categorical binning, and per-layer stats.
- `reenrich.log`: Full run log.

---

### 6. Section-Aware Additive Delta-Merge

Merge the pulled donor manifest onto the live published manifest additively:

```bash
.venv/bin/python scripts/lexicon/merge_translation_delta.py \
  --live site/src/data/lexicon-manifest.json \
  --pulled batch_state/class-b-reenrich-pulled/manifest.json \
  --local-live \
  --report batch_state/merge-report.json \
  --write
```

Verification output checks:
- `overwrite_proof_modified_nonempty_en: 0` (zero non-empty target field overwrites).
- `old_gate_not_rising: true` (count of old-gate unanchored entries did not increase).

---

### 7. Published Lineage Verification, CAS & Pointer Update

`merge_translation_delta.py` performs a pre-write Compare-And-Swap (CAS) guard on the local `live_path` file bytes pre/post merge.
For published release lineage verification prior to publishing:

1. Re-pull the published manifest / pointer (`lexicon-manifest.pointer.json` or release asset) and compare `json_sha256` against the baseline recorded at snapshot time.
2. If the published release lineage moved (SHA-256 drift), re-pull the published manifest as live baseline, re-run `merge_translation_delta.py`, and verify full invariants (`overwrite_proof == 0`, `old_gate_not_rising == true`, entry count invariance).
3. Verify fingerprint sidecar and pointer gate:

```bash
.venv/bin/python scripts/lexicon/publish_manifest.py \
  --manifest site/src/data/lexicon-manifest.json \
  --verify-only
```

---

### 8. Shard Export Integrity

Export the open dataset shards with temporary-file atomic renames and per-shard SHA-256 hashes:

```bash
.venv/bin/python scripts/lexicon/export_open_dataset.py \
  --write
```

Output integrity verification:
- Each shard in `data/lexicon-dataset/dataset/*.jsonl` is written as `.tmp` first, then atomically renamed.
- `data/lexicon-dataset/dataset/_metadata.json` records `shard_integrity` containing per-shard `sha256`, `bytes`, and `entries`.

---

### 9. Residual Metrics Census

Upon completion of the full-catalog campaign, record the summary metrics in the release notes / PR:

- **Total Catalog Target**: Recorded in `target_snapshot.json` (`count`, `sha256`).
- **Categorical Binning Breakdown**:
  - `ENRICHED`: Entries with learner English anchor or translation.
  - `DETERMINISTIC_EXCLUSION`: Proper nouns and deterministic exclusions.
  - `UNRESOLVED_RESIDUAL`: Remaining unanchored entries.
- **Layer Coverage Counters**:
  - `proverbs`: Entries with filled proverb sayings.
  - `usage_notes`: Entries with filled usage notes essays.
  - `grinchenko`: Entries with Grinchenko 1907 attestation cards.
  - `forms`: Entries with VESUM morphology paradigms.
