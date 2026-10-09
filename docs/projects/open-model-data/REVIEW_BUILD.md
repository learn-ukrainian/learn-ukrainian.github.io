# Epic #6321 — private review build RB-1 (design v1.4.1)

Status: APPROVED — v1.3 Sol APPROVE (`design-rb1-sol-r3`); v1.3.1 editorial tightenings; v1.4 records the operator
decision of 2026-10-06 (word cards first, §6(b)), approved with the word-card data plan (`design-cards-plan-sol-r2`);
v1.4.1 editorial: §5 scope note and work-package table annotations (no rule changes).
Authority: operator decision 2026-10-06 on #6321 and its addendum (00:25Z): build the complete dataset (plan v3.5.0,
C1–C7 + C9) as a **private review build** for Ukrainian researchers, on the project's own build host, against the local
Sources MCP and `sources.db`; every value carries `source_id`, snapshot, locator, `licence_ref` and attribution; no
public publishing, no Hugging Face upload, no public artifact, no new scraping, no data copied off that host or into
this repository. The dataset licence (E6) and public-export rules stay open. Plan principles P1–P6 bind unchanged.
This document is a **versioned amendment for the review build only**: it does not edit PLAN.md, does not claim D4,
training readiness or epic completion.

## 1. Outcome, denominator, non-goals
- **Outcome.** One versioned, deterministic build directory on host-only storage holding, per component: records,
  complete unit accounting, adjudication and D3 receipts, per-source licence notices, a researcher README (review-only
  status, denominators, withholding reasons, normalization rules, annotation-layer and reference multiplicity), and an
  independent rebuild comparison. **RB-1 is delivered only when all eight components pass §4 and §7.** A build with a
  failing component is a diagnostic artifact, never "RB-1 delivered".
- **Accounting units ≠ records.** Each component declares its unit, and the framework counts units with its own
  query (§4.6), independent of the extractor. Measured 2026-10-06 on `origin/main` 3e4bdb3dd9, read-only:
  C1 unit = sentence × annotator in UA-GEC gec-only train (1,706 documents, 1,749 annotation files, 31,037 unique
  source sentences, 32,306 sentence × annotator units — Sol r2 measurement);
  C2 unit = (ULIF entry, grammatical slot) variant group; C3 unit = ULIF synonyms (75,955) / antonyms (2,103) section;
  C4 unit = ULIF phraseology section (8,133); C5 unit = Правопис paragraph (168) × printed example;
  C6 unit = sentence × annotator in the gec-fluency train layer containing `F/Calque` (2,113 markers), and the 342
  Антоненко `style_guide` rows; C7 unit = a form the Антоненко text names as wrong; C3 also covers meaning: unit = СУМ-20 sense of an
  unquarantined article (168 senses of 89 articles); C9 unit = printed heading found in
  allowlisted textbook pages (school grades 1–11: 163 files / 32,941 page rows; university `uni-*`: 21 files / 2,956).
- **Non-goals.** Training, baselines, margins, E13, D4 (no money is spent); ruler sealing beyond the exclusions in §5
  (E9 seals before any training build); the dataset licence; any upload; the Atlas word-card projection (§6);
  СУМ-11 vs СУМ-20 meaning-distortion pairs (not in plan C7; v1.0's C7(b) is dropped).

## 2. Privacy and containment (fail closed)
- Code in this repository (`scripts/projects/open_model_data/review_build/`, tests under
  `tests/projects/open_model_data/review_build/`). Tests and fixtures are **synthetic** (invented strings marked
  `SYNTHETIC`, never copied dictionary or textbook text). Real-data must-fail fixtures are generated at build time into
  the output directory by `verify` and never committed.
- **Output guard** (`--out` required): resolve the real path; walk the real path and every ancestor and refuse if any
  contains a `.git` entry, equals or lies under the repository root, any of its worktrees, or the private infra
  checkout (no reliance on `git` commands or `GIT_*` env); refuse if any component of the given path is a symlink;
  refuse unless the mount's filesystem type (from `/proc/self/mountinfo`, longest-prefix match) is in {ext4, xfs,
  btrfs}; create `0700` directories and `0600` files with `umask 077`; a pre-existing directory must be owned by the
  user, mode exactly `0700`, and carry no POSIX ACL (`os.listxattr` shows no `system.posix_acl_*`). Any check that
  cannot run refuses.
