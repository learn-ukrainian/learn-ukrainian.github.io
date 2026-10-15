# Word cards — pilot assembly findings (#8981, mechanics-only)

- **Run:** 2026-10-15, frozen pilot `registry/atlas/pilot/pilot-v1.json` (manifest `7e95dbc7…`, 150 units, 272 source records), identity registry v2, held `sources.db` / `vesum.db` (`vesum@53923150073b4fc7`). Read-only; cards are host-only output, never committed: `build` refuses a destination inside the repository that git does not ignore.
- **Scope:** `build(S, V, I, O, R)` for the data-first slice fields (`WORD_CARDS_DATA_PLAN.md` §3) plus per-field accounting for WC-S01–WC-S10. Atlas page rendering, practice items, the dataset projection (#8988) and the Gate 2 golden set are separate, parked or later work; none is claimed here. Nothing in a card is model-written: every Ukrainian value is a verbatim source value with its locator.
- **Certification:** none. Cards are uncertified mechanics output (`quality.linguistic_review.status = none`, no practice eligibility). A green run proves the mechanics, never linguistic correctness.

## 1. How to run

```bash
A="--manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json \
   --register docs/sources/permissions-register.yaml --output <host-only dir>"
.venv/bin/python -m scripts.atlas.word_card_assembly build    $A   # cards/, ledger.json, build-manifest.json, report.json
.venv/bin/python -m scripts.atlas.word_card_assembly verify   $A   # exit 1 on any failed check
.venv/bin/python -m scripts.atlas.word_card_assembly rehearse $A   # withdrawal + rollback; exit 1 on failure
```

`build` refuses to start on source-row drift against the frozen literal rows, on a register whose pinned entries changed, on a held-out overlap, and on any card or sense the registry does not allocate. `verify` rebuilds twice, re-reads every locator from the held sources, validates every card against `schemas/word-card-v1.schema.json` and compares the on-disk cards to the in-memory build.

## 2. Result

| measure | value |
| --- | --- |
| cards (one per frozen unit) | 150 = 122 lexeme + 13 proper name + 15 MWE |
| assertions | 4,206 (ULIF 2,046 · VESUM 2,010 · PULS 134 · aggregator 15 · stress-trie 1), all with source, snapshot, exact locator, group/tier, licence reference |
| frozen source records cited | 272 / 272 |
| locators re-read and matched (read-only) | 4,206 / 4,206 |
| schema-valid cards · rebuild byte-identical · public projection of an untouched card equals the card | 150 · yes · yes |
| identity (VESUM↔ULIF, `identity.md` §4) | 136 high · 7 medium · 7 unresolved |
| `homograph_of` links (derived) | 14 |
| paradigm propositions (one per slot) | 1,070 verified · 219 variant · 486 single-source · 1 conflict |
| stress | 3 verified · 1 variant (`по́ми́лка`) · 1 conflict (`вряди́-годи́` vs stress trie) · 130 single-source |
| withdrawal rehearsal (the withdrawal unit's ULIF record; the whole stress-trie source) | record: 4 assertions removed, `pos`/`spelling` fall from `verified` to `single-source`, `stress`/`grammatical_label` become `suppressed`; source: `вряди́-годи́` stress `conflict` → `single-source`. Neither leaves a suppressed value or locator in any public projection; a rebuild under the selector is identical; lifting it restores the baseline bytes |

### WC-S01…WC-S10 accounting

Dispositions are per field per card (closed vocabulary: `asserted`, `held`, `unresolved`, `source_absent`, `not_in_frozen_inputs`, `not_applicable`). `not_in_frozen_inputs` means the source is not part of the frozen pilot S, not that it lacks the word.

| id | pilot outcome |
| --- | --- |
| WC-S01 | ULIF/VESUM carry identity, morphology, relations (27 synonym and 6 antonym groups aligned). **Modern meaning is absent for all 135 lexemes**: the held СУМ-20 crawl (100 articles) has none of them and ВТС is not admitted (plan §6.1). Recorded `source_absent`, never filled. |
| WC-S02 | Examples exist only where ULIF phraseology matches an allocated MWE record (none in the pilot). ГРАК/frequency: not in frozen S. |
| WC-S03 | Spelling asserted from ULIF and VESUM; Правопис and spelling variants not in frozen S. |
| WC-S04, WC-S05, WC-S08 | Antonenko / Karavansky, ЕСУМ / Грінченко, СУМ-11 contrast: not in frozen S. |
| WC-S06 | PULS level on 134 cards, spelling-keyed; ambiguous where the spelling has several cards. No sense-to-level mapping is claimed. |
| WC-S07 | Stress per lexeme; per-form stress retained in each paradigm value; alternatives preserved as `variant`/`conflict`. |
| WC-S09 | 30 cards carry 125 relation groups that cannot be aligned to one sense; they are retained non-voting, visible, unresolved. |
| WC-S10 | Verified by `verify`: every assertion's source, snapshot, locator, subject, quality state and source-record identity resolve. |

## 3. Findings and where each is folded

| # | Finding (evidence) | Disposition |
| --- | --- | --- |
| F1 | **Keyed declared sets were not representable.** A slot listing two forms (`rod.sg=замку\|замка`) was split as `slot=форма` strings, so equal sets reported `conflict`. | Fixed in `scripts/atlas/word_card_resolver.py` (`_resolve_keyed` strips the slot key before the set rule); example cards unchanged; pinned by `tests/test_word_card_resolver.py`; `schema.md` §8.1. |
| F2 | **Unaligned sense-level evidence had no home.** 125 relation groups sit on 30 cards whose senses or groups do not satisfy the one-unit rule. Putting them on a sense would be position-picking; dropping them hides evidence. | Retained as assertions on the **card** subject with `mapping {confidence: unresolved, basis: sense, ambiguous: true}`, never resolved into `fields`. Machine-checked in `schemas/word-card-v1.schema.json` (`assertion.allOf`); `schema.md` §6. Alignment needs overlay `sense_map` entries (language lane). |
| F3 | **`practice_eligibility: []` was ambiguous.** | Absence of a mode means not eligible (`schema.md` §9.5, JSON-schema description). The pilot evaluates no mode. |
| F4 | **Stress-trie lineage in `schema.md` §9.1 was stale** (`G-UWS?`, "possibly ULIF-derived"). The register (2026-10-06) records the data as ULIF-derived. | Assembly uses `G-ULIF`, tier 2: it never corroborates ULIF. `schema.md` §9.1 updated. |
| F5 | **`differs` in `identity.md` §4 step 2 over-rejects.** Taken literally ("any slot with a different form"), 59 of 135 pilot ULIF entries failed to match their single VESUM entry: ULIF and VESUM print variants and granularity differently (ULIF numeral and pronoun slots carry no number or person; VESUM adds archaic forms; ULIF files participles under `past`). | Refined in code and `identity.md` §4: `differs` = a common slot whose form sets are **disjoint** (or no common slot); one-sided variants are `compatible`; asterisk-marked ULIF forms are excluded from the form set; dimensions only one side states are dropped before comparing; VESUM forms tagged `arch/var/rare/long/short` are their own proposition `<slot>~<tag>`. Result: 136 high · 7 medium · 7 unresolved. **Needs advisor read: it refines a reviewed identity rule.** |
| F6 | **Aggregator `word` markup is inconsistent**: one of 15 pilot rows is `<fna>…</fna>` structured, 14 are `form {{</fras>}}`. | `aggregator_form()` handles both and must equal the frozen unit head. |
| F7 | **The aggregator entry body is not segmentable without a reviewed extractor** (heading variants, labels, numbered senses, quotations in one text). | Held as `entry_body_unsegmented` for 15/15 MWE cards; a ULIF phraseology record attaches only when its definition **and** a quotation are contained in the body (same dictionary record, `identity.md` §9). **Residual: reviewed aggregator segmenter (open-model-data).** |
| F8 | **No pilot MWE card has a same-record ULIF phraseology among the pilot entries**; 7 accepted ULIF idioms under pilot lexeme entries have no allocated MWE card (and 44 are withheld by the C4 rules). | Accounted in `ledger.json` `unattached`; they need identity allocation before assembly. **Residual: MWE identity allocation (open-model-data).** |
| F9 | **114 legacy `atlas0` article cards are allocated but not assembled.** Redirecting or splitting them needs reviewed overlay `merge`/`split` entries; the registry has none, and assembly must not invent them. | Not emitted; 150 unit cards only. **Residual: W4 redirect/split rehearsal (#8980).** |
| F10 | **Preposition-bound, asterisk-marked and unmapped-label slots** (C2 spec) withhold 235 preposition-bound, 91 asterisk-marked, 6 unmapped-label and 1 doubly-flagged ULIF slots, mostly the locative and the vocative. VESUM still asserts them, so those slots are `single-source`. | Kept per the C2 spec, with reason codes. Whether to accept preposition-bound locatives is a spec question, not decided here. |
| F11 | **The WP3 ingestion modules iterate whole tables** (78k relation sections, 8k phraseology): more than 10 minutes on the full harvest. | `write_extract()` copies the pilot entries, their homonym siblings and their sections verbatim; the same modules run unchanged in 3 s. Row digests and citations are identical to the held snapshot. |
| F12 | **Held `sources.db` has advanced since the freeze** (harvest continues; whole-file digest differs). All 272 frozen rows are byte-identical. | Frozen rows are re-read literally at every build; the build manifest records the freeze digest and the observed digest; the build id does not depend on whole-file drift. |
| F13 | **The register file grew after the freeze**; the whole-file digest no longer matches `source_register_sha256`. | The pinned referenced-entries digest (`register-pin`) authenticates the register; the build records that digest. |

## 4. Not done, with owner

| item | owner | state |
| --- | --- | --- |
| Atlas page render and practice items on the pilot build (Gate 1 presentation part) | Atlas lane, parked by the 2026-10-12 disposition | not started; no claim |
| Dataset projection of C2/C3/C4 and equivalence proof (W3, #8988) | open-model-data | not started |
| Redirect/split rehearsal and changed-snapshot import (W4) | open-model-data (#8980) | withdrawal and rollback rehearsed; redirect/split not |
| Held-out isolation (W0) | open-model-data | `heldout_isolation: unverified` — no membership manifest exists; no oracle output was used |
| Modern meaning for the lexemes (СУМ-20 harvest, ВТС admission) | open-model-data (#9609, plan §6.1) | blocking for WC-S01 learner outcomes |
| Sense alignment of 125 relation groups; identity overlay for 7 unresolved/7 medium cards | language lane (Gemini via AGY + sources) | needs reviewed overlay entries |
| Independent language-lane review of the pilot cards | language lane | not performed |
