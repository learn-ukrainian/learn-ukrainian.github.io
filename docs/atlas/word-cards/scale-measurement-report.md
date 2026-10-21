# Word-card universe scaling and prerequisite measurement

Refs #8977 and #11031, OO-38. Measurement date: 2026-10-20 UTC.
Code examined: `32c865184103995267241b9c4f8cb4b79b2c35cb`.
Scope: compute-only investigation, read-only source queries, and one authentic
pilot replay. No Ukrainian content was generated, and no source store changed.

## Answer to the time question

A defensible time to finish all words is **UNKNOWN**. The production universe
specification and its prerequisite evidence were not supplied, the combined
source denominator is unfrozen, and no Phase 6 throughput run was admitted.

For resource planning only, repeating the observed pilot workload at the same
cost per allocated unit gives about **28.24 hours and 22.09 GiB of JSON** for the
685,391-unit lemma-plus-successful-ULIF subtotal. Preserving VESUM entry identities
instead gives 705,193 units, **29.05 hours and 22.73 GiB**. Both omit supplementary
units and assume the pilot's sparse output and exclusions repeat. These are
arithmetic scenarios, not forecasts, bounds, or completion estimates.

The replay took 22.2477 seconds for 150 allocated pilot units, but wrote only
138 cards. The other 12 have the recorded reason
`proper_name_without_source_scope`. Process exit 0 therefore did not satisfy the
predeclared check of 150 emitted cards. No certified-card production rate follows.
Source coverage, identity resolution, independent evaluation and certification
remain outside those time figures.

## Engine prerequisite audit

The implementation and its [Phase 6 contract](universe-reconciliation-spec.md)
require the following authentic, digest-pinned inputs.

| Input | Repository finding | Consequence |
| --- | --- | --- |
| `spec_path`, `word-card-universe-spec.v1`, and trusted SHA-256 | Schema and synthetic test constructor exist; no tracked production JSON or YAML instance found. No private locator was supplied. | Cannot enter `_load()` successfully. |
| `source_spec`, `word-card-gold-spec.v1` | Schema and Phase 4 procedures exist; no tracked production specification found. | No replayable complete source manifest, accounting, census or lexical universe. |
| Phase 4 `word-card-complete-data.v1` clearance | No tracked production receipt found. | Phase 1/2 completion and source accounting with zero unresolved gaps are unproven. |
| `certifications`, nonempty Phase 5 receipt array | Schema and fixtures exist; no tracked production `word-card-certification-receipt.v1` found. | No authentic exact-card certification inventory for `_plan()`. |
| `inventory`, `word-card-universe-inventory.v1` | No tracked production instance found. | Independent lexical dimensions, card allocation and source strata are unavailable. |
| `plan`, `word-card-universe-plan.v1` | No tracked production instance found. | No full-denominator mapped, unresolved and excluded dispositions. |
| `runtime_sha256` and `resource_acceptance` | No supplied frozen runtime binding or accepted full-scale trial. | Ordinary `build()` also needs full-scale resource and resume evidence. |

The audit covers the tracked tree, including sparse paths through Git, rather
than assuming a missing materialized directory means absent source. Private
steward evidence might exist elsewhere; this task received no such locator.
The pilot manifest, identity registry and batch-1 receipt are different schemas
and cannot substitute for these inputs. Synthetic acceptance actors and fixtures
are mechanics tests, not production authority.

The tracked-document search returned no matches, exit 1:

```bash
git grep -n -E \
  'word-card-(universe-spec|universe-inventory|universe-plan|gold-spec|complete-data|certification-receipt)\.v1' \
  HEAD -- '*.json' '*.yaml' '*.yml'
```

### Exact observed refusal

Both actual calls below used an intentionally absent spec in ignored local
storage. The all-zero digest is a probe argument, never an accepted pin.
They demonstrate the first missing-file failure only, not later gate execution.