- **Everything that can hold text goes to `--out` only:** logs, tracebacks (the CLI catches, writes the traceback to
  `--out/logs/`, prints only record ids, component and row keys), SQLite temp (`PRAGMA temp_store=MEMORY`), the README/card,
  review inputs and receipts. Error messages and gate failures print only `record_id`, component and `row_key` (never locators,
  which may contain headwords, and never text).
- No network code: a test fails if the package imports `requests`, `httpx`, `urllib.request`, `http.client`,
  `socket`, `huggingface_hub`, `subprocess` or `os.system`.
- **Private infra manifest** (optional commit): produced only by a function with a tested field allowlist (hashes,
  counts, versions, code SHA, reason-code tallies); a test fails if any string field outside the allowlist or any
  Cyrillic text appears.
- **Review seats (D3, adjudication) and the addendum.** The plan's D3 (operator-approved) requires Sol and Opus to read
  sampled records. They run as fleet sessions on this same host (the normal subscription CLIs), read sample files from
  `--out` by path; when each review settles the driver moves its result file into `--out/reviews/` and leaves only a
  hash stub in local task state; no dataset file is copied to any other host, drive, repository or service. Driver interpretation, reported to the operator: model inference over bounded samples
  is the approved review method, not copying the dataset off the host. If the operator disagrees, D3 stops and the
  build is a diagnostic artifact (§1), not RB-1.

## 3. Record and provenance contract (`omd-review-record.v1`) — owned by WP0 only
`review_build/contract.py` is written by WP0 and frozen at its merge; component WPs dispatch after WP0 merges and
import it; any contract change returns to WP0 (one owner).

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Outcome = Literal["accepted", "rejected", "withheld", "excluded"]

@dataclass(frozen=True)
class Citation:
    source_id: str      # permissions-register id
    store: str          # "sources.db" | "vesum.db" | "ua-gec"
    table: str          # table name, or path relative to the UA-GEC root for file-backed rows
    row_key: str        # the table's real primary key as name=value pairs, e.g. "id=13834";
                        # UA-GEC: "file=data/gec-only/train/annotated/0012.a2.ann;sentence=4" (official reader index)
    field: str          # column name; for JSON columns "column#/json/pointer"
    locator: str        # non-empty human locator, e.g. "§ 7, с. 13–14"; "ULIF: абсолю́тний (1), synonyms group 1"
    field_sha256: str   # sha256 of the UTF-8 bytes of the column value as stored (whole column, before pointer)

@dataclass(frozen=True)
class Value:
    slot: str           # catalog slot, context part, or response part name
    text: str           # exact text placed in the record
    citations: tuple[Citation, ...]   # first = primary; further = supporting (e.g. VESUM beside ULIF); never empty
    span: tuple[int, int] | None      # offsets in transform(primary field); None = whole field
    transform: str      # id from the framework's closed transform registry (§4.1), e.g. "verbatim",
                        # "ulif_html_text@1", "line_excision@1"

@dataclass(frozen=True)
class Candidate:
    component: str      # "C1".."C7", "C9"
    unit_id: str        # accounting key of the source unit
    outcome: Outcome
    reason: str         # from the component's closed reason list
    evidence: tuple[str, ...]   # rejected: cited positive evidence (required); withheld/excluded: what is missing
    operation: str      # catalog operation
    slots: tuple[Value, ...]    # catalog slot values
    context: tuple[Value, ...]  # model-visible source context (e.g. the C7 pair), fixed serializer
    response: tuple[Value, ...] # response parts, fixed serializer
    flags: tuple[str, ...]      # e.g. "translation:ru", "c7_opt_in", "soviet_colonization_context"
