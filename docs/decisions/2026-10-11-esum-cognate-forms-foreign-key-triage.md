# Decision & Triage Record: ESUM Cognate Forms Foreign-Key Baseline

**Date:** 2026-10-11  
**Status:** RESOLVED (decision-only)  
**Issue:** [#8417](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8417)  
**Parent:** #4706, #6321 (open-model-data)  
**Author:** Gemini (open-model-data lane driver)  
**Reviewer:** Codex / Claude (cross-family)  

---

## 1. Outcome & Executive Summary

This decision record provides the authoritative triage and durable remediation roadmap for the **134,836 foreign-key violations** in `data/sources.db` between `esum_cognate_forms.entry_id` and `esum_etymology_meta.id`.

### Key Findings
1. **Root Cause:** A complete ID-space displacement exists between `esum_cognate_forms` (`entry_id` range `62,945..215,657`, total 134,836 rows) and `esum_etymology_meta` (`id` range `215,658..251,834`, total 36,177 rows). The two ID spaces are strictly disjoint (`max(entry_id) == 215,657` vs `min(id) == 215,658`). Consequently, 100% of rows in `esum_cognate_forms` fail the foreign-key check against `esum_etymology_meta`.
2. **Semantic Safety Scoped to Audited MCP Lookups:** Sources MCP tools (`search_esum` and `search_esum_batch` in `scripts/wiki/sources_db.py`) query **only** `esum_etymology_meta` (exact lemma matches) and `esum_etymology` (FTS5 full text search). Neither tool references or joins `esum_cognate_forms`. Lexical lookup paths used by curriculum authoring and agent pipelines are fully functional and unaffected by this issue.
3. **Downstream Structured-Data Gap:** In contrast, downstream structured consumers that join on `esum_cognate_forms`—specifically `scripts/etymology/build_data_manifest.py`, which executes `LEFT JOIN esum_cognate_forms f ON f.entry_id = e.id`—currently match 0 rows due to the disjoint ID spaces. This results in empty structured cognate dictionaries `{}` and `null` proto-forms. While the manifest builder falls back gracefully to raw etymology text without crashing, structured programmatic access to parsed cognates from the database remains unpopulated until durable remediation.
4. **Contract Protection:** Live host mutations are strictly prohibited. Existing Phase 3 recovery and freeze gates (`phase3_recovery_contracts.py`, `phase3_live_ingest_gate.py`, and `phase3_university_content_audit_freeze.py`) explicitly pin and verify `foreign_key_failure_count == 134836` with cryptographic hash `9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb`.
5. **Remediation Roadmap:** Durable re-keying and cleanup is scheduled for the next major database cutover (Sources DB v5/v6 re-ingest). The remediation sequence requires historical archiving, clean-table extraction in an isolated database copy (or adding `--dest-table` support to the extractor), transaction-safe table promotion or online SQLite backup streaming, and an atomic, comprehensive update of all live-gate and freeze contract pins and input bindings.

---

## 2. Root Cause Analysis

### Database Schema Definition
In `data/sources.db`:
```sql
CREATE TABLE esum_cognate_forms (
    entry_id INTEGER PRIMARY KEY,
    cognate_forms TEXT NOT NULL DEFAULT '{}',
    proto_form TEXT,
    extracted_count INTEGER NOT NULL DEFAULT 0,
    expected_count INTEGER NOT NULL DEFAULT 0,
    cognate_forms_recovered TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
);

CREATE TABLE esum_etymology_meta (
    id INTEGER PRIMARY KEY,
    lemma TEXT NOT NULL,
    vol INTEGER NOT NULL,
    page INTEGER NOT NULL,
    entry_hash TEXT NOT NULL DEFAULT '',
    etymology_text TEXT NOT NULL,
    cognates TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'ЕСУМ',
    UNIQUE(lemma, vol, page, entry_hash)
);
```

### ID Space Divergence
Authoritative query against `data/sources.db`:
```sql
SELECT 'esum_etymology_meta', COUNT(*), MIN(id), MAX(id) FROM esum_etymology_meta
UNION ALL
SELECT 'esum_cognate_forms', COUNT(*), MIN(entry_id), MAX(entry_id) FROM esum_cognate_forms;
```
Result:
| Table | Row Count | Min ID | Max ID |
|---|---:|---:|---:|
| `esum_etymology_meta` | 36,177 | 215,658 | 251,834 |
| `esum_cognate_forms` | 134,836 | 62,945 | 215,657 |

Notice:
- `max(entry_id)` in `esum_cognate_forms` is `215,657`.
- `min(id)` in `esum_etymology_meta` is `215,658` (`215,657 + 1`).
- The two ID spaces are **strictly disjoint**. Every single row in `esum_cognate_forms` references an ID strictly lower than any existing ID in `esum_etymology_meta`.
- Consequently, `PRAGMA foreign_key_check(esum_cognate_forms)` returns exactly **134,836** rows (100% of the table).

### Historical Context
- On **2026-05-14** (commit `638bbffbee`, PR #1996: "feat(etymology): Phase 1 — 31k static HTML pages + foundational scripts (POC)"), `scripts/etymology/extract_cognate_forms.py` was introduced to regex-extract cognate forms from etymology texts.
- While the empirical disjointness between `esum_cognate_forms` (`62,945..215,657`) and `esum_etymology_meta` (`215,658..251,834`) is verified by SQLite inspection, the exact intermediate historical migration mechanics that produced this sequential offset (such as unrecorded re-indexing, auto-increment rollover, or multi-stage table consolidation during early development) are not documented in commit logs or ADRs and represent an unverified historical migration artifact.
- Because SQLite connections run by default without `PRAGMA foreign_keys = ON`, foreign key constraints were not enforced at insert time, preserving the table without runtime errors while creating the 134,836 foreign key violations.

---

## 3. Query Impact & Semantic Audit

### Audited MCP Lookups: `search_esum` and `search_esum_batch`
Inspection of `scripts/wiki/sources_db.py`:
- `search_esum_batch()` (lines 3499–3559): Queries `esum_etymology_meta` directly for exact lemma matches (`meta.lemma = requested.word COLLATE NOCASE`).
- `search_esum()` (lines 3780–3880): Queries `esum_etymology_meta` for candidate lemma matches and `esum_etymology` (FTS5 table) for full-text matches.
- **Neither function joins or queries `esum_cognate_forms`.**
- Verification: Runtime invocation of `search_esum('серце')` and `search_esum_batch(['дім', 'мова'])` executes cleanly without error and returns full etymology entries with reconstructed forms, volume, and page citations.
- Conclusion: Textual and lemma etymology lookups utilized across agent workflows and curriculum authoring are completely unaffected.

### Downstream Structured-Data Gap (`build_data_manifest.py`)
- `scripts/etymology/build_data_manifest.py:100`:
  ```sql
  SELECT e.id, e.lemma, e.vol, e.page, e.etymology_text,
         COALESCE(f.cognate_forms, '{}') AS cognate_forms,
         ...
  FROM esum_etymology_meta e
  LEFT JOIN esum_cognate_forms f ON f.entry_id = e.id
  ```
  Because `f.entry_id = e.id` yields **0 matches** across all 36,177 entries in `esum_etymology_meta`, the `LEFT JOIN` evaluates to `NULL` for all columns of `f`. `COALESCE` safely defaults to `{}` for `cognate_forms`, and `proto_form` evaluates to `None`.
- Impact: While `build_data_manifest.py` falls back gracefully to raw `etymology_text` without raising a database exception, structured programmatic access to parsed cognates from `sources.db` is currently empty/unpopulated until remediation.

### Frozen Count Invariant
- `scripts/projects/open_model_data/phase3_recovery_contracts.py`:
  Pins `"lexical_esum_cognate_forms": 134836` as an accounted asset count.

---

## 4. Frozen Contracts & Non-Goals

### Non-Goal: No Live Host Database Mutation
Ad-hoc deletion, re-keying, or in-place truncation of `esum_cognate_forms` in `data/sources.db` is **strictly prohibited**.
The exact failure count and cryptographic hash of the foreign-key violations are frozen into regression contracts:
- `scripts/projects/open_model_data/phase3_live_ingest_gate.py`:
  ```python
  require(
      receipt.get("foreign_key_failure_count_before") == 134836
      and receipt.get("foreign_key_failure_count_after") == 134836,
      "rehearsal foreign-key count drift",
  )
  ```
- `scripts/projects/open_model_data/phase3_university_content_audit_freeze.py`:
  ```python
  "foreign_key_failure_count": 134836,
  "foreign_key_failure_sha256": "9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb",
  ```
- Any uncoordinated modification to `data/sources.db` will break `tests/test_open_model_phase3_university_content_audit_freeze.py` and fail production gate checks.

---

## 5. Durable Remediation Roadmap (Database Cutover v5/v6)

When the next scheduled major database cutover takes place:

### Extractor Constraints & Isolation Requirement
Inspection of `scripts/etymology/extract_cognate_forms.py` reveals two important constraints:
1. **Target Table is Hardcoded:** The script creates and writes strictly to `esum_cognate_forms` (lines 181, 213). Its CLI accepts only `--db`, `--telemetry`, and `--min-coverage-pct`; it does not accept a `--dest-table` argument.
2. **Conflict Handling Retains Pre-existing Rows:** It executes:
   ```sql
   INSERT INTO esum_cognate_forms (entry_id, cognate_forms, proto_form, extracted_count, expected_count)
   VALUES (?, ?, ?, ?, ?)
   ON CONFLICT(entry_id) DO UPDATE SET ...
   ```
   Executing the script against an existing populated database leaves all 134,836 orphan rows (IDs `62,945..215,657`) untouched while adding the 36,177 canonical rows (IDs `215,658..251,834`), retaining all foreign-key violations.

Therefore, durable remediation must be executed in an **isolated database copy** where the target table is cleanly initialized, or `--dest-table` support must be added to the extractor as an engineering prerequisite prior to cutover.

### Step-by-Step Remediation Sequence in Isolated Database
1. **Staging Environment Setup:**
   Copy `data/sources.db` to an isolated workspace build path (e.g. `data/sources.db.cutover_staging`).
2. **Preserve Legacy Archive:**
   Export the 134,836 existing rows into an unconstrained legacy archive table so historical fine-grained extractions remain accessible:
   ```sql
   CREATE TABLE esum_cognate_forms_legacy_archive AS SELECT * FROM esum_cognate_forms;
   ```
3. **Clean Table Reset in Isolated Database:**
   Drop and recreate an empty `esum_cognate_forms` table in the isolated database:
   ```sql
   DROP TABLE esum_cognate_forms;
   CREATE TABLE esum_cognate_forms (
       entry_id INTEGER PRIMARY KEY,
       cognate_forms TEXT NOT NULL DEFAULT '{}',
       proto_form TEXT,
       extracted_count INTEGER NOT NULL DEFAULT 0,
       expected_count INTEGER NOT NULL DEFAULT 0,
       cognate_forms_recovered TEXT NOT NULL DEFAULT '{}',
       FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
   );
   ```
4. **Regeneration Run:**
   Execute the extractor against the isolated staging copy:
   ```bash
   .venv/bin/python scripts/etymology/extract_cognate_forms.py \
     --db data/sources.db.cutover_staging \
     --telemetry data/telemetry/cognate_extraction_v5.json
   ```
   Because the destination table was freshly created, all 36,177 canonical entries are inserted with exact 1:1 foreign-key alignment to `esum_etymology_meta.id`.
5. **Integrity Verification:**
   Verify foreign-key consistency and row parity on the isolated database:
   ```sql
   -- Must return 0 rows:
   PRAGMA foreign_key_check(esum_cognate_forms);

   -- Must equal the count of esum_etymology_meta (36,177):
   SELECT COUNT(*) FROM esum_cognate_forms;
   ```

### Promotion & Cutover Architectures
SQL `ROLLBACK` cannot undo a filesystem file replacement (`os.replace` / `shutil.move`). The cutover procedure must therefore follow one of two verified, transaction-safe promotion architectures:

- **Option A: In-Database Transactional Table Swap (Same SQLite Database):**
  If staging is populated in the database file via `esum_cognate_forms_staging`, promotion executes actual DDL statements inside an explicit SQLite transaction boundary:
  ```sql
  BEGIN IMMEDIATE TRANSACTION;
  ALTER TABLE esum_cognate_forms RENAME TO esum_cognate_forms_old;
  ALTER TABLE esum_cognate_forms_staging RENAME TO esum_cognate_forms;
  DROP TABLE esum_cognate_forms_old;
  -- If any failure or constraint violation occurs before COMMIT, ROLLBACK restores exact prior tables:
  COMMIT;
  ```

- **Option B: Online Database Streaming Cutover (Separate Candidate Database File):**
  When promoting an isolated database candidate file (`sources.db.cutover_staging`) into production (`data/sources.db`), follow the proven repository cutover protocol from `scripts/projects/open_model_data/phase3_vspu_db_cutover.py:524, 874`:
  1. Capture a byte-level pre-cutover rollback snapshot (`sources.db.pre_cutover_backup`).
  2. Enforce clean WAL on target: verify WAL does not exist or has 0 bytes via `PRAGMA wal_checkpoint(TRUNCATE)`.
  3. Stream candidate into target using the SQLite Online Backup API:
     ```python
     with open_readonly(candidate) as src, sqlite3.connect(target) as dst:
         src.backup(dst)
         dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
     ```
  4. Validate post-cutover evidence on target (`PRAGMA foreign_key_check == 0`, row counts match candidate).
  5. If validation fails, restore exact pre-state using `_restore_exact_prestate` (online backup from pre-state backup or byte copy fallback).

### Comprehensive Contract & Gate Update Checklist
Because Phase 3 gates enforce cryptographic hashes across multiple receipts and byte files, the database cutover PR must atomically update all dependent contracts, receipt bindings, and artifacts:

1. **Zero-Violation Hash Derivation:**
   In `phase3_live_ingest_gate.py:371`, `incremental_textbook_ingest.py:396`, and `phase3_university_content_audit_freeze.py:326`, the foreign-key evidence hash is computed via:
   ```python
   hashlib.sha256(json.dumps(fk_rows, separators=(",", ":")).encode("utf-8")).hexdigest()
   ```
   When `PRAGMA foreign_key_check` returns 0 violations, `fk_rows` is empty (`[]`). Compact JSON serialization yields `b"[]"`, which produces the exact SHA-256 hash:
   `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
   *(Note: This is the SHA-256 of serialized empty JSON `[]`, NOT the hash of empty raw bytes `e3b0c442...`).*

2. **Live-Ingest Gate (`scripts/projects/open_model_data/phase3_live_ingest_gate.py`):**
   - **Hash & Count Constants:**
     - Update `EXPECTED_FOREIGN_KEY_HASH` (line 38) from `"9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb"` to `"4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"`.
     - Update `EXPECTED_LIVE_DB_SHA256` (line 37) to the new whole-database byte SHA-256 after the cutover.
   - **Input Receipt Bindings (`EXPECTED_INPUT_HASHES`, lines 41–53):**
     - `copied_database_rehearsal_receipt_sha256`: Re-pinned to the byte SHA-256 of the newly generated rehearsal receipt that verifies 0 violations.
     - `pre_ingest_backup_receipt_sha256` and `pre_ingest_backup_provider_verification_sha256`: Re-pinned to the freshly created pre-cutover database backup receipt and cloud verification receipt.
     - `pr6631_drive_backup_receipt_sha256` and `pr6631_drive_provider_verification_sha256`: Updated to match the pre-cutover drive archive receipts.
     - `validate_bound_inputs()` (lines 246–251) and `_validate_pr_backup()` (lines 196–200) strictly enforce these input pins.
   - **Rehearsal & Receipt Emission:**
     - Update rehearsal verification checks at lines 169–172 (`foreign_key_failure_count_before == 0`, `foreign_key_failure_count_after == 0`, and rehearsal hash assertions to `"4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"`).
     - Update gate receipt emission at line 282 (`database.foreign_key_failure_count: 0`).
     - Regenerate admission receipt `data/projects/open_model_data/admission/phase3_live_ingest_gate_v1.json` and update `EXPECTED_GATE_SHA256` (line 35).

3. **University Content Audit Freeze (`scripts/projects/open_model_data/phase3_university_content_audit_freeze.py`):**
   - **Database Invariants (`EXPECTED_DATABASE`, lines 55–66):**
     - `foreign_key_failure_count`: Update from `134836` to `0`.
     - `foreign_key_failure_sha256`: Update from `"9938f7cbab..."` to `"4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"`.
     - `sha256`: Update to the new whole-database byte SHA-256.
   - **Input Receipt Bindings (`EXPECTED_BINDINGS`, lines 41–53):**
     - Re-pin `live_ingest_gate_v1_sha256`, `live_ingest_receipt_sha256`, and backup receipt hashes to match the newly generated cutover gate receipts.
   - **Output Artifact Verification:**
     - Regenerate `registry/projects/open_model_data/admission/phase3_university_content_audit_freeze_v1.json`.
     - Update `EXPECTED_OUTPUT_SHA256` (line 39) to match the new byte hash of the output artifact.
   - Verify that all 9 checks in `tests/test_open_model_phase3_university_content_audit_freeze.py` pass cleanly.

4. **Recovery Contracts (`scripts/projects/open_model_data/phase3_recovery_contracts.py`):**
   - Update `"lexical_esum_cognate_forms"` count to the newly extracted canonical count (`36177`).

5. **Historical Preservation & Successor Contracts:**
   - Historical freeze evidence (the Phase 3 receipts, artifacts, and hashes recording the pre-cutover state with 134,836 count and hash `9938f7cbab...`) remains archived under `registry/projects/open_model_data/admission/` or an immutable `historical/` directory.
   - Successor contracts enforce the new zero-violation baseline without erasing or invalidating the historical audit record.

6. **Decision-Only Invariant for Issue #8417:**
   - As required by the terminal goal of issue #8417 (`decision-only`), no live database files or contract pins are modified in this issue. The existing contracts and hashes remain intact.

---

## 6. Verification Summary

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| `PRAGMA foreign_key_check(esum_cognate_forms)` | 134,836 rows | 134,836 rows | PASS |
| `test_open_model_phase3_university_content_audit_freeze.py` | 9 passed | 9 passed | PASS |
| `search_esum` runtime execution | Valid hits | Valid hits, 0 errors | PASS |
| `search_esum_batch` runtime execution | Valid batch dict | Valid batch dict, 0 errors | PASS |
| `scripts/ci/check_issue_task_quality.py --issue 8417` | `verdict=PASS` | `verdict=PASS` | PASS |