```python
from pathlib import Path
from scripts.atlas.word_card_universe import build

for limit in (1000, 10000):
    build(Path('batch_state/reports/absent-universe-spec.json'), '0' * 64,
          Path(f'batch_state/reports/universe-{limit}.sqlite3'), max_units=limit)
```

Each call raised `FileNotFoundError`, errno 2:

```text
[Errno 2] No such file or directory: '<worktree>/batch_state/reports/absent-universe-spec.json'
```

The public error abbreviates the absolute worktree prefix. Neither checkpoint
existed afterward. This API does not wrap a missing spec in a typed `REFUSED`
result. The call reaches `gold.read()` through `build()` and `_load()` and fails
at `Path.read_bytes()` before opening SQLite.

`max_units` limits new checkpoint writes after full prerequisite replay. It is
an interruption boundary, not a 1,000- or 10,000-unit input sample. The optional
`resource_trial=True` skips only the resource-acceptance adapter. It still
requires a real spec, complete sources, inventory, plan and current certifications.
No prerequisites were fabricated to obtain a timing.

## Exact local counts and denominator limits

The queries ran in a read transaction on each database using SQLite URI
`mode=ro` and `PRAGMA query_only=ON`. `sources.db` had mode `0444`; `vesum.db`
had mode `0644` and was opened read-only. Size and modification time were
unchanged across the queries. This is a local database snapshot, not an
independently accepted source freeze. There was no cross-database atomic freeze.

| Quantity | Exact count | Query or evidential role |
| --- | ---: | --- |
| Distinct literal VESUM lemmas | 422,656 | `SELECT COUNT(DISTINCT lemma) FROM forms_all` |
| VESUM entries, preserving entry IDs | 442,458 | `SELECT COUNT(DISTINCT entry_id) FROM forms_all` |
| VESUM form rows | 6,970,759 | `SELECT COUNT(*) FROM forms_all` |
| All ULIF entry rows | 269,269 | `SELECT COUNT(*) FROM ulif_dictua_entries` |
| ULIF rows with homonym check set | 262,812 | `SELECT COUNT(*) FROM ulif_dictua_entries WHERE homonym_checked=1` |
| Successful checked ULIF entries | 262,735 | Same predicate plus `status='ok'` |
| Checked ULIF parse-error entries | 77 | `status='parse_error' AND homonym_checked=1` |
| Distinct successful checked ULIF queries | 250,680 | `COUNT(DISTINCT normalized_query)` with the successful checked predicate |
| ULIF phraseology sections | 8,133 | `SELECT COUNT(*) FROM ulif_dictua_sections WHERE kind='phraseology'` |
| Declared supplementary universe units | UNKNOWN | No frozen source manifest supplied. Unknown is not zero. |
| Declared MWE universe units | UNKNOWN | Phraseology sections and accepted extractions do not establish unique frozen MWE membership. |
| Combined frozen source-unit denominator | UNKNOWN | Requires independently enumerated source units and exact manifests. |

The ULIF status cross-check was 262,735 successful checked rows, 3 successful
unchecked rows, 77 checked parse errors, 7 unchecked parse errors and 6,447
unchecked `not_found` rows, summing to 269,269. Excluding parse errors from a
throughput subtotal does not erase them from source-accounting obligations.

The requested spelling-level diagnostic sum is
`422656 + 262735 = 685391`. At entry level the corresponding sum is
`442458 + 262735 = 705193`. Counting every checked ULIF row instead yields
`442458 + 262812 = 705270`, including 77 parse errors needing dispositions.
None is the number of unique Ukrainian words or certified cards. Cross-source
homographs and homonyms require identity resolution, and VESUM source units may
have a finer grain than entries. Do not deduplicate source units by spelling.

[The source matrix](../../../registry/atlas/source-completeness/required-source-matrix.md)
is explicitly `UNFROZEN` and retains `G-UNIVERSE`. The final denominator is
`N = sum(len(range.units) for range in source_manifest.ranges)` after all
memberships are `KNOWN`, as `_enumerate()` implements. The associated lexical,
spelling, sense, MWE, form and card counts remain separate dimensions.

