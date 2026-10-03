<!--
Canonical plan for epic #6321 (open-model-data). Version: v3.4.4 (2026-10-03).
Approval: v3.4.2 (sha256 b1a39a78b262a3418fa8cba4019ed882991e802ab18b7ff25f2dc12673ec4ed2) was reviewed over three
rounds by GPT-6.1 Sol (review of record; round 3 APPROVE) and Claude Opus 5.5 (rounds 1-2). The operator approved v3.3 on
2026-10-03 and ordered v3.4. v3.4.3 adds the operator's 2026-10-03 decisions on O4 and O5. v3.4.4 adds the operator's
2026-10-03 decisions on O1, O2, O3 and O6 and component C9 (textbooks).
Source sha256 of the body below (every line after this comment, verbatim):
2d5db0ae7d15336b61c361c1dacdf89c3c9811cfd0109acc8f156f16149e94e1
Verify: sed '1,/^-->$/d' PLAN.md | sha256sum
Landed by issue #9586 (step E0). Do not edit the body in place; changes need a new plan version.
-->
# Epic #6321 — plan v3.4.4 (working plan), 2026-10-03

Status: APPROVED. v3.4.2 (sha256 b1a39a78…) passed review (GPT-6.1 Sol round 3 APPROVE, review of record). v3.4.3 added the operator's decisions on O4 and O5; v3.4.4 records the operator's decisions on O1, O2, O3 and O6 (all 2026-10-03) and adds component C9 (textbooks) that O3 requires (change logs at the end). v3.4 (sha256 2d98a49d…) was reviewed by GPT-6.1 Sol (`plan-review-6321-v34-sol`,
CHANGES_REQUESTED, 4 blockers) and Claude Opus 5.5 (`plan-review-6321-v34-opus`, CHANGES_REQUESTED, 2 blockers).
Both passed the sources-MCP canary (verify_word, ULIF, query_pravopys). Every finding is adopted below; the
change log at the end maps each one. Also added: component C8 (literary pronunciation, Погрібний 1992 — operator:
very important) and step E3c. Supersedes v3.3 (operator-approved 2026-10-03, sha256 419a6afe…).
"Measured" = measured 2026-10-03 on the primary host at `origin/main` ea0201ee70, read-only.

## Goal
An open dataset of original Ukrainian text that teaches an AI model proper modern Ukrainian without Russian poisoning,
measurably improves a model on each required skill, and contains nothing invented.
Out of scope: count targets; Kyivan Rus / Middle Ukrainian text (30,287 literary chunks — kept, not used); dialect
component (#8141 closed: no published dialect dictionary held); base-model pre-training; public release (a separate
follow-up issue filed at E-final; the epic ends release-ready).

