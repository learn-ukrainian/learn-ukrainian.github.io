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
5. **Remediation Roadmap:** Durable re-keying and cleanup is scheduled for the next major database cutover (Sources DB v5/v6 re-ingest), requiring an archive step, clean staging/truncation, validation (`PRAGMA foreign_key_check == 0`), and atomic contract updates.

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

### Extraction Mechanism & Staging Requirement
`scripts/etymology/extract_cognate_forms.py` operates via:
```sql
INSERT INTO esum_cognate_forms (entry_id, cognate_forms, proto_form, extracted_count, expected_count)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(entry_id) DO UPDATE SET ...
```
Because the extractor relies on `ON CONFLICT(entry_id) DO UPDATE`, executing it against an existing populated table **does not remove orphan rows**. Running the extractor directly against the current database will simply insert 36,177 rows (IDs `215,658..251,834`) while leaving all 134,836 orphan rows (IDs `62,945..215,657`) intact, leaving foreign-key violations unchanged.

Therefore, durable remediation must execute the following staged sequence:

### Execution Steps
1. **Archive Legacy Forms:**
   Prior to modification, export the existing 134,836 rows to an unconstrained archive table or backup file (e.g. `esum_cognate_forms_legacy_archive` or SQLite archive) to prevent loss of historical fine-grained extractions:
   ```sql
   CREATE TABLE esum_cognate_forms_legacy_archive AS SELECT * FROM esum_cognate_forms;
   ```
2. **Clean Staging Table:**
   Create a clean staging table with the foreign-key constraint defined:
   ```sql
   CREATE TABLE esum_cognate_forms_staging (
       entry_id INTEGER PRIMARY KEY,
       cognate_forms TEXT NOT NULL DEFAULT '{}',
       proto_form TEXT,
       extracted_count INTEGER NOT NULL DEFAULT 0,
       expected_count INTEGER NOT NULL DEFAULT 0,
       cognate_forms_recovered TEXT NOT NULL DEFAULT '{}',
       FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
   );
   ```
3. **Regenerate from Canonical Meta:**
   Run `scripts/etymology/extract_cognate_forms.py` targeting the staging table against the 36,177 canonical entries in `esum_etymology_meta`.
4. **Validation & Table Swap:**
   - Verify integrity: `PRAGMA foreign_key_check(esum_cognate_forms_staging)` must return **0 rows**.
   - Verify count: Row count must match expected entry count (36,177).
   - Atomically swap tables:
     ```sql
     DROP TABLE esum_cognate_forms;
     ALTER TABLE esum_cognate_forms_staging RENAME TO esum_cognate_forms;
     ```
5. **Atomic Contract & Hash Updates:**
   Atomically update Phase 3 recovery contracts and freeze gates in the database cutover PR:
   - `scripts/projects/open_model_data/phase3_recovery_contracts.py`: update `"lexical_esum_cognate_forms"` count to the newly extracted count (36,177).
   - `scripts/projects/open_model_data/phase3_live_ingest_gate.py`: update `foreign_key_failure_count_before` and `after` to `0`.
   - `scripts/projects/open_model_data/phase3_university_content_audit_freeze.py`: update `foreign_key_failure_count` to `0` and update `foreign_key_failure_sha256` to the new hash.
   - Run `tests/test_open_model_phase3_university_content_audit_freeze.py` to confirm all 9 checks pass.

---

## 6. Verification Summary

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| `PRAGMA foreign_key_check(esum_cognate_forms)` | 134,836 rows | 134,836 rows | PASS |
| `test_open_model_phase3_university_content_audit_freeze.py` | 9 passed | 9 passed | PASS |
| `search_esum` runtime execution | Valid hits | Valid hits, 0 errors | PASS |
| `search_esum_batch` runtime execution | Valid batch dict | Valid batch dict, 0 errors | PASS |
| `scripts/ci/check_issue_task_quality.py --issue 8417` | `verdict=PASS` | `verdict=PASS` | PASS |
