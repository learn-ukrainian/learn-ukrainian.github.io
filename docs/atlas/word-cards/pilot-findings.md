# Word cards — pilot assembly findings (#8981, mechanics-only)

- **Run:** 2026-10-15, frozen pilot `registry/atlas/pilot/pilot-v1.json` (manifest `7e95dbc7…`, 150 units, 272 source records), identity registry v3, held `sources.db` / `vesum.db` (`vesum@53923150073b4fc7`) and the ULIF raw-response cache. Read-only; cards are host-only output, never committed.
- **Scope:** `build(S, V, I, O, R)` for the data-first slice fields (`WORD_CARDS_DATA_PLAN.md` §3) plus per-field accounting for WC-S01–WC-S10. Atlas page rendering, practice items, the dataset projection (#8988) and the Gate 2 golden set are separate, parked or later work; none is claimed here. Nothing in a card is model-written: every Ukrainian value is a verbatim source value with its locator.
- **Contract:** the retained `identity.md` §4 and `schema.md` §6/§13 rules, unchanged. An earlier draft of this assembler broadened identity matching (intersecting form sets, dimension projection, `<slot>~<tag>` propositions) and put unaligned sense evidence on the card subject; both were reverted because they changed reviewed rules without designated approval.
- **Certification:** none. Cards are uncertified mechanics output (`quality.linguistic_review.status = none`, no practice eligibility). A green run proves the mechanics, never linguistic correctness. `heldout_isolation: unverified`: no held-out membership manifest was used, and the author cannot attest it.

## 1. How to run

```bash
A="--manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json \
   --register docs/sources/permissions-register.yaml --output <host-only dir> \
   --sources-db <abs sources.db> --vesum-db <abs vesum.db> --atlas-db <abs atlas.db>"
.venv/bin/python -m scripts.atlas.word_card_assembly build    $A   # cards/, ledger.json, build-manifest.json, report.json
.venv/bin/python -m scripts.atlas.word_card_assembly verify   $A   # exit 1 on any failed check
.venv/bin/python -m scripts.atlas.word_card_assembly rehearse $A   # withdrawal + rollback; exit 1 on failure
```

`build` refuses to start on source-row drift against the frozen literal rows, on a register whose pinned entries changed, on a held-out overlap, on a missing or corrupt raw ULIF object (naming its digest and entry), on any card, sense or holding sense the registry does not allocate, and on any persistent card, sense or source-record id that differs from the frozen allocation's creation and mint evidence (F17). Output is written only outside every registered checkout of the repository or into git-ignored paths of the running checkout; the primary checkout and every sibling worktree are refused before any directory is created, file written or stale card deleted. `verify` re-audits the allocation, checks each card's identity, senses and sense maps against it without rebuilding (`identity_binding`), rebuilds twice, re-reads every locator, re-authenticates derived forms, checks relation-unit conservation and suppressed provenance, validates every card against `schemas/word-card-v1.schema.json`, checks public tombstones and compares the on-disk cards to the build.

The supplied-output verifier also derives each assertion's permitted source routes from its allocated subject's frozen evidence. Persistent record attribution is required for frozen-row evidence. Direct rows, derived forms, relation groups and same-record phraseology retain their distinct record and snapshot rules. Record withdrawal uses these independently derived bindings, so removing attribution cannot make an assertion escape a certified withdrawal. Regression controls cover coherent foreign-homograph rewrites, forged snapshots and missing attribution. These checks prove mechanics; independent exact-head review and held-out evaluation remain required.

## 2. Result

| measure | value |
| --- | --- |
| cards (one per frozen unit) | 150 = 122 lexeme + 13 proper name + 15 MWE |
| assertions | 3,163 (ULIF 2,036 · VESUM 977 · PULS 134 · aggregator 15 · stress-trie 1), all with source, snapshot, exact locator, group/tier, licence reference |
| frozen source records | 272: 271 cited by assertions, 1 held by the ledger (the paradigm section behind refused forms, F1) |
| locators re-read and matched (read-only) | 3,163 / 3,163 |
| consumed inputs in the build id | 396 row lookups and query results (ULIF homonym queries, `ulif_forms` with fingerprint and raw-page digests, VESUM lemma queries including empty ones, СУМ-20 headers) plus the WP3 extract digest |
| derived ULIF forms | 142 / 145 consumed entries authenticate against the parse of their held raw page; 3 are refused (F1) |
| identity (VESUM↔ULIF, `identity.md` §4) | 87 high (`unique_match`, 15 of them MWE) · 3 medium (no VESUM entry of the class) · 60 unresolved |
| relation units (C3 synonym/antonym groups) | 158 / 158 conserved: 2 aligned (one active sense, one group) · 156 held on an `unsplit` sense, `unresolved`, non-voting · 0 on a card subject |
| `homograph_of` links (derived) | 14 |
| paradigm propositions (one per slot) | 541 verified · 159 variant · 784 single-source |
| stress | 1 variant (`по́ми́лка`) · 1 conflict (`вряди́-годи́` vs stress trie) · 133 single-source |
| withdrawal rehearsal (all exit 0, every withdrawn build verifies) | record: 4 assertions · stress-trie source: 1 · whole ULIF source plus an overlapping record, in either order: the same 2,036 assertions and identical cards, the record selector credited with its 4 · a declared stress set and a paradigm slot by exact `value_norm`: 1 each · an assertion-id selector whose id no longer exists, through its pinned content fallback: 1 · rebuild under the selectors is identical; lifting them restores the baseline bytes |

### WC-S01…WC-S10 accounting

Dispositions are per field per card (closed vocabulary: `asserted`, `held`, `unresolved`, `source_absent`, `not_in_frozen_inputs`, `not_applicable`). `not_in_frozen_inputs` means the source is not part of the frozen pilot S, not that it lacks the word.

| id | pilot outcome |
| --- | --- |
| WC-S01 | ULIF carries labels and relations; VESUM morphology attaches only on a matched identity (87 cards). **Modern meaning is absent for all 135 lexemes**: the held СУМ-20 crawl (100 articles) has none of them and ВТС is not admitted (plan §6.1). Recorded `source_absent`, never filled. |
| WC-S02 | Examples exist only where ULIF phraseology matches an allocated MWE record (none in the pilot). ГРАК/frequency: not in frozen S. |
| WC-S03 | Spelling asserted from ULIF, and from VESUM on matched cards; Правопис and spelling variants not in frozen S. |
| WC-S04, WC-S05, WC-S08 | Antonenko / Karavansky, ЕСУМ / Грінченко, СУМ-11 contrast: not in frozen S. |
| WC-S06 | PULS level on 134 cards, spelling-keyed; ambiguous where the spelling has several cards. No sense-to-level mapping is claimed. |
| WC-S07 | Stress per lexeme; per-form stress retained in each paradigm value; alternatives preserved as `variant`/`conflict`. |
| WC-S09 | 156 relation groups wait on `unsplit` senses for a language-lane `sense_map`; 2 are aligned. |
| WC-S10 | Verified by `verify`: every assertion's source, snapshot, locator, subject, quality state and source-record identity resolve. |

## 3. Findings and where each is folded

| # | Finding (evidence) | Disposition |
| --- | --- | --- |
| F1 | **Derived `ulif_forms` rows were trusted without authentication**, and the build id ignored supplemental inputs: a mutated form with zeroed fingerprints was attached and verified, and the build id stayed the same. | Every consumed entry's rows are checked with the existing mechanisms (`compute_ulif_entry_fingerprint`, `ulif_raw_cache.get`, `parse_ulif_entry`): parser version, entry fingerprint, the manifest's paradigm page digest, and equality with the parse of the held page. Missing or corrupt raw objects stop the build; inconsistent rows are refused (ledger `forms_unauthenticated`), never attached or compared. Entries 22696, 76793 and 265001 parse to exactly their stored rows from the referenced page, but their stored entry fingerprints are stale (the entry or sections changed after the forms build), so they are refused as `stale_source_snapshot`: the `замок` castle and lock cards stay unresolved. The build id now hashes every row and query result consumed. **Residual: re-derive the forms of those three entries with the existing forms builder (a source-store write, outside this repair; open-model-data).** |
| F2 | **Identity matching departed from `identity.md` §4**: aspect was not compared, proper-name cards fell back to common-noun VESUM entries, identical paradigms separated only by stress were `stress_and_paradigm/high`, and overlapping form sets matched. | Restored: same POS and proper/common class, `equal`/`subset`/`differs` on whole slot form sets, aspect compatibility (biaspectual matches either), stress applied after paradigm, and the method names what separated the candidates (`stress_only/medium` when stress alone did). Unselected candidates and their per-candidate relation stay in the ledger (`vesum_correspondence_unresolved`). Measured: 57 of the 60 unresolved cards have no VESUM candidate of their class whose slot form sets equal ULIF's or contain them as a subset of slots; 2 compete with refused forms (F1); 1 has two compatible VESUM entries. **Residual: language-lane overlay `identity` entries, or a reviewed matching-rule change with designated approval.** |
| F3 | **Overlapping suppressions depended on selector order; structured values could not be selected.** | Selectors match the original assertion inventory and the union is suppressed; each selector is credited with every match, the assertion's `suppression_ref` is the smallest matching id. `assertion_content` compares the exact canonical proposition regenerated from the raw value under the selector's pinned normaliser (a declared set stays a whole set, a paradigm slot stays its slot); an unavailable normaliser fails closed. An `assertion_id` selector is resolved against the whole original inventory: while the id exists anywhere it withdraws that assertion alone, and its fallback must still describe it (else the selector is refused); the fallback applies only once the id is gone. A `source_record` selector is refused when its record is not allocated, when its `source_id` differs from the record's source, or when its `alias_at_creation` is not one of the record's aliases. |
| F4 | **Valid withdrawn builds failed `verify`.** | Retained suppressed assertions are checked whole (identity, record, register, locator); the takedown report must credit every suppressed assertion and cover exactly the declared selectors; an `asserted` ledger field whose assertions were all withdrawn must be in the takedown; public tombstones, recomputed resolutions, sense maps and links are checked independently, and untouched cards must equal their projection. Each declared selector's intended match set is recomputed without the assembler's matcher (`word_card_verify.intended_matches`, from the stored `value_norm` and the registry's source records) and must equal what it was credited and what was suppressed; an inconsistent selector fails. |
| F5 | **The host-only guard checked only the running checkout.** | Output paths are canonicalised (symlinks followed) and refused in the primary checkout and every registered sibling worktree, including worktrees outside the primary tree; only host scratch or git-ignored paths of the running checkout are written; discovery failure refuses. The same guard covers `rehearse`, the extract and every stale-card deletion. |
| F6 | **Unaligned relation groups were placed on the card subject, and a single group on an `unsplit`-only card was "aligned".** | Restored `schema.md` §6: automatic alignment needs exactly one **active** sense and one source group; every other group waits whole on the card's `unsplit` sense with an `unresolved` mapping and appears in that sense's `sense_map`. Three cards had no `unsplit` sense; registry v3 appends one holding sense to each (`allocate_pilot_identities --append-holding`, below). A build against a registry without them refuses with `MissingAllocation`. |
| F7 | **Keyed declared sets were not representable.** A slot listing two forms (`rod.sg=замку\|замка`) was split as `slot=форма` strings, so equal sets reported `conflict`. | Fixed in `scripts/atlas/word_card_resolver.py` (`_resolve_keyed` strips the slot key before the set rule); pinned by `tests/test_word_card_resolver.py`; `schema.md` §8.1. |
| F8 | **`practice_eligibility: []` was ambiguous.** | Absence of a mode means not eligible (`schema.md` §9.5, JSON-schema description). The pilot evaluates no mode. |
| F9 | **Stress-trie lineage in `schema.md` §9.1 was stale.** The register (2026-10-06) records the data as ULIF-derived. | Assembly uses `G-ULIF`, tier 2: it never corroborates ULIF. |
| F10 | **The aggregator `word` markup is inconsistent and its entry body is not segmentable without a reviewed extractor.** | `aggregator_form()` handles both markups; bodies are held as `entry_body_unsegmented` (15/15 MWE cards). **Residual: reviewed aggregator segmenter (open-model-data).** |
| F11 | **No pilot MWE card has a same-record ULIF phraseology**; 7 accepted ULIF idioms under pilot lexeme entries have no allocated MWE card (44 more are withheld by the C4 rules). | Accounted in `ledger.json` `unattached`. **Residual: MWE identity allocation (open-model-data).** |
| F12 | **114 legacy `atlas0` article cards are allocated but not assembled**: redirecting or splitting them needs reviewed overlay entries. | Not emitted; 150 unit cards only. **Residual: W4 redirect/split rehearsal (#8980).** |
| F13 | **Preposition-bound, asterisk-marked and unmapped-label ULIF slots** (C2 spec) withhold 233, 89, 6 and 1 doubly-flagged slots. | Kept per the C2 spec, with reason codes. |
| F14 | **The WP3 ingestion modules iterate whole tables**: more than 10 minutes on the full harvest. | `write_extract()` copies the pilot entries, their homonym siblings and their sections verbatim; the same modules run unchanged in seconds, and the copied rows' digest is a build input. |
| F15 | **Held `sources.db` and the register file have advanced since the freeze**; all 272 frozen rows are byte-identical. | Frozen rows are re-read literally; the pinned referenced-register-entries digest authenticates the register. |
| F16 | **Source-record attribution ignored the snapshot of the correspondence** (second review): a later snapshot reusing a frozen row's locator for another record rebound six assertions while `build` exited 0. | Each frozen row is bound through the registry correspondence whose source, locator **and** snapshot are the row's (`bound_source_record`); a missing, held, ambiguous or competing claim in that snapshot refuses before any card is assembled, and `source_record_key` is the strongest alias observed in that snapshot. `verify` re-derives the binding and checks every cited frozen row and its key against it. On the reviewer's later-snapshot registry the pilot builds the same cards as the frozen registry, apart from the build block. |
| F17 | **Persistent ids could be reassigned without a refusal** (R3-F1): two pilot card ids swapped, an `unsplit` holding sense relabelled `active` against its mint, or two source-record ids swapped together with their mint targets. Each was accepted by `build` and passed `verify`, because both used the same mutable registry as their oracle; the swap kept every id unique. | `identity_allocation_check` pins the frozen identity allocation by a fixed reviewed digest (`schema.md` §13). It covers the reviewed v2 allocation plus the holding epoch that `holding_check` admits against host-derived obligations. Loader, `Inputs`, `build` and `verify` refuse a differing allocation or a stale derived view with `MissingAllocation` before any source read. `verify` checks supplied cards' ids, creation keys, kinds, senses, seed provenance and sense maps against the audited allocation without rebuilding. Existing records' later-snapshot history still builds the same cards (F16). On the pilot: 150 cards and 158 relation units (2 aligned, 156 held) are unchanged, and verify passes. **Residual: independent exact-head review with fresh mechanical controls (open-model-data).** |

### Registry v3: append-only holding senses

`allocate_pilot_identities --append-holding` reads the frozen entries' relation units and applies the assembler's own placement check (`needs_holding_sense`) to each card's seed senses. On the pilot it found exactly three cards (`wc_02a5cjxcpbcf`, `wc_cvkw5nzdg00n`, `wc_bgr5q9c06wxg`; 7 held units) and appended one `unsplit` sense to each under the build `pilot-holding-sense-allocation-8981@sha256:<manifest>`, events `ie_0692`–`ie_0694`. Every v2 identity, sense, event and source record is unchanged (v2's event list is a strict prefix); the step is idempotent. Verification accepts only v2 plus exactly this append, and `--apply` now refuses to regenerate an existing allocation.

## 4. Not done, with owner

| item | owner | state |
| --- | --- | --- |
| Independent held-out evaluation of the repaired SHA and registry digest (source mutation, proper-name/aspect/stress, overlapping/structured withdrawal, all output routes) | codex-open-model-data; execution by a non-author evaluator under the existing holder grant | not run; restoration is not verified until it is |
| Re-derivation of the three stale-fingerprint form entries (F1) | open-model-data | source-store write, outside this repair |
| Identity of the 60 unresolved and 3 medium cards (F2) | language lane | needs reviewed overlay `identity` entries |
| Sense alignment of 156 held relation groups | language lane | needs reviewed overlay `sense_map` entries |
| Atlas page render and practice items on the pilot build | Atlas lane, parked by the 2026-10-12 disposition | not started |
| Dataset projection of C2/C3/C4 (W3, #8988) and redirect/split rehearsal (W4, #8980) | open-model-data | not started |
| Modern meaning for the lexemes (СУМ-20 harvest, ВТС admission) | open-model-data (#9609, plan §6.1) | blocking for WC-S01 learner outcomes |
| Independent language-lane review of the pilot cards | language lane | not performed |
