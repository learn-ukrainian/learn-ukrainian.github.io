# VESUM marker-preserving re-ingest — design v2 (issue #5092)

> Status: PANEL-CLEARED design (2026-07-14). Advisor draft v1 → 3-seat cross-family panel
> (REVISE ×2; one reply lost to #5091) → orchestrator adjudication (binding deltas D1-D6) →
> advisor revision v2 incorporating all deltas normatively. Release pin live-verified:
> dict_uk v6.8.0 @ bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824 (gh api, 2026-07-14).
> First-PR scope = migration step 1 ONLY (lock + exporter + importer + schema + generated
> fixtures + shadow DB); no consumer migration, no production-DB switch.

# VESUM re-ingest design v2 — #5092

Decision: use a marker-preserving full dataset with a compatibility view that hides only `bad`, `subst`, and `obsc`. Preserve current consumer behavior by keeping `arch`, `coll`, `slang`, and dialect-marked analyses visible. Policy-aware consumers use a separate inspection API.

## R1 — Schema and semantics

- Store every upstream analysis in:

  `forms_all(form_id, entry_id, word_form, lemma, pos, tags, source_comment, source_location)`

  `form_id` identifies one analysis; `entry_id` preserves upstream entry identity.

- Normalize analysis-scoped policy markers into:

  `form_markers(form_id, marker, origin, marker_class)`

  The normalized marker set includes `bad`, `subst`, `obsc`, `coll`, `slang`, `arch`, and dialect markers derived from exact structured or comment evidence. Markers must never bleed across homographs or sibling analyses.

- `subst` means “нестандартні форми,” not a grammatical feature. The current classification in `enrich_manifest.py` must be corrected.

- `arch` means archaic and sometimes dialectal. It must not be normalized to definite `dialect`. Exact evidence such as `# діалект` may produce an analysis-scoped dialect marker. These meanings follow the [published VESUM tag description](https://uacorpus.org/rozmitka-tekstiv/morfologichna-rozmitka).

- Keep `forms` as the compatibility view. It excludes only analyses marked:

  - `bad`
  - `subst`
  - `obsc`

- Analyses marked `arch`, `coll`, `slang`, or confirmed dialect remain visible in `forms`, with their markers exposed in `tags`. This preserves current marker-aware consumer behavior. Register and heritage policy belongs in `inspect_*` and downstream gate policy, not in compatibility-view exclusion.

- Existing `verify_word`, `verify_words`, and `verify_lemma` continue querying `forms`:

  - `bad`-, `subst`-, or `obsc`-only forms return empty/NOT FOUND.
  - `arch`, `coll`, `slang`, and dialect-marked forms remain returned with their markers.
  - Mixed homographs retain every default-visible analysis; excluded analyses remain available through inspection.

- Add `inspect_word`, `inspect_words`, and `inspect_lemma`, querying `forms_all` and `form_markers`. Results must contain:

  - separate `clean_analyses` and `marked_analyses`;
  - effective markers without collapsing analysis identity;
  - pinned release and pipeline identity;
  - a closed status enum covering at least `CLEAN`, `KNOWN_INVALID`, `NONSTANDARD`, `COLLOQUIAL`, `SLANG`, `ARCH_OR_DIALECT_UNRESOLVED`, and a mixed/indeterminate state requiring contextual resolution.

- Never add `include_flagged=True` to the legacy boolean-shaped API.

## R2 — Reproducible pin

Pin dict_uk `v6.8.0`, commit `bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824`. [Release evidence](https://github.com/brown-uk/dict_uk/releases).

Commit `scripts/config/vesum_source.lock.json` containing:

- full upstream commit;
- pinned release-asset URL, byte size, and SHA-256;
- parser/exporter version and exact parser-code SHA-256;
- operator-entrypoint version and exact entrypoint-code SHA-256;
- marker-policy version;
- expected semantic row counts;
- expected counts for every normalized marker class;
- canonical exported-data identity.

The importer version may replace a separate importer hash only if the version provably and immutably identifies the exact importer implementation. The same lock must imply the same upstream source, exporter, importer, marker policy, and semantic dataset.

The primary source is the pinned v6.8.0 release asset `dict_corp_vis.txt.bz2`, not a Gradle/JVM expansion. Direct inspection established that this asset is block-structured: an unindented lemma analysis opens a paradigm, indented analyses are its forms, and inline comments remain structurally bound within that block. Derive `entry_id` from the block ordinal and `source_location` from its line span in the hash-locked asset. This preserves comment-to-paradigm identity without a cross-homograph join. A supplemental source-tree pass is permitted only if fixture generation proves that an evidence class is absent from the release export; document that exception and its rationale.

Hash a canonically sorted JSONL export containing analyses, markers, and provenance. This semantic hash is the reproducibility identity; byte-identical SQLite files are not required across SQLite versions.

The build must fail on any source hash, pipeline-code hash, release identity, tagset, semantic hash, row-count, or marker-count mismatch.

## R3 — Contract tests

Generate the fixture manifest deterministically from the hash-locked v6.8.0 release asset at lock time. Hand-picked fixture lemmas are forbidden. Each generated fixture must record its source location, raw tags/comment evidence, normalized markers, and expected compatibility/inspection results. The resulting manifest is frozen by the lock.

The examples below are discovery hints only; they become fixtures only if the generator verifies their required properties in the pinned source.

Required probe classes:

- Clean analysis: legacy FOUND; inspection `CLEAN` (`книга` is illustrative).
- `bad` plus clean orthographic counterpart: bad-only form returns legacy empty and inspection `KNOWN_INVALID`; the clean counterpart remains FOUND (`дзига`/`дзиґа` is illustrative).
- `subst`: legacy empty; inspection `NONSTANDARD`. Candidate selection must come from the pinned source rather than assumptions about `такшо` or `штані`.
- `obsc`: legacy empty; inspection uses bad-like `KNOWN_INVALID` treatment.
- Colloquial: the locked v6.8.0 release asset has zero `coll` tag tokens and no reusable analysis-level comment encoding. The fixture and lock record `coll` as a known-absent class; lexical/comment text such as `розм.` must not be promoted to a marker.
- `slang`: legacy FOUND with `slang` retained; inspection `SLANG` (`бабло` is illustrative).
- `arch`: legacy FOUND with `arch` retained; inspection routes to `ARCH_OR_DIALECT_UNRESOLVED`, never `KNOWN_INVALID` (`аби-де` is illustrative).
- Pure dialect: an analysis with exact dialect evidence and no clean homograph; legacy FOUND, dialect evidence preserved, and inspection routes through dialect/heritage policy rather than invalid-word handling.
- Dialect homograph: only the evidenced analysis receives the dialect marker; clean homonymous analyses remain clean and visible (`кокні` is illustrative).
- Mixed modern/archaic: legacy remains FOUND and inspection exposes both analysis classes (`звір` is illustrative).
- 2019-orthography pair: generate and verify a clean modern spelling and a corresponding `bad` spelling. `проєкт` versus `проект :bad` is illustrative and must be verified from the pinned source before use.
- `alt` orthographic variant: remains compatibility-visible, retains `alt` in tags/inspection output, and is not misclassified as `bad`, `subst`, or `obsc`.
- Unknown marker/tagset drift: ingest fails rather than silently mapping or accepting it.
- Release or pipeline-identity mismatch: ingest and inspection fail closed.

Regression assertions must explicitly distinguish visibility classes:

- Every `bad`-, `subst`-, and `obsc`-only probe maps to `[]` under `verify_words`.
- `arch`-, `coll`-, `slang`-, and dialect-only probes remain returned by legacy verification with markers intact.
- Mixed analyses retain per-analysis identity and never transfer a marker to a clean homograph.

## R4 — Migration order

1. Land the lockfile, marker-preserving exporter, new importer, schema, generated fixtures, canonical JSONL comparison, and shadow-built DB. Supersede or disable `scripts/rag/import_vesum.py` for production of the new DB; the old v6.7.5/comment-stripping path must not be able to emit a database claiming the new schema or lock identity.

2. Add compatibility and inspection APIs without switching the production DB. Land MCP `inspect_word`, `inspect_words`, and `inspect_lemma` tools, handlers, schemas, and tool descriptions here. Update agent documentation and prompts that currently instruct callers to infer semantics from `verify_*` tags.

   Until activation, `inspect_*` must read the shadow DB through an explicit database path, unless the production DB first receives the complete `forms_all`/`form_markers` schema. Pointing inspection at an old production schema must return a structured unavailable/fail-closed result, not an uncaught `no such table` error.

3. Migrate marker-aware consumers against the shadow DB:

   - MCP `check_modern_form` and handlers exposing `is_archaic`;
   - `heritage_classifier` archaism attestation;
   - Atlas `enrich_manifest` and marked-paradigm generation;
   - other consumers whose behavior depends on returned markers.

   Correct `subst` classification during this step. Any `inspect_*` use in steps 3–5 must continue targeting the shadow DB until activation.

4. Add regression coverage around legacy boolean consumers, including spelling/audit checks, Russian-shadow checks, learner-state normalization, practice-deck generation, relation generation, scoring, and direct compatibility-view queries.

   Pure vocabulary-existence paths remain on legacy `verify_*`. The grammar-lexical gate is not such a path: it must migrate to `inspect_*` plus R5 policy at or before activation.

5. Migrate analytics and mining consumers where marked analyses are intentionally useful. Inspection-based migrations continue using the shadow DB; consumers needing only default-visible existence stay on the compatibility view.

6. Compare old and new outputs, compatibility-view results, inspection results, fixture results, canonical semantic hashes, row counts, and marker counts. Quantify and justify every acceptance delta caused by newly hiding `subst` and `obsc`. `arch`, `coll`, and `slang` visibility must not regress. Any unexplained delta blocks activation.

   Activate the versioned DB atomically only after the inspection-aware grammar-lexical gate and required marker-aware consumers are ready. The DB identity, runtime configuration, and gate policy must switch coherently.

## R5 — Grammar-lexical gate

The grammar-lexical gate consumes `inspect_words`, never raw `forms` presence or legacy `verify_words`.

- Clean compatible analyses with no coexisting bad-like analysis yield form validity `VESUM_ATTESTED`. Stylistic or heritage homographs do not by themselves make the spelling invalid; contextual policy still applies if the marked analysis is the intended reading.

- A token containing both a clean analysis and a `bad`, `subst`, or `obsc` analysis must never auto-pass merely because the clean analysis exists:

  - deterministic contextual POS disambiguation selecting the clean analysis may yield `VESUM_ATTESTED`;
  - selection of the bad-like analysis follows its rejection rule;
  - absent reliable disambiguation, emit `AUDIT`.

- Flagged-only `bad`, `subst`, or `obsc` yields deterministic `REJECT / VESUM_BADSTYLE`, except for structurally identified quotation or teaching-error roles.

- `coll` or `slang` means the form exists but generates a register candidate. Reject only through a versioned role/level register policy. Dialogue, quotation, and intentional voice remain eligible.

- `arch` or confirmed dialect is never rejected as a nonword. Require heritage lookup and then produce `HERITAGE_ALLOWED`, apply the relevant register policy, or emit `AUDIT`.

- An unknown marker, ambiguous `arch`/dialect interpretation, missing release identity, pipeline-identity mismatch, or inspection failure yields `AUDIT`, never ACCEPT.

- Compatibility-view visibility is not policy approval. In particular, legacy visibility of `arch`, `coll`, `slang`, and dialect preserves consumers but does not permit the grammar-lexical gate to bypass inspection.

- Continue lexical-use and contextual checks after form acceptance. A clean VESUM analysis proves morphological possibility, not correct meaning or usage in the learner’s sentence.

No files changed. Verification: all four design artifacts and binding D1–D6 spec were read; final status remained `## main...origin/main [behind 4]`.
