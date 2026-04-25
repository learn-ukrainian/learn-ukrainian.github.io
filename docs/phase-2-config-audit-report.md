# Phase 2 Config Audit Report

Scope: EPIC #1577 Phase 2 / issue #1583, audited against Phase 0 policy authority in `docs/north-star.md`, `docs/lesson-contract.md`, and `docs/best-practices/activity-pedagogy.md`.

Verdicts:

- `MATCHES_POLICY` — value matches Phase 0 policy.
- `DRIFT_FROM_POLICY` — stale value with a mechanical Phase 0 fix applied.
- `UNDEFINED_BY_POLICY` — Phase 0 does not define the value; left unchanged.
- `CONTRADICTS_POLICY` — clear conflict needing a follow-up issue instead of a mechanical edit.

| File:line | Constant / item | Current value after audit | Verdict | Action |
| --- | --- | --- | --- | --- |
| `scripts/config.py:18` | `TRACK_CONFIG` schema | Track → model/persona/immersion range table | `MATCHES_POLICY` | Schema retained. |
| `scripts/config.py:20` | `TRACK_CONFIG["a1"].immersion_range` | `[0.10, 0.50]` | `MATCHES_POLICY` | A1 remains ramped per Phase 0 A1+A2 bootstrap. |
| `scripts/config.py:25` | `TRACK_CONFIG["a2"].immersion_range` | `[0.50, 0.90]` | `MATCHES_POLICY` | A2 remains ramped through final A2 band. |
| `scripts/config.py:30` | `TRACK_CONFIG["b1"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.85, 1.0]` to B1 100% Ukrainian. |
| `scripts/config.py:35` | `TRACK_CONFIG["b2"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.95, 1.0]` to B1+ 100% Ukrainian. |
| `scripts/config.py:40` | `TRACK_CONFIG["c1"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:45` | `TRACK_CONFIG["c2"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:52` | `TRACK_CONFIG["hist"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.95, 1.0]` to seminar 100% Ukrainian. |
| `scripts/config.py:57` | `TRACK_CONFIG["istorio"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:62` | `TRACK_CONFIG["bio"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:67` | `TRACK_CONFIG["lit"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:74` | `TRACK_CONFIG["lit-*"].immersion_range` | `[1.0, 1.0]` for all lit subtracks | `MATCHES_POLICY` | No change. |
| `scripts/config.py:121` | `TRACK_CONFIG["ruth"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.97, 1.0]` to seminar 100% Ukrainian. |
| `scripts/config.py:126` | `TRACK_CONFIG["oes"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.97, 1.0]` to seminar 100% Ukrainian. |
| `scripts/config.py:131` | `TRACK_CONFIG["b2-pro"].immersion_range` | `[1.0, 1.0]` | `DRIFT_FROM_POLICY` | Changed from `[0.95, 1.0]` to B1+ 100% Ukrainian. |
| `scripts/config.py:136` | `TRACK_CONFIG["c1-pro"].immersion_range` | `[1.0, 1.0]` | `MATCHES_POLICY` | No change. |
| `scripts/config.py:152` | `IMMERSION_POLICIES["a1"]` | A1 bands 5-48% Ukrainian with sentence caps 10-14 | `MATCHES_POLICY` | Left unchanged; Phase 0 keeps A1 ramp. |
| `scripts/config.py:281` | `IMMERSION_POLICIES["a2"]` | A2 bands 20-90% Ukrainian with sentence caps 15-18 | `MATCHES_POLICY` | Left unchanged; Phase 0 puts transition out of English inside A2. |
| `scripts/config.py:385` | `IMMERSION_POLICIES["b1"]` | Single `b1-core`, 100-100%, no English in body, Tab 2 carve-out | `DRIFT_FROM_POLICY` | Deleted stale B1 entry band and collapsed B1 to the Phase 0 rule from #1582. |
| `scripts/config.py:398` | `IMMERSION_POLICIES["default"]` | `b2+`, 100-100%, no English in body, Tab 2 carve-out | `DRIFT_FROM_POLICY` | Changed from 95-100% and "technical terminology" exception to Phase 0 B1+ rule. |
| `scripts/config.py:417` | `OVERSHOOT_FACTOR` | `1.5` for B1+, A1/A2 helper returns `1.0` | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 does not prescribe generation overshoot. |
| `scripts/config.py:426` | `MAX_SENTENCE_LENGTH` | `25` | `UNDEFINED_BY_POLICY` | Left unchanged because no active callers; follow-up #1587 filed to remove or replace with per-band source. |
| `scripts/config.py:445` | `get_config()` fallback | Unknown tracks default to `[0.5, 1.0]` | `UNDEFINED_BY_POLICY` | Left unchanged; fallback behavior not specified by Phase 0. |
| `scripts/config.py:454` | `_immersion_track_key()` | Known policy families use explicit key; otherwise `default` | `MATCHES_POLICY` | No change; B2+ tracks now resolve to 100% default. |
| `scripts/config.py:462` | `_find_immersion_band()` | First matching `max_module` band | `MATCHES_POLICY` | No change; B1 now has one band. |
| `scripts/audit/config.py:11` | `PROPER_NAME_WHITELIST` | Seed whitelist with code comment for reviewer-approved PR additions | `DRIFT_FROM_POLICY` | Added Phase 0 P4 governance comment; did not bulk-add names. |
| `scripts/audit/config.py:51` | `AUDIT_THRESHOLDS.word_count_fail_pct` | `12` | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 says word targets are minimums but does not define this legacy fail percentage. |
| `scripts/audit/config.py:53` | `AUDIT_THRESHOLDS.immersion_tolerance_pct` | `3` | `UNDEFINED_BY_POLICY` | Left unchanged; B1+ now uses shared 100% bands, but Phase 0 does not define A1/A2 tolerance. |
| `scripts/audit/config.py:54` | `AUDIT_THRESHOLDS.naturalness_min_score` | Derived from `LEVEL_THRESHOLDS` | `MATCHES_POLICY` | No change; avoids duplicate naturalness numbers. |
| `scripts/audit/config.py:58` | `AUDIT_THRESHOLDS.severity_update` | `40` | `UNDEFINED_BY_POLICY` | Left unchanged; no Phase 0 source citation found. |
| `scripts/audit/config.py:59` | `AUDIT_THRESHOLDS.severity_rewrite` | `75` | `UNDEFINED_BY_POLICY` | Left unchanged; no Phase 0 source citation found. |
| `scripts/audit/config.py:68` | `GRAMMAR_CONSTRAINTS["A1"]` | Max 10 words, 1 clause, no participles/subordinate clauses | `MATCHES_POLICY` | No change; consistent with A1 band strings. |
| `scripts/audit/config.py:78` | `GRAMMAR_CONSTRAINTS["A2"]` | Max 15 words, 2 clauses, no participles | `MATCHES_POLICY` | No change; consistent with A2 band strings except late A2's 18-word cap lives in immersion rule. |
| `scripts/audit/config.py:87` | `GRAMMAR_CONSTRAINTS["B1"]` | Max 30 words, 4 clauses, full aspect/participles | `MATCHES_POLICY` | No change; matches new B1 rule string sentence cap. |
| `scripts/audit/config.py:96` | `GRAMMAR_CONSTRAINTS["B2"]` | Max 35 words, 6 clauses, full grammar | `MATCHES_POLICY` | No change; matches B2+ default rule string sentence cap. |
| `scripts/audit/config.py:106` | `GRAMMAR_CONSTRAINTS["C1"]/["C2"]` | 50/100 word caps | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 says full Ukrainian, not exact C-level sentence caps. |
| `scripts/audit/config.py:662` | `LEVEL_CONFIG["A1"].priority_types` | Removed `classify` | `DRIFT_FROM_POLICY` | Aligned with deprecated `classify` policy. |
| `scripts/audit/config.py:678` | `LEVEL_CONFIG["A2"].priority_types` | No `select`/`reading`; includes matrix-valid A2 types | `MATCHES_POLICY` | No change. |
| `scripts/audit/config.py:731` | B1 `LEVEL_CONFIG` variants | B1 min immersion `100`; priority types exclude forbidden reading/critical-analysis | `DRIFT_FROM_POLICY` | Updated B1 variants to match 100% Ukrainian + B1 activity matrix. |
| `scripts/audit/config.py:819` | B2/C1/OES/RUTH `LEVEL_CONFIG.priority_types` | Priority types are subsets of their Phase 0 pipeline allowlists | `DRIFT_FROM_POLICY` | Removed out-of-matrix priority types after live matrix alignment. |
| `scripts/audit/config.py:1445` | `ACTIVITY_RESTRICTIONS["A1"]` | Deprecated/out-of-level types forbidden, including `select`/`classify` | `DRIFT_FROM_POLICY` | Expanded to mirror Phase 0 A1 matrix restrictions. |
| `scripts/audit/config.py:1457` | `ACTIVITY_RESTRICTIONS["A2"]` | Deprecated/out-of-level types forbidden, including `select`/`classify` | `DRIFT_FROM_POLICY` | Expanded to mirror Phase 0 A2 matrix restrictions. |
| `scripts/audit/config.py:1470` | `ACTIVITY_RESTRICTIONS["B1"]` | Deprecated/out-of-level types forbidden; `essay-response` allowed | `DRIFT_FROM_POLICY` | Expanded to mirror Phase 0 B1 matrix restrictions. |
| `scripts/audit/config.py:1584` | `AI_CONTAMINATION_PATTERNS` | Includes Phase 0 examples: "Let's dive in", "In conclusion", "It's important to note", "Buckle up", "Great job!" | `DRIFT_FROM_POLICY` | Added deterministic P5 banlist phrases. |
| `scripts/audit/config.py:558` | `VALID_ACTIVITY_TYPES` | Still includes deprecated/legacy schema types | `CONTRADICTS_POLICY` | Left for schema cleanup; follow-up #1585 filed. |
| `scripts/audit/config.py:295` | `ACTIVITY_COMPLEXITY` | Still includes some deprecated/out-of-matrix type-level rules | `CONTRADICTS_POLICY` | Left for schema cleanup; follow-up #1585 filed. |
| `scripts/audit/checks/activities.py:337` | Anagram level-restriction emission | Specialized anagram rule is the single violation source when `anagram_forbidden` is set | `DRIFT_FROM_POLICY` | Avoided duplicate generic + specialized anagram violations while preserving matrix restrictions. |
| `scripts/common/thresholds.py:37` | `REVIEW_PASS_FLOOR` | Global `8.0` per-dimension pass floor | `CONTRADICTS_POLICY` | Follow-up #1586 filed because Phase 0 requires per-level per-dimension LLM QG floors. |
| `scripts/common/thresholds.py:41` | `REVIEW_REJECT_FLOOR` | Global `6.0` hard reject floor | `UNDEFINED_BY_POLICY` | Left unchanged; should be revisited with #1586. |
| `scripts/common/thresholds.py:44` | `STYLE_REVIEW_TARGET` | `9.0` target | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 does not define this number. |
| `scripts/common/thresholds.py:50` | `STYLE_REVIEW_DIMENSION_FLOOR` | `8.5` | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 does not define this number. |
| `scripts/common/thresholds.py:58` | `LevelThresholds` schema | `target_words`, `naturalness_min` only | `CONTRADICTS_POLICY` | Follow-up #1586 filed for per-level per-dimension floors. |
| `scripts/common/thresholds.py:77` | `LEVEL_THRESHOLDS.target_words` | A1 1200, A2 2000, B1-C1 4000, C2 5000 | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 treats targets as minimums but does not set numbers. |
| `scripts/common/thresholds.py:77` | `LEVEL_THRESHOLDS.naturalness_min` | A1/A2/B1 9.0, B2+ 8.0 | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 does not prescribe specific naturalness floors. |
| `scripts/pipeline/config_tables.py:23` | `TRACK_PERSONAS` | Track persona table | `UNDEFINED_BY_POLICY` | Left unchanged; Phase 0 voice describes stages but not exact persona strings. |
| `scripts/pipeline/config_tables.py:78` | `IMMERSION_RULES` | Derived from `IMMERSION_POLICIES` | `MATCHES_POLICY` | No direct edit; now derives only `b1-core`, no stale B1 band. |
| `scripts/pipeline/config_tables.py:87` | `GOLDEN_FRAGMENTS["intermediate"]` | B1 example has no English glosses in sample body | `DRIFT_FROM_POLICY` | Removed English parenthetical translations and updated note to Tab 2-only English. |
| `scripts/pipeline/config_tables.py:160` | `LEVEL_CONSTRAINTS` | A1/A2/B1/B2 sentence and grammar constraints | `MATCHES_POLICY` | No change; B1 30 and B2 35 match immersion rule strings. |
| `scripts/pipeline/config_tables.py:878` | `INLINE_ONLY_TYPES` | `image-to-letter`, `letter-grid`, `watch-and-repeat` | `MATCHES_POLICY` | No change; matches activity-pedagogy §4. |
| `scripts/pipeline/config_tables.py:884` | `WORKBOOK_ONLY_TYPES` | Long-form workbook-only set | `MATCHES_POLICY` | No change; matches activity-pedagogy §4. |
| `scripts/pipeline/config_tables.py:908` | `ACTIVITY_CONFIGS["a1"]` | Matrix-aligned A1 allow/forbid lists | `DRIFT_FROM_POLICY` | Added missing both-context A1 types, removed `classify`, kept `select` forbidden. |
| `scripts/pipeline/config_tables.py:928` | `ACTIVITY_CONFIGS["a1-checkpoint"]` | No `classify`; `select` forbidden | `DRIFT_FROM_POLICY` | Checkpoint variants are not in the matrix, but deprecated types were removed/forbidden. |
| `scripts/pipeline/config_tables.py:948` | `ACTIVITY_CONFIGS["a2"]` | Matrix-aligned A2 allow/forbid lists | `DRIFT_FROM_POLICY` | Made A2 placement match docs and added `select` forbidden. |
| `scripts/pipeline/config_tables.py:968` | `ACTIVITY_CONFIGS["a2-checkpoint"]` | No `classify`; `select` forbidden | `DRIFT_FROM_POLICY` | Checkpoint variants are not in the matrix, but deprecated types were removed/forbidden. |
| `scripts/pipeline/config_tables.py:988` | `ACTIVITY_CONFIGS["b1-core"]` | Matrix-aligned B1 allow/forbid lists | `DRIFT_FROM_POLICY` | Removed B1 reading/critical-analysis, added B1 order/odd-one-out placements, added `select` forbidden. |
| `scripts/pipeline/config_tables.py:1008` | `ACTIVITY_CONFIGS["b2"]` | Matrix-aligned B2 allow/forbid lists | `DRIFT_FROM_POLICY` | Removed B2 unjumble/critical-analysis drift; added documented placements. |
| `scripts/pipeline/config_tables.py:1028` | `ACTIVITY_CONFIGS["c1-core"]` | Matrix-aligned C1 allow/forbid lists | `DRIFT_FROM_POLICY` | Removed authorial-intent drift and aligned placements. |
| `scripts/pipeline/config_tables.py:1049` | `ACTIVITY_CONFIGS["c2"]` | Matrix-aligned C2 allow/forbid lists | `DRIFT_FROM_POLICY` | Removed match-up drift; added authorial-intent/debate workbook placements. |
| `scripts/pipeline/config_tables.py:1070` | `ACTIVITY_CONFIGS["hist"]` | Matrix-aligned HIST allow/forbid lists | `DRIFT_FROM_POLICY` | Added inline match-up and workbook mark-the-words. |
| `scripts/pipeline/config_tables.py:1086` | `ACTIVITY_CONFIGS["bio"]` | Matrix-aligned BIO allow/forbid lists | `DRIFT_FROM_POLICY` | Added inline match-up, workbook mark-the-words/source-evaluation. |
| `scripts/pipeline/config_tables.py:1102` | `ACTIVITY_CONFIGS["istorio"]` | Matrix-aligned ISTORIO allow/forbid lists | `DRIFT_FROM_POLICY` | Added inline match-up and workbook mark-the-words. |
| `scripts/pipeline/config_tables.py:1118` | `ACTIVITY_CONFIGS["lit"]` | Matrix-aligned LIT allow/forbid lists | `DRIFT_FROM_POLICY` | Added inline match-up and workbook mark-the-words. |
| `scripts/pipeline/config_tables.py:1137` | `ACTIVITY_CONFIGS["b2-pro"]` | Matrix-aligned B2-PRO allow/forbid lists | `DRIFT_FROM_POLICY` | Added documented metalinguistic and placement entries; removed critical-analysis. |
| `scripts/pipeline/config_tables.py:1153` | `ACTIVITY_CONFIGS["c1-pro"]` | Matrix-aligned C1-PRO allow/forbid lists | `DRIFT_FROM_POLICY` | Added highlight-morphemes and comparative-study placements. |
| `scripts/pipeline/config_tables.py:1173` | `ACTIVITY_CONFIGS["oes"]` | Matrix-aligned OES allow/forbid lists | `DRIFT_FROM_POLICY` | Removed extra ISSUE-502 live allowlist entries not present in Phase 0 matrix. |
| `scripts/pipeline/config_tables.py:1191` | `ACTIVITY_CONFIGS["ruth"]` | Matrix-aligned RUTH allow/forbid lists | `DRIFT_FROM_POLICY` | Removed extra ISSUE-502 live allowlist entries not present in Phase 0 matrix. |
| `scripts/pipeline/config_tables.py:1221` | `get_track_skill()` | B1 early/late skill split remains | `UNDEFINED_BY_POLICY` | Left unchanged; no branch on stale B1 band key and no Phase 0 skill-file policy. |
| `scripts/pipeline/config_tables.py:1233` | `get_immersion_rule()` | Delegates to shared config | `MATCHES_POLICY` | No change; gets new B1/default rules. |
| `scripts/pipeline/config_tables.py:1238` | `get_golden_fragment()` | B1 uses intermediate fragment, B2+ advanced/seminar | `MATCHES_POLICY` | No routing change; B1 fragment content fixed. |
| `scripts/pipeline/config_tables.py:1314` | `_split_type_list()` | Comma-list parser | `UNDEFINED_BY_POLICY` | Left unchanged. |
| `scripts/pipeline/config_tables.py:1319` | `_phase_out_activity_type()` | Dynamic removal helper | `MATCHES_POLICY` | No change; supports A1 anagram phase-out. |
| `scripts/pipeline/config_tables.py:1343` | `_resolve_activity_config_key()` | `b1` → `b1-core`, `c1` → `c1-core` | `MATCHES_POLICY` | No change; no stale B1 entry key. |
| `scripts/pipeline/config_tables.py:1360` | `get_activity_config()` | Deep-copy config with A1 anagram phase-out | `MATCHES_POLICY` | No change; tests added for matrix parity. |
| `scripts/build/contracts/module-contract.md:32` | §1 Level contract | Explicit B1+ 100% body + Tab 2 carve-out | `DRIFT_FROM_POLICY` | Added Phase 0 B1+ rule and adjusted reviewer-side violation text. |
| `scripts/build/contracts/module-contract.md:65` | §2 Section contract | Plan section coverage authority | `MATCHES_POLICY` | No change. |
| `scripts/build/contracts/module-contract.md:105` | §3 Dialogue contract | Corpus-grounded dialogue requirement | `MATCHES_POLICY` | No change. |