```
Output JSONL record: `record_id, component, operation, catalog_line_id, catalog_version, status: "review_only",
instruction, context, response, values[] (slot, text, provenance id), provenance{id: Citation fields + snapshot +
span + transform + licence_ref + attribution}, flags, tool_flags`.
- `record_id` = sha256 of canonical JSON (UTF-8, sorted keys, no whitespace, `ensure_ascii=False`) of
  `{component, operation, unit_id, values: [[slot, text, [citation tuples…], span, transform] …]}` — unit, text and
  citations included.
- **Catalog line assignment**: within (component, operation, applicable-template set), records sorted by `record_id`
  are assigned lines round-robin over the applicable lines → exact balance. Template applicability follows the
  catalog's own rules (e.g. C2 with-sense only when the sense slot is non-empty and discriminating).
- `snapshot` = `<store>:<table>@<full sha256>` over `(row_key, field_sha256)` sorted by the UTF-8 bytes of `row_key`, of every row of that table the
  build read, all reads inside one read transaction per DB opened by the §9 read-only helper (`mode=ro`, `query_only`,
  ATTACH denied; transaction pinning as in `open_snapshot`, `scripts/curriculum/evidence/sources.py`); manifest also pins register, catalog, parser and code SHAs and the
  UA-GEC files hash.
- `licence_ref` = `permissions-register.yaml#<source_id>` + `terms.licence.name`. University textbooks need their own
  register row (`textbooks` covers grades 1–11), added with #9609's pending rows (with the Правопис 2019 row).
- `attribution` is produced by a per-source **attribution adapter** (WP0) that maps the register's `citation.form`
  to held metadata: VESUM version from `scripts/config/vesum_source.lock.json`; Антоненко edition/year from #9609's
  edition/holdings records, with the `style_guide` section title as locator where `page` is empty or 0 (`page` is null on 279 rows and 0 on
  63; page 0 is not a printed page); a row with no positive page and no section title is withheld
  (`locator_unavailable`);
  textbook author, title, grade, publisher, year from the book's own imprint page, cited (C9). Where a register form
  asks for data no held source records (e.g. СУМ-11 volume/page; the instruction-style `textbooks` form), the register
  row is amended to the held granularity with #9609's pending rows (after #9643), never filled by guess. The output is
  a resolved bibliographic string + `; ` + locator. Any placeholder, instruction sentence, or form the adapter cannot
  map withholds that source's records (`attribution_unresolved`); a must-fail fixture covers the instruction-style
  form.

## 4. Gate (runs on every build and in `verify`; any failure fails the component)
1. **Quotation.** Text/span equality applies to the **primary** citation; supporting citations authenticate
   agreement independently (e.g. VESUM has the same unstressed form and tags for a ULIF stressed form). Re-read each citation by `(store, table, row_key, field)` from the pinned snapshot; `field_sha256`
   matches; `text == transform(field)[span]`. Transforms come only from a closed framework registry (WP0), each with a
   property test proving it only removes or reorders nothing it should not: `verbatim`; `ulif_html_text@1` (text nodes
   in document order, whitespace collapsed, no insertion); `line_excision@1` (drops whole lines matched by a
   declared running-head/page-number pattern, records dropped line ranges); `dehyphenate@1` (joins `X-\nY` only when
   `XY` is a VESUM word form and `X-Y` is not, records each join). Components cannot register transforms. Locator
   non-empty; nothing in instruction/context/response outside catalog template text, cited values and serializer
   separators.
2. **Relationship (P5).** Each component ships a declarative **binding spec** (data, reviewed with the component) that
   the framework checks over citation identities, independent of the extractor: e.g. C3: slot headword cites
   `ulif_dictua_entries.id = E`, response cites `ulif_dictua_sections` rows with `entry_id = E` and one
   `sense_or_group_id`; C5: rule and example cite the same `pravopys_paragraphs` row and the example span lies inside an
   example-list region located by the framework's own colon-list parser; C7: a shared **contrast-pair identity** = the cited Антоненко `style_guide` row + its adjudication
   receipt; the СУМ-11 citation binds to the pair's *rejected* form, the ULIF/VESUM citations bind to the *recommended*
   form (each side keeps its own form key), and the response equals the recommended model-visible member — a swapped
   recommendation or a pair not named by that row fails; C9: heading and body cite pages of the same `source_file`, body pages contiguous from the heading page to the
   page before the next heading. Store/table/source_id compatibility table checked for every citation.
   Semantic binding errors that structure cannot see are caught by D3 (§7), not claimed by the gate.
3. **Source roles**, re-derived from the DB row of each citation (never from component metadata): `sum11` only in C7,
   only bound to the rejected side of an admitted contrast pair whose recommended side carries ULIF/VESUM citations, marked `soviet_colonization_context` with
   `sovietization_risk` and keywords; `zno_*` never; UA-GEC test never; dev-carve-out documents never; documents with
   `is_sensitive=1` never; any train sentence whose normalized hash occurs in UA-GEC test (44 measured) never
   (`ruler_overlap`); Погрібний never; textbook rows only from allowlisted `source_file`s (grades 1–11 and `uni-*`).
