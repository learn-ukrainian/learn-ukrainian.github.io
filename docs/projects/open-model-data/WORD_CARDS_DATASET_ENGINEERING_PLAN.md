# Word-card dataset engineering companion plan

Version: 0.3.0. Status: CONDITIONAL DESIGN AGREED; implementation acceptance pending. This companion applies the [proposed standard](../../best-practices/dataset-engineering.md) and [template](../../best-practices/dataset-plan-template.md) to #8977, #8988, and #8989. The conditional P1-P9 proposal has designated Opus and Sol agreement. Independent precommitted held-out execution, fresh critical full-scope exact-head review and landing remain pending; the agreement authorizes this literal integration only. It neither replaces nor version-resets prior approved plans. No dataset, pilot certification, fresh gold, or release is claimed here.

Documentation issue ancestry: [#10772](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10772) → [#8791](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8791) → [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321). #8977 is the related card programme, not #10772's native parent.

## Outcome and responsibility

The proposed first release is a standalone lexical base for private research collaboration with specifically named UNLP researchers, proposed for read-only access through a project HF organization, conditional on the access capability decision in the [storage design](HF_DATASET_STORAGE_DESIGN.md#access-capability-decision). Organization-wide read access is not per-repository least privilege. Actual identities, namespace, grants, and entitlement await operator-controlled verification. The consumer is lexical research and deterministic dataset projections under [#8988](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8988) and opt-in historical contrast under [#8989](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8989). It is not training readiness, public distribution, or Atlas rollout.

The accountable open-model-data driver owns scope, source checks, integration, and disposition. The source-inventory owner is the open-model-data lane under #10512/#9401. Extraction code uses Sol or Opus, never model-written Ukrainian records. Before execution the driver must appoint named extraction and annotation leads, a separate human-gold steward, qualified human adjudicators, and an independent evaluator. The release, maintenance, and takedown roles belong to open-model-data pending named assignment. Unassigned roles block execution, not this documentation proposal. The operator retains accounts, permission decisions, and public GO.

## Authority and phase mapping

Execution authority is the [current #8977 programme, 2026-10-12 block](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8977#current-plan-2026-10-12), then the fresh-gold contract [#10514](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10514). Read these before historical designs. Source completeness [#10512](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10512), independent certification [#10515](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10515), and full coverage #10516 remain separate prerequisites and proof obligations.

Historical approved [WORD_CARDS_DATA_PLAN v1.1.2](WORD_CARDS_DATA_PLAN.md), [REVIEW_BUILD v1.4.1](REVIEW_BUILD.md), and [migration gates](../../atlas/word-cards/migration.md) retain their data, accounting, identity, source, and review obligations. Conflicting historical W0-before-any-development, pilot/gold ordering, and Atlas-first consumer sequencing are superseded by the current programme. This proposal does not revive them.

| Current operation / stage | Historical mapping and retained obligation | Permission and evidence boundary |
| --- | --- | --- |
| Phase 1 source completion | W0 source handover; source inventory and facet-specific admission across W1–W9 | Complete authentic data and independently reconciled source matrix #10512 precede fresh gold. Missing/corrupt/quarantined input is not genuine dictionary absence. |
| Phase 2 engineering | W1a/W1b assembly mechanics, W2 comparison repairs, W3 projection mechanics, W4 withdrawal/identity work, W5 contrast mechanics | May run alongside source completion with draft inputs. No accepted facts, dataset export, training, semantic certification, or release claims. |
| Phase 3 mechanics-only fixture | Existing 150-unit inventory; bounded W1–W5 technical work | Development fixture, not a dataset-quality pilot. Reproduce draft digests, identities, locators, dispositions, suppression and rollback. Gold seal is not an entry gate for these permitted mechanics. |
| Phase 4 fresh independent gold | W0 isolation intent and W7/Gate 2 evaluation contract, with historical sequencing superseded | #10514 requires Phase 1 complete and a frozen final evaluation specification. Independently controlled fresh gold replaces no source prerequisite. Old 220 cases stay development regressions. |
| Proposed quality pilot → measured gate; current Phase 5 certification | W1–W5 semantic checks, applicable W6/Gate 1 data obligations, W7/Gate 2, #10515 | Actual dataset-quality pilot construction requires admitted seal first. Independent pilot certification uses its own protected inputs. Measured gate must pass before scale. |
| Proposed scaled build; current Phase 6 full coverage | W8 PULS later coverage and W9 full-scale accounting | Requires source completion, admitted seal, pilot certification, and every applicable original gate. The seal alone is insufficient. Retain streaming/resource/resume and full-denominator reconciliation. |
| Proposed independent evaluation → publish; current Phase 7 release | W3/W9 projection equivalence, #8988/#8989 release evidence and RB-1 component gates | Evaluate the exact scaled artifact on a separate untouched final partition. Private HF collaboration is a proposed later target, not an amendment authorizing transfer from RB-1's host-only review boundary. |
| Parked Atlas presentation/practice | Historical W6 rendered pages, generated exercise semantics, eligibility/progress | Remains an Atlas obligation under the current programme. It is not a new Data blocker or a claim of Atlas delivery. Applicable Gate 1 technical/identity/source checks remain required. |

If an operation's fixture-versus-dataset status is ambiguous, refuse it before writing. In particular, renaming accepted records or exports as a mechanics fixture does not authorize them.

## Preserved fields, source units, and topology

The [schema](../../atlas/word-cards/schema.md) and [identity contract](../../atlas/word-cards/identity.md) remain the existing designs. The proposed standalone lexical base has its own private repo, version, card, DoR, and DoD. C2 forms/stress, C3 meanings/relations, C4 phraseology, and C7 contrast are deterministic named configurations of the same pinned card version, never independent mutable fact stores. C7 requires explicit opt-in. C1 correction pairs, C5 spelling, C6 calques, and C9 textbook knowledge retain separate dataset plans/repos and stable card-ID links where applicable.

One card per word is not a homograph merge rule. Preserve lexeme, homonym, sense, and MWE identities, many-to-many source correspondence, variants, conflicts, redirects, and source-specific sense partitions. Source homonym numbers do not become global IDs. Topology remains a proposal. The historical RB-1 no-network/host-only constraint means storage/export is a separate approved release step, not uploader code inside its builders. A future schema or consumer mismatch must return with evidence for designated review; do not collapse identities or rewrite REVIEW_BUILD to fit storage.

| Field / source unit | Retained acceptance and accounting |
| --- | --- |
| `paradigm`, ULIF entry × slot variant group; VESUM entry/slot | Compare all variants using the reviewed component applicability/reason lists. Keep asterisk, preposition-bound, unmapped/header, parse-error, and unbridgeable-homonym omissions. Genuine disagreement remains conflict. VESUM morphology is not stress evidence. |
| `stress`, source-stressed form bound to lexeme/POS/sense where applicable | Retain source variants versus conflicts and source lineage; never resolve by model intuition. |
| `senses[]`, `definition_uk`, unquarantined source article/sense | Seed mapped СУМ-20, then ВТС only after admission, then ULIF nonblank `sense_gloss`; preserve stable sense IDs and unsplit/no-meaning cases. Quarantined articles remain excluded. ВТС edition/register/parsing admission stays required. |
| Sense-bound `synonyms` / `antonyms`, ULIF relation section | Preserve `sense_or_group_id`. Non-visible source sense stays `sense_not_visible`, not position-based alignment. Retain the wrong-homonym must-fail control and direct-extraction equivalence. |
| MWE idiom, source phraseology section | Keep identifiable expression, source definition and author-labelled citations from the same section. Unresolved sense, definition, or citation stays withheld. Edition evidence is required. |
| `russification_exposed`, cited contrast row plus adjudication | Preserve correction direction, both cited spans, two-seat adjudication, source-scoped modern corroboration, and opt-in export. СУМ-11 is historical `soviet_colonization_context` with risk/keywords, never modern definition, norm, stress, example, or answer. |

All assertions keep `source_id`, `snapshot_id`, exact `locator`, `licence_ref`, `extraction_version`, attribution, subject/scope, and quality disposition. Evidence units remain separate from accepted facts. Preserve `english_gloss`, its sense equivalent `gloss_en`, `cefr`, examples, collocations, practice eligibility, and all WC-S01–WC-S10 source-role obligations as existing scope/later obligations; this slice does not erase or generate them.

The full source denominator is **UNKNOWN**. Owner: open-model-data source-inventory lead. Resolving event: #10512 complete-data receipt and #9401 frozen source matrix, with per-source versions/checksums, required ranges, all source-unit counts, and independent reconciliation. Freeze source units, spellings, lexemes, senses, MWEs, forms, and cards separately. Every unit ends once as accepted, held, withheld with reason, or excluded with reason. Counts in old designs describe their historical snapshots, not current full coverage.

Retain the existing mechanics inventory's 150 source-local units, 272 selected literal rows, 114 legacy allocation projections, and 140 aliases as separate historical denominators from migration §3. Its 22 source-only correspondence gaps remain unresolved there, not silently allocated. Recheck actual manifests before any future build. Preserve the later PULS A1–B1 obligation of 4,512 rows, including 962 + 1,386 + 2,164 level rows, and many-to-many VESUM accounting. PULS coverage is not a first mechanics-fixture gate. Retain W2's unexplained-disagreement stop rule, W3 unit-by-unit equivalence, W4 withdrawal/changed-snapshot/rollback and redirect/split/rebuild identity checks, W5 contrast checks, and RB-1 P1–P6 and component-specific gates.

## Freeze status and fresh-gold prerequisites

The independent metadata audit supplied for this correction (`e13b1acd892e4f90`, 2026-10-16) establishes the following observational limits. It opened no protected case payloads. It is lineage evidence, not gold or dataset-quality evidence.

| Observation | Evidence and limit |
| --- | --- |
| Public mechanics inventory | 150 units and 272 selected rows, including 135 ULIF entries and one paradigm section; zero relation sections. File SHA-256 `19caa9148c76294156f12b4d1b11c11f4563ba0facac142460dd927543a7bc71` identifies mechanics, never gold. |
| Historical timing | First Git record `2026-10-03T12:52:45Z` is a recording date, not an authenticated runtime freeze. |
| Current stored ULIF | Strict read-only observation counted 269,269 local entries. This is not a source-complete register denominator. Current complete-content hash and authenticated snapshot date remain UNKNOWN. |
| Source completion | Existing receipt says `complete=false`; five source-completion ACs remain unmet. Independently reconciled full coverage, counts, current content hash and date are mandatory before constructing new gold. Owner: source lead, resolving through #10512/#9401. |
| Relation repair #10182 | No direct selected-section overlap with this pilot, which contains no relation sections. Downstream output and gold affected cases remain UNKNOWN. An independent steward must trace candidate dependencies against authenticated source versions in protected evidence. Code chronology cannot establish an affected-case list. |
| Gate 2 | No admitted seal SHA/date or authenticated authority established. Candidate existence is unproven, not disproved. The verifier refusal below remains unchanged. |

The audit's historical build fingerprint does not authenticate current content. Raw-capture completeness and reference resolution remain prerequisites. The driver retains the audit receipt and the independent steward owns protected candidate-lineage evidence. No author selection, rebuild, source operation or seal is performed by this correction.

The existing verifier command, expressed relative to the project interpreter, is:

```bash
.venv/bin/python -m scripts.atlas.word_card_foundation verify \
  --manifest registry/atlas/pilot/pilot-v1.json \
  --registry registry/atlas/identity/registry.json --for-evaluation
```

The driver's captured literal refusal is:

```text
REFUSED: Evaluation refused: authenticated operator authority/signature and acceptance thresholds are not established; Gate 2 remains open
```

This is reported metadata evidence, not an author-run semantic evaluation or proof of a gold manifest. A future owning implementation lane must bind the admitted manifest SHA, UTC seal date, authenticated authority/signature, thresholds, code/input versions, separate steward and isolation receipt. Scaled construction remains prohibited until that seal and every original applicable prerequisite pass.

[#10514](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10514), observed OPEN during this documentation task, retains these five exact criteria:

- AC-01: Require the Phase 1 complete-data receipt before constructing new gold. Freeze the final source universe, evaluation specification and case/stratum denominators.
- AC-02: Appoint an evaluation steward separate from the assembler and qualified independent adjudicators. Select fresh representative cases and failure strata from complete data, without deriving gold from the old 220 cases or assembler rules.
- AC-03: Adjudicators inspect authenticated source evidence without assembler outputs. Every expected identity, field value, conflict and abstention resolves to its exact source evidence and appropriate claim scope.
- AC-04: Seal membership and expected answers away from the assembler. Verify isolation across aliases, related source records and access itself using #9608 infrastructure; a membership hash alone is insufficient.
- AC-05: Independent isolation and adjudication proof records zero assembler access to protected membership/answer keys and source-backed coverage for every expectation. Keep disagreements and abstentions explicit.

## Conditional contract and reference bindings

The integrated contract below retains every G01-G35 table and AC-01 through AC-05. Its source is the Opus v2 contract SHA-256 `4fb1746630bc1038c8f327fd63bc9558b7a4553136aa38c2ffbbee5c7e8a31be`, with decision delta `271a9b97ed569401bdaa33891f40898fa9a131038da2fc5fb7867ff7efc2f5b5` and full Sol designated assessment `f467d3bbd4e72af2a1e74d90d8f7815d25c80e79e5b32d9a60f7c5ce64e21da5`. G19 applies the assessment's sole nonmaterial followup: child bounds do not in general establish a union bound. All other gate table contents retain the agreed bytes. Prior development checks T1-T12 are author diagnostics, not independent held-out evidence or execution ratification.

Line references such as W:179 and S:84 identify the preserved source at commit `81a0109d78b5ead2151cc34b9b16f30507d698d8`, not this integrated document's line numbers. Their detailed obligations remain incorporated. Section references §0-§9 identify the conditional contract below. C identifies the retained candidate gate inventory, SHA-256 `e473d9de63f3bdd7be3eaa7752cd98d3099575c87ed281e80098e480379bef33`; its tables are reproduced below. Historical evidence notes in retained gates describe that proposal's evidence boundary, not new execution results.

| Alias | Source at the preserved commit |
| --- | --- |
| W | [Word-card companion](https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/81a0109d78b5ead2151cc34b9b16f30507d698d8/docs/projects/open-model-data/WORD_CARDS_DATASET_ENGINEERING_PLAN.md) |
| D | [Word-card data plan](WORD_CARDS_DATA_PLAN.md) |
| S | [Dataset engineering standard](../../best-practices/dataset-engineering.md) |
| Q | [Word-card schema specification](../../atlas/word-cards/schema.md) |
| J | [Word-card JSON Schema](../../../schemas/word-card-v1.schema.json) |
| T | [Dataset plan template](../../best-practices/dataset-plan-template.md) |
| H | [HF storage design](HF_DATASET_STORAGE_DESIGN.md) |

## Fresh 220-case structural Gate 2 recommendation

The old 220 cases are development regressions only, including published named witnesses in migration §4. They cannot supply fresh gold. This proposal concretely retains **exactly 220 fresh independently adjudicated structural cases: 200 hard plus 20 ordinary controls**. It preserves the category obligations with new, independently selected source cases. Previously disclosed example words remain regression/coverage references; the steward selects fresh equivalents, never those exposed witnesses as untouched evidence.

Recommend exactly 132 replay cases and 88 protected held-out cases. The 60/40 allocation tests both deterministic overlay replay and blind structural matching. Each case is assigned once after overlap resolution. Related source/alias closures cannot span pools or other audit partitions. If the frozen source universe cannot provide this allocation, stop for a reviewed replacement proposal without shrinking the 220/200/20 requirement.

| Migration §4 category | Fresh total | Replay | Protected held-out |
| --- | ---: | ---: | ---: |
| Multiple ULIF homonyms / homographs | 40 | 24 | 16 |
| Stress doublets | 20 | 12 | 8 |
| Proper-name/common-noun pairs | 20 | 12 | 8 |
| Aspect pairs | 20 | 12 | 8 |
| Aspect homographs | 5 | 3 | 2 |
| MWEs under several headwords | 20 | 12 | 8 |
| Multi-sense words with unsplit senses | 20 | 12 | 8 |
| Stress disagreements, genuine and identity artefacts | 20 | 12 | 8 |
| Tier-3-only cards | 10 | 6 | 4 |
| ULIF header damage | 10 | 6 | 4 |
| Cited historical contrast pairs | 15 | 9 | 6 |
| Ordinary agreeing controls | 20 | 12 | 8 |
| **Total** | **220** | **132** | **88** |

Before selection/execution, #10514 requires complete authentic sources, a frozen final universe/specification, a named independent human-gold steward/gold isolator and qualified adjudicators. The driver appoints them; role labels are not appointments. The steward privately binds category assignment, case-to-source keys, aliases, pairs/triples after expansion, expected cards, identities, variants/conflicts and expected abstentions to a hashed manifest. Expansion/card counts remain UNKNOWN until independent source adjudication; 220 is the pre-expansion case denominator. Preserve exact source locators for every expectation and the migration single-source-removal recomputation tests. No assembler output supplies expected truth.

The steward initially seals all expectations, then discloses only the 132 replay cases to the author for exact overlay `identity`/`split`/`merge` regression. They are exposed replay, never untouched held-out evidence. The 88 cases and all related closures remain isolated under #9608, outside every build input and overlay. The evaluator runs them only against the frozen implementation at the measured gate. A held-out case used for a fix is retired to regression and replaced by the steward under a newly frozen ledger, never inserted into the evaluated overlay.

Recommend these exact-count thresholds at the **actual authenticated operator freeze**: replay reproduced exactly; **0 wrong merges, ≤2 wrong splits per hard category, false abstentions ≤5%, and 0 ordinary-control errors**. Wrong partners are identity errors and fail; variant/conflict mismatches and other incorrect structural outcomes fail. False abstentions use human-answerable case counts, reported overall and per category, with the 5% ceiling applied to each nonempty denominator without rounding up permitted errors. An undefined required denominator makes the gate incomplete. Report expected-match coverage, wrong merges/splits/partners, correct and false abstentions, variant/conflict accuracy, expanded pair/card counts and category confusion separately. Zero model-written Ukrainian, resolvable locators and source-removal recomputation remain required.

These are recommendations, not accepted thresholds or an operator seal. The operator must ratify the exact per-category applicability and thresholds with authenticated authority/signature at freeze. Gate 2's count-based structural test and the statistical field-quality tests below have different estimands. **All gates must pass**; neither replaces, pools into, nor takes precedence over the other. In particular, the 88-case challenge test cannot prove a 1% population error bound, and ≤2 wrong splits cannot override zero-critical-failure rules elsewhere.

## 0. Reading rule

All G01-G35 tables, AC-01 through AC-05, every threshold, per-cell, per-sign and per-endpoint minimum, the critical override and Gate 2's operator-signed sealed manifest with operator-set thresholds at freeze are retained. Seventeen tables retain the candidate text; eighteen carry the agreed amendments. Where a retained table's wording conflicts with §1-§8 or an amended table, the amended text controls. Numbers marked "planning" are planning constraints, not authority to evaluate. P1-P9 (§8) have conditional designated design agreement only. Independent precommitted held-out execution remains pending; nothing here authorizes allocation, selection, labelling, building or release. No build, gold or certification starts before the #10512 complete current frozen source receipt.

## 1. Conditional input gates

Every gate needs a typed PASS receipt. I1-I5 precede partition allocation; I6-I10 precede any selection. A failure blocks the dependent operation; this contract waives none.

| ID | Input | PASS condition | Owner and resolving event |
| --- | --- | --- | --- |
| I1 | Source-complete inventory and closure graph | #10512 complete-data receipt and #9401 frozen source matrix; closure graph of related source records, aliases, lexeme families and derivations frozen with digest; every source unit has one disposition | Source-inventory lead; #10512/#9401 |
| I2 | Release ledger R and member disposition δ (§2) | Every candidate member/obligation, including withheld and absent-output obligations and every container instance, has one primary δ class, owning cells and release disposition by exact row of the §2.2 member table or a §2.3 rule; δ applied to every path instance of the actual export, including every nested `value` path, yields zero U-class members and zero exported X-class members; E equals the ledger's exported set | Driver with source lead; designated review of the ledger digest |
| I3 | Registered cell inventory | Planning domains (the six, plus any designated-added domain) and children c=(f,s,r) defined only from source/frame-visible variables; field-domain table of §2 applied; C counted; full-frame counts \|F_c\|, \|F_f\| and \|G_cal\| recorded | Driver; designated review of every child and any added domain |
| I4 | Reserved closures R_res | Steward freezes R_res = R_struct ∪ R_exp before allocation: closures of the 220 fresh structural cases, and closures of exposed development witnesses (old 220, mechanics150 units, publicly named examples) | Independent gold steward; #10514 |
| I5 | Allocation | Steward draws private v_g ~ iid U(0,1) on the statistical universe U*; preregistered shares ρ from frame counts only; realized pool sizes and post-development remainder sizes N°(F) (§3.7) recorded | Steward; one draw, no redraw without designated review |
| I6 | Applicability A(g,c,e) (§6) | Frozen from I1-I3 and the frozen evaluated artifact's structure, with inputs, rules and digest, before selection | Steward/statistician per evaluated artifact |
| I7 | Supply | Every required frame in its sub-partition holds at least its required n; every promised endpoint frame is nonempty or has a designated-reviewed STRUCTURALLY_EMPTY receipt; screening caps hold | Source lead and statistician |
| I8 | Test family and inference binding | m_rel, m_cal, n_rel and c recomputed by §7 from I3/I7; thresholds unchanged; every claim bound to its §3.7 target, law, N and inclusion probability; recomputation receipt reviewed | Statistician; designated review before selection |
| I9 | Labour and capacity (§4) | H⁺ computed from the 99th-percentile task count of the actual design and measured timing upper limits is at most the secured, named, staffed hours | Annotation lead; staffing receipt |
| I10 | Authority and custody | Named appointments (G06); designated agreement on P1-P9; Gate 2 operator-signed sealed manifest with operator-set thresholds at authenticated freeze; #10514 seal and isolation receipts; receipt that a qualified outside-family evaluator froze fresh private challenges before seeing the agreed artifact | Driver, operator, steward, evaluator |

## 2. N1: total member disposition δ

### 2.1 Members and classes

A member is any JSON path instance in an exported record (card, sense, link, assertion, tombstone, field resolution, projection row), including the record root, every object, array and map container, every array item, every leaf, and every nested node inside a free-form `value`; and every path instance, container or leaf, of every release-level file (README/YAML card, Croissant/RAI, build/source/licence manifests, changelog, release mapping, receipts). δ gives each member exactly one primary class:

| Class | Meaning | Coverage obligation |
| --- | --- | --- |
| D | Field value claim | Value, citation, abstention and accounting endpoints of the owning cell; identity endpoint of every cell of that subject |
| I | Identity, attachment, state or lineage | Identity endpoint in every cell where the subject has obligations; accounting endpoint for successors and redirects |
| P | Provenance or source binding | Citation/source-binding and accounting endpoints of the owning cell |
| A | Disposition, review, status, suppression, emitted state, applied overlay | Accounting/eligibility endpoint of the owning cell |
| R | Deterministic member: a scalar computed from other members and pinned rules, or a structural container whose presence, JSON type, key set or element multiset, cardinality and order are fixed by the I2 ledger, J and pinned rules | Exhaustive recomputation census (P9): every exported R member recomputed; any mismatch is an accounting failure of every owning cell and a G26/G28 failure; never sampled |
| V | Release, build, version and metadata envelope | Non-statistical gates G28, G29, G30, G32, G33 |
| X | Explicitly deferred field or item | Must be absent from E; ledger keeps the obligation as withheld:deferred:<reference>; any exported X member is an N1 FAIL |
| U | Unmatched path, key, field name, link type, overlay kind or derivative | INCOMPLETE; blocks export and selection until a designated-reviewed δ extension with its cell and budget |

Field-domain table, covering all 24 schema field names exactly once:

| Field name | Scope | Owning planning domain and child rule | Basis |
| --- | --- | --- | --- |
| `spelling` | card | MORPH (morphology/identity) | Q:62; W:40 |
| `pos` | card | MORPH | Q:62,123 |
| `grammatical_label` | card | MORPH | Q:62,123 |
| `gender` | card | MORPH | Q:62,123 |
| `aspect` | card | MORPH | Q:62,123 |
| `paradigm` | card | MORPH | W:40; D:44 |
| `spelling_variants` | card | MORPH | W:40 variant lists |
| `frequency` | card | MORPH child, its admitted corpus-frequency source (P5) | Q:123,164; lexeme-level scalar whose main risk is attachment |
| `heritage_status` | card | MORPH child, its admitted heritage-attesting source (P5); no modern stress or meaning truth borrowed | Q:123,168 |
| `transliteration` | card | MORPH child, derived-rule source (P5); value expectation is the pinned rule applied to the source-backed spelling | Q:89,123 |
| `stress` | card | STRESS | W:41; D:45 |
| `mwe_form` | card | MWE | Q:102; W:44 |
| `mwe_frame` | card | MWE | Q:102; W:44 |
| `english_gloss` | card | X, deferred | D:52; W:47 |
| `cefr` | card | X, deferred | D:52; W:47 |
| `definition_uk` | sense | MEANING; on MWE-card senses MWE is the owning cell and the MEANING mapping is explicit dual attachment, never a second pooled trial | W:42; D:46; Q:103 |
| `sense_label` | sense | MEANING | Q:97; D:46 labels bound to sense |
| `register` | sense | MEANING | Q:97,183 |
| `synonyms` | sense | SYNANT | W:43; D:47 |
| `antonyms` | sense | SYNANT | W:43; D:47 |
| `russification_exposed` | sense | CONTRAST (opt-in C7) | W:45; D:49 |
| `gloss_en` | sense | X, deferred by equivalence with `english_gloss` (P7) | Q:187; D:52 |
| `examples` | sense | X, deferred | D:52; W:47 |
| `collocations` | sense | X, deferred | D:52; W:47 |

A P5 child exists only if the I2 ledger exports at least one member of that field; a field without an admitted source is held under G07's ordinary source-admission disposition, which is not a scope exclusion. The six planning domains are unchanged; no field is absorbed into an existing child to keep a six-cell budget.

### 2.2 Literal member table

Classification is by exact match of a path instance's pattern against one row of this table. `<F>` stands for a field-name key (card enum under `fields`, sense enum under `senses[].fields`), `<slot>` for a `propositions` key, `<name>` for a `build.inputs.*` key, `[]` for any array item, and `$` for the record root. No row covers another row by prefix: an ancestor is never classified by its descendants' rows, and a descendant is never classified by its ancestor's row. The only exceptions are the §2.3 rules, each of which names the node it starts from and includes that node. The table has one row for every one of the 236 path patterns that J defines at the pinned version, containers and leaves alike; development check T2 recomputes that set from J and requires equality. Kind records whether the schema node can hold children; every container instance also falls under the §2.4 structural census, whatever its primary class. The Change column compares each row with the class that v1's prefix rule gave the same pattern.

| # | Path pattern | Kind | Class | Owning cell | Note | Change from v1 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `$` | container | R | every cell of the card | Card record container: presence of the card in the ledger, JSON type, required key set | v2: was U in v1 |
| 2 | `assertions` | container | R | every cell of the card | Container: element multiset equals the ledger's exported assertions and tombstones for the card, its senses and its links | v2: was U in v1 |
| 3 | `assertions[]` | container | R | `assertion.field`; deferred field gives X, unresolvable field gives U (§2.3) | Item container: one ledger assertion or tombstone | v2: was U in v1 |
| 4 | `assertions[].assertion_id` | leaf | R | `assertion.field`; on a tombstone, the field of the ledger member it tombstones; unresolvable gives U | | as v1 |
| 5 | `assertions[].extraction_confidence` | leaf | P | `assertion.field` | | as v1 |
| 6 | `assertions[].extraction_version` | leaf | P | `assertion.field` | | as v1 |
| 7 | `assertions[].field` | leaf | D | `assertion.field` | | as v1 |
| 8 | `assertions[].independence_group` | leaf | R | `assertion.field` | | as v1 |
| 9 | `assertions[].licence_ref` | container | P | `assertion.field` | | as v1 |
| 10 | `assertions[].licence_ref.appears_in` | container | P | `assertion.field` | | as v1 |
| 11 | `assertions[].licence_ref.appears_in[]` | leaf | P | `assertion.field` | | as v1 |
| 12 | `assertions[].licence_ref.register_source_id` | leaf | P | `assertion.field` | | as v1 |
| 13 | `assertions[].licence_ref.register_version` | leaf | P | `assertion.field` | | as v1 |
| 14 | `assertions[].locator` | leaf | P | `assertion.field` | | as v1 |
| 15 | `assertions[].mapping` | container | I | `assertion.field` | | as v1 |
| 16 | `assertions[].mapping.ambiguous` | leaf | I | `assertion.field` | | as v1 |
| 17 | `assertions[].mapping.basis` | leaf | I | `assertion.field` | | as v1 |
| 18 | `assertions[].mapping.confidence` | leaf | I | `assertion.field` | | as v1 |
| 19 | `assertions[].mapping.note` | leaf | A | `assertion.field` | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 20 | `assertions[].producer` | container | P | `assertion.field` | | as v1 |
| 21 | `assertions[].producer.derived_id` | leaf | P | `assertion.field` | | as v1 |
| 22 | `assertions[].producer.kind` | leaf | P | `assertion.field` | | as v1 |
| 23 | `assertions[].producer.name` | leaf | P | `assertion.field` | | as v1 |
| 24 | `assertions[].producer.produced_at` | leaf | P | `assertion.field` | | as v1 |
| 25 | `assertions[].producer.version` | leaf | P | `assertion.field` | | as v1 |
| 26 | `assertions[].review` | container | A | `assertion.field` | | as v1 |
| 27 | `assertions[].review.approved_for` | container | A | `assertion.field` | | as v1 |
| 28 | `assertions[].review.approved_for[]` | leaf | A | `assertion.field` | | as v1 |
| 29 | `assertions[].review.date` | leaf | A | `assertion.field` | | as v1 |
| 30 | `assertions[].review.lane` | leaf | A | `assertion.field` | | as v1 |
| 31 | `assertions[].review.record` | leaf | A | `assertion.field` | | as v1 |
| 32 | `assertions[].review.status` | leaf | A | `assertion.field` | | as v1 |
| 33 | `assertions[].snapshot_id` | leaf | P | `assertion.field` | | as v1 |
| 34 | `assertions[].source_id` | leaf | P | `assertion.field` | | as v1 |
| 35 | `assertions[].source_record_id` | leaf | P | `assertion.field` | | as v1 |
| 36 | `assertions[].source_record_key` | leaf | P | `assertion.field` | | as v1 |
| 37 | `assertions[].status` | leaf | A | `assertion.field` | | as v1 |
| 38 | `assertions[].subject` | container | D | `assertion.field` | | as v1 |
| 39 | `assertions[].subject.id` | leaf | D | `assertion.field` | | as v1 |
| 40 | `assertions[].subject.kind` | leaf | D | `assertion.field` | | as v1 |
| 41 | `assertions[].suppression_ref` | leaf | A | `assertion.field` | | as v1 |
| 42 | `assertions[].tier` | leaf | R | `assertion.field` | | as v1 |
| 43 | `assertions[].value` | free-form | D | `assertion.field` | | as v1 |
| 44 | `assertions[].value/**` | free-form descendant | D | `assertion.field` | every nested node of free-form `value`, container or leaf; I2 inventories the actual nested paths | as v1 |
| 45 | `assertions[].value_norm` | leaf | D | `assertion.field` | | as v1 |
| 46 | `build` | container | V | release | | as v1 |
| 47 | `build.build_id` | leaf | V | release | | as v1 |
| 48 | `build.card_version` | leaf | R | release | | as v1 |
| 49 | `build.inputs` | container | V | release | | as v1 |
| 50 | `build.inputs.I` | container | V | release | | as v1 |
| 51 | `build.inputs.I.<name>` | container | V | release | | as v1 |
| 52 | `build.inputs.I.<name>.content_sha256` | leaf | V | release | | as v1 |
| 53 | `build.inputs.I.<name>.note` | leaf | A | release | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 text (v1 row `build.inputs` made each input note A; prefix resolution alone gave V) |
| 54 | `build.inputs.I.<name>.ref` | leaf | V | release | | as v1 |
| 55 | `build.inputs.I.<name>.version` | leaf | V | release | | as v1 |
| 56 | `build.inputs.O` | container | V | release | | as v1 |
| 57 | `build.inputs.O.<name>` | container | V | release | | as v1 |
| 58 | `build.inputs.O.<name>.content_sha256` | leaf | V | release | | as v1 |
| 59 | `build.inputs.O.<name>.note` | leaf | A | release | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 text (v1 row `build.inputs` made each input note A; prefix resolution alone gave V) |
| 60 | `build.inputs.O.<name>.ref` | leaf | V | release | | as v1 |
| 61 | `build.inputs.O.<name>.version` | leaf | V | release | | as v1 |
| 62 | `build.inputs.R` | container | V | release | | as v1 |
| 63 | `build.inputs.R.<name>` | container | V | release | | as v1 |
| 64 | `build.inputs.R.<name>.content_sha256` | leaf | V | release | | as v1 |
| 65 | `build.inputs.R.<name>.note` | leaf | A | release | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 text (v1 row `build.inputs` made each input note A; prefix resolution alone gave V) |
| 66 | `build.inputs.R.<name>.ref` | leaf | V | release | | as v1 |
| 67 | `build.inputs.R.<name>.version` | leaf | V | release | | as v1 |
| 68 | `build.inputs.S` | container | V | release | | as v1 |
| 69 | `build.inputs.S.<name>` | container | V | release | | as v1 |
| 70 | `build.inputs.S.<name>.content_sha256` | leaf | V | release | | as v1 |
| 71 | `build.inputs.S.<name>.note` | leaf | A | release | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 text (v1 row `build.inputs` made each input note A; prefix resolution alone gave V) |
| 72 | `build.inputs.S.<name>.ref` | leaf | V | release | | as v1 |
| 73 | `build.inputs.S.<name>.version` | leaf | V | release | | as v1 |
| 74 | `build.inputs.V` | container | V | release | | as v1 |
| 75 | `build.inputs.V.<name>` | container | V | release | | as v1 |
| 76 | `build.inputs.V.<name>.content_sha256` | leaf | V | release | | as v1 |
| 77 | `build.inputs.V.<name>.note` | leaf | A | release | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 text (v1 row `build.inputs` made each input note A; prefix resolution alone gave V) |
| 78 | `build.inputs.V.<name>.ref` | leaf | V | release | | as v1 |
| 79 | `build.inputs.V.<name>.version` | leaf | V | release | | as v1 |
| 80 | `build.rules_version` | leaf | V | release | | as v1 |
| 81 | `card_id` | leaf | I | every cell where the card has obligations | | as v1 |
| 82 | `card_kind` | leaf | I | every cell of the card | | as v1 |
| 83 | `fields` | container | R | every cell of the card | Map container: key set equals the ledger's exported card fields; deferred keys absent | v2: was U in v1 |
| 84 | `fields.<F>` | container | R | <F> (card field) | deferred <F> subtree is X (§2.3 rule X1) | as v1 |
| 85 | `fields.<F>.comparison` | leaf | R | <F> (card field) | | as v1 |
| 86 | `fields.<F>.independence_groups_agreeing` | leaf | R | <F> (card field) | | as v1 |
| 87 | `fields.<F>.independence_groups_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 88 | `fields.<F>.level_policy` | leaf | A | <F> (card field) | J describes it for `english_gloss` only; inside a deferred subtree X1 makes it X, elsewhere it is A as in v1 | as v1 |
| 89 | `fields.<F>.mapping_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 90 | `fields.<F>.non_voting` | container | R | <F> (card field) | | as v1 |
| 91 | `fields.<F>.non_voting[]` | container | R | <F> (card field) | | as v1 |
| 92 | `fields.<F>.non_voting[].assertion_id` | leaf | R | <F> (card field) | | as v1 |
| 93 | `fields.<F>.non_voting[].reason` | leaf | R | <F> (card field) | | as v1 |
| 94 | `fields.<F>.proposition` | leaf | R | <F> (card field) | | as v1 |
| 95 | `fields.<F>.propositions` | container | R | <F> (card field) | | as v1 |
| 96 | `fields.<F>.propositions.<slot>` | container | R | <F> (card field) | | as v1 |
| 97 | `fields.<F>.propositions.<slot>.independence_groups_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 98 | `fields.<F>.propositions.<slot>.mapping_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 99 | `fields.<F>.propositions.<slot>.resolution_ref` | leaf | R | <F> (card field) | | as v1 |
| 100 | `fields.<F>.propositions.<slot>.selected` | string, array or null | D | <F> (card field) | | as v1 |
| 101 | `fields.<F>.propositions.<slot>.selected[]` | leaf | D | <F> (card field) | | as v1 |
| 102 | `fields.<F>.propositions.<slot>.state` | leaf | R | <F> (card field) | | as v1 |
| 103 | `fields.<F>.resolution_ref` | leaf | R | <F> (card field) | | as v1 |
| 104 | `fields.<F>.selected` | string, array or null | D | <F> (card field) | | as v1 |
| 105 | `fields.<F>.selected[]` | leaf | D | <F> (card field) | | as v1 |
| 106 | `fields.<F>.state` | leaf | R | <F> (card field) | the emitted state is also an accounting obligation of <F> | as v1 |
| 107 | `fields.<F>.values` | container | R | <F> (card field) | | as v1 |
| 108 | `fields.<F>.values[]` | container | R | <F> (card field) | | as v1 |
| 109 | `fields.<F>.values[].assertion_ids` | container | R | <F> (card field) | | as v1 |
| 110 | `fields.<F>.values[].assertion_ids[]` | leaf | R | <F> (card field) | | as v1 |
| 111 | `fields.<F>.values[].declared_by` | leaf | R | <F> (card field) | | as v1 |
| 112 | `fields.<F>.values[].declared_set` | leaf | R | <F> (card field) | | as v1 |
| 113 | `fields.<F>.values[].independence_groups` | container | R | <F> (card field) | | as v1 |
| 114 | `fields.<F>.values[].independence_groups[]` | leaf | R | <F> (card field) | | as v1 |
| 115 | `fields.<F>.values[].independence_groups_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 116 | `fields.<F>.values[].mapping_evidenced` | leaf | R | <F> (card field) | | as v1 |
| 117 | `fields.<F>.values[].value_norm` | leaf | D | <F> (card field) | | as v1 |
| 118 | `identity` | container | I | every cell of the card | | as v1 |
| 119 | `identity.confidence` | leaf | I | every cell of the card | | as v1 |
| 120 | `identity.decided_at` | leaf | I | every cell of the card | | as v1 |
| 121 | `identity.decided_by` | leaf | I | every cell of the card | | as v1 |
| 122 | `identity.method` | leaf | I | every cell of the card | | as v1 |
| 123 | `identity.notes` | container | A | every cell of the card | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 124 | `identity.notes[]` | leaf | A | every cell of the card | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 125 | `identity.source_keys` | container | I | every cell of the card | | as v1 |
| 126 | `identity.source_keys[]` | container | I | every cell of the card | | as v1 |
| 127 | `identity.source_keys[].key` | leaf | I | every cell of the card | | as v1 |
| 128 | `identity.source_keys[].match_note` | leaf | A | every cell of the card | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 129 | `identity.source_keys[].snapshot_id` | leaf | I | every cell of the card | | as v1 |
| 130 | `identity.source_keys[].source_id` | leaf | I | every cell of the card | | as v1 |
| 131 | `key_at_creation` | container | I | every cell of the card | | as v1 |
| 132 | `key_at_creation.mwe_key` | leaf | I | every cell of the card | | as v1 |
| 133 | `key_at_creation.paradigm_key` | leaf | I | every cell of the card | | as v1 |
| 134 | `key_at_creation.pos` | leaf | I | every cell of the card | | as v1 |
| 135 | `key_at_creation.source_keys` | container | I | every cell of the card | | as v1 |
| 136 | `key_at_creation.source_keys[]` | container | I | every cell of the card | | as v1 |
| 137 | `key_at_creation.source_keys[].key` | leaf | I | every cell of the card | | as v1 |
| 138 | `key_at_creation.source_keys[].match_note` | leaf | A | every cell of the card | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 139 | `key_at_creation.source_keys[].snapshot_id` | leaf | I | every cell of the card | | as v1 |
| 140 | `key_at_creation.source_keys[].source_id` | leaf | I | every cell of the card | | as v1 |
| 141 | `key_at_creation.spelling` | leaf | I | every cell of the card | | as v1 |
| 142 | `key_at_creation.stress_patterns` | container | I | every cell of the card | | as v1 |
| 143 | `key_at_creation.stress_patterns[]` | leaf | I | every cell of the card | | as v1 |
| 144 | `links` | container | R | every cell of the card | Container: element multiset equals the ledger's exported links of the card | v2: was U in v1 |
| 145 | `links[]` | container | I | by type: `aspect_pair` and `homograph_of` MORPH; `stress_variant_of` STRESS; `synonym` and `antonym` SYNANT; `component_of` MWE; `russification_contrast` CONTRAST; `see_also` has no registered source role, so U | `see_also` subtree is U (§2.3 rule U1) | as v1 |
| 146 | `links[].assertion_ids` | container | I | the link's cell | | as v1 |
| 147 | `links[].assertion_ids[]` | leaf | I | the link's cell | | as v1 |
| 148 | `links[].basis` | leaf | I | the link's cell | | as v1 |
| 149 | `links[].derived_by` | leaf | R | the link's cell | | as v1 |
| 150 | `links[].endpoints` | container | I | the link's cell | | as v1 |
| 151 | `links[].endpoints[]` | container | I | the link's cell | | as v1 |
| 152 | `links[].endpoints[].id` | leaf | I | the link's cell | | as v1 |
| 153 | `links[].endpoints[].role` | leaf | I | the link's cell | | as v1 |
| 154 | `links[].endpoints[].sense_id` | leaf | I | the link's cell | | as v1 |
| 155 | `links[].link_id` | leaf | R | the link's cell | | as v1 |
| 156 | `links[].note` | leaf | A | the link's cell | a note stating a Ukrainian form or value is reclassified D and is U until mapped | as v1 |
| 157 | `links[].state` | leaf | I | the link's cell | | as v1 |
| 158 | `links[].type` | leaf | I | the link's cell | | as v1 |
| 159 | `merged_into` | leaf (id or null) | I | every cell of the card | | as v1 |
| 160 | `overlay_applied` | container | R | every cell of the card | Container: element multiset equals the ledger's applied overlays | v2: was U in v1 |
| 161 | `overlay_applied[]` | container | I | by kind: `merge`, `split`, `identity`, `sense_map`, `link` in the touched cell; `resolve`, `variant`, `suppress` in the touched cell; `level_override` X | class by `kind` value (§2.3 rule X3) | as v1 |
| 162 | `overlay_applied[].author` | leaf | I | the overlay item's cell | | as v1 |
| 163 | `overlay_applied[].date` | leaf | I | the overlay item's cell | | as v1 |
| 164 | `overlay_applied[].evidence` | leaf | I | the overlay item's cell | | as v1 |
| 165 | `overlay_applied[].kind` | leaf | I | the overlay item's cell | | as v1 |
| 166 | `overlay_applied[].lane` | leaf | I | the overlay item's cell | | as v1 |
| 167 | `overlay_applied[].overlay_id` | leaf | I | the overlay item's cell | | as v1 |
| 168 | `quality` | container | R | every cell of the card | Container: required key set per J | v2: was U in v1 |
| 169 | `quality.extraction_confidence_min` | leaf | R | every cell of the card | | as v1 |
| 170 | `quality.identity_confidence` | leaf | I | every cell of the card | | as v1 |
| 171 | `quality.linguistic_review` | container | A | every cell of the card | | as v1 |
| 172 | `quality.linguistic_review.approved_for` | container | A | every cell of the card | | as v1 |
| 173 | `quality.linguistic_review.approved_for[]` | leaf | A | every cell of the card | | as v1 |
| 174 | `quality.linguistic_review.date` | leaf | A | every cell of the card | | as v1 |
| 175 | `quality.linguistic_review.lane` | leaf | A | every cell of the card | | as v1 |
| 176 | `quality.linguistic_review.record` | leaf | A | every cell of the card | | as v1 |
| 177 | `quality.linguistic_review.status` | leaf | A | every cell of the card | | as v1 |
| 178 | `quality.practice_eligibility` | container | R | every cell of the card | Required by J; while D:52 defers practice eligibility the ledger value is the empty array; any item is X | v2: was X in v1 |
| 179 | `quality.practice_eligibility[]` | container | X | every cell of the card | deferred, D:52 | as v1 |
| 180 | `quality.practice_eligibility[].eligible` | leaf | X | every cell of the card | deferred, D:52 | as v1 |
| 181 | `quality.practice_eligibility[].mode` | leaf | X | every cell of the card | deferred, D:52 | as v1 |
| 182 | `quality.practice_eligibility[].reasons` | container | X | every cell of the card | deferred, D:52 | as v1 |
| 183 | `quality.practice_eligibility[].reasons[]` | leaf | X | every cell of the card | deferred, D:52 | as v1 |
| 184 | `quality.practice_eligibility[].rules_version` | leaf | X | every cell of the card | deferred, D:52 | as v1 |
| 185 | `quality.practice_eligibility[].sense_id` | leaf | X | every cell of the card | deferred, D:52 | as v1 |
| 186 | `schema_version` | leaf | V | release | | as v1 |
| 187 | `senses` | container | R | every cell of the card | Container: element multiset equals the ledger's exported senses; order by `order` | v2: was U in v1 |
| 188 | `senses[]` | container | R | every cell where the sense has obligations | Item container: one ledger sense | v2: was U in v1 |
| 189 | `senses[].fields` | container | R | every cell of the sense | Map container: key set equals the ledger's exported sense fields; deferred keys absent | v2: was U in v1 |
| 190 | `senses[].fields.<F>` | container | R | <F> on that sense | deferred <F> subtree is X (§2.3 rule X1) | as v1 |
| 191 | `senses[].fields.<F>.comparison` | leaf | R | <F> on that sense | | as v1 |
| 192 | `senses[].fields.<F>.independence_groups_agreeing` | leaf | R | <F> on that sense | | as v1 |
| 193 | `senses[].fields.<F>.independence_groups_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 194 | `senses[].fields.<F>.level_policy` | leaf | A | <F> on that sense | J describes it for `english_gloss` only; inside a deferred subtree X1 makes it X, elsewhere it is A as in v1 | as v1 |
| 195 | `senses[].fields.<F>.mapping_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 196 | `senses[].fields.<F>.non_voting` | container | R | <F> on that sense | | as v1 |
| 197 | `senses[].fields.<F>.non_voting[]` | container | R | <F> on that sense | | as v1 |
| 198 | `senses[].fields.<F>.non_voting[].assertion_id` | leaf | R | <F> on that sense | | as v1 |
| 199 | `senses[].fields.<F>.non_voting[].reason` | leaf | R | <F> on that sense | | as v1 |
| 200 | `senses[].fields.<F>.proposition` | leaf | R | <F> on that sense | | as v1 |
| 201 | `senses[].fields.<F>.propositions` | container | R | <F> on that sense | | as v1 |
| 202 | `senses[].fields.<F>.propositions.<slot>` | container | R | <F> on that sense | | as v1 |
| 203 | `senses[].fields.<F>.propositions.<slot>.independence_groups_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 204 | `senses[].fields.<F>.propositions.<slot>.mapping_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 205 | `senses[].fields.<F>.propositions.<slot>.resolution_ref` | leaf | R | <F> on that sense | | as v1 |
| 206 | `senses[].fields.<F>.propositions.<slot>.selected` | string, array or null | D | <F> on that sense | | as v1 |
| 207 | `senses[].fields.<F>.propositions.<slot>.selected[]` | leaf | D | <F> on that sense | | as v1 |
| 208 | `senses[].fields.<F>.propositions.<slot>.state` | leaf | R | <F> on that sense | | as v1 |
| 209 | `senses[].fields.<F>.resolution_ref` | leaf | R | <F> on that sense | | as v1 |
| 210 | `senses[].fields.<F>.selected` | string, array or null | D | <F> on that sense | | as v1 |
| 211 | `senses[].fields.<F>.selected[]` | leaf | D | <F> on that sense | | as v1 |
| 212 | `senses[].fields.<F>.state` | leaf | R | <F> on that sense | the emitted state is also an accounting obligation of <F> | as v1 |
| 213 | `senses[].fields.<F>.values` | container | R | <F> on that sense | | as v1 |
| 214 | `senses[].fields.<F>.values[]` | container | R | <F> on that sense | | as v1 |
| 215 | `senses[].fields.<F>.values[].assertion_ids` | container | R | <F> on that sense | | as v1 |
| 216 | `senses[].fields.<F>.values[].assertion_ids[]` | leaf | R | <F> on that sense | | as v1 |
| 217 | `senses[].fields.<F>.values[].declared_by` | leaf | R | <F> on that sense | | as v1 |
| 218 | `senses[].fields.<F>.values[].declared_set` | leaf | R | <F> on that sense | | as v1 |
| 219 | `senses[].fields.<F>.values[].independence_groups` | container | R | <F> on that sense | | as v1 |
| 220 | `senses[].fields.<F>.values[].independence_groups[]` | leaf | R | <F> on that sense | | as v1 |
| 221 | `senses[].fields.<F>.values[].independence_groups_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 222 | `senses[].fields.<F>.values[].mapping_evidenced` | leaf | R | <F> on that sense | | as v1 |
| 223 | `senses[].fields.<F>.values[].value_norm` | leaf | D | <F> on that sense | | as v1 |
| 224 | `senses[].merged_into` | leaf (id or null) | I | every cell of the sense | | as v1 |
| 225 | `senses[].order` | leaf | I | every cell of the sense | | as v1 |
| 226 | `senses[].seeded_from` | leaf | I | MEANING | | as v1 |
| 227 | `senses[].sense_id` | leaf | I | every cell where the sense has obligations | | as v1 |
| 228 | `senses[].sense_map` | container | I | every cell of the sense | | as v1 |
| 229 | `senses[].sense_map[]` | container | I | every cell of the sense | | as v1 |
| 230 | `senses[].sense_map[].mapped_by` | leaf | I | every cell of the sense | | as v1 |
| 231 | `senses[].sense_map[].source_id` | leaf | I | every cell of the sense | | as v1 |
| 232 | `senses[].sense_map[].source_sense_key` | leaf | I | every cell of the sense | | as v1 |
| 233 | `senses[].state` | leaf | I | every cell of the sense | | as v1 |
| 234 | `split_into` | container (array or null) | I | every cell of the card | | as v1 |
| 235 | `split_into[]` | leaf | I | every cell of the card | | as v1 |
| 236 | `state` | leaf | I | every cell of the card | | as v1 |

Two record families outside J have explicit rows of their own:

| Members | Class | Owning cell and rule |
| --- | --- | --- |
| C2/C3/C4/C7 projection row record and every path instance in it | The row record is R (recomputed from the pinned card version, W3 unit equivalence); every other instance takes the class of the J pattern it is mapped to by the pinned projection mapping registered in I2 | An instance with no registered mapping is U |
| Release-level file and every path instance in it, container or leaf | V | Its named gate in G28-G33; a file absent from the I2 release-file list is U |

### 2.3 Explicit value-dependent rules

Each rule names the node it starts from; it applies to that node and to every §2.2 row whose pattern begins with that node's pattern.

| Rule | Start node | Condition | Class |
| --- | --- | --- | --- |
| X1 | `fields.<F>`; `senses[].fields.<F>` | <F> is `english_gloss` or `cefr` (card), or `gloss_en`, `examples` or `collocations` (sense) | X |
| X2 | `assertions[]` | the item's `field` names an X1 field, or the ledger member a tombstone tombstones belongs to one | X |
| X3 | `overlay_applied[]` | `kind` is `level_override` | X; `kind` `resolve`, `variant` or `suppress` gives A; `merge`, `split`, `identity`, `sense_map` or `link` keep the row class I |
| U1 | `fields.<F>`; `senses[].fields.<F>`; `assertions[]`; `links[]`; `overlay_applied[]` | <F> or `assertion.field` is outside the 24 names, a tombstone's member is unresolvable, the link `type` is `see_also`, or the overlay `kind` is outside J's enum | U |
| U2 | any path instance | no exact §2.2 row and no §2.3 rule applies | U |
| N | rows whose Note cites the note rule | the note states a Ukrainian form or value | D, and U until mapped |

X1 leaves the J-required containers `fields` and `senses[].fields` exported; only the deferred keys are absent. `quality.practice_eligibility` is J-required, so that container is exported as an R member whose ledger value is the empty array while D:52 defers practice eligibility; each of its items is X.

### 2.4 Structural census of containers (P9)

For every exported container instance, the steward recomputes from the I2 ledger, J and pinned ordering rules, never from the exported children: presence (a J-required container must be present; an optional one is present exactly when the ledger exports at least one child of it), JSON type, required key set, the key set (maps) or element multiset (arrays) as the ledger's exported children of that instance, cardinality, and order where a pinned rule defines one (`senses` by `order`; link `endpoints` by role rank then id). Elsewhere comparison is order-insensitive and the order is recorded. Every exported record also validates against pinned J. Any mismatch is an accounting failure of every owning cell of the container and a G26/G28 failure. This census is machine work over every container instance. It does not sample and does not certify the children's semantic truth, which their own rows cover.

### 2.5 Coverage equation

Let G_all be the frozen closure graph, U* = {closures with at least one D/I/P/A obligation} minus R_res, and E the exported members. PASS requires all of: E equals the ledger's exported set; every m in E with class D/I/P/A belongs to a closure in U* ∪ R_res and has nonempty owning cells; every closure in U* has positive pre-allocation probability of selection into a certification or final draw for every endpoint of its owning cells, so no frame member is structurally excluded (after allocation, development-allocated closures are covered as §3.7 and E10 state, not by those draws); every R_res closure is in the P3 census; every R member, including every container instance, is in the P9 recomputation; every V member is covered by its named gate; X ∩ E = ∅ and U ∩ E = ∅. Pooled endpoint frames are G_e = {g ∈ U* : A(g,c,e) ≠ ∅ for some c}. Critical observations anywhere keep G24's absolute override.

## 3. Sampling design

3.1 Universe and strata. U* is defined in §2.5. R_res closures are never in a sampling frame; they are covered by the P3 census and enter the whole-release estimate E10 as its exact census stratum. The development sub-partitions are TRAIN_f, PANEL_f, ENRICH_f, CALU and DEV_f for every f. For a frame F, its post-development remainder F° is F minus the closures whose v_g falls in a development interval; N°(F) is its size and F^dev the rest. No claim targets a realized slice F ∩ P.

3.2 Membership-independent allocation (P6). Preregistered disjoint intervals of [0,1) on the private v_g define sub-partitions TRAIN_f, PANEL_f, ENRICH_f, CALU, DEV_f, CERT, FINAL_f, FINALU and the release-only remainder REL, for every planning domain f. Shares ρ use frame counts only; no membership pattern, human label, workflow output or correctness enters. For every frame F and sub-partition P, membership of F's closures in P is iid Bernoulli(ρ_P), and given \|F ∩ P\| the slice is a uniform subset of F. Closure-disjointness of every partition and sub-partition holds by construction. Shares must leave a binomial shortfall probability below 1e-6 for every required pool; this is a feasibility requirement, not a conditioning device. A realized shortfall stops the affected claim without redraw (§3.8).

3.3 Coordinated simple random sampling. The steward draws a second private ordering u_g ~ iid U(0,1). For frame F in sub-partition P and size n, S(F,P,n) is the n members of F ∩ P with the smallest u_g. This is permanent-random-number selection; the INSEE coordination note (Gros and Merly-Alpa, section I.B) describes smallest-number selection within a stratum, and Ohlsson 1995 is cited for lineage only, not read. Given F ∩ P, it is an SRS without replacement of F ∩ P. Which population it is an exact SRS of, once the allocation stage is integrated, is stated per claim in §3.7. Frames in one sub-partition are positively coordinated, so one closure and its labels can serve several tests; each test keeps its own marginal law. Selection never excludes closures because another frame selected them.

3.4 Observation scope. DOMAIN labels every applicable obligation of a selected closure in the children of the frame's planning domain f. FULL labels every applicable obligation in every registered cell. PANEL_f, ENRICH_f and FINAL_f are DOMAIN; DEV_f, CALU, CERT and FINALU are FULL. An observed critical event anywhere applies G24.

3.5 Frames and sizes.

| Sub-partition | Frames and draw | Observation | Unique floor |
| --- | --- | --- | --- |
| TRAIN_f | S(F_f, TRAIN_f, 10); disclosed | DOMAIN | 10 per f, 60 total |
| PANEL_f | For each child c of f: S(F_c, PANEL_f, 100) | DOMAIN | ≥100 per f, ≥600 total |
| ENRICH_f | Screen per child: S(F_c, ENRICH_f, k_c), with frame-only water-filling k_c so the distinct screened closures of f number at most 10,000; sign draws: the first 500 c-negatives and first 500 c-positives in u-order among the screened | DOMAIN | ≥1,000 per f (signs of one child are disjoint), ≥6,000 total |
| CALU (P1) | Screen S(G_cal, CALU, S_U) with fixed S_U ≤ 10,000; union sign; first 500 union-negatives and first 500 union-positives in u-order | FULL | ≥1,000 |
| DEV_f | S(F_f, DEV_f, 50) | FULL | 50 per f, 300 total |
| CERT | For each pooled endpoint e: S(G_e, CERT, n_rel) | FULL | ≥n_rel ≥ 2,000 |
| FINAL_f | For each child c of f and endpoint e: S(F_{c,e}, FINAL_f, n_rel) | DOMAIN | ≥n_rel per f, ≥12,000 total |
| FINALU (P2) | For each pooled endpoint e: S(G_e, FINALU, 2,000) | FULL | ≥2,000 |
| R_res (P3) | Census of every closure | FULL | all |

Two-phase sign draws. Within a child, the selected 500 c-negatives are the 500 c-negatives of the screen with the smallest u. Given the screen, the u-order among its members is a uniform permutation independent of which members are c-negative, so the draw is a uniform 500-subset of the screen's c-negatives once their count M_{c,-} is at least 500. The same argument applies to positives and to CALU. The full-frame law is in §3.7.

3.6 Unique floors. Partitions are disjoint, so floors add: training 60; calibration 6,600 (panel 600 + enrichment 6,000); development pilot 300; certification 2,000; final 12,000. This totals 20,960 distinct closures plus 220 structural pre-expansion cases, which is the exact decomposition of W:189's 21,180. P1 and P2 add at least 3,000 distinct closures (23,960 plus 220 cases). A designated-added planning domain adds 10, 100, 1,000, 50 and 2,000 at the initial per-domain figures, and needs its own screening cap.

3.7 Inference binding (F1). Every confidence or risk statement names one target population, one sampling law, the conditioning it uses, the inclusion probability and the N used in exact finite inversion. Two laws are used.

Law M: full frame, marginal over allocation and ordering. Precondition M: the scored outcome of every closure in the target (human source truth, the frozen assembler output and the evaluated workflow version's decisions) is fixed before any information derived from v or u (membership, labels or results of any draw) reaches anyone able to change it. Because v and u are iid and independent of those outcomes, given \|F ∩ P\| = m ≥ n the slice F ∩ P is a uniform m-subset of F and S(F,P,n) a uniform n-subset of it. So S is a uniform n-subset of F, and every g in F has inclusion probability n/\|F\|, whatever m is. For a two-phase sign draw, the screen is a uniform k_c-subset of F_c; given its c-negative count M_{c,-} ≥ 500, those c-negatives are a uniform subset of the full-frame c-negative subpopulation F_c^-, so the draw is a uniform 500-subset of F_c^- with inclusion probability 500/\|F_c^-\|.

Law C: post-development remainder, conditional on σ_D. σ_D is the development information: which closures have v_g in a development interval, their u_g, and every label, output, ranking, tuning and repair derived from them. Precondition C: the evaluated artifact is a function of σ_D, the sources and pre-allocation inputs only, because no information from closures in CERT, FINAL_f, FINALU or REL reaches anyone able to change the artifact before its freeze (W:139, W:213, G20). Given σ_D, the v_g of remainder closures are iid uniform on the union of the non-development intervals, and their u_g are iid uniform and independent of σ_D. Hence for P in {CERT, FINAL_f, FINALU} and \|F ∩ P\| = m ≥ n, S(F,P,n) is a uniform n-subset of F°, with inclusion probability n/N°(F). Law M does not hold for these draws: the evaluated artifact depends on σ_D through workflow selection and tuning on calibration (W:213) and through pilot repairs, so a development closure's outcome can differ systematically from a remainder closure's.

| Claim | Target population | Law | N for exact finite inversion | Inclusion probability |
| --- | --- | --- | --- | --- |
| E1, E2 | c-sign closures of the full frame, F_c^s | M, two-phase | \|F_c^s\| is unknown before screening. The exact Clopper-Pearson upper bound is used; development check T9 shows it is never below the exact hypergeometric upper bound at any admissible N on the planning grid; the statistician re-verifies at the realized design (W:179) | 500/\|F_c^s\| |
| E3 | F_c | M | \|F_c\| | 100/\|F_c\| |
| E4, E5 | Union-sign closures of G_cal, G_cal^s | M, two-phase | As E1 | 500/\|G_cal^s\| |
| E6 | G_cal | M | \|G_cal\| | S_U/\|G_cal\| |
| E7 | Pair universe of all (g,c) with g in F_c | Derived from E1-E3 | a_c = \|F_c\| / Σ_c \|F_c\| | Not a draw |
| E8 | G_e° | C | N°(G_e) | n_rel/N°(G_e) |
| E9 | F_{c,e}° | C | N°(F_{c,e}) | n_rel/N°(F_{c,e}) |
| E10 | Whole release Ω_e (§5) | C for G_e°; census for R_res; §5 rule for G_e^dev | N°(G_e) in the sampled stratum | 2,000/N°(G_e) in the sampled stratum; 1 in the census stratum |
| E11 | R_res | Census | Not sampled | 1 |
| E12 | F_c (descriptive) | M, two-phase | \|F_c\| | (k_c/\|F_c\|)(500/M_{c,s}) |

Consequences. (a) The realized slice size \|F ∩ P\| enters only supply checks. Inverting with it for any target above is prohibited; Sol's counterexample gives coverage 0.7833 instead of 0.99 (development check T7). (b) A workflow version changed after information from its own evaluation draw was revealed fails precondition M on that draw. Its counts are reported as a disclosed repeated attempt (S:62, G20), carry no design-based bound and cannot be ratified by G25 for that draw, because W:162 requires valid marginal sampling assumptions and W:179 verifies them. No redraw rule is adopted. (c) Using the full-frame N, or law M, for E8-E10 is prohibited; development check T8 shows the coverage loss when the artifact is tuned on development closures. (d) The G22 and G23 lot is G_e° and F_{c,e}°. This is W:179's "remaining pool after all earlier allocations", where the earlier allocations are the development ones. CERT-slice closures stay in the final lot population because precondition C keeps them from influencing the artifact. Development-allocated closures of a cell are exported with ordinary dispositions (S:74). Their final-artifact quality is reported in E10's development stratum and never claimed under a G22 or G23 bound.

3.8 Supply conditioning. Every claim is made jointly with its own proceed event. A shortage at any I7 check gives INCOMPLETE and no claim for the affected claim, never PASS and never a redraw (G35). For each test i, PASS_i requires its own supply event, and given its own size statistics (and σ_D under law C) its sample has the §3.7 law. So P(PASS_i and θ_i above its bar) ≤ a_i whatever the other supply events are, and the familywise probability of any false PASS is at most .05 by Bonferroni. No coverage or error statement is made conditional on realized supply. Conditioning on another overlapping frame's supply can raise a test's error rate (development check T10 shows 0.107 at nominal 0.05) while the joint probability stays below a_i. For information only, the statistician reports the probability of all size supplies, computed from frame counts and shares.

3.9 Transport. Calibration claims reach the full frame F_c or G_cal through law M only. Release-artifact claims reach the whole release only through E10's explicit strata. No statement in this contract assumes that development closures share the remainder's error rate (W:203: an unsupported transport assumption blocks the claim).

## 4. A1: units and labour

For partition p: U_p is the number of distinct selected closures; A_p the sum over frames of selected closures (appearances, reported by frame type); U_p^scr the distinct screened closures; K = 220 structural pre-expansion cases and K^exp their expanded closures, cards and pairs. A decision unit is a closure × applicable field decision (W:185), with identity, variant and conflict decisions typed separately. Let D(g, scope) be the decision units of g within the union of the observation scopes of every frame that selected or screened g in p. Then T_p = Σ over selected and screened g of \|D(g, scope)\|. A label is reused across frames only within one partition and only for an identical decision, source and scope; never across partitions or fields.

Labour vector for task class j: independent labels 2T; adjudications J (measured initial disagreements); agreement audits ⌈0.10 (T − J)⌉; blind dispute reads (measured); structural expansion and adjudication; specialist two-seat contrast work; P3 census tasks counted the same way. P9 recomputation, the §2.4 container census and E10's development-stratum scoring are machine work and create no label task. Hours H = Σ_j n_j t_j / 60, with t_j measured in disclosed training (W:191). Gate I9 uses H⁺ = Σ_j n_j^99 t_j⁺ / 60, where n_j^99 is the steward's private 99th percentile of the count over the PRN design computed from frames only, t_j⁺ the upper confidence limit of measured timing, and J at the planning upper rate of 20% until measured. A measured disagreement rate above planning stops before exhaustion (W:191). Receipts report U, A, U^scr, K, K^exp, T, labels, adjudications, audits and hours separately and never add different units. The historical figures 3,494.7-7,624.8 and 12,404.7-27,064.8 hours are unvalidated planning scenarios; this design's task count is expected to differ (FULL scopes, per-endpoint frames, census) and is known only at I9. Marginal task-count percentiles alone do not establish joint staffing adequacy. Actual measured timing, secured named staffing and the I9 receipt remain prerequisites, not claims made by this document.

## 5. A2: estimands and inference

Gates use exact unweighted SRS inference only; weighted sums never enter binomial formulas. The target, law and N of every row are fixed by §3.7.

| ID | Target and unit | Sample | x and n | Inference | Role |
| --- | --- | --- | --- | --- | --- |
| E1 | c-negative closures of the full frame F_c, closure-domain, frozen workflow w | ENRICH_f negative draw | any wrong c member accepted; n=500 | exact upper at a=.05/m_cal ≤ .02 | G16 gate |
| E2 | c-positive closures of F_c | ENRICH_f positive draw | any correct answerable c member rejected or abstained on; n=500 | upper ≤ .05 | G17 gate |
| E3 | Child natural negative prevalence on F_c | PANEL_f, 100 per child | c-negatives / 100 | exact two-sided hypergeometric at N=\|F_c\|, tails a/2 | G18 interval in m_cal |
| E4 | Union-negative closures of G_cal (a wrong member in any registered cell) | CALU negative draw | any wrong member anywhere accepted; n=500 | upper ≤ .02 | G16/G19 gate (P1) |
| E5 | Union-positive closures (no wrong member, at least one correct answerable member) | CALU positive draw | any correct answerable member anywhere rejected or abstained on; n=500 | upper ≤ .05 | G17/G19 gate (P1) |
| E6 | Union-negative prevalence of G_cal | CALU screen of S_U | union-negatives / S_U | exact two-sided 95% hypergeometric at N=\|G_cal\| | descriptive, outside the family |
| E7 | Group-in-cell pair mass | E1-E3 | Σ_c a_c q_c U_c, a_c = \|F_c\| / Σ_c \|F_c\| | original worst-case sums of simultaneous child bounds (W:205) | supplemental, labelled pair-level |
| E8 | Unique closures of G_e° (pilot certification lot) | CERT | any applicable member failing anywhere; n=n_rel | x ≤ c(m_rel) and exact upper ≤ .01 at a=.05/m_rel; hypergeometric verification at N°(G_e) | G22 gate |
| E9 | Closures of F_{c,e}° (final lot) | FINAL_f | any applicable c member failing; n=n_rel | same, at N°(F_{c,e}) | G23 gate |
| E10 | Whole release Ω_e: unique closures, any applicable member failing anywhere | FINALU (sampled stratum), P3 census and the development-stratum rule | see below | exact strata combination; Bonferroni over 5 endpoints, 95% simultaneous | S:84 overall estimate (P2), not a release gate |
| E11 | R_res closures | P3 census | exact counts per endpoint and cell | exact, no sampling error | P3 |
| E12 | Assertion-level rates on F_c | ENRICH_f, PANEL_f | descriptive | stratified closure bootstrap; weights 1/(π_screen π_draw), π_screen = k_c/\|F_c\|, π_draw = 500/M_{c,s} | descriptive (G19) |

E10, whole-release overall estimate (F2, S:84). For pooled endpoint e, Ω_e is every closure of the exact release ledger with an applicable obligation at e. It is the disjoint union of three strata, each counted in unique closures with the FULL any-member outcome:

- Sampled stratum G_e°, of size N°_e: the FINALU draw of 2,000 under law C, with x_e failing closures; exact two-sided hypergeometric interval [L°_e, U°_e] for its failure count D°_e at N°_e, with tails .005 each; point estimate N°_e x_e / 2,000.
- Census stratum R_res,e, of size N^R_e: the P3 census gives the exact failure count D^R_e.
- Development stratum G_e^dev, of size N^dev_e: development-allocated U* closures. A closure is resolved when the frozen final rubric scores every applicable obligation at e from existing sealed, blind, source-backed labels (FULL-scope CALU screens and DEV; DOMAIN-scope labels when every applicable obligation at e lies in that domain). The N^K_e resolved closures give the exact count D^K_e. The other N^u_e = N^dev_e − N^K_e closures are unresolved and count 0 in the lower and 1 in the upper bound (worst-case bounds for unobserved outcomes, Manski 2003). This scoring is machine comparison of the exact artifact with labels that already exist. It is not a test sample, creates no label task, is exposed and is never held-out evidence.

With N_e = N°_e + N^R_e + N^dev_e, the report gives L_e = (D^R_e + D^K_e + L°_e)/N_e and U_e = (D^R_e + D^K_e + U°_e + N^u_e)/N_e; the point estimate (D^R_e + D^K_e + N°_e x_e/2,000)/(N_e − N^u_e) over the resolved mass, with that denominator stated; and every stratum's size, count or interval. D^R_e and D^K_e are exact, the unresolved part is bounded, and [L°_e, U°_e] is exact under law C, so P(the whole-release rate lies in [L_e, U_e], or no report) ≥ .99 per endpoint and ≥ .95 over the five endpoints. A census stratum contributes no sampling error. The resolved-mass point estimate is not a whole-release point estimate while N^u_e > 0. An E10 interval cannot discharge S:84's prohibition on exporting unresolved fields as accepted facts. G22/G23 remainder bounds are never whole-release certification. When N^u_e > 0 the estimate is partially identified and reported as such, and S:84's rule that unsampled or underpowered strata remain unresolved applies to that mass. The unreserved remainder rate D°_e/N°_e, the census rate and the development-stratum figures are reported under those names and are never called the whole-release estimate. Unique-closure, appearance and pair figures stay separate; no pair estimate or weighted sum enters E10.

Union versus cell. A child bound does not in general bound a union failure. If a closure is negative in six cells whose events differ and each child falsely accepts independently at exactly 2%, its union false-acceptance probability is 1 − 0.98⁶ ≈ 11.4%. Child bounds do control the union event when every closure's union outcome coincides with one tested child outcome, for example single-cell closures, or overlapping cells with identical frames and member obligations. P1 tests the union event directly, which is adequate for any overlap structure. Over a single union stratum, "falsely accepted negative groups ≤ .02 × negative-group prevalence" is equivalent to r_U,− ≤ .02, so no prevalence interval enters that gate.

Multiplicity and overlap. Within a sub-partition, frames overlap (endpoints, children) and closures are reused; tests are dependent and Bonferroni is valid without independence, given valid marginal laws (§3.7). No closure is in two sub-partitions. Receipts report the multiplicity distribution μ(g), the number of registered cells with obligations, from frames.

Finite populations. W:179's hypergeometric verification at the realized design, at the N that §3.7 binds to each claim, remains a statistician obligation before ratification, including sign subpopulations whose size is unknown before screening. This contract does not claim that it holds.

## 6. A3: applicability

A(g,c,e) is the set of preregistered obligations of closure g in cell c at endpoint e, frozen at I6 from source/frame obligations, δ and the evaluated artifact's structure. Human labels, missing labels, workflow decisions and correctness never change A.

| Endpoint | Applicable obligations |
| --- | --- |
| Identity attachment | Every obligation of g in c, including withheld and required-absent ones: recorded attachment or explicit no-attachment disposition against the source-backed subject, lexeme, sense or MWE |
| Asserted value | Every D member the artifact asserts in c, including unsupported assertions |
| Citation/source binding | Every asserted value requiring provenance and every emitted P member; a required binding that is missing is an applicable failure |
| Abstention decision | Every obligation: assert, withhold or required absence against sealed source answerability |
| Accounting/eligibility | Every obligation: expected source units, dispositions, emitted A members, R-class recomputation result and identity scope |

Endpoint frames are F_{c,e} = {g : A(g,c,e) ≠ ∅} and G_e. Identity, abstention and accounting share F_c, so under 3.3 they share one sample. Value and citation frames are subsets with their own samples of exactly n_rel. Supply is checked at I7, before selection, from frames alone. A promised endpoint with an empty frame receives a STRUCTURALLY_EMPTY receipt with its derivation; it neither passes nor disappears, and the family is recomputed only after designated review before selection. Humans label blind to outputs. A missing required label, or a human N/A on an applicable obligation, makes the gate INCOMPLETE; source-unresolved is a legitimate answerability label. Smaller n, borrowing across fields, panel or partitions, and post-result extension or replacement are prohibited.

## 7. Test-family arithmetic

Release family: m_rel = 5 + 5C, a_rel = .05/m_rel. For n, c(n) is the largest x whose exact upper bound at a_rel is at most 1%. n_rel(m) is the smallest n ≥ 2,000 with m · P(X > c(n) | n, .001) ≤ .05; consumer risk at pR = .01 is then at most a_rel by Clopper-Pearson duality. These are binomial planning values; the G25 hypergeometric verification uses the N that §3.7 binds to each claim. Planning values:

| C | m_rel | n_rel | c | Upper bound at c | Family producer risk at AQL |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 35 | 2,000 | 7 | 0.951504% | 3.808504% |
| 7 | 40 | 2,000 | 7 | 0.961546% | 4.352575% |
| 8 | 45 | 2,000 | 7 | 0.970361% | 4.896647% |
| 9 | 50 | 2,110 | 8 | 0.999541% | 1.727435% |
| 10 | 55 | 2,124 | 8 | 0.999856% | 1.992227% |
| 11 | 60 | 2,138 | 8 | 0.999550% | 2.277731% |
| 12 | 65 | 2,150 | 8 | 0.999663% | 2.568002% |

Calibration family: m_cal = 2WC + C + 2W for W ≤ 3 workflows, comprising child sign gates, child panel intervals and union sign gates (P1). For C = 6 and W = 3, m_cal = 48 (42 without P1). The decision rule is unchanged: exact upper ≤ 2% (negatives) and ≤ 5% (positives) at a = .05/m_cal. At n = 500 and m_cal = 48: one false acceptance gives 1.822660% (pass), two give 2.215602% (fail); ten nonacceptances give 4.745998% (pass), eleven give 5.030328% (fail). The original illustration that eleven pass (4.986987%) holds only at m_cal = 42. The development check recomputes every value.

## 8. Conditionally agreed additions

| ID | Addition | Why it is needed | Consequence |
| --- | --- | --- | --- |
| P1 | CALU union calibration: S_U ≤ 10,000 FULL screen, 500 + 500 union draws, 2W union gates | Child bounds do not bound W:205's unique-group aggregate when a closure's union outcome differs from every tested child outcome (§5); a direct union test is adequate for any overlap structure | m_cal 42 → 48; ≥1,000 FULL-labelled selected closures; new screening cap |
| P2 | Whole-release overall estimate E10: FINALU sampled stratum on G_e° (law C), P3 census stratum and development stratum, combined over unique closures with each stratum's mass stated | S:84 requires the overall estimate on the exact release artifact with its weighting, denominator and uncertainty; a U*-only or pair estimate cannot substitute | ≥2,000 FULL-labelled closures per pooled endpoint; five report-only intervals, 95% simultaneous; no label task beyond FINALU |
| P3 | Census of R_res | Reserved closures are exported with ordinary dispositions (S:74) but have zero inclusion probability; S:84 forbids exporting unsampled strata as accepted facts | All members FULL-labelled blind; critical events zero; noncritical exact proportion ≤ 1% per nonempty endpoint and cell; replay results exposed, protected results held by the steward; exact counts enter E10 |
| P4 | Per-endpoint SRS frames | Fixed 2,000-closure draws cannot guarantee 2,000 eligible at value and citation endpoints | More closures where F_{c,e} is a proper subset of F_c; computed at I7/I9 |
| P5 | MORPH children for `frequency`, `heritage_status`, `transliteration`, conditional on ledger export | These are required card fields without a home; exclusion would need designated approval | Each adds 5 final tests, 2W calibration gates and one panel interval, and shares the MORPH cap; all three give C = 9, m_rel = 50, n_rel = 2,110, c = 8 |
| P6 | Membership-independent sub-partitions, with every claim bound to law M or law C (§3.7) and supply handled jointly (§3.8) | Keeps unique floors and exact equal-probability samples together, and states which population each sample is an exact SRS of | Each child draws on a share of its partition; small children need larger frames (I7); release lots are post-development remainders |
| P7 | `gloss_en` deferred with `english_gloss` | Q:187 defines both as one scaffold field pair; D:52 defers `english_gloss` | If rejected, `gloss_en` needs a designated new planning domain with full floors and tests before any export |
| P8 | Labour gate I9 | No measured task budget exists | Selection waits for measured timing and a staffing receipt |
| P9 | Exhaustive recomputation census for R members, including the §2.4 structural census of every container instance | Deterministic members and container structure have an exact check; sampling them would be weaker | Machine work; every mismatch fails |

If P1 is not agreed, the 42-test family of W:209 supports W:205's unique-group aggregate limits only for closures whose union outcome coincides with one tested child outcome. The frozen cell inventory (I3) can establish that for some designs, for example single-cell closures, or overlapping cells with identical frames and member obligations. Where it cannot, the aggregate claim is blocked by W:205's own stop on unsupported transport. That is a support gap, not an exact contradiction in every overlapping design, and P1 is not claimed to be the only adequate design. The recommended designated decision is to adopt P1.

## 9. Gate tables

### G01. AC-01, researched interpretation

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation AC-01; S:7-19,50-78,99; W:221 | Requested reference families and supported interpretation | Citation/claim, not a sampled group | Datasheets, Data Cards, cards, Croissant/core/RAI, current NeurIPS requirements, IAA/CIs, held-out/contamination practice | Supported practice separated from project choices | Not a rate; supported claims and limits | All named reference families/claims | Material unsupported interpretation blocks documentation agreement | All named families; no omitted requested family | No numerical confidence gate | Fabricated evidence/leakage blocks | Methodology documentation only | Unavailable source is explicit; no invented source support |

### G02. AC-02, standard and template completeness

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation AC-02; S:21-48,80-99; T:7-68; W:222 | DoR, five transitions, DoD and one-page template | Required item/transition | Owners, denominators, sources/licences, seal, thresholds/n, independent evaluation, release/maintenance | Complete requirement coverage | Not a rate; mapped items | Every requested item in T and S | Missing required item blocks affected gate; proposed template is not a filled execution plan | All applicable items | No new universal cutoff | Stronger original gates retained | Contract completeness only | Blanks block their execution gate; no invented owner identity |

### G03. AC-03, preserved word-card contract

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation AC-03; W:13-90,92-213,223 | Existing programme, retained obligations, metadata-only freeze status and calibration | Requirement/evidence statement | All original source/identity/gold/evaluation gates | Preserve, or explicit UNKNOWN with owner/event | Not a rate; requirement mapping and metadata limits | Every retained applicable obligation | Fabricated seal or weakened prerequisite blocks | All required evidence or honest unresolved state | Structural and statistical gates all pass separately | W:143 global override retained | Proposal does not establish gold or quality | Reported verifier refusal at W:76-82 was not rerun; SHA/date/authority remain unestablished here |

### G04. AC-04, private-release design and separately scoped code

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation/design AC-04; H:3-109; W:224; issue AC-04 plus scoped safety paragraph | Private default, plan capacity versus observed capacity, version mapping, cards, field provenance, custody, public conditions; uploader safety remains whole-issue scope | Design requirement; separate code behavior | Direct Hub client without persistent login; private default; refusal on public/unknown privacy; pre-network quarantine retained | Design review plus independently reviewed behavior evidence in code lane | Not a rate | All AC-04 design and attached safety behaviors | Any unmet relevant access/quality/safety gate blocks action | All attached behaviors and design conditions | No new sample scheme | Transfer safety never certifies facts | No account, identity, token, upload, or entitlement claim | Code candidate/tests/CI not inspected or executed here; code author and driver retain this work |

### G05. AC-05, designated agreement and delivery

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Documentation AC-05; S:3,95-99; T:68; W:3,225-227; H:3 | Exact proposed process and implementation head | Distinct nonauthor proof and delivery receipt | Sol content criticism, Opus designated agreement, exact-head outside-family APPROVE, same-head CI, merge, issue evidence, common cleanup | Each distinct gate evidenced; self-test is development only | Not a rate | All approval/delivery obligations | Missing agreement, moved head, or material unresolved finding blocks | All required receipts | CI suite results require run IDs; none claimed here | No report substitutes for approval | Documentation delivery, separate from dataset DoD | This worker supplies none of those final gates; driver owns them |

### G06. Execution DoR and appointments

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Quality-pilot entry; S:23-38; T:9-45; W:11,114,124-128,191; §1 | Frozen universe, closure graph, δ ledger, cell inventory, applicability, design, rubric and versioned plan | Source unit, identity, record, field, closure, appearance, case and task counted separately (§4) | Named driver/source/extraction/annotation/gold/evaluator/release/maintenance/takedown owners; receipts I1-I10 | Every applicable DoR item PASS; I1-I5 before allocation, I6-I10 before selection | Not a rate; completed entries and receipts | All DoR items, I1-I10 and actual appointments | Missing item or receipt blocks the relevant transition | Complete inventory and assigned people, not role labels | Preregister n_rel(m), c, m_rel, m_cal, risks, CIs, frames, shares, PRN procedure, caps, probabilities, task formula and stop policy (§3-§7) | No invented Ukrainian/protected access | Known-source extraction only | UNKNOWN denominator blocks allocation and sampling; permitted engineering is separately classified; this contract waives no I-gate |

### G07. Source completion and field admission

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Source gate; W:21,38-51,59-66,86; S:26-28; D:33-58; Q:54-77,91-97,182-187; J:379-409; §2 | Every registered source/field cell and the δ-classified release ledger R | Source unit with exact snapshot/locator; ledger member with its δ class | All required ranges, spellings, lexemes, senses, MWEs, forms/cards; every member path of every exported record and release file | Accepted, held, withheld-reason or excluded-reason exactly once; one primary δ class (D, I, P, A, R, V, X, U) per member; §2 field-domain table for all 24 names | Not a rate; reconciled dispositions; counts of U-class members and exported X-class members, both required to be 0 | Complete frozen source universe and ledger, currently UNKNOWN | Missing/corrupt/quarantined input is not absence; unexplained W2 disagreement stops; any U-class member is INCOMPLETE and any exported X-class member is FAIL | #10512 complete-data receipt, #9401 matrix and I2 ledger receipt with δ digest | No inference replaces complete inventory | Wrong homonym/sense, unsupported definition, reversed correction fail | Actual admitted pinned-source scope; a field is admitted for export only with registered cell coverage | Retain ULIF variant/omission lists; VESUM morphology is not stress; SUM20 quarantine; VTS edition/admission; ULIF nonblank gloss; sense_not_visible; MWE section/edition/citations; two-seat historical contrast and modern corroboration; english_gloss, gloss_en (P7), cefr, examples, collocations and practice eligibility stay ledger obligations as withheld:deferred; frequency, heritage_status and transliteration export only as MORPH children (P5) with an admitted source, otherwise held with a source-admission reason |

### G08. Fresh gold admission and custody

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gold entry; W:24,68-90,114-116,139; S:28-29; T:30-36; H:34-38 | Fresh frozen source universe and independent audit partitions | Closure/case with separately recorded expansion | Independently selected authentic source expectations after complete-data receipt | #10514 AC-01..05 preserved: source first, separate steward/adjudicators, blind source labels, sealed membership/answers, access/isolation proof | Not a rate; expected decisions linked to sources and admitted receipt | Every expectation and protected access path | Hash alone is insufficient; leaked proof invalid | Authenticated authority/signature, manifest SHA, UTC seal date, thresholds, code/input versions, steward/isolation receipts | No small structural set supplies population precision | Gold leakage fails absolutely | Fresh protected evaluation only when admitted | No author gold read; old 220 are regressions; affected candidate lineage remains steward-owned UNKNOWN; existing refusal remains open |

### G09. Partition and closure disjointness

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All partitions; W:96,116,126-141,197-205; S:29,72-78,87; H:38; §3.1-3.3 | Whole closure graph before cell restriction; sub-partitions TRAIN_f, PANEL_f, ENRICH_f, CALU, DEV_f, CERT, FINAL_f, FINALU, REL; reserved R_res | Unique closure group across all partitions and sub-partitions | Training, structural replay/held-out, exposed development witnesses, panel, enrichment, union calibration, development pilot, certification, final and union final | No related closure crosses partitions or sub-partitions; R_res frozen by the steward before allocation; allocation uses private v_g only, with shares from frame counts | Overlapping closures reported, not an accuracy rate | Searched partition/closure universe and exclusions; N(R_res) and its member counts per cell | Any prohibited overlap blocks affected independent proof | Fresh disjoint capacity for each promised partition; realized pool sizes at least the need (I7) | Private v_g and u_g draw state; public 10772 only for safe arithmetic/bootstrap; shares fixed before the draw; no redraw without designated review | Leakage disqualifies | Local checks only for searched scope; pretrained exposure UNKNOWN | Label reuse across frames only within one sub-partition; R_res is never in a sampling frame and no sampled bound extends to it; it is covered by the P3 census and enters the E10 whole-release estimate as its exact census stratum (P2); no detectable release complement, guessable-ID digest or membership-bearing public filename |

### G10. Structural replay

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gate 2 replay; W:94-120 | Preregistered structural categories, not field-quality cells | Case; expanded cards/pairs and closure counts separate | Fresh 132 of exactly 220 cases, disclosed only after sealing | Exact identity/split/merge overlay reproduction | Replay mismatches | 132 pre-expansion cases, with category counts below | Any reproduction mismatch fails replay requirement | Category replay allocations retained: 24,12,12,12,3,12,12,12,6,6,9,12 | Exact-count recommendation; authenticated ratification required | Global critical failure rule also applies | Exposed deterministic replay only | Not held-out; related closures excluded elsewhere; expansion counts UNKNOWN |

### G11. Structural protected threshold gate

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gate 2 protected; W:94-120 | Hard categories plus ordinary controls | Pre-expansion case with closure isolation | 88 protected cases; initially evaluated alongside certification | Source-adjudicated identity, variants/conflicts and expected abstention; wrong partners/other incorrect structural outcomes fail | 0 wrong merges; <=2 wrong splits per hard category; false abstentions <=5% overall and each nonempty answerable category; 0 ordinary-control errors | Applicable case counts, false-abstention denominator human-answerable cases; no rounding up allowances | Any prohibited structural error fails; report category confusion and expanded pair/card counts | Totals/replay/protected: homonyms 40/24/16; stress doublets 20/12/8; proper/common 20/12/8; aspect pairs 20/12/8; aspect homographs 5/3/2; MWE 20/12/8; unsplit senses 20/12/8; stress disagreement 20/12/8; tier3 10/6/4; header damage 10/6/4; cited contrast 15/9/6; ordinary 20/12/8. Total 220/132/88 = 200 hard +20 ordinary | Exact-count recommendations at actual authenticated freeze; no 1% population claim | <=2 wrong splits cannot override critical rule; 0 model-written Ukrainian, resolvable locators and source-removal recomputation retained | Structural challenge correctness, not release population accuracy | Required undefined denominator makes gate INCOMPLETE; exposed case retired/replaced after refreeze, never added to overlay as proof |

### G12. Human reliability

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reliability; W:185; S:54-64; T:41-44 | Each applicable field decision/task, with identity/variant/conflict typed separately | Sampling closure; rating unit group × applicable field | Two independent qualified humans, blind to model/assembler outputs | Nominal supported / unsupported / source-unresolved; originals retained | Raw agreement and nominal alpha components as registered estimator requires | All sampled ratings, eligible pairs, missing pairs and marginals reported separately | Undefined coefficient cannot pass; alpha lower bound must be >=0.80 | Two labels per unit; no invented minimum n for alpha | Two-sided 95% interval, 10,000 stratified closure-bootstrap resamples, public seed 10772 | Reliability is not truth | Human consistency by task, not accuracy | Missing ratings, prevalence/skew and undefined estimates explicit; refinement only disclosed training/calibration before refreeze |

### G13. Blind adjudication and agreement audit

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gold reliability process; W:187; S:64; T:41 | Disagreements, sampled agreements, candidate/gold disputes | Labelled unit with closure context | Third independent human for initial disagreements; separate blind dispute reader | Source-backed outcomes; competing outcomes unlabelled/random order; no candidate/gold identity cue | Adjudicated decisions and audited agreements, not a rate gate | All disagreements plus private random 10% of agreements, disputes separately | Systematic label error investigated; corrected final gold invalidates affected test | All disagreements; 10% agreements | Existing audit allocation, no new hypothesis family | Leakage/unsupported gold does not pass | Defensible expectations, not candidate-consensus truth | Preserve originals/rationale/version/counts; independently reviewed refreeze/fresh proof after correction |

### G14. Human supply and budget feasibility

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Capacity; W:130-139,189-191,201; S:30,33; T:42; §3.6, §4 | Planning domains and registered children from I3 | Distinct closures U, appearances A, screened closures U^scr, cases K and K^exp, decision tasks T and labour units, each kept separate | Unique floors: training 60, calibration 6,600 (plus CALU 1,000, P1), development pilot 300, certification 2,000, final 12,000 (plus FINALU 2,000, P2); 220 structural pre-expansion cases; at most 10,000 distinct screened closures per planning domain (plus at most 10,000 for CALU, P1) | Feasible frozen supply and secured named human work before selection (I7, I9) | Not a quality rate; task counts and hours by class | 21,180 is reported only as 20,960 distinct closures plus 220 pre-expansion cases; additions reported separately | Unaffordable work, missing roles, insufficient negatives or H⁺ above secured hours stops before selection or exhaustion | Training 10 per f; development 50 per f; panel 100 per child and at least 100 per f; enrichment at least 500 per sign per child and at least 1,000 per f; certification n_rel per pooled endpoint; final n_rel per child endpoint and at least 2,000 per f | Two labels per task; third-human adjudication of disagreements; 10% agreement audit; T, labels, J and audits per §4; H⁺ from measured t⁺ and the 99th-percentile T; the historical 3,494.7-7,624.8 and 12,404.7-27,064.8 hour figures are unvalidated scenarios, not this design's budget | No feasibility shortcut weakens quality | Staffing plan only, not measured capacity | Expansion, specialist and census work counted; reserves/replacements fixed; each designated-added planning domain adds 10+100+1,000+50+2,000 distinct closures and needs its own cap |

### G15. Calibration screening, sign and supply

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Calibration selection; W:128,134,195-203,209; §3.5 | Child c=(f,s,r) in ENRICH_f, using M(g,c) first; union stratum in CALU (P1) | Distinct closure restricted to c (child) or the whole closure (union), once per sign | Nonempty fully labelled M(g,c) in ENRICH_f; fully labelled closures in CALU | Child: any wrong asserted c member gives c-negative, otherwise at least one correct answerable c member gives c-positive; union: the same rule over all registered members; remaining fully labelled category separate | Sign-pool supply M_c,- and M_c,+; M_U,- and M_U,+; no judge-based selection | N_c = \|F_c\|, the full frame (law M, §3.7); the slice size N(F_c ∩ ENRICH_f) is a supply quantity only; k_c screened, M_c,s sign pool, 500 selected per sign; CALU: \|G_cal\|, S_U screened, M_U,s, 500 per sign | One wrong member fixes the negative sign of that domain; any missing required label gives INCOMPLETE | At most 10,000 distinct screened per planning domain, shared by its children through preregistered frame-only water-filling k_c; fixed S_U at most 10,000 (P1); at least 500 distinct negative AND 500 positive per child and for the union; no borrowing | PRN: screen is the first k_c of F_c ∩ ENRICH_f by u; each draw is the first 500 of a screened sign pool by u, an exact SRS of the full-frame sign subpopulation under law M (§3.7); probabilities k_c/\|F_c\| and 500/M_c,s retained for descriptive weights; sizes frozen before results | Any observed critical event disqualifies the workflow | Conditional groups of the full frame F_c in the frozen assembler-output distribution per child; union sign population of G_cal; law M, so only versions meeting precondition M on their draw can be ratified (§3.7) | Zero-member group excluded with count; zero supply blocks; old negatives and constructed challenges separate, never natural supply; a cap is no proof of supply; child allocations never multiply the cap |

### G16. Calibration negative endpoint

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Conditional false acceptance; W:197-203,209-211; §5 E1, E4 | Each workflow w and child c, M(g,c); union stratum per w (P1) | One sampled negative closure-domain (child) or negative closure (union) | Complete labelled negative draw under G15 | Human-negative before any workflow decision | x_w,c,- = sampled c-negatives with ANY wrong c member accepted by w; x_w,U,- = sampled union-negatives with ANY wrong member anywhere accepted | n = 500 sampled distinct negatives, each once | Any accepted wrong member adds 1 regardless of member count; a wrong member outside c adds 0 to c but counts for the union | At least 500 per child and per union; panel, another child or the union cannot supply a minimum | m_cal = 2WC + C + 2W (48 for C=6, W=3; 42 without P1); a = .05/m_cal; upper beta.ppf(1-a,x+1,n-x), zero 1-a**(1/n), all-failure 1; PASS only if upper is at most .02; planning at m_cal=48, n=500: x=1 1.822660% passes, x=2 2.215602% fails | Any critical anywhere disqualifies, even if this bound passes | Conditional group false acceptance at most 2% per child and for the union population, frozen workflow/assembler distribution | Not an assertion rate; missing required labels INCOMPLETE; mixed groups never positive; zero n cannot PASS |

### G17. Calibration positive endpoint

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Positive nonacceptance/coverage; W:197-201,209-211; §5 E2, E5 | Each workflow w and child c, M(g,c); union stratum per w (P1) | One sampled positive-answerable closure-domain (child) or closure (union) | Positive-only pool after G15 | Correct answerable asserted members within c (child) or anywhere (union); a negative in another cell changes the union sign only | x_w,c,+ = sampled c-positives with ANY correct answerable c member rejected or abstained on; x_w,U,+ likewise over all members | n = 500 sampled distinct positives | Any such nonacceptance adds 1; many members never multiply n | At least 500 per child and per union, separate from negatives | Same m_cal and a; PASS only if upper is at most .05, hence coverage at least .95; planning at m_cal=48, n=500: x=10 4.745998% passes, x=11 5.030328% fails; the original x=11 illustration (4.986987%) holds only at m_cal=42 | Global disqualification unchanged | Positive-group coverage per child and for the union, not all-assertion coverage | Correct members of mixed negative groups descriptive only; missing required labels INCOMPLETE; no sign inflation from another field |

### G18. Independent probability-panel prevalence

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Calibration panel; W:134,197,205,209; §3.5, §5 E3 | Each child c in PANEL_f, no enrichment | Probability-sampled closure-domain | Nonempty fully labelled c members in PANEL_f, closure-disjoint from enrichment | Same domain-restricted signs as G15 | c-negatives among the sampled | All sampled eligible closures, 100 per child | Any human wrong c assertion gives the negative sign; it is not a workflow failure | 100 per child by S(F_c, PANEL_f, 100); at least 100 distinct per f and 600 in total | C exact two-sided negative-prevalence intervals within m_cal, tails a/2, boundary cases included; finite-population verification G25 | Critical failure global | Natural child negative-group prevalence; design transport only | Positive prevalence in [0, 1-L_negative] with no exhaustiveness assumption; missing required labels INCOMPLETE; union prevalence comes only from the CALU screen (E6), never from summed child panels |

### G19. Aggregate calibration claim and descriptive rates

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aggregate claim; W:203-209; S:62,68,84; §5 E4-E7, E12 | Union population G_cal of unique closures for the original group-level aggregate; child pairs only for the supplemental pair mass | Unique closure for union claims; closure-in-child pair for the supplemental mass | CALU union draws (P1); PANEL intervals and child bounds for the pair mass | Union sign over all registered members; child signs domain-restricted | Union: x_w,U,- and x_w,U,+ (G16, G17); supplemental pair mass Σ_c a_c q_c,s U_c,s | Union: the union sign draws; pair: Σ_c N_c | Union failure is any member anywhere; pair counts are per child | Existing minima; 500 per union sign | The W:205 limits (falsely accepted negative groups at most .02 × negative-group prevalence; nonaccepted positive answerable groups at most .05 × positive prevalence) are tested exactly as union conditional bounds within m_cal; union prevalence reported with an exact 95% interval outside the family; the pair mass keeps the original nonnegative worst-case sums of simultaneous child bounds | Global disqualification | Union claim: unique-closure group aggregate on G_cal; the pair mass is labelled group-in-cell and never presented as unique | Child bounds do not in general establish a union bound (six independent children at 2% can give 11.4%); weighted sums never become binomial n; descriptive assertion P(accept) and two-phase weights retained; unsupported transport or inadequate precision blocks the aggregate claim |

### G20. Workflow selection, loss and freeze

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Calibration selection/freeze; W:195-197,209-213; S:60-64 | Complete two-family/tool/rule/routing/screener workflow, every child and the union stratum | Paired closure predictions | At most 3 preregistered versioned workflows on identical selected closures and all their in-scope members | Eligibility requires G16 and G17 in every child AND for the union (P1), and zero criticals; loss critical/false acceptance=10, false abstention/other error=1, correct=0 | Design-weighted human loss and shared wrong decisions | Registered weighted calibration population, never assertion trial n | Accept-all must fail the negative endpoints; abstain-all the positive endpoints; one-vs-many guard retained | All required sign/child/union supplies; no eligible workflow means stop | 10,000 paired closure-bootstrap comparisons with familywise adjustment; inconclusive differences retain the stronger eligible two-family source-verified workflow | Criticals disqualify absolutely, not merely loss 10 | Workflow ranking on calibration only | Freeze complete workflow hashes before certification; no tuning on protected pilot/final; a screener cannot independently win acceptance authority; exposed negatives are not held-out proof |

### G21. Dataset-quality pilot construction

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pilot; W:25,130-141; S:38-43; T:51; §3.5 | Frozen development-pilot sub-partitions DEV_f | Closure, with source/record/field counts separately | 300 development closures, 50 per planning domain by S(F_f, DEV_f, 50), after admitted seal | Independent full source-fidelity inspection of every member (FULL); disposition/provenance census | Lost/duplicate units=0; required provenance coverage=100%; semantic results explicit | Every required unit/field/provenance item in the frozen pilot | Any critical fails; every unexplained loss/duplication violates the census | 300 distinct closures; distinct from mechanics150 and all R_res | Inspection/census, not the certification estimator | Zero critical failures | Quality pilot artifact only | Mechanics150/272/114/140 and 22 historical gaps do not supply this sample or gold; no source missingness hidden |

### G22. Independent pilot certification, five pooled endpoints

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wrong identity attachment; W:136,139-151,179; S:43; §5 E8, §6 | Pooled frozen frame G_identity in CERT; cell reports separate | Unique closure once over all applicable members (FULL) | Applicable identity obligations under §6, including withheld and required-absent ones | Source-adjudicated identity question | x_identity = closures with any wrong applicable attachment | n_identity = n_rel distinct closures by S(G_identity, CERT, n_rel) | One failed applicable member gives a closure failure | n_rel(m_rel) eligible distinct closures, at least 2,000 | G25 prerequisites; m_rel = 5 + 5C, a = .05/m_rel; c and n_rel by §7 (n=2,000, c=7 while m_rel is at most 45); exact upper at most 1% | Wrong homonym/sense also critical, therefore zero tolerated there | Pooled unique-closure error of the post-development remainder lot G_identity° (law C, §3.7), no 1% cell claim; development-allocated closures are reported in E10, never under this bound | Required missing labels INCOMPLETE; STRUCTURALLY_EMPTY only by reviewed receipt; never filler n |
| Wrong asserted value; W:136,141-151,179; §6 | G_value in CERT | Unique closure (FULL) | Applicable asserted values, including unsupported assertions | Human source truth | x_value = closures with any wrong value | n_value = n_rel by S(G_value, CERT, n_rel); lot G_value° | Any wrong eligible value fails the closure | n_rel, at least 2,000 eligible | Same family, exact bound | Critical subset absolutely fails | Same pooled unique-closure estimand on the remainder lot | Same missingness rule; value-ineligible closures never count in n |
| Invalid citation/source binding; W:136,141-151,179; §6 | G_citation in CERT | Unique closure (FULL) | Every asserted value requiring provenance and every emitted binding | Source-backed locator and scope; a missing required binding is a failure | x_citation = closures with any invalid or missing required binding | n_citation = n_rel by S(G_citation, CERT, n_rel); lot G_citation° | Any invalid eligible binding fails the closure | n_rel, at least 2,000 eligible | Same family, exact bound | Critical subset absolutely fails | Same pooled unique-closure estimand | Same missingness rule; omission never makes the endpoint N/A |
| Incorrect abstention decision; W:136,141-151,179; §6 | G_abstention = G_identity in CERT | Unique closure (FULL) | Every obligation: assert, withhold or required absence | Abstention on answerable evidence is wrong; human-confirmed unresolved is legitimate | x_abstention = closures with any wrong abstention decision | n_abstention = n_rel, the same sample as identity | Any wrong eligible decision fails the closure | n_rel | Same family, exact bound | Critical subset absolutely fails | Same pooled unique-closure estimand | Missing label is not unresolved; N/A is never a denominator |
| Accounting/eligibility violation; W:136,141-151,179; §6 | G_accounting = G_identity in CERT | Unique closure (FULL) | Every obligation, emitted A members and R-class recomputation results | Frozen source/accounting rubric | x_accounting = closures with any violation | n_accounting = n_rel, the same sample as identity | Any eligible violation fails the closure | n_rel | Same family, exact bound | Critical subset absolutely fails | Same pooled unique-closure estimand | No lost/withheld/absent member silently dropped |

### G23. Untouched final audit, five endpoints in every registered cell

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wrong identity attachment; W:128,137-151,179; S:45,84; §3.5, §5 E9-E10 | Each child c=(f,s,r) in FINAL_f, exact scaled artifact | Closure restricted to M(g,c,identity) (DOMAIN) | Nonempty applicable c identity obligations | Human source-backed labels, no calibration sign filter | x_c,identity = closures with any wrong applicable c attachment | n_c,identity = n_rel distinct closures by S(F_c,identity, FINAL_f, n_rel) | A wrong member of another field/source/risk does not alter local x or n | n_rel per child endpoint (at least 2,000); FINAL_f sub-partitions are closure-disjoint, so at least 2,000 distinct closures per planning domain and 12,000 in total; appearances reported separately | G25; 5C child tests plus five pooled, m_rel = 5 + 5C; a = .05/m_rel; c and n_rel by §7; upper at most 1% | Any critical globally fails, regardless of local pass | Child-specific group endpoint on known pinned sources, for the post-development remainder lot F_{c,identity}° (law C, §3.7); development-allocated closures are reported in E10, never under this bound | Required missing labels INCOMPLETE; no N/A in n; an empty promised frame needs a reviewed STRUCTURALLY_EMPTY receipt before selection |
| Wrong asserted value; W:137,141-151,179; §6 | Each child c in FINAL_f | Closure restricted to M(g,c,value) | Applicable c asserted values | Source truth, not judge consensus | x_c,value = closures with any wrong applicable c value | n_c,value = n_rel by S(F_c,value, FINAL_f, n_rel), an exact SRS of the value-eligible frame | Any failure within c; other cells neither dilute nor add | n_rel per child endpoint | Same family and exact bound | Global override | Child-specific group error on the same remainder lot, not assertion error | Same missingness rule; never borrowed from the identity sample |
| Invalid citation/source binding; W:137,141-151,179; §6 | Each child c in FINAL_f | Closure restricted to M(g,c,citation) | Applicable c bindings, including required missing ones | Frozen source/scope/locator labels | x_c,citation = closures with any invalid or missing required c binding | n_c,citation = n_rel by S(F_c,citation, FINAL_f, n_rel) | Any c failure counts once | n_rel per child endpoint | Same family | Global override | Same domain-specific limit | Same missingness rule |
| Incorrect abstention decision; W:137,141-151,179; §6 | Each child c in FINAL_f | Closure restricted to M(g,c,abstention) | Every c obligation, including expected withholding/absence | Answerability/withholding labels as frozen | x_c,abstention = closures with any wrong applicable c decision | n_c,abstention = n_rel, the same sample as identity | Any wrong c decision counts once | n_rel per child endpoint | Same family | Global override | Same domain-specific limit | Missing, unresolved and N/A distinct; no sign-based exclusion |
| Accounting/eligibility violation; W:137,141-151,179; §6 | Each child c in FINAL_f; FINALU overall estimate (P2) | Closure restricted to M(g,c,accounting); FINALU unique closure (FULL) | Every c obligation, emitted A members and R-class results | Frozen rubric, complete evidence | x_c,accounting = closures with any applicable c violation | n_c,accounting = n_rel, the same sample as identity | Any c violation counts once | n_rel per child endpoint; FINALU 2,000 per pooled endpoint from G_e° | Same family for child tests; E10 whole-release interval per pooled endpoint from the FINALU stratum (exact hypergeometric at N°(G_e), tails .005), the exact R_res census count and the development stratum (exact where completely labelled, otherwise worst-case 0/1), Bonferroni over 5, 95% simultaneous, outside the release family | Global override | Same domain-specific limit; E10 gives the S:84 whole-release unique-closure estimate with each stratum's mass, not a release gate; remainder, census and development figures keep their own names | Supply checked at I7 before selection; FINALU never replaces a child test |

### G24. Absolute critical-failure override

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All semantic/acceptance gates; W:118-120,143,199,209-211; S:97 | Entire observed workflow/artifact, all cells | Observed critical event, separate from local trial counts | Invented Ukrainian, wrong homonym/sense, unsupported definition, reversed correction, gold leakage, accepted suppressed content | Existing critical taxonomy retained; not a universal new stress-critical rule | Observed critical count must be 0 | All observed relevant events, not a population absence estimator | Any observed critical anywhere fails absolutely | Zero observed criticals plus all other gates | No CI/c allowance excuses a critical | Overrides all passing statistics and structural allowances | No sample establishes zero criticals in population | Missing evidence cannot certify absence; unrelated noncritical field errors remain local |

### G25. Exact inference, finite pools and lot disposition

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Statistical ratification; W:147-181,209; S:30,66-68; T:38; §7 | Each claim's §3.7 target: full frame F_c, F_c^s, G_cal or G_cal^s (law M) or post-development remainder G_e° or F_{c,e}° (law C); never a realized slice | Independent closure under the §3 design, with the §3.7 law of each claim | Frozen finite N bound per claim by §3.7 (\|F_c\|, \|G_cal\|, N°(G_e), N°(F_{c,e}); unknown sign-subpopulation N handled by the Clopper-Pearson bound shown not below the hypergeometric bound), sampling fractions, disjointness, actual eligible n; slice sizes enter supply only | Binary any-member group failure, not weighted/correlated assertions | x closures; c from §7 for certification/final | n_rel for those endpoints; 500 per calibration sign; panel 100 per child | Every bound and all other gates must pass | Exact supply after allocation; shortage gives no claim; every error statement is joint with the claim's own proceed event, never conditional on realized supply (§3.8); no repeated mining or optional stopping | Release AQL=.001, pR=.01; family producer risk at most 5%; consumer at most .05/m_rel per bad endpoint; n_rel(m) is the smallest n of at least 2,000 meeting both, with c(n) the largest x whose exact upper is at most 1%; m_rel=35: n=2,000, c=7, x=7 upper .951504%, x=8 1.026759%, pass .999999999947/.999989859878/.998911856129 at p=.0001/.0005/.001, .000745046658 at p=.01, union producer bound 3.808504%; m_rel=50: n=2,110, c=8; hypergeom.cdf(c,N,D,n) at preregistered integer brackets of N*pA and N*pR and exact tail inversion, also for calibration and panel draws, before ratification | Criticals not part of the noncritical allowance | Lot disposition separate from weighted quality estimation | Bonferroni needs no cross-cell/endpoint independence; the exact SRS law of each claim and its precondition are stated in §3.7 (law M needs outcomes fixed before draw information is revealed; law C needs the artifact to depend only on development information); a claim whose precondition fails is not ratified; changed n, c, design or test count needs re-review BEFORE selection; a blind census is separately reviewed and never an automatic held-out waiver |

### G26. Scaled build and retained historical obligations

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Scale entry/exit; W:15-51,82,139,217,227; S:38,44; T:53; §2 | Exact pinned full source universe, deterministic configurations | Source unit/identity/record/field separately conserved; exported member with δ class | Source complete, admitted seal, pilot certification, structural Gate 2, every applicable W/RB original prerequisite | Each unit accepted/held/withheld/excluded once with reason; preserve IDs/variants/conflicts; §2 coverage equation holds for the exact export | Full reconciliation and P9 recomputation mismatches (required 0), not a sample substitute | Frozen full denominator, UNKNOWN until source receipt; every exported member | Unexplained W2 disagreement, failed W3 unit-equivalence/W4 withdrawal-identity/W5 contrast/RB P1-P6/component gate, any U-class or exported X-class member, or any recomputation mismatch blocks | Full promised coverage; retain PULS 4512=962+1386+2164 later rows and many-to-many VESUM accounting | Streaming/resource/resume, accounting and recomputation proof, no invented statistical budget | Global override | Complete construction of the exact artifact, not release certification | Historical mechanics150, 272 rows, 114 projections, 140 aliases and 22 unresolved gaps remain separate; Atlas presentation/practice parked with its owner, applicable technical/source gates retained |

### G27. Deduplication, contamination and split proof

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Build/release isolation; S:72-78,87; T:24-26; W:126,139,217; H:38 | Consumer splits and audit partitions, applicable source/author/book/lexeme boundaries | Closure with exact/near duplicate identities | All compared records, aliases, related records, paraphrases and derivations | Pinned fingerprint/normalization/near-match method and manual match adjudication | Overlap numerator and unresolved matches | Searched denominator/exclusions, explicit | Leakage/prohibited overlap blocks affected proof | All required comparison scopes | No new similarity threshold or audit sample invented | Gold leakage absolute | Only searched scope, not opaque pretraining absence | Preserve source identity before normalization; pretrained exposure UNKNOWN where unresolved; no protected content in logs/cards/public receipts |

### G28. Reproducibility and exact artifact identity

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clean-room build/replay; S:42,44-45,86; T:60; W:217; H:48-50,58 | Exact frozen build artifact/shards/configurations | File/shard/build manifest, not statistical trial | Pinned source checksums/code/config/dependencies/tools/seeds, order, writer/compression/shards, null/withheld/conflict meanings | Independent clean-room digest comparison; judge outputs pinned with provenance for replay | Hash mismatches must be resolved | All declared artifacts/manifests | Changed artifact or unjustified mismatch blocks corresponding proof | Complete reproducible manifest and independent comparison | No confidence substitute for hash identity | Semantic/critical gates also required | Reproduction of exact bytes only | Replay does not establish judge correctness; no invented row counts or shard size |

### G29. Metadata and release evidence

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Release metadata; S:46,84-95; T:59,66-67; W:217; H:46-52,109; §4, §5 | Each dataset repo and its exact artifact | Required substantive field/file/receipt | README/YAML card, core/RAI Croissant, build/source/licence/provenance manifests, attribution, changelog, partitioned data, quality/limits | Pinned validators plus substantive human/source content; authentic-source facts/no model-written Ukrainian | Not a rate; validated complete content | All required metadata and receipt fields, all V-class members | Missing substantive answer/receipt blocks release | Complete metadata and safe typed receipts | Actor/independence/time, input/artifact/code/tools, command, denominator/metric/CI, opaque protected locator and digest | Protected leakage blocks | Documentation and validation, not semantic quality alone | Group versus record rates separate; unique-closure, pair-level and assertion-level figures labelled and never mixed; U, A, U^scr, K, K^exp and T reported in their own units; public metadata has no private content/membership; generated stub/transport cannot pass |

### G30. Provenance, source scope and distribution conditions

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Source/release scope; W:40-47,217; S:27,85,87,89-90; T:21-23,62; H:17,52,73-91; §2 | Each released record/field, P-class member and mixed-source derivation | Field/source assertion | Exact source/edition/snapshot/locator, subject/scope, licence_ref, attribution, extraction version, disposition/dependencies | Internal authentic-source use decided; private transfer has owner/authority/scope receipt; public review/current GO separate | Missing/incompatible provenance dispositions, not a new quality rate | Every exported field, P-class member and derivative | No blanket repository licence cures incompatible terms; unknown transfer scope blocks that transfer; a missing required binding is also a G22/G23 citation failure | All source records/dispositions; H rows ULIF, SUM20, Pravopys, textbooks, VESUM not exhaustive | No new rights/legal threshold or authority invented | Unsupported modern use of historical normative context remains prohibited | Only authorized exact material/fields/recipients/purpose | Preserve verbal/open-licence evidence; pending evidence is not refusal; private restrictions cannot extinguish upstream rights; E6 project licence operator-owned; legal exceptions unestablished here |

### G31. Private access capability and gold separation

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Access/release entry; H:7-38,95-109; S:46,90; T:61; W:9,36 | Approved recipient/source scope and separately controlled gold | Effective access boundary | Approved topology/entitlement/namespace; scoped auth; private visibility; allowed read-only collaborator paths and denied author gold paths, including inherited privileges/caches/logs | Operator/custodian verifies capability and records receipt; evaluator verifies custody without author opening gold | Not a rate; allowed/denied checks | All required scopes/paths and inherited privileges | Unknown visibility/auth/entitlement/grants blocks relevant action; private flag alone no seal | Complete capability receipt before repo creation/transfer | No inferred current entitlement; organization-wide read not per-repo least privilege | Gold exposure invalidates proof | Verified access boundary only | Resource Groups vs separate organizations is operator decision; PRO/private/gated not proof; no identity/token receipt inspected |

### G32. Storage headroom and overage stop

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Upload capacity; H:40-44; S:46; T:63 | Actual approved billing/organization scope | Measured retained/new bytes and overhead | All retained versions, new shards/metadata, source partitions, duplicates/version overhead, reserve | Retained+new+overhead+reserve <= verified included capacity | Total planned occupied bytes including reserve | Verified included capacity; existing cited individual PRO 1TB is a plan figure, not headroom | Unknown billing/usage blocks capacity claim; stop before unapproved paid overage | Proposed reserve max(20% verified included capacity, one complete next release), pending approval | Measurement/account verification, not statistical CI | All quality/custody gates also bind | Capacity for that release only | No zero-cost-revision assumption; local sizes not billed usage; reconcile after readback; do not delete versions to fit; no current quota verification here |

### G33. Version mapping and authorized readback

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Publish exit; H:54-58,105-109; S:46,88-90; T:55 | Exact released version and permitted recipient access | Tag/commit/manifest/shard and readback receipt | Version -> tag -> exact commit -> digests; append-only archived mapping and independently controlled manifest | Pin commit, verify digests/access; moved mismatched tag refused and owner notified | Mismatched/missing content/access receipts | All release payload and expected authorized readback | Transport alone cannot pass; moved reference/changed artifact invalidates relevant proof | Complete release mapping, semantic final report, seal, review, metadata/access/capacity/provenance and owner receipts | No upload or current readback claimed | Global quality/custody overrides | Exact same-artifact private delivery only | Public release separately needs current operator GO and required source-specific review; no auth/Hub action here |

### G34. Maintenance, withdrawal and conditional purge

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Release readiness/maintenance; H:60-71; S:91; T:64; W:217 | Dependent shards/projections/derivatives/caches/mirrors/reimports and historical refs | Dependency/ref/object with owned disposition | Named staffed maintenance/takedown owners; suppression survives rebuild/rollback | Source changes trace/suppress and issue new reviewed release/disposition; withdrawal != body purge | Remaining reachable exposure, not claimed complete recall | All scoped current/historical refs/objects plus known recipient copies | Unassigned roles/procedure block release; unresolved purge exposure remains owned | Proposed acknowledgement/scope/current suppression <=24h and scoped purge decision <=72h, pending staffing approval | Separate explicit operator authorization EACH destructive event, inventory/loss/verification plan; independent retired-ref/object readback | Accepted suppressed content critical | Only verified suppression/removal scope | Supported provider mechanism evidence required; private/anonymous denial insufficient; existing client copies cannot be recalled by ref edits; no destruction here |

### G35. Stop, invalidation and receipt validity

| partition/gate | registered cell/domain | independent unit | eligible members | sign/label rule | numerator | denominator | any-member failure rule | minimum supply | confidence/test-budget allocation | critical failure override | population claim | exclusions/missingness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Every transition; S:95-99; T:65-68; W:30,82,120,181,191,213,227; H:58,109; §1, §8 | Exact frozen artifact, design and input/workflow versions | Criterion/stage receipt | All applicable statistical, nonstatistical and original gates, I1-I10 and agreed P1-P9 | PASS/FAIL/UNKNOWN/INCOMPLETE with actor independence/time, digest, denominator, metric/CI and protected receipt locator | Not a rate; complete valid evidence chain | All applicable criteria for the whole terminal outcome | Failed threshold/source/seal/leakage/accounting/identity/rights/reference/scope gate, failed I-gate, U-class or exported X-class member blocks the transition; after two rounds change approach | Fresh proof after material change/exposure; no optional stopping, redraw or repeated final peeking | No post-result threshold/sample change; a STRUCTURALLY_EMPTY endpoint or changed test family needs designated review before selection; a conditional census cannot satisfy an infeasible held-out promise | Critical failures never averaged away | Stage-specific verified outcome only | Residual owner/event explicit; UNKNOWN can describe future evidence but never passes an execution gate; documentation cannot close source/gold/quality obligations; if P1 is not agreed, W:205's unique-group aggregate claim is BLOCKED under its unsupported-transport stop unless I3 shows every closure's union outcome coincides with one tested child outcome (§8); this is a support gap, not an exact contradiction in every overlapping design |

## Gate inventory coverage

| Existing file and lines | Contract tables |
| --- | --- |
| S:3-19 | G01-G05 |
| S:21-34 | G06-G09,G14,G25,G30 |
| S:36-48 | G21-G23,G26,G28-G33 |
| S:50-68 | G12-G20,G25 |
| S:70-78 | G09,G27 |
| S:80-99 | G05,G22-G35 |
| T:3-26 | G02,G06-G09,G27,G30-G31 |
| T:28-45 | G08-G20,G22-G25 |
| T:47-68 | G05,G21-G23,G26-G35 |
| W:3-30 | G03,G05-G09,G21-G23,G26,G35 |
| W:32-51 | G07,G26,G30 |
| W:53-90 | G03,G07-G08 |
| W:92-120 | G08-G11,G24 |
| W:122-181 | G09,G14-G19,G21-G25 |
| W:183-191 | G12-G14,G35 |
| W:193-213 | G15-G20,G24-G25 |
| W:215-227 | G01-G05,G26,G28-G30,G34-G35 |
| H:3-38 | G04-G05,G08-G09,G26,G30-G31 |
| H:40-60 | G28-G34 |
| H:62-91 | G30,G34 |
| H:93-109 | G04,G29-G33,G35 |
| H:111-118 | Existing supporting-reference index; no additional independent pass gate |

Incorporated historical rules are retained by exact incorporation points W:15-28,38-51,114,118,217,227. This preparation does not claim a fresh audit of the linked historical plans, source matrix, component implementations, permissions registers or external specifications. It does not replace their detailed gates with this summary.

## Acceptance-criterion map

| Issue criterion | Contract coverage |
| --- | --- |
| AC-01 | G01 retained; evidence limits in §5 and the decision delta |
| AC-02 | G02 retained; G06 and §1 input gates |
| AC-03 | G03 retained; G06-G26 and §1-§7 for freeze status, member coverage, sampling, inference binding, statistics and judge calibration |
| AC-04 | G04 retained, including the separately owned uploader safety behaviour; G29-G34 |
| AC-05 | G05 retained; designated agreement on P1-P9 is an additional precondition, not a substitute |

## Retained binomial planning examples

[NIST acceptance-sampling guidance](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc21.htm) distinguishes a lot disposition from quality estimation. The [NIST operating-characteristic construction](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc232.htm) specifies acceptable/rejectable rates, producer/consumer risk and `(n,c)`. Its binomial model assumes a sufficiently large lot with independent trials; finite sampling needs a separate check.

These original illustrations retain the C=6, m_rel=35 release example and the pre-P1 m_cal=42 comparison. They are development arithmetic, not the actual frozen design or ratification. With P1, calibration uses m_cal=48 for C=6 and W=3; its pass/fail examples are in §7. Actual child counts, eligible supply, laws M/C and finite N must be verified under §3.7 and G25 before selection. The independent all-pass product below is illustrative only.

| Exact binomial planning quantity | Result |
| --- | ---: |
| Upper bound at x=7, n=2,000, m=35 | 0.951504% |
| Upper bound at x=8, which fails | 1.026759% |
| Per-endpoint P(pass) at p=0.01%, 0.05%, 0.1% | 0.999999999947, 0.999989859878, 0.998911856129 |
| Per-endpoint P(pass) at rejectable p=1% | 0.000745046658 |
| All 35 pass at AQL, **if endpoints independent** | 0.962611119 (false rejection 3.738888%) |
| False-rejection upper bound at AQL, **arbitrary endpoint dependence** | 35 × (1 − 0.998911856129) = 3.808504% |

Endpoint dependence is expected because fields share groups. The independent product is illustrative only; Bonferroni confidence and the union risk bound do not need endpoint independence. They still require valid marginal sampling assumptions. Producer-risk calculations assume no critical failures, correct gold and all other gates satisfied. They do not predict the entire pipeline's actual pass probability. At any rate above pR, the probability of accepting that bad endpoint decreases; the all-pass event is a subset. Report achieved risks, all endpoint estimates and intervals, not just PASS. Acceptance sampling decides release; it is not a substitute for prevalence-weighted quality estimation.

Reproduce the proposed binomial arithmetic with the project interpreter and SciPy; this uses no membership or data:

```python
from scipy.stats import beta, binom

n, c, m = 2000, 7, 35
print("upper at c and c+1", *(beta.ppf(1 - .05/m, x + 1, n - x)
                                 for x in (c, c + 1)))
for p in (.0001, .0005, .001, .01):
    print(p, binom.cdf(c, n, p))
print("independent all-pass", binom.cdf(c, n, .001)**m)
print("producer union bound", m * binom.sf(c, n, .001))
print("calibration one-error upper", beta.ppf(1 - .05/42, 2, 499))
```

## Retained workflow counterexamples

A workflow accepting everything has group false acceptance 100% on a nonempty human-negative pool and fails. A workflow abstaining on everything has zero group answerable coverage and 100% group positive nonacceptance and fails. Deterministic counterexamples must verify both, even with 99.5% natural positive-group prevalence. Within a child or the FULL union scope, a mixed group with one wrong and 999 correct assertions counts once as negative: accepting its wrong member adds one failing group to x and one group to n, never 1,000 independent trials, and the group cannot also supply the positive minimum. Rejecting any one correct answerable member in a positive group likewise yields one group failure. Score critical/false acceptance loss 10, false abstention/other error 1, correct outcome 0, with critical failures disqualifying absolutely. Rank eligible complete workflows by design-weighted human loss; report shared errors and 10,000 paired closure-bootstrap comparisons with familywise adjustment. Inconclusive differences retain the stronger eligible two-family source-verified workflow without declaring the cheap screener a winner. No eligible workflow means stop.

## Release, stopping, and requirement map

Release follows the [private HF design](HF_DATASET_STORAGE_DESIGN.md). Card/Croissant/RAI validation, field-level provenance/licence, exact/near deduplication, pinned build inputs/code/tools/configuration, clean-room hash comparison, same-artifact independent evaluation/review, version mapping and readback all remain required. Source changes and takedowns invalidate dependent exports and trigger suppression plus a new reviewed release/disposition. No bulk deletion is authorized.

| Documentation criterion | Sections and evidence | Remaining owner |
| --- | --- | --- |
| AC-01 | Standard evidence, IAA and contamination sections with primary links | Driver and non-author source/content critics verify interpretation. |
| AC-02 | Standard DoR/five stages/DoD, compact template, this filled plan | Driver validates completeness against the frozen checklist. |
| AC-03 | Authority mapping, preserved fields, freeze status, sampling, statistics and judge calibration | Source lead #10512; separate steward #10514; evaluator #10515. No seal or quality certification is claimed. |
| AC-04 | HF design's custody, capacity, permissions and version mapping | Release owner/operator verify authorized namespace, entitlement and grants before any transfer. |
| AC-05 | PROPOSED status in all documents; standard documentation closeout | Conditional Sol/Opus design agreement is recorded above. Driver obtains separate precommitted held-out execution and fresh critical full-scope exact-head CF on all seven paths, then same-head CI, merge, issue evidence and common cleanup. |

Stop on fabricated seal, source incompleteness, model-written Ukrainian, protected-data access, sample infeasibility, leakage, failed threshold/check, unsupported rights claim, or scope drift. Literal integration and the designated G19 wording correction are the stopping boundary. Any contested finding, fundamental new class, or necessary source/population/labour/policy/schema change stops for the existing operator/designated decision. No third blind prose correction or self-approval is authorized. Future execution evidence may remain UNKNOWN only with owner, resolving event and blocked operation. Retained W2 disagreement, ВТС admission, identity, PULS, full-scale resource and all original residuals stay with their existing lane owners. Current dataset transition remains blocked pending source-completion, valid gold and independent certification evidence. This documentation author delivers a pushed candidate only; independent unseen-checklist proof and approval remain the driver's responsibility.