## Verification

| Check | Result |
| --- | --- |
| Branch current | `git log --oneline HEAD..origin/main` was empty after fetch. |
| Phase 0 commit | `de97c45572` is an ancestor of `HEAD`. |
| B1 stale key search | Required stale-key regex over `scripts/` and `tests/` returned no matches. |
| Activity matrix parity | Added `tests/test_config_tables.py::TestActivityPedagogyMatrix`; targeted pytest passed. |
| Audit/pipeline priority parity | `tests/audit/test_config_invariants.py::test_audit_priority_subset_of_pipeline_allowed` passed. |
| Ruff per Python edit | `ruff check scripts/config.py`, `scripts/audit/config.py`, `scripts/pipeline/config_tables.py`, and changed tests passed. |
| Requested full pytest target | `.venv/bin/pytest scripts/audit/ scripts/common/ scripts/pipeline/` collected 0 tests and exited with pytest code 5. |

## Sub-Issues Filed

| Issue | Label | Rationale |
| --- | --- | --- |
| #1586 | `reboot-blocker` | Per-level per-dimension LLM QG threshold schema is needed before Phase 4 QG. |
| #1585 | `mvp-deferred` | Legacy activity registries still need a schema cleanup pass after live matrix alignment. |
| #1587 | `backlog` | Unused global `MAX_SENTENCE_LENGTH` should be removed or replaced with a per-band helper. |