4. **Text hygiene.** Reasoning markers refused by a pattern list (`<think…>`, `<thought…>`, `Step \d`, `Крок \d`,
   `Міркування:`, …, extended by fixtures); duplicate `record_id` refused. Identical `(instruction, response)` text
   from **different** source units is allowed and reported as duplicate groups (authentic repeats, e.g. 661 C1 groups,
   max 31); training-time dedup is out of scope.
5. **Prefix and repetition** per the catalog spec (`instruction-prefix.v1-draft` at lengths 1 and 4 on text and ids;
   `instruction-repetition.v1-draft`: whole-template top1/top5, 8-token suffix top1 ≤ 0.60, 8-gram prevalence ≤ 0.60),
   per (component, operation); N ≥ 10 must PASS; N < 10 is reported as "insufficient evidence" (never PASS) and the
   README marks that operation not training-ready. RB-1 makes no training-readiness claim, so an N < 10 census
   operation (likely C7) does not block delivery; it does block any later training build.
6. **Accounting.** For each component the framework counts units with the component's declared **unit query** (SQL
   or file glob, reviewed with the component) and requires: every counted unit appears exactly once in the candidate
   stream; accepted + rejected + withheld + excluded = counted units; counted units equal the frozen count for that unit grain, measured
   by the unit query when the component's WP merges and recorded in the component spec (C1: 32,306 sentence ×
   annotator units; a later change needs a recorded reason); the dev carve-out and test-overlap sets are recomputed by
   the gate from the corpus, not taken from the component; every `rejected` carries cited evidence.
Must-fail fixtures (synthetic in CI; real-data ones generated into `--out` by `verify`): quote absent from cited row;
wrong span inside the right row; empty locator; a paraphrasing "transform"; wrong-homonym ULIF synonym group;
wrong-paragraph Правопис example; C7 pair with mismatched form keys; СУМ-11 text alone; a UA-GEC test or test-overlap
sentence; a dev document; a grade-0 / private textbook row; mixed-edit C6 unit; unresolved attribution placeholder;
reasoning text; a unit missing from the candidate stream.

## 5. Components — unit, binding, accept/withhold

> **Scope since v1.4 (§6(b)):** C1, C5, C6 and C9 are built directly by RB-1 as written here. The C2, C3, C4 and C7
> rules below (and their §4 gate checks, including the `sum11` role in §4.3) stay normative as the word cards'
> acceptance rules and the card projections' gate (`WORD_CARDS_DATA_PLAN.md` §3); RB-1 does not extract them directly.
- **Split manifest (WP1, E9 part).** Excluded from every component: UA-GEC test; the dev carve-out = whole authors
  ordered by sha256(`omd-rb1-dev` + author_id) until ≥ 10% of gec-only train documents (measured: 84 authors,
  171 documents, 10.02%), both layers; `is_sensitive` documents; train sentences whose hash occurs in test. Excluded
  units are counted as `excluded:<reason>`.
- **C1.** Unit = sentence × annotator, gec-only train layer, official `ua_gec` reader. Learner sentence ↔ that
  annotator's corrected sentence of the same document. Unchanged sentences kept (preservation). Translation
  submissions kept and flagged with source language (O5). Multiple annotators of a document give multiple records;
  the README states reference multiplicity. Withhold: unaligned, empty.
- **C2.** Unit = (ULIF entry, grammatical slot) with **all** its variants. Accept only when VESUM's form set for the
  same lemma and slot equals ULIF's form set exactly (complete agreement; never select a variant). VESUM has no homonym
  column, so the bridge is: lemma match, and if the lemma has several ULIF homonyms whose form sets for that slot
  differ, withhold (`homonym_unbridgeable`). Stress from ULIF `form_stressed` (+ `dual_stress_flag`). Each form value
  cites ULIF (primary) and VESUM (supporting). Withhold: `marked_asterisk`, preposition-bound, `unmapped_labels`, the
  59 failed entries, `parse_error` groups, header cells that are not authenticated. Template applicability per catalog
  (with/without sense; discriminating sense only).
