# Word-card dataset engineering companion plan

Version: 0.1.0. Status: PROPOSED. This companion applies the [proposed standard](../../best-practices/dataset-engineering.md) and [template](../../best-practices/dataset-plan-template.md) to #8977, #8988, and #8989. It needs designated Sol and Opus agreement and landing before it binds. It neither replaces nor version-resets prior approved plans. No dataset, pilot certification, fresh gold, or release is claimed here.

Documentation issue ancestry: [#10772](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10772) → [#8791](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8791) → [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321). #8977 is the related card programme, not #10772's native parent.

## Outcome and responsibility

The proposed first release is a standalone lexical base for private research collaboration with specifically named UNLP researchers, granted read-only access through a project HF organization. Actual identities, namespace, grants, and entitlement await operator-controlled verification. The consumer is lexical research and deterministic dataset projections under [#8988](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8988) and opt-in historical contrast under [#8989](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8989). It is not training readiness, public distribution, or Atlas rollout.

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

All assertions keep `source_id`, `snapshot_id`, exact `locator`, `licence_ref`, `extraction_version`, attribution, subject/scope, and quality disposition. Evidence units remain separate from accepted facts. Preserve `english_gloss`, `cefr`, examples, collocations, practice eligibility, and all WC-S01–WC-S10 source-role obligations as existing scope/later obligations; this slice does not erase or generate them.

The full source denominator is **UNKNOWN**. Owner: open-model-data source-inventory lead. Resolving event: #10512 complete-data receipt and #9401 frozen source matrix, with per-source versions/checksums, required ranges, all source-unit counts, and independent reconciliation. Freeze source units, spellings, lexemes, senses, MWEs, forms, and cards separately. Every unit ends once as accepted, held, withheld with reason, or excluded with reason. Counts in old designs describe their historical snapshots, not current full coverage.

Retain the existing mechanics inventory's 150 source-local units, 272 selected literal rows, 114 legacy allocation projections, and 140 aliases as separate historical denominators from migration §3. Its 22 source-only correspondence gaps remain unresolved there, not silently allocated. Recheck actual manifests before any future build. Preserve the later PULS A1–B1 obligation of 4,512 rows, including 962 + 1,386 + 2,164 level rows, and many-to-many VESUM accounting. PULS coverage is not a first mechanics-fixture gate. Retain W2's unexplained-disagreement stop rule, W3 unit-by-unit equivalence, W4 withdrawal/changed-snapshot/rollback and redirect/split/rebuild identity checks, W5 contrast checks, and RB-1 P1–P6 and component-specific gates.

## Freeze status and fresh-gold prerequisites

Metadata observation supplied by the driver at `2026-10-16T03:04:49Z`: **NOT VERIFIED; no admitted W0/Gate 2 seal established; manifest SHA unavailable; freeze date unavailable**. This observation covers tracked `registry/atlas` metadata, the existing evaluation verifier, and the driver's bounded filename-only scan of `tests/golden` and local agent metadata. It does not establish global absence. No protected membership or answers were opened. The 150-unit fixture digest and unrelated RB-1 held-out receipts cannot substitute for a card-gold seal.

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

The historical 220-case gate, its 200 hard cases plus 20 ordinary controls, category composition, expansion counts, replay checks, and coverage/error/abstention/variant-conflict metrics remain traceable obligations under migration §4. Current disposition makes all old 220 development-only; its former approximately 60/40 replay/held-out description proves no untouched final evidence today. Proposed fresh samples below are additional evidence, not a silent replacement or relabelling of that obligation. The driver must reconcile the retained gate with #10514/#10515 before certification and cannot report Gate 2 passed on development regressions.

## Proposed sampling and numeric criteria

These numbers are **proposed project choices pending approval and source-inventory feasibility**, not universal research thresholds. No sample is selected here. The risk rationale is strict source fidelity and identity attachment, with separate estimates for stress and sense-bound fields. A row is a scored field assertion or expected abstention; the independent sampling unit is a closure group of related source records, aliases, lexeme families and derivations. Count each group once for binomial endpoints, marking it failed if any scored member fails. Do not count inflected forms as independent trials.

Freeze the cluster graph, source/author/book boundaries, sampling frame, inclusion probabilities, weights, and seed `10772` before selection. Keep all members in one partition. Book/author/source holdout applies to claims of unseen-source transfer. The proposed initial evaluation concerns extraction from known pinned sources; it makes no unseen-book or unseen-dictionary claim. Authors cannot access protected selected closures. The steward runs the frozen assembler against protected evaluation inputs and retains outputs, membership and labels separately from author-accessible development data. If source completion and custody cannot support these boundaries, stop and return the infeasible design to the driver.

Planning strata are morphology/identity, stress, meanings, synonyms/antonyms, phraseology/MWEs, and opt-in historical contrast. Freeze actual **field × source × risk** cells after the inventory. Do not let a large ULIF stratum hide a small supplementary source. The six-cell examples below are minimum planning budgets, not a declaration of six actual source cells or a full coverage denominator. Additional cells increase the budget before gold selection.

| Partition / artifact | Proposed size and selection | Use and passing rule |
| --- | --- | --- |
| Disclosed annotation training | 60 independent groups, 10 per planning stratum, authentic source evidence | Train human annotators on rubric; never reuse for judge ranking or certification. No inference about population quality. |
| Sealed judge calibration | 600 fresh independent groups, initially 100 per planning stratum, disjoint from all other partitions | Compare at most three preregistered judge configurations against independently human-labelled evidence. Freeze selection before certification. Cell-specific imprecision can fail selection. |
| Actual dataset-quality pilot | 300 development groups, initially 50 per stratum, sampled after admitted seal; disjoint from gold | Inspect all pilot output for citations/identity, dispositions, deterministic rebuild and must-fail controls. Zero critical failures, zero lost/duplicate units, and 100% required provenance. This is distinct from the 150-unit mechanics inventory. |
| Independent pilot-certification inputs | 600 new sealed groups, initially 100 per stratum, separate from calibration and final test | Independent #10515 evaluation of the frozen pilot implementation/configuration and pilot artifact receipts. Five pooled binary endpoints below have one-sided simultaneous 95% upper error bounds ≤1%; every cell has zero observed critical failures. Cell CIs remain explicit and limited. |
| Untouched final release test | At least 700 independent groups per registered field/source/risk cell; six-cell planning minimum 4,200 | Evaluate only the frozen selected pipeline and exact scaled release. For up to 30 registered binary tests, require simultaneous one-sided 95% upper error bounds ≤1% for every test and zero observed critical failures. More tests require a new preregistered sample budget. |

Pilot certification's five binary endpoints are wrong identity attachment, wrong asserted value, invalid citation/source binding, incorrect abstention decision, and accounting/eligibility violation. The full 300-group pilot also receives a census for source fidelity and applicable existing controls. Passing pooled certification does not certify every source cell to 1%; the final stage adds cell-level evidence. Every pilot-certification source/field cell is reported with its denominator and CI, including zero-error cells. Gold cases contain appropriate absent/conflict/withheld outcomes as well as positive facts. Critical failures include invented Ukrainian, wrong homonym/sense attachment, unsupported definition, reversed correction, gold leakage, and accepted suppressed content; any occurrence fails regardless of aggregate score.

For the final test, preregister endpoint applicability by cell without consulting results. If a source has too few independent groups, use a full census of that finite cell with independent source-based review, report its actual finite denominator, and limit the claim to that snapshot. Do not reuse related records to reach 700 or silently drop a cell. Inability to support the promised claim blocks release of that scope and returns to the driver; it does not shrink the mission unilaterally.

Each sampled group stays in the scoring denominator. A missing human label makes that gate INCOMPLETE. A model abstention on a human-answerable item is an error; an abstention on a human-confirmed unresolved item can be correct. Report coverage and false acceptance separately, with confusion matrices by field/source. Human unresolved evidence is a visible gold outcome, not an invented answer. Only justified not-applicable fields have a preregistered separate denominator.

## Statistical specification and arithmetic

Report raw human agreement, nominal Krippendorff alpha before adjudication, label prevalence/marginals and missingness. Use 10,000 stratified cluster bootstrap resamples, seed `10772`, for alpha, weighted quality estimates and paired judge differences. Preserve related records and judge pairs in each resampled group. Use two-sided 95% percentile intervals and disclose estimator limitations or degenerate/undefined intervals. Require alpha lower bound ≥0.80 for human rubric reliability; otherwise refine on disclosed training/calibration and refreeze before certification. Alpha is a reliability measure, not a correctness certificate. See [IAA references in the standard](../../best-practices/dataset-engineering.md#annotation-reliability-and-judge-selection).

For gate binary group-failure proportions, use one-sided Clopper-Pearson bounds with Bonferroni `alpha = 0.05/m`, where `m` is the frozen number of simultaneous tests. A zero-error bootstrap alone is inadequate. For zero failures the upper bound is `1 - (0.05/m)**(1/n)`. At certification `m=5`, `n=600`, the bound is 0.7646%, below the proposed 1% pooled limit. An individual zero-error cell of 100 has unadjusted 95% upper risk 2.9513%, so this pilot result cannot establish a 1% cell guarantee.

At final evaluation `m=30`, `n=700` per tested cell, zero errors gives upper risk **0.9097%**, below 1%. At least **637** independent groups are needed for this zero-error bound; 700 leaves margin, but some nonzero outcomes will still fail. For an unadjusted single endpoint, zero errors among 150 gives upper risk **1.9773%**, among 220 **1.3525%**, and among 4,200 **0.0713%**. The pooled 4,200 bound cannot replace the simultaneous per-cell bounds. Under simple independent sampling, the worst-case normal 95% half-width is about 4.00 percentage points at 600 and 1.51 points at 4,200; these are planning approximations, not the gate estimator or proof of representativeness. Cluster/stratum weights may increase uncertainty.

The calculations are reproducible with the project interpreter and standard library:

```python
import math

for n, m in [(100, 1), (150, 1), (220, 1), (600, 5), (700, 30), (4200, 1)]:
    print(n, m, round(100 * (1 - (0.05 / m) ** (1 / n)), 4))
print(math.ceil(math.log(0.05 / 30) / math.log(0.99)))
```

Freeze exact finite-population sizes, weights, cluster design and number of tests before creating gold. If that changes the estimand or required sample, re-review the specification before sampling. No optional stopping, repeated final peeking, or adding cases until a CI passes. A failed certification/final test stops the transition. After repair, exposed cases become disclosed regressions and an independent steward supplies fresh evidence for a newly frozen evaluation under the original scope and thresholds.

## Judge calibration against human labels

Gemini 3.8 Flash is only a proposed inexpensive first-pass fixed-rubric screener until measured selection. Per-record acceptance requires two independent model families plus VESUM/Sources checks for the relevant facets; human-gold construction remains independent of all model judgements. Models cannot write Ukrainian facts or replace human annotation. Source occurrence alone is not facet-specific normative evidence.

Before opening calibration, register at most three candidate configurations, exact model/harness attestation, prompt/rubric/parser/tool versions and comparison budget. Candidates must use the same admissible source evidence and label schema. Measure each judge against two independent qualified humans, with a third human adjudicating disagreements from authentic evidence, blind to model outputs. Preserve both original human labels and adjudicated outcomes. Human gold is not two-model consensus.

Rank eligible configurations by human-label agreement after these proposed gates: zero critical failures, answerable coverage ≥95%, and simultaneous one-sided 95% upper bound on false acceptance ≤2%. Use nine calibration tests for three configurations across error, false acceptance, and abstention endpoints; score all 600 groups and count incorrect/unsupported abstentions. Report all cell results and CIs. Preregister loss as 10 for critical/false acceptance, 1 for false abstention or other incorrect label, and 0 for correct outcomes; critical failures still disqualify absolutely. Choose the lowest weighted loss among eligible candidates. Bootstrap paired loss differences with all three comparisons adjusted to family-wise 95% confidence. If differences are inconclusive, retain the stronger eligible source-verified two-family workflow rather than claim a winning cheap screener. If no candidate qualifies, stop selection. Coverage and abstention costs prevent a model from winning by refusing everything.

Calibration is the only partition for candidate ranking or rubric/prompt tuning. Freeze the winner and all associated hashes before independent pilot certification. Neither pilot certification nor the final release test may rank candidates or tune prompts. The untouched final partition measures the frozen selection on the exact scaled artifact. If any protected labels or membership become exposed, invalidate affected proof and refer fresh selection to the independent steward; do not inspect protected payloads to diagnose this documentation task.

## Release, stopping, and requirement map

Release follows the [private HF design](HF_DATASET_STORAGE_DESIGN.md). Card/Croissant/RAI validation, field-level provenance/licence, exact/near deduplication, pinned build inputs/code/tools/configuration, clean-room hash comparison, same-artifact independent evaluation/review, version mapping and readback all remain required. Source changes and takedowns invalidate dependent exports and trigger suppression plus a new reviewed release/disposition. No bulk deletion is authorized.

| Documentation criterion | Sections and evidence | Remaining owner |
| --- | --- | --- |
| AC-01 | Standard evidence, IAA and contamination sections with primary links | Driver and non-author source/content critics verify interpretation. |
| AC-02 | Standard DoR/five stages/DoD, compact template, this filled plan | Driver validates completeness against the frozen checklist. |
| AC-03 | Authority mapping, preserved fields, freeze status, sampling, statistics and judge calibration | Source lead #10512; separate steward #10514; evaluator #10515. No seal or quality certification is claimed. |
| AC-04 | HF design's custody, capacity, permissions and version mapping | Release owner/operator verify authorized namespace, entitlement and grants before any transfer. |
| AC-05 | PROPOSED status in all documents; standard documentation closeout | Driver obtains distinct Sol content criticism, Opus agreement and exact-head CF, then same-head CI, merge, issue evidence and common cleanup. |

Stop on fabricated seal, source incompleteness, model-written Ukrainian, protected-data access, sample infeasibility, leakage, failed threshold/check, unsupported rights claim, or scope drift. After two review rounds with material blockers, change approach with the driver without reducing thresholds or denominators. Retained W2 disagreement, ВТС admission, identity, PULS, full-scale resource and all original residuals stay with their existing lane owners. Current dataset transition remains blocked pending source-completion, valid gold and independent certification evidence. This documentation author delivers a pushed candidate only; independent unseen-checklist proof and approval remain the driver's responsibility.