The historical pilot declares 15 MWE units within its 150 units. The data plan
reports 3,385 accepted WP3 phraseology extractions. Neither count can be added
as the global MWE denominator: their membership, overlap and unit grain have
not been reconciled with a complete source manifest.

## Observed pilot resources

One run executed `scripts.atlas.word_card_assembly build`, including input loading,
full-store fingerprinting, WP3 extraction, assembly and JSON writes. It did not
execute Phase 6, the full verifier, language review or certification. The frozen
pilot manifest digest was
`7e95dbc7d5b0b5dcf2df329bfc319abf699a16d1ae4ce92706eb994acda97197`.

| Measurement | Observed value |
| --- | ---: |
| Wall time, `perf_counter()` around subprocess | 22.247732 s |
| Aggregate child user CPU | 16.941860 CPU-s |
| Aggregate child system CPU | 3.921690 CPU-s |
| Aggregate child peak resident memory | 117,268 KiB, 114.52 MiB |
| Allocated input units | 150 |
| Written card files | 138, with 2,993 assertions |
| Written JSON files, including ledgers | 141 |
| Card JSON logical bytes | 4,710,337 |
| All output JSON logical bytes | 5,191,076 |
| All output JSON filesystem allocation | 5,492,736 bytes |

CPU and peak RSS use Linux `RUSAGE_CHILDREN`; the accounting also includes earlier
Git subprocesses from revision and prerequisite probes. CPU is therefore an
approximate pilot cost, and RSS is the maximum across these children. Parent
measurement queries are excluded.
The measurement was run on a multi-core Linux host under shared load; no cache
flush or exclusive host reservation occurred.
There is one observation, so no median, variance, or confidence interval.
Temporary extraction storage, raw-source cache, SQLite checkpoint, journals,
protected evaluation and release artifacts are excluded from the output sizes.

The current replay reported 85 high, 1 medium and 52 unresolved identities for
its 138 emitted cards. The [historical pilot findings](pilot-findings.md) report
87 high, 3 medium and 60 unresolved across 150 cards, or 58%, 2% and 40%.
These are different output populations. The current run verified 272 frozen
rows while applying today's output-scope filter. The literal 150-output check
failed; the 12 exclusions are explicit in the ledger. No claim of historical
output equivalence, held-out isolation or linguistic accuracy follows.

### Conditional arithmetic per 1,000 allocated units

For the observed workload only, multiply additive costs by `1000 / 150`.
This retains the replay's 138 emitted cards per 150 allocations and sparse fields.

| Cost | Per 1,000 allocated units | Per 10,000 allocated units |
| --- | ---: | ---: |
| Wall time | 148.32 s | 1,483.18 s, 24.72 minutes |
| CPU time | 139.09 CPU-s | 1,390.90 CPU-s |
| Output JSON logical size | 34.61 MB | 346.07 MB |
| Output filesystem allocation | 36.62 MB | 366.18 MB |
| Peak RAM | UNKNOWN | UNKNOWN |

MB denotes decimal bytes; GiB denotes `2**30` bytes. RAM is a peak, not an
additive per-unit consumption. The observed 114.52 MiB cannot be multiplied
into a production memory budget. Phase 6 holds whole-universe dictionaries,
card bodies and inventory in memory before batching, even with `max_units=1000`.
A production RAM estimate requires representative full-input resource trials.

The scenario formula is `wall_seconds = 22.247732454 * N / 150` and
`json_bytes = 5191076 * N / 150`. For the 705,193-entry subtotal it gives
104,592.97 seconds, 98,085.53 CPU-s and 24,404,736,384 logical bytes.
The scaled CPU figure reflects aggregate child CPU, including the earlier Git
probe subprocesses noted above.
Filesystem allocation scales to 24.05 GiB under the same small-file distribution.
Additional declared units would add 148.32 seconds and 34.61 MB per 1,000 only
under these same assumptions. There is no numerical total for the unfrozen N.