- **C3.** Unit = one ULIF synonyms/antonyms section. Headword (with homonym index) of entry E ↔ the section's members
  via `ulif_html_text@1` on its stored `raw_html`. `sense_or_group_id` is structural, not semantic: when entry E has
  more than one group of the kind and the catalog's model-visible discriminator (the group's own printed lead word or
  gloss) is absent, withhold (`sense_not_visible`).
- **C3 meaning (СУМ-20).** Operator 2026-10-06 lists СУМ-20; plan P2 makes it the meaning authority. Unit = one
  `sum20_senses` row of an unquarantined `sum20_articles` row: headword (stressed headword, POS) ↔ that sense's
  verbatim definition, with its `register_labels` and the sense's own `sum20_citations` as context, all bound to the
  same article and sense (binding spec). The 11 quarantined articles never appear. Catalog operation added by WP-CAT.
  Census D3 (< 300).
- **C4.** Unit = one ULIF phraseology section: idiom ↔ its definition ↔ its citations (author labels), same section.
  Фразеологічний словник only if held as text with an edition record (#9609's edition file decides); otherwise its
  units are not in the denominator and the README says "not held" (residual → E7).
- **C5.** Unit = example printed inside a paragraph's own colon-introduced example list; rule text and example cite
  the same paragraph (`§ N`). Hyphenation only via `dehyphenate@1` or the paragraph's `hyphen_alternatives` when
  unambiguous; otherwise withhold. Needs the Правопис register row (§3).
- **C6.** (a) Unit = sentence × annotator in the **gec-fluency** train layer with ≥ 1 edit, **all** edits `F/Calque`
  (measured: 1,230 blocks contain F/Calque, 50 pure): sentence ↔ that annotator's correction; mixed units are
  `excluded:mixed_to_c1` (C1 draws its own units from the gec-only layer). Layer recorded in provenance.
  (b) Антоненко: candidate pairs only where the book's own text names both the rejected and the recommended form
  (verbatim spans, same `style_guide` row); ships only after Sol and Opus (fresh sessions, MCP canary, tool quotes)
  both sign it off; tools first, then debate; unresolved → withheld.
- **C7 (opt-in, flag `c7_opt_in`, never default).** Unit = a form the Антоненко text names as wrong. Admitted pair =
  that form is a СУМ-11 headword (СУМ-11 row cited as `soviet_colonization_context`, with `sovietization_risk` and
  keywords) **and** the book's recommended form is attested in ULIF and VESUM (cited); the pair (both forms, order by
  hash) is model-visible `context`; target = the modern ULIF/VESUM-attested form verbatim (catalog
  `modern_norm_selection`). Adjudicated by Sol and Opus like C6(b). Small denominator is a known residual (#8791).
- **C9.** Unit = a printed heading detected in allowlisted page text by a reviewed heading grammar (e.g. `§ N. Title`,
  `Тема N`, `Розділ N`, numbered headings at line start, matched on the page line itself, position recorded).
  Body = the text from the heading to the next heading, across contiguous pages of the same book, running heads and
  page numbers removed only by `line_excision@1`, hyphenation only by `dehyphenate@1`. Book identity (title, grade or
  university level, authors, publisher, year) from the book's own imprint/title page, cited; missing → withhold the
  book. OCR-damage screen, table-of-contents and exercise detectors (exercise without printed answer → withhold) are
  fixed in code **and reviewed by a non-author before the first build**; thresholds and their effect are reported.
  Never `textbook_sections.section_title` (it is `Сторінка N` on all 35,897 rows).
- Every component: `split` is not asserted — all records are `status: review_only`.

## 6. Deviation from plan sequencing (versioned amendment, needs this approval)
Changed for RB-1 only: (a) no E13 gate before C2–C9 (no training claim; D4 stays open); (b) **withdrawn in v1.4** by the operator
decision of 2026-10-06 on #6321 ("word-level data comes from the word cards — no drift, no rush"): C2 (forms,
stress), C3 (relations and СУМ-20 meaning), C4 (phraseology) and C7 (Russification contrast) are projections of the
word cards (#8988, #8989), built after the cards pass their gates, per
[`WORD_CARDS_DATA_PLAN.md`](WORD_CARDS_DATA_PLAN.md). Their §5 unit and binding rules stay normative: they become the
cards' acceptance rules and the projections' gate. The reviewed WP2/WP3 extraction and the WP6 C7 extractor are reused
as card ingestion, not merged as RB-1 components. C1, C5, C6 and C9 continue directly as designed. Unchanged: P1–P6, PA3-style gate (§4),
catalog-only project text, D1–D3 for RB-1, ruler exclusions above, every PA gate before any training build.
**Catalog amendment (WP-CAT)** before rendering: set catalog status from `draft` to reviewed for RB-1 use (PA6 reviews
recorded on #9611) add the `context` serialization for C7's pair, and add a C3 `sense_definition` operation for
СУМ-20; amend the C9 exclusion "until #8341 supplies authenticated printed headings" to name WP5 (which is #8341's
implementation) as that supplier; author Sol, reviewers Opus + Gemini 3.8 Flash
(neither author; precedent of #9679).

## 7. Quality review (D2, D3)
- D2: every record's Ukrainian tokens checked against local `vesum.db`; misses become `tool_flags` (escalation, never
  rejection of authentic text) and a stratum for D3.
- D3 per component: ≥ 300 accepted → stratified random sample of 300; < 300 → census. Seed = sha256 of the frozen
  build manifest + round number. Two independent fresh sessions (GPT-6.1 Sol, Claude Opus 5.5; MCP canary first, tool
  quotes required; never the session that wrote that component's code) each judge every sampled record OK / MINOR /
  WRONG / UNSUPPORTED. Receipts bind each verdict to `record_id` + build digest. Aggregation: WRONG from both seats → WRONG; WRONG from
  one seat → WRONG if tools confirm, else the disagreement path; UNSUPPORTED from either seat → withheld unless resolved with tool evidence;
  disagreement → tools first, then Sol↔Opus debate with tool quotes, unresolved → withheld as unresolved. Pass: WRONG ≤
  2% with Wilson 95% upper bound ≤ 5% (census: 0 WRONG after fixes), and records withheld by review stay in the candidate stream as `withheld:review_<class>` (accounting
  unchanged) and leave the record files. **After any fix the component is rebuilt and reviewed again by fresh sessions on the
  exact new build**: a census component is re-reviewed in full; a sampled component draws a new sample of 300 from
  records not previously sampled, and when fewer than 300 unseen records remain it reviews all unseen records plus a
  seeded sample of previously reviewed records to reach 300 (or the whole population if smaller). Passing only the old
  sample is not a pass.
- Gemini 3.8 Flash may add fixed-rubric per-record checks as a signal only.
- Rebuild comparison (plan D5): a second build from the same pinned inputs must give identical record files,
  accounting and manifest hashes.

## 8. Work packages, order, routing
| WP | Scope | Author | Code review (exact head) |
| --- | --- | --- | --- |
| WP0 | contract, transform registry + property tests, snapshot reader, output guard, register/attribution resolver, catalog renderer + balanced assignment, writer, manifest + private manifest allowlist, gate §4 (quotation, binding-spec engine, roles, hygiene, prefix/repetition, accounting), synthetic must-fail fixtures, CLI `build`/`verify`, determinism test | GPT-6.1 Sol | Claude Opus 5.5 |
| WP-CAT | catalog status + C7 context serialization | GPT-6.1 Sol | Opus + Flash |
| WP1 | split manifest + C1 + C6(a) | Claude Opus 5.5 | GPT-6.1 Sol |
| WP2 | C2 → card ingestion since v1.4 (#9820) | GPT-6.1 Sol | Claude Opus 5.5 |
| WP3 | C3 (ULIF relations + СУМ-20 meaning) + C4 → card ingestion since v1.4 (#9821) | GPT-6.1 Sol | Claude Opus 5.5 |
| WP4 | C5 | Claude Opus 5.5 | GPT-6.1 Sol |
| WP5 (#8341) | C9 (heading grammar, imprint metadata, detectors) | Claude Opus 5.5 | GPT-6.1 Sol |
| WP6 | C6(b) + adjudication tasks; C7 extractor kept as card input since v1.4 (#9823, #8982) | GPT-6.1 Sol | Claude Opus 5.5 |
| WP7 | builds, D2, D3, README, rebuild comparison, delivery | driver; reviewers Sol + Opus | — |
Order: WP0 and WP-CAT first; WP1–WP6 dispatch in parallel after WP0 merges. Routing is confirmed from live capacity at
each dispatch. Kimi, Grok, Cursor and OpenRouter routes do no Ukrainian work (plan role map); Grok may critique
engineering design only.

## 9. #9609 read-only guard — structural redesign
Replace per-shape dataflow analysis with a reference rule over `scripts/` (tests are out of scope: they build their
own fixture DBs; a separate test forbids tests from opening the real `data/*.db` writable): outside an allowlist,
**any reference** to a connection constructor fails — the attributes `connect` and `Connection` of the modules
`sqlite3`, `sqlite3.dbapi2` and `_sqlite3` in any context (call, assignment, argument, return, subclassing), importing
those names from those modules (`from sqlite3 import connect`, `from sqlite3.dbapi2 import Connection`, …), any alias
of those modules followed by those attributes, `getattr(<module>, …)` on them, and `importlib.import_module` /
`__import__` of them. Everything else goes through one helper,
`open_readonly(path)`: `sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)`, then `PRAGMA
query_only=ON` and an authorizer denying `ATTACH`/`DETACH`. Allowlisted writer files (ingest/build writers) are listed
with their target DB and a reason; a test asserts each opens only its declared target. Residual, stated: code built from
strings (`exec`) is out of scope. AC4 of #9609 is re-scoped to this rule. #9662 stays open until its migration
denominator (137 sites) reaches zero raw-path URIs with the special-character regression test.

## 10. Stop and residual policy
Stop and report on: any record text that is not source, catalog or serialization; any need for model-written
Ukrainian; any gate that cannot pass without lowering a bar; any Ukrainian judgment outside Sol/Opus/Flash; any spend;
any data leaving this host other than the §2 review-seat interpretation. Residuals with owners: C7 small denominator
(#8791, operator acquisition); Фразеологічний словник if not held (E7); D4, rulers (E8/E9/E13, after the operator's
compute decision); word-card equivalence (#8988/#8989, with the Atlas lane); else the driver.

## 11. Delivery
The driver tells the operator the build location (private handoff, not public text), the README, per-component
counts, D3 results and residuals. Nothing is sent anywhere by the build.

## 12. Findings map
v1.3 → v1.3.1 (Grok r3, editorial tightening; Sol approved v1.3 a2bd9843…): stdout never prints locators (§2);
Антоненко page 0 = empty, rows without page or section withheld (§3).
v1.2 → v1.3 (Grok r2): review results moved into `--out` (§2); printed fields (§2); `unit_id` in `record_id`, snapshot
sort, read-only helper (§3); attribution adapters + register amendments (§3); accounting grain and gate-recomputed
splits (§4.6); N < 10 handling (§4.5); D3 agreed-WRONG and withheld-in-stream (§7); D5 rebuild (§7); СУМ-20 meaning
under C3 (§1, §5, §6); C9 catalog withhold names WP5 (§6); guard covers `Connection`, `dbapi2`, `_sqlite3` (§9).
v1.1 → v1.2 (Sol r2): C7 contrast-pair identity (§4.2, §4.3); D3 re-review rule (§7); primary vs supporting
citations (§4.1); C1 unit count (§1); diagnostic-artifact wording (§2).

v1.0 → v1.1:
Sol 1 / Grok 3 relationship + circular quote check → §4.1 closed transform registry, §4.2 binding specs, D3 for
semantics. Sol 2 / Grok 5 C9 → §5 C9 heading grammar, delivered-only-if-all-pass §1. Sol 3 / Grok 3 C2 → §5 C2
complete variant agreement, homonym bridge, `citations` tuple §3. Sol 4 / Grok 3 C6 → §5 C6(a) pure-F/Calque fluency
units. Sol 5 C7 → §5 C7 form contrast with visible context, §6 WP-CAT; v1.0 C7(b) dropped. Sol 6 / Grok 7 D3 → §7.
Sol 7 / Grok 9 attribution, snapshot, labels → §3. Sol 8 / Grok 8 guard → §9. Grok 1 privacy → §2. Grok 2 ids → §3.
Grok 4 duplicates → §4.4, balanced assignment §3. Grok 6 accounting → §4.6. Sol 9–11 SHOULD → header, §3, §8, §1.
Grok SHOULDs → §4.5 full metric set, §4.3 `is_sensitive`, §2 FS/ACL rules and manifest allowlist, §5 C9 detector
review; v1.0 C7(b) homonym-number keys moot.