## What changed since v3.3
1. **ULIF complete.** Measured: 262,735 verified `ok` + 77 `parse_error` = 262,812 register rows (plus 3 unverified
   `ok` and 6,447 legacy `not_found`); sections paradigm 250,205 / synonyms 75,955 (45,280 entries) / antonyms 2,103 /
   phraseology 8,133 (6,553 entries); `ulif_forms` 4,742,272 stressed forms (build `ulif-forms-v4`, 59 failed
   entries). Retired dump gone (#8798 closed); a stray 16 KB `data/ulif_dump.db` remains (E1 removes). Master plan
   #8400 still OPEN (word-card consumers remain), collection itself complete.
2. **Word-card programme** approved (#8976, 2026-09-27); schema (#8978) and permissions register (#8979, 29 sources)
   merged; foundation PR #9519 open with two approvals; identity/assembly/takedown/pilot/Russification view not
   started. Dataset children #8988, #8989 wait on them.
3. **Operator IP decision 2026-09-27 (#8977, binding):** rights are the operator's responsibility; nothing held; no
   outreach; register = provenance and takedown record, not a publication gate. The register still records several
   planned sources as in copyright / all rights reserved (table under O1) → asked per component in O1.
4. **Old-plan work** 2026-10-02/03 (#9511 phraseology generator; #8341 school-subject rewriter) fails the restart
   principles (acceptance check failed; ungrammatical rewriting, Sol consult STOP_APPROACH).
5. **Training lesson (#8338):** templated reasoning copied by the model; format validity 100% → 2.8%. Also prior art:
   `scripts/projects/ua_open_weight_eval/hf_jobs_*` (#6273) ran Gemma 4 on HF Jobs; result recorded
   `invalid_semantic_output` — the evaluator must check response integrity.
6. **Seats (operator 2026-10-03):** authoritative for planning and Ukrainian judgment: GPT-6.1 Sol and Claude Opus 5.5.
   Gemini 3.8 Flash: bounded tasks only. Gemini 4: pending GA. This differs from the current `model-assignment.md`
   table (Flash first for Ukrainian review) → recorded there by step E-R (rules PR) before any review relies on it.
7. **No GPU on the primary host.** #8338 used a T4; HF Jobs path exists (paid).
8. **Правопис 2019 not held;** `query_pravopys` live-fetches 2019.pravopys.net (an unofficial site with ads). The
   official published text must be acquired (E3b).
9. **Погрібний «Українська літературна вимова» (1992) is held as a scan** (28 pp, sha256 5ea39606…, local data mirror);
   the `sources.db` rows (28 page chunks) are Tesseract OCR that loses transcription brackets, stress marks and the
   superscript vowel letters. The scan is legible (page 10 inspected). A clean transcription is needed (E3c).

## Principles
- **P1 No model- or script-written text.** Records contain only (a) verbatim text from a held source row, (b) lines
  from the reviewed instruction catalog with slots filled from source fields (catalog interpolation), and (c)
  lossless serialization (JSON keys, field labels from a fixed schema). No paraphrase, synonym substitution, filler,
  reasoning text, `<thought>` blocks or worked solutions written by code or a model. Transcription of a scanned source
  (E3c) is source acquisition, not authoring: it is verified against the page image and contains nothing absent there.
- **P2 Backbone and facet roles.** Forms: VESUM v6.8.0 + ULIF paradigms/forms. Stress: ULIF `form_stressed`
  (with `dual_stress_flag`). Spelling: Правопис 2019 (after E3b). Literary pronunciation: Погрібний 1992 (after E3c).
  Synonyms, antonyms, phraseology, usage labels: ULIF `ulif_dictua_*` only. Meaning: СУМ-20 (89 official articles) and
  ВТС (unofficial copy — checking only). Etymology: ЕСУМ. Calques: Антоненко-Давидович «Як ми говоримо» (169 chunks)
  and UA-GEC `F/Calque`. Human corrections: UA-GEC (CC BY 4.0). Exam tasks: ZNO/NMT with official keys. СУМ-11: only
  Russification evidence (opt-in subset). Facet authorities: the table in `ukrainian-linguistics.md` §4 (not restated).
  A tool miss escalates; it never condemns authentic text by itself.
- **P3 Lexical facts by structured agreement.** A form fact enters a record only when VESUM and ULIF agree on the tuple
  (lemma, homonym/sense, grammatical slot, variant). Single-source forms are **omitted**, not queued for review. ULIF
  forms with `marked_asterisk`, preposition-bound forms (на/у), entries with `unmapped_labels`, and the 59 failed
  entries are omitted until a rule for each is written and reviewed.
- **P4 Rights are decided — not a blocker in this epic.** The operator decided (O1, O3, 2026-10-03; consistent with the
  2026-09-27 decision on #8977) that authentic Ukrainian sources — textbooks, dictionaries, ULIF, Правопис, Погрібний,
  Антоненко-Давидович, literature — are used verbatim to teach a model proper Ukrainian, as the operator's IP responsibility.
  The dataset is for UNLP and the Ukrainian education system; UNLP reviews it first and decides on release. Agents and
  reviewers do not raise copyright or permission as an objection, gate, hold or open question in this epic. What remains is
  provenance only: every source has a register entry, every record a locator, each licence-distinct input ships with its own
  licence notice, and takedown requests arrive as GitHub issues.
- **P5 Relationship, not only quotation.** A record must be right about what it pairs: the answer belongs to the
  question's lemma, sense, slot or case. Every component defines its source-supported binding (table below) and the
  gate tests it with must-fail fixtures of genuine quotations attached to the wrong sense or question.
- **P6 No tools, no verdict.** Every review starts with a tool canary on its model × harness; Ukrainian findings quote
  tool output; factual claims quote a command, file or URL.

## Role map
| Role | Seat |
| --- | --- |
| Driver | Claude Opus 5.5 (open-model-data lane) |
| Data author | Extraction code only, dispatched; cross-family exact-head review |
| Ukrainian experts (sample review, sign-off, debate) | GPT-6.1 Sol (primary) and Claude Opus 5.5 (fresh seat, never the driver session) — both passed the MCP canary 2026-10-03 |
| Bounded Ukrainian tasks | Gemini 3.8 Flash (AGY): fixed-rubric per-record checks only |
| Gemini 4 | After GA + canary; operator decides its role |
| Disagreements | Tools first; then Sol and Opus debate with tool quotes; unresolved → **withheld as unresolved** (not called wrong) |
| Evaluation steward | A dedicated GPT-6.1 Sol task family (`eval-steward-6321-*`) that never builds training data, mixes or catalog lines; sole writer of the final set; final set stored outside the repo with only its hash committed; every read logged |
| Rights and sources owner | Operator |
| Excluded from Ukrainian work | Kimi, Grok, Cursor routes; Fable and Astra (cost) |
| Reviewer independence | Catalog and sample reviewers are never the seat that wrote the catalog or extraction code under review |

## Components
**All components are required** (operator decision O4, 2026-10-03): each must ship and pass D1–D4. C3, C4 depend on the Atlas word-card pilot (#8981) and C7 on the Russification view (#8982), so the epic's end depends on those atlas-lane items; that dependency is tracked, not waived.
| ID | Req. | Component | Source (measured) | Binding (P5) | Depends on |
| --- | --- | --- | --- | --- | --- |
| C1 | **Required (pilot)** | Grammar correction | UA-GEC gec-only train minus dev (1,706 train docs before dev carve-out) | learner sentence ↔ its aligned human-corrected sentence, same doc and annotator | E1 E4 E5 E9 E10 |
| C2 | **Required** | Forms and paradigms | VESUM ∩ ULIF on the P3 tuple | lemma + homonym + slot → the agreed form (stress from ULIF) | E4 E5 E10 |
| C5 | **Required** | Spelling | Правопис 2019 official text (E3b) | only the examples printed inside each paragraph, paired with that paragraph (§ locator); no code-chosen rule for outside cases | E3b E4 E5 E10 |
| C8 | **Required** | Literary pronunciation | Погрібний 1992 clean transcription (E3c); stress cross-check against ULIF (a mismatch is unresolved, never a correction of the book) | each printed word **with its phonetic context** ↔ its printed transcription ↔ the supporting paragraph span ↔ **the book's own verdict from the same paragraph (norm / admissible variant / non-norm, quoted)** ↔ rule paragraph and page. Non-norm transcriptions (e.g. [иван], [вил], [байдужи], which the book calls outside or a gross violation of the norm) appear only as the rejected side of a contrast, never as a target; ambiguous status → withheld | E3c E4 E5 E10 |
| C6 | **Required** | Calques | UA-GEC `F/Calque` (2,397 edits) first; Антоненко-Давидович passages by chunk/row locator | the human correction edit; book pairs only where the book's own text names both forms, each pair signed off by Sol and Opus | E4 E5 E10, O1 |
| C3 | **Required** | Synonyms, antonyms | ULIF sections via word cards (#8988) | headword sense ↔ ULIF group for that sense | #8981, E4 E5 E10, O1 |
| C4 | **Required** | Phraseology | ULIF phraseology + Фразеологічний словник (edition to verify, register: probably Білоноженко та ін., 2003) via word cards | idiom ↔ its definition ↔ its citation, same dictionary entry | #8981, E3 edition, E4 E5 E10, O1 |
| C7 | **Required** | Russification contrast | ULIF/VESUM vs СУМ-11 via #8982 | opt-in subset, excluded from default split, never pre-training (#8989) | #8982 |
| C9 | **Required** | Subject knowledge from Ukrainian textbooks | School textbooks (grades 1–11) and university textbooks in `textbooks` / `textbook_sections` (40,151 sections; 209 source files incl. 21 university) | a catalog question whose slot is the textbook's own section title (or the book's own printed question with its printed answer) ↔ the verbatim section text that the title heads, with book, grade, section and page locator; exercises without printed answers, tables of contents and OCR-damaged text are withheld; no rewriting of any kind | E1 E3 E4 E5 E10 |
Every source unit a component considers is accounted for as accepted, rejected (positive evidence of error, cited)
or unresolved (withheld, not called wrong).
Rulers only, never training: UA-GEC test split; 1,616 keyed exam tasks (30 `own-statement` essay tasks with empty keys
excluded); protection cases from authentic literary/regional text.

## Pilot admission gates (PA) — produced by E1–E11, required before E12 builds data
| # | Gate | Proof |
| --- | --- | --- |
| PA1 | **Quarantine.** 412 git-ignored files (637,987,720 bytes) under `data/projects/open_model_data` and the tracked record files (gold seeds 2×150; components decolonization 250, grammar 17; review samples) sealed with tombstones; every loader refuses them (`train_and_eval_real_model`, `gemma_hardware_probe`, `package_unified_dataset` — which today *requires* tombstoned v05 —, `upload_to_huggingface`, `v4_format_decolonization`, `v4_open_weight_learning_study`, `v4_pilot_canary_evaluation`, `scripts/dataset/train_gemma_huggingface.py`, both notebooks — one calls `create_repo(private=False)`); the guard covers `release/` tombstones; #9511 and #8341 code archived; stray `data/ulif_dump.db` removed. | Inventory + loader-refusal tests |
| PA2 | **Sources authenticated.** Provenance (origin, edition, hash) and register entry for every planned source incl. ZNO, Правопис 2019, Погрібний 1992; 11 `v1-official-codification` СУМ-20 rows quarantined; Фразеологічний словник edition verified. **Read-only enforcement repo-wide**: a test fails on any writable `sqlite3.connect` to `sources.db`/`vesum.db` outside ingest code (today: `v6_mine_ulif_phraseology.py:2288`, `v5_mine_middle_ukrainian.py:497`, `v4_production_shards_assembly.py:1253,1302,1581–1585`, `phase3_decolonization_partition.py:315,317`, `v5_mine_kyivan_rus_epigraphy.py:348,415,659` — fixed or archived). | Holdings manifest + test |
| PA3 | **Source and relationship gate.** Fails when: quoted text is absent from the cited row; a record lacks a locator; a source role is wrong (СУМ-11 as norm); text is neither source nor catalog nor serialization; a genuine quotation is bound to the wrong sense, slot or question (P5); generated rights flags appear as provenance. | Must-fail fixtures: 175 deleted rows; invented definitions on real headwords; row-1206 misattribution; #8341 rewritten sentences; #9511 `<thought>` rows; wrong-sense ULIF synonyms (e.g. «рада» homonyms); wrong-paragraph Правопис example; a non-norm Погрібний transcription ([иван] as the target for «Іван») |
| PA4 | **Acceptance check extended:** PA3 gate; instruction-prefix concentration measured separately (PA6); reasoning-text refusal; one approved-authority list replacing the three in code (33 in `audit_dataset_acceptance.py`; 22 + 21 in `v5_evaluation_harness.py`), generated from the §4 table and the register. Every old set fails for its named defect. | Checker runs on old sets + clean fixture |
| PA5 | **Split isolation.** Before any extraction: dev carved from UA-GEC gec-only train by **author-disjoint (hence document-disjoint)** selection on `author_id`, keeping all annotations and both layers of each document together (mirrors the official split, which shares 0 authors; train has 752 authors, the largest with 102 docs; only 2 annotator ids exist, so annotator-disjointness is impossible); dev doc ids excluded from both layers (gec-only and gec-fluency share 2,976 matching edit pairs in train) and from C1 and C6; multi-reference scoring (M2 against all available references; translation submissions kept and tagged by source language per O5, with per-stratum reporting; only 43 train docs have a second reference, so dev is mostly single-reference while test has 332 annotation files for 166 docs — dev and final scores are reported with their reference counts and never compared as equals). Exam and protection material frozen by source group (`work_id` / document) and excluded from C4 citations. A sentence-hash and n-gram overlap gate runs between every component and both rulers. | Split manifest + overlap-refusal fixtures |
| PA6 | **Instruction catalog** drafted (parallel to PA3–PA4) and reviewed by Sol and Opus (neither its author); prefix-concentration threshold fixed before builds. | Catalog + two reviews + checker test |
| PA7 | **Rulers sealed** by the evaluation steward: dev and final per required component (C1 UA-GEC; C2 forms from held-out lemmas; C5 Правопис examples held out by paragraph; C9 held out by whole textbook (book-disjoint); C8 Погрібний items held out **stratified by rule paragraph** (every rule seen in training, held-out examples per rule; the overlap gate applies); C3 held-out headword senses; C4 held-out idioms; C6 held-out calque edits (UA-GEC test `F/Calque`) and book pairs held out by row; C7 held-out contrast pairs (the model tells the imposed form from the norm)), plus 1,616 keyed exam tasks and protection cases. Evaluator canaries: gold high; **echo low on correction, echo high on preservation**; empty low everywhere; response-integrity check (lesson of #6273). Metrics from each benchmark's own definition; greedy decoding; evaluator robust to reasoning tags. Old #8338 evaluator and suites quarantined, not reused. | Canary receipts + sealed hashes |
| PA8 | **Seat canaries** recorded (Sol, Opus headless — both passed 2026-10-03 in the v3.4 reviews; Gemini Flash; Gemini 4 at GA) and the operator's seat decision recorded in `model-assignment.md` (E-R). | Receipts + merged rules PR |
Each child issue keeps its own task card and live dispatch preflight; PA gates do not replace them.

## Definition of Done (epic)
| # | Condition | Proof |
| --- | --- | --- |
| D1 | Every shipped component passes the extended check on its final files (0 records without locator, 0 unresolved quotes, 0 copies, 0 non-source text outside catalog/serialization, 0 relationship-gate failures, prefix threshold met, register entry per source). | Checker report |
| D2 | Facet tool checks per the escalation rule; rejections only on positive evidence; unresolved withheld and counted. | Per-record receipts + accounting |
| D3 | Per component: if ≥ 300 records, stratified random sample N = 300 reviewed by Sol and Opus (OK / MINOR / WRONG / UNSUPPORTED), WRONG ≤ 2% with Wilson 95% upper bound ≤ 5%; if < 300 records, **census** with 0 WRONG after fixes. UNSUPPORTED records are withheld unless resolved. | Review files + counts |
| D4 | On the sealed final set, the proof model trained on accepted data beats its baseline by the pre-registered margin **on each component's ruler** (C1–C9) with protection non-inferiority (greedy). A failed final evaluation leaves D4 unmet; further development needs a fresh independent final set. | Scorecard (model id, data version, set hashes) |
| D5 | Deterministic rebuild gives identical hashes. | Two rebuilds compared |
| D6 | Release-ready (not released): per-component licence notices (P4), dataset card, takedown path; public-release follow-up issue filed. | Card + notices + issue |
| D7 | Zero trainable residue: quarantined artifacts unreachable by any loader; old issues closed with pointers; old code archived; quarantine, loader and rebuild tests retained in CI; docs current. | Tests + inventory |
| D8 | Closeout hygiene: every child merged at reviewed head with lifecycle evidence; worktrees and branches reaped; residual count 0 or each residual owned. | Closeout receipts |

**Stop rule (dev ruler only).** A *trial* = one data mix trained once on the fast-loop model with the pre-registered
recipe. *Gain* = dev improvement ≥ the pre-registered margin on every required component present in the mix, with
protection non-inferiority. Mix families are frozen before any training: F1 = C1; F2 = C1 + C2; F3 = C1–C9 (C7 only in its opt-in split). A trial = one weighting of one family. Aggregate budget: at most 3 trials per family and 9 trials in total on the fast-loop model, never reset by renaming a family or switching model; 3 consecutive trials without gain in a family, or the total budget spent without a passing F3, → stop and report with a new plan version. The final set is never used for these decisions.
**E13 pass bar (pilot).** C1-only mix shows gain on the C1 dev ruler with protection non-inferiority within 3 trials;
otherwise stop and propose a plan version before E14+.

## Issue chain
| # | Issue | Depends on | Terminal goal | Route (impl / review) |
| --- | --- | --- | --- | --- |
| E0 | Plan v3.4.x lands in the repo as the canonical versioned plan (`docs/projects/open-model-data/PLAN.md`, replacing `ROADMAP_250K_SOVEREIGN_UKRAINIAN.md`); epic body rewritten; seat handoffs point to it | approval | merge | driver writes / Sol reviews |
| E-R | Record operator seat decision 2026-10-03 in `model-assignment.md` | — | merge | Sonnet / cross-family |
| E1 | Quarantine + loader refusal + archive old generators (PA1) | E0 | merge | Sol or Opus / cross-family |
| E2 | Old ULIF dump retirement | — | **done** (#8798) | — |
| E3 | Source authentication, register rows (ZNO, Правопис, Погрібний), edition verification, repo-wide read-only test (PA2) | E0 | merge | Sol / Opus |
| E3b | Acquire official Правопис 2019 text with provenance into `sources.db` | E0 | merge | Sonnet or Sol / cross-family |
| E3c | Погрібний 1992 clean transcription. Notation frozen before transcription: the complete symbol inventory is taken from the book's own notation key (pp. 4–5: primary and secondary stress, non-syllabicity, affricates, length, softening marks, devoicing, approximation vowels) and each symbol class is verified against image crops; every symbol gets one distinct encoding and a normalization rule (NFC). Starting codepoints: U+0301 primary stress; U+A675 combining Cyrillic и and U+2DF7 combining Cyrillic е for approximation letters printed above a vowel; U+0306 breve for non-syllabic [ў]; U+0361 tie for [д͡з], [д͡ж]; one fixed apostrophe codepoint for softness (incl. long soft consonants); [ґ] distinct from [г]; underlining of orthographic words recorded as a field, not markup; any Latin codepoint inside a transcription is rejected; illegible spans are withheld, not guessed. Method: render 28 pages; Sol and Opus transcribe independently from page images; script diff; disagreements adjudicated by a third, non-transcribing seat (bounded Gemini Flash check of the cropped image under a fixed rubric) with the operator as final authority; plus a census of every bracketed transcription (≈1,600 bracket tokens over ≈24 content pages, OCR estimate) against the image, because both seats can misread faint handwritten marks alike. Only adjudicated text replaces the OCR rows (old rows kept as superseded); custody report updated (it still lists the PDF as missing) | E0 | merge | Sol + Opus transcribe / third seat adjudicates / census / cross-family code review |
| E4 | Source and relationship gate + fixtures (PA3) | E3 | merge | Sol / Opus |
| E5 | Acceptance check extension (PA4) | E4 | merge | Sol / Opus |
| E6 | Per-component licence notices + dataset licence choice (P4, O1) | O1 | decision + merge | operator / driver |
| E7 | Book acquisition (#8791) + Орфоепічний словник української мови (Пещак та ін., Довіра 2001–2003, ~140k words) as a C8 extension candidate | operator | decision / ingest | operator |
| E8 | Compute venue and model selection: baselines, Ukrainian tokens/word, measured LoRA fit with pinned runtime, quantization, sequence length, batch; text-only LoRA path confirmed for Gemma 4 E-models (any-to-any); interruption recovery; bounded unavailable-GPU stop. Fix margin and protection bound after baselines | E9, O2 | decision-only | driver measures / operator approves |
| E9 | Rulers + split isolation + evaluator canaries (PA5, PA7) | E3; E3b and E3c for the C5 and C8 rulers | merge | eval steward (Sol) / Opus |
| E10 | Instruction catalog: draft now, checker test after E5 (PA6) | draft: E0; test: E5 | merge | Sol drafts / Opus reviews |
| E11 | Seat canaries incl. Gemini Flash; Gemini 4 at GA (PA8) | E0 | audit-only | driver |
| E12 | Pilot C1 data build | PA1–PA8 | merge | Sol / Opus; sample review Sol + Opus |
| E13 | Pilot measurement on dev (fast-loop model); pass bar above | E12, E8 | audit-only | driver |
| E14 | C2 forms | E13 pass, PA gates | merge | — |
| E15 | C8 pronunciation | E3c, E13 pass | merge | — |
| E16 | C5 spelling | E3b, E13 pass | merge | — |
| E17 | C6 calques | E13 pass, O1 | merge | — |
| E18 | C3/C4 via word cards (#8988) | #8981, E13 pass, O1 | merge | with atlas lane |
| E19 | C7 Russification subset (#8989) | #8982 | merge | with atlas lane |
| E-final | Final evaluation (D4) by the steward; closeout D5–D8; file the public-release follow-up | required components | certify | — |

## Old and open issues
| Issue | Disposition at E0 |
| --- | --- |
| #8140 ULIF idioms | Close with pointer: generator archived (E1), idioms re-enter as C4 (E18) |
| #8341 school subjects | Re-scoped to C9 (verbatim textbook sections; the rewriting approach stays stopped) |
| #8330 release assembly | Close with pointer: superseded by D6 + E-final |
| #8331 held-out benchmark | Close with pointer: superseded by E9 |
| #8988 / #8989 | Kept → E18 / E19 |
| #8791 | Kept → E7 |
| #8141 | Closed 2026-10-03 (not planned) |

## Operator decisions (all decided 2026-10-03)
- **O1 — verbatim use of in-copyright sources: YES** (operator's IP responsibility; see P4).
- **O2 — training venue: measure first.** E8 measures fit on free Colab and brings a measured recommendation, including any paid
  option, to the operator before training.
- **O3 — school and university textbooks: USED as record sources** → component C9.
- **O4 — all components required.** **O5 — UA-GEC translations kept, tagged, per-stratum metrics.**
- **O6 — the epic ends release-ready;** public release is a separate follow-up after UNLP review.

## Change log v3.4 → v3.4.1
- Sol B1 / Opus B1 (split leakage) → PA5, C1 binding, E9.
- Sol B2 (evaluator canary, exam keys, per-skill proof) → PA7, D4 per required component, 1,616 keyed tasks.
- Sol B3 (relationship checks, P3 tuple) / Opus S7 → P3, P5, PA3 fixtures, binding column.
- Sol B4 (frozen scope, stop rule) → required/optional column, accounting, stop rule definitions, E13 pass bar, D4 failure disposition.
- Opus B2 / Sol S6 (rights framing, 195 count) → O1 table, O3 by named source (measured 11 non-school files, not 34), O4–O6 added; O5 re-measured (940 translations, 581 ru) and recommendation reasoned.
- Opus S3 (writable connects) → PA2 repo-wide test with locations.
- Opus S4 / Sol S5 (ordering; R gates circular) → PA gates; E12 no longer waits on E6/E8; E10 parallel draft; E13 bar.
- Opus S5 (C5/C6 hidden judgment) → C5 printed examples only; C6 UA-GEC first, row locators, per-pair sign-off.
- Opus S6 (Правопис source unofficial) → E3b official text.
- Opus S8 (HF Jobs prior art, text-only LoRA) / Sol S6 (O2 fit) → O2, E8, PA7 response integrity.
- Opus S9 (seat routing vs binding rules) → E-R rules PR.
- Sol S7 (Wilson at small N) → D3 census rule, UNSUPPORTED withheld, reviewer independence.
- Sol NIT / Opus NITs → reasoning-text refusal wording; D7 without test-count target; three authority lists; stray dump; ULIF counts; #8400 open; edition verification; ZNO + Правопис rows.
- Operator 2026-10-03 → C8 + E3c (Погрібний), E7 orthoepic dictionary candidate.

## Change log v3.4.1 → v3.4.2 (round 2)
- Opus N1 (annotator-disjoint impossible) → PA5 author-disjoint on `author_id`; reference-count reporting.
- Opus N2 (C8 polarity) → C8 binding carries the book's verdict; non-norm only as rejected side; PA3 fixture.
- Opus N3 (notation) → E3c codepoint table, Latin rejection.
- Opus N4 (21 university files) → O3.
- Opus N5 (adjudication independence, shared misreads) → third-seat adjudication + census of bracketed items; ULIF mismatch = unresolved.
- Opus N6 (page hold-out holds out rules) → C8 ruler stratified by rule paragraph.
- Sol round 2: PA5 document-disjointness (all annotations together); C8 phonetic context + paragraph span + withheld ambiguity; E3c full inventory from the book's key, image-verified, NFC, illegible withheld; frozen mix families F1–F3 with a 9-trial aggregate budget; E9 depends on E3b/E3c.
- Stopping rule (driver, after two rounds): round 3 is a resolution check by the review of record (Sol) only; new finding classes become recorded residuals unless they are blockers to the pilot.

## Change log v3.4.2 → v3.4.3 (operator decisions only)
- O4 decided: all components C1–C8 required; rulers added for C3, C4, C6, C7; D4 per component; F3 = C1–C8.
- O5 decided: UA-GEC translations kept, tagged, per-stratum metrics.
- O1, O2, O3, O6 remain open operator decisions, each with the step it must precede.

## Change log v3.4.3 → v3.4.4 (operator decisions)
- O1 yes; O2 measure first; O3 textbooks used → required component C9 (verbatim sections, book-disjoint ruler); O6 release-ready, UNLP review first. P4 rewritten: rights are decided and not a blocker in this epic.
