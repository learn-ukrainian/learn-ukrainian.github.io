# Plan of record: Atlas open lexical layer (humans + machines)

**Status:** SETTLED for implementation sequencing — **no merges until CI is healthy**  
**Date:** 2026-07-25  
**Umbrella epic:** [#4387](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4387)  
**Lane:** atlas / practice-hub  

**Sources of settlement:**

| Artifact | Role |
| --- | --- |
| Gemini 3.1 Pro detailed plan | Author draft |
| Sol `gpt-5.6-sol` review | APPROVE-WITH-CHANGES (fatal schema/lifecycle fixes) |
| Claude Opus 5 review | APPROVE-WITH-CHANGES (enrichment parallel-truth, homograph, rights) |
| Prior 3-advisor strategy | BUILD-WITH-CONSTRAINTS |

Local dual-write (gitignored) retains full broker dumps under `.claude/atlas-epic/plans/alona-truth/`.

---

## 1. Verdict

**BUILD-WITH-CONSTRAINTS.**

Build an open Ukrainian **lexical join layer** that:

- extends **Word Atlas** for humans (UI + Practice Hub),
- exports structured data for machines (JSONL / later OntoLex),
- powers **activity generation** without inventing citations,
- carries a **sourced normative** (anti-calque / Surzhyk) layer.

Do **not** race to define all ~409k VESUM lemmas. VESUM is a **morphology floor** (stubs), not full lexicography.

---

## 2. Operator Decision Cards (accepted defaults 2026-07-25)

Operator directive: proceed. Defaults applied:

| ID | Decision | Default |
| --- | --- | --- |
| **DC-A** | Public sentence text | **Two-tier:** full lexicon local; public export only rows with explicit redistributable rights + attribution; else **pointer / short quotation** with bibliography |
| **DC-B** | Homograph / lemma layer | **Address early** (lemma_entries or equivalent) before freezing VESUM maps into SRS/export IDs |
| **DC-C** | Prescription model | Multi-authority **stances** + project editorial strength + corpus frequency evidence; **no boolean russianism** |
| **DC-D** | Alona / teacher seed privacy | **Private/local by default** until operator grants publish consent; Example deck may be local-first |
| **DC-E** | Alona input SSOT | **Document curated table (1018)** is Practice seed vocabulary; raw two-table extract + problem log remain audit trail; sentence file is **evidence**, not silent product truth |
| **DC-F** | GitHub Pages capacity | Prefer **Release assets + pointers** for large artifacts; GitHub Pro optional comfort, not required architecture |

---

## 3. Architecture rules (binding)

1. **`atlas.db` is a query projection**, rebuilt by `scripts/atlas/atlas_db.py` / hydrate — not a hand-edited store.  
2. **Durable SSOT for new lexical content** lives in **versioned files** under `data/lexicon/` (or equivalent), re-ingested on every rebuild (same pattern as synonym verdicts).  
3. **Schema must match live DB:** `articles.slug` is the article key; no invented `articles(id)`.  
4. **Migration matrix required** before new tables: map existing `enrichment` sections, `related_entries`, `article_provenance` → target model (no parallel-truth fork).  
5. **Attestation ≠ AuthoredExample** (separate entities).  
6. **FTS substring hits are candidates only** until locator, rights, span, and review admission exist.  
7. **Practice remains static-shard first** for early phases (no GraphQL requirement).  
8. **CI is currently broken — open PRs may exist, but do not merge product until CI green.**

---

## 4. Phased roadmap

| Phase | Work | Exit criteria |
| --- | --- | --- |
| **0a** | Inventory + migration matrix (docs) | Written matrix over enrichment/provenance; dual-read policy |
| **0b** | Schema v2 ADR + builder SCHEMA + external source files | Round-trip fixture; FK integrity with `foreign_keys=ON` |
| **1** | Alona reconcile + rights audit of sentence candidates | 1018 conservation; redistributable flags; quarantine weak/no_hit |
| **2** | Gold vertical slice (32–50) → static Practice shards → local Astro | Deterministic round-trip; local session works via `./services.sh start astro` |
| **3** | Full Example/Test deck from curated seed (local privacy policy) | Operator human smoke pass |
| **4** | Atlas↔VESUM census (exact/ambiguous/unmapped) | Rates published; no forced fake IDs |
| **5** | Teaching-sense editorial pilot | Human review sample + error rates |
| **6** | Prescription pilot (50) with authority resolver | Dispute policy; external sample review |
| **7** | Versioned machine export (JSONL first) | License filter gate; after CI healthy |

**Non-goals early:** 409k definitions; LLM-only glosses as published truth; embeddings as sense authority; orphan SQL migrations wiped by hydrate.

---

## 5. Alona / Practice vertical slice (first human+machine test)

**Input evidence (local):**

- Curated: `.claude/atlas-epic/plans/alona-truth/v2-curated.jsonl` (1018)  
- With sentences: `v2-curated-with-sentences.jsonl` (993 ok / 4 weak / 21 no_hit)  
- Problem log + originals under same directory  

**Product name:** Example / Test deck (not “private teacher product” in UI).  

**Machine test:** JSONL (or builder projection) with stable IDs + provenance.  
**Human test:** Practice session on local Astro.

---

## 6. Infra parallel track

- Extend `atlas_db.py` SCHEMA + re-ingest sources; benchmark DB size (today ~180MB+ before expansion).  
- Large public artifacts → **GitHub Releases**, not Pages blob.  
- Backup of `data/` / sources remains operator ops.  
- No merge of export CI jobs until CI fixed.

---

## 7. Issue checklist (opened under #4387)

| Issue | Topic |
| --- | --- |
| **#5793** | Parent: Open lexical layer (plan of record) |
| **#5788** | Inventory + migration matrix (docs first) |
| **#5789** | Schema/lifecycle ADR |
| **#5790** | Alona seed + sentence rights audit |
| **#5791** | Builder v0 schema + round-trip fixture |
| **#5792** | Gold vertical slice → Practice (local Astro) |

Implementation order follows section 4; **docs/matrix issues may proceed while CI is red; code PRs wait for CI.**

---

## 8. Immediate next engineering (after this docs PR)

1. Inventory matrix issue (docs, worktree).  
2. Schema/lifecycle ADR issue.  
3. Alona rights audit issue.  
4. Only then builder schema code.

---

**X-Agent trailer on commits:** `grok/4387-atlas-lexicon-plan-docs`