Fixed store hashing costs make repeated pilot batches differ from a single
large build. Full cards may have more senses and assertions. Phase 6 adds source
and certification replay, canonical hashing, sorting, SQLite indexes, atomic
batches and resume checks. Each invocation revalidates the full universe; many
small resumes repeat that cost. Cold caches, concurrency and SQLite journal
peaks also change resources. No hotspot profile was captured, so no measured
limiter, speedup or production linearity is claimed.

Historical F14 says whole-table ingestion took more than ten minutes, while
pilot extraction took seconds. It supplies no exact elapsed time or consumed
full-harvest count. It cannot yield an entries-per-second rate. `load_inputs()`
now calls `write_extract()` before the same ingestion modules, while still
fingerprinting source stores. The historical observation supports investigating
scan and replay cost; it does not measure current Phase 6 throughput.

## Bottlenecks and what removes them

| Bottleneck | Evidence and effect | Required removal and owner |
| --- | --- | --- |
| Source coverage | Unfrozen source matrix and missing complete-data clearance prevent enumeration. Historical WC-S01 had no modern meanings for its 135 lexemes; the current replay still records 120 `source_absent` and 18 held definition fields. Counts measure available records, not field completeness. | Open-model-data owner completes Phase 1 source freeze, ingestion and Phase 2 reconciliation, retaining each gap and authentic source locator. Rights are already decided and are not a gate. |
| Identity resolution | Historical 60 unresolved identities comprise 57 without a same-class equal/subset paradigm, 2 competing with refused forms, and 1 with two compatible candidates. Spellings cannot choose a homonym. | Language lane supplies reviewed identity mappings and source evidence. Automation uses POS and proper/common class, aspect compatibility, whole-slot matching, stress evidence and separate homonym IDs. Repair stale forms upstream; matching-rule changes require designated approval. Faster scans do not resolve ambiguous identity. |
| Certification per release | Phase 6 replays Phase 5 receipts for exact card bytes and the same complete-data universe. A mechanically built checkpoint cannot authorize export. No production certification packet was supplied here. | Certification steward and independent language reviewers run Phase 5 batch pipelines with held-out source-side evaluation, exact artifacts, qualification and receipt verification. Changed inputs or runtime invalidate affected proof. This report authorizes no new pipeline design. |

## Reproduction and residual ownership

Local retained evidence consists of
`batch_state/reports/scale-measurement-probe.py.txt`,
`batch_state/reports/scale-measurement-evidence.json`, and
`batch_state/reports/pilot-output/report.json`. The probe is rerunnable in a
fresh ignored reports area with the task-prescribed shared interpreter via
standard input. The text suffix prevents accidental test imports. Its
raw diagnostics and host-only cards remain untracked. The public report omits
host locations and Ukrainian source bodies.

The pilot invocation used the shared interpreter, the three explicit read-only
primary database paths, and these repository-relative inputs:

```bash
"$PROJECT_PYTHON" -m scripts.atlas.word_card_assembly build \
  --manifest registry/atlas/pilot/pilot-v1.json \
  --registry registry/atlas/identity/registry.json \
  --register docs/sources/permissions-register.yaml \
  --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB" --atlas-db "$ATLAS_DB" \
  --output batch_state/reports/pilot-output
```

The environment names above stand for the task-prescribed shared interpreter
and primary store paths. The measurement probe opened SQLite using those
absolute paths with URI `mode=ro`, never a worktree-relative source DB.

There are three prerequisite residual groups, owned as in the bottleneck table:
source freeze and combined denominator; identity dispositions; certification and
resource acceptance. Once admitted, the accountable driver can measure real
Phase 6 resource trials at interruption boundaries 1,000 and 10,000 against the
same full freeze, then obtain full-scale interruption/resume and independent
reconciliation proof. They must also reconcile the 12 pilot exclusions before
using any 150-emitted-card acceptance claim. This report leaves #8977 open;
Issue #11031 is closed for engine implementation, not proof of production execution.
No independent held-out evaluation was performed in this investigation.
