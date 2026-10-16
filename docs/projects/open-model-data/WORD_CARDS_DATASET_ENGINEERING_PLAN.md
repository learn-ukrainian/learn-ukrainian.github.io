# Word-card dataset engineering companion plan

Version: 0.2.0. Status: PROPOSED. This companion applies the [proposed standard](../../best-practices/dataset-engineering.md) and [template](../../best-practices/dataset-plan-template.md) to #8977, #8988, and #8989. It needs designated Sol and Opus agreement and landing before it binds. It neither replaces nor version-resets prior approved plans. No dataset, pilot certification, fresh gold, or release is claimed here.

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

All assertions keep `source_id`, `snapshot_id`, exact `locator`, `licence_ref`, `extraction_version`, attribution, subject/scope, and quality disposition. Evidence units remain separate from accepted facts. Preserve `english_gloss`, `cefr`, examples, collocations, practice eligibility, and all WC-S01–WC-S10 source-role obligations as existing scope/later obligations; this slice does not erase or generate them.

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

## Proposed sampling and numeric criteria

Numbers below remain PROPOSED pending both reviewers, inventory feasibility and authenticated ratification. They preserve the quality bars while replacing the original underpowered zero-error design. A row is a field assertion or expected abstention. The independent sampling unit is a closure group of related source records, aliases, lexeme families and derivations. A group fails an endpoint if any scored member fails. Report **group error rates separately from record/field rates**; many forms in one group are not independent trials.

Freeze the closure graph, source/author/book boundaries, sampling frame, inclusion probabilities, weights and scoring rules. Public seed `10772` may reproduce arithmetic or bootstrap resampling of safe aggregates. **Protected membership selection uses steward-controlled private random draw state**, never a public seed or reconstructible author-accessible manifest. Keep that draw state, membership and answers private. Authors cannot reconstruct membership from released complements. No current selection is authorized.

The initial claim concerns extraction from known pinned sources, not unseen-source transfer. Freeze actual field × source × risk cells after #10512. Six planning cells are morphology/identity, stress, meanings, synonyms/antonyms, phraseology/MWEs and opt-in historical contrast. They are budget examples, not the final inventory. A source-specific small cell cannot hide in a large ULIF pool. Freeze endpoint applicability before selection, with enough eligible independent groups for each endpoint. Extra cells require a new reviewed budget before gold creation.

| Partition / artifact | Proposed independent groups | Use and boundary |
| --- | --- | --- |
| Annotation training | 60, initially 10 per planning cell | Disclosed authentic-source rubric training only. |
| Fresh structural Gate 2 | Exactly 220 cases above, with closure accounting recorded separately | 132 exposed replay plus 88 protected structural cases. No overlap with any partition below or training. Not a field-quality estimator. |
| Sealed workflow calibration | 600 probability-sampled groups, initially 100 per cell, plus an independent enrichment frame yielding ≥500 human-negative and ≥500 human-positive groups per cell | At least 6,600 groups across six cells; three complete workflows maximum. Source-labelled negatives, sampling weights and fixed screening budget below. No final-proof reuse. |
| Dataset-quality pilot | 300 development groups, initially 50 per cell, after admitted seal | Full independent source-fidelity inspection, provenance and accounting census; zero critical failures, zero lost/duplicate units and 100% required provenance. Distinct from mechanics150. |
| Independent pilot certification | 2,000 fresh sealed groups, probability-sampled from the frozen eligible frame | #10515 evaluates frozen implementation and pilot receipts. Five pooled endpoints; each has n=2,000. Every source/field cell also reports counts and CIs without a 1% cell claim. |
| Untouched final release audit | 2,000 fresh sealed groups per registered field/source/risk cell; six-cell minimum 12,000 | Frozen workflow on exact scaled artifact. Five endpoints per cell, up to 30 tests in the initial budget. No selection/tuning. |

All partitions are disjoint by closure, including the structural replay pool, training and pilot. The fresh 88-case structural pool is first evaluated alongside independent pilot certification; it is never relabelled as the final release audit. Its source-backed labels, and all calibration/certification/final labels, are prepared independently before the quality pilot under the admitted seal. Source-complete selection and source evidence, not old cases or assembler rules, define gold. Failures cannot tune an already exposed partition into new proof.

Pilot/final binary endpoints are wrong identity attachment, wrong asserted value, invalid citation/source binding, incorrect abstention decision, and accounting/eligibility violation. Score each eligible group on all five frozen decision questions, including expected withholding/absence. Missing required human labels make the gate INCOMPLETE. Abstention on human-answerable evidence is an error; human-confirmed unresolved evidence is a legitimate gold outcome. Preregister truly not-applicable fields and their separate counts; n cannot include them for an inapplicable endpoint.

Critical failures include invented Ukrainian, wrong homonym/sense attachment, unsupported definition, reversed correction, gold leakage and accepted suppressed content. **Any observed critical failure fails absolutely**, even if a statistical endpoint allows noncritical errors. No sample proves an absolute population absence of critical failures.

### Acceptance sampling and quality estimation

[NIST acceptance-sampling guidance](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc21.htm) distinguishes a lot disposition from quality estimation. The [NIST operating-characteristic construction](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc232.htm) specifies acceptable/rejectable rates, producer/consumer risk and `(n,c)`. Its binomial model assumes a sufficiently large lot with independent trials; finite sampling needs a separate check.

Recommend for noncritical group failures: acceptable quality level AQL `pA=0.001` (0.1%), rejectable level `pR=0.01` (1%), family producer risk ≤5%, and consumer risk ≤`0.05/35` for each bad endpoint. These planning points do not weaken the **≤1% simultaneous one-sided upper error bound at 95% familywise confidence**. Ratification remains required.

Use `n=2,000, c=7` for each endpoint. Freeze `m=35` across five pooled certification and thirty final-cell endpoints, with Bonferroni `a=0.05/35`. Accept only if every endpoint has `x≤7`, its exact Clopper-Pearson upper bound is ≤1%, and all nonstatistical/critical gates pass. For `x>0`, compute `beta.ppf(1-a, x+1, n-x)`; for zero use `1-a**(1/n)`, and for `x=n` use 1. Check both c=7 and c=8 explicitly, rather than assume allowing errors meets the bound.

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

Before ratification, the steward/statistician must verify finite sizes `N`, closure disjointness, remaining pool after all earlier allocations, sampling fractions and human-negative supply. For sampling without replacement, calculate `hypergeom.cdf(c, N, D, n)` at preregistered integer defective counts bracketing `N*pA` and `N*pR`, and invert exact hypergeometric tails for finite-snapshot bounds. Verify producer/consumer limits and ≤1% simultaneous bounds for that actual design. Weighted or unequal-probability counts cannot be passed into binomial formulas as though independent unweighted trials. More than 35 tests, smaller eligible n or a changed design needs re-review and recalculated n/c before selection, never post-result extensions.

If a finite cell cannot supply the protected disjoint samples, stop the sampled claim. A proposed fallback is an **independently blind, source-grounded census labelling of the exact artifact's source universe**, before comparison with assembler outputs, under #10514 isolation. It can verify that one finite snapshot and report exact counts; it cannot establish independent-sample inference, unseen-source transfer or a held-out claim when the pool overlaps calibration. The census is a separate conditional proposal requiring designated review of feasibility and isolation, not automatic permission to waive disjointness. A small census cannot satisfy an infeasible held-out promise.

### Human reliability, dispute handling and capacity

Two qualified humans independently label each group's expected source-to-identity mapping, field values and validity/answerability disposition from authenticated evidence, blind to assembler/model outputs. The alpha rating unit is a group × applicable field decision with nominal categories `supported`, `unsupported`, `source-unresolved`; identity/variant/conflict decisions are separately typed tasks. Report pre-adjudication raw agreement, nominal Krippendorff alpha with 10,000 stratified closure bootstrap resamples, seed `10772`, and two-sided 95% intervals by task. Require alpha lower bound ≥0.80; refine only on disclosed training/calibration before refreeze. Report prevalence, skew, marginals, missing pairs and undefined coefficients. An undefined coefficient never earns a perfect score or passes that requirement. Reliability is not accuracy; authentic-source review supplies correctness evidence.

Preserve both original labels and source references. A third qualified independent human adjudicates initial disagreements without model outputs. For suspected gold or candidate/gold disputes, a separate blind reader sees competing outcomes **unlabelled and randomly ordered**, with authentic source evidence; the reader is not told which outcome came from the candidate or old gold. Audit a private random 10% of agreements by the same source-grounded procedure. Retain pre-adjudication labels, decisions, rationale, version and all affected counts. The steward investigates systematic label errors. Confirmed final-gold corrections invalidate the affected frozen test and require independently reviewed refreeze/fresh proof; never select an outcome to improve candidate scores or silently rescore until passing.

The six-cell planning minimum is **21,180 groups/cases**: 60 + 220 + 6,600 + 300 + 2,000 + 12,000, before extra cells, replacement or expansion work. The 60,000-group screening ceiling includes up to 6,000 selected calibration groups, so budgeting every screened group adds up to 54,000 labels-in-pairs plus adjudication units beyond this minimum; screen these independently even when most are correct. Gate 2 cases may expand to more work and cannot be counted as a measured closure count. Budget two human labels for every unit plus adjudication and agreement audits. Planning assumption: 4–8 minutes per independent label, 10–20 minutes per adjudication, 10–20% initial disagreement plus 10% of remaining agreements audited. This implies about **3,494.7–7,624.8 human hours** at the minimum, or **12,404.7–27,064.8 hours** if all 60,000 screening groups are used and no extras beyond that ceiling are needed. Both ranges exclude expansion/specialist overhead and are planning assumptions, not measured capacity or an execution commitment.

The annotation lead must measure task/stratum timing in disclosed training, retain uncertainty and specialist availability, name both labelers and the adjudicator/independent dispute reader, and secure the resulting hours before threshold ratification/execution. The driver appoints that lead and steward; staffing is presently UNKNOWN. The source lead certifies pool size; the steward reserves fresh replacements and a fixed negative-screening budget before selection. Stop before exhaustion, unaffordable human work, unfilled roles or inadequate negative counts. No repeated final peeking, optional stopping or adding cases until a CI passes. A failed certification/final gate stops; repairs require a newly frozen evaluation and fresh steward-controlled proof, with capacity checked again.

## Calibration of complete acceptance workflows

The selection unit is the **complete acceptance workflow**: both independent model families, source/VESUM tools, rules, routing, combination logic and any screener. Gemini 3.8 Flash can be an inexpensive fixed-rubric first-pass screener only if that exact placement is calibrated as part of the whole workflow. A cheap single judge cannot win acceptance authority. No model writes Ukrainian facts or supplies human truth. Measure correlated/shared wrong decisions of both families and the combined workflow against independent humans.

Register at most three workflows with exact model/harness attestations and prompt/rubric/parser/tool/combination versions. The steward independently draws the same calibration frame for all workflows, excluding every other partition and closure. Humans label authenticated source expectations before seeing workflow outputs. Candidate assertions judged wrong by humans are **human-negative candidate outputs**; false acceptance is `accepted human-negative outputs / all human-negative outputs`, never divided by all 600 probability-panel groups. Sensitivity is accepted human-positive outputs / human-positive outputs; specificity is nonaccepted human-negative outputs / human-negative outputs. Report reject versus abstain separately in each denominator, plus incorrect values and false abstentions on human-answerable cases. Missing labels mean incomplete, not exclusion.

Proposed enrichment oversamples independently defined source × risk cells, with simple random screening and sign-conditional draws within each cell, without using model accept/reject decisions to choose cases. Before any candidate runs, the steward freezes source-backed expectations and privately draws a maximum screening frame of **10,000 independent closure groups per planning cell**. Against those expectations, independent humans classify the frozen assembler's candidate assertions, blind to all judge-workflow decisions. Source evidence defines truth, never model consensus. From this labelled frame draw ≥500 human-negative and ≥500 human-positive groups per cell at random, without other partition overlap. Every complete workflow sees the same assertions. Record both screening and conditional-draw probabilities and weights. Stop INCOMPLETE if the fixed frame cannot provide a required sign/cell; the 10,000 cap is a proposed labour ceiling, not evidence that 500 negatives exist. Low natural error rates may make this design infeasible, requiring a reviewed new design before selection, not repeated mining until passing.

Known development negative witnesses never count toward these fresh denominators. Independently constructed source-literal misattachment challenges can supplement failure testing, but report them separately: they cannot supply natural-negative counts, prevalence or final held-out performance. The conditional-rate gate refers to human-confirmed negatives in the frozen assembler output distribution within registered strata. Inclusion weights transport the stratified sample only to its registered source/risk frame; an unrepresented error mechanism remains unresolved.

The separate 600-group probability panel estimates natural prevalence and aggregate performance without negative enrichment. Retain frame counts and `weight=1/inclusion_probability` for every stratum and the labelled screening stage. Report prevalence-weighted aggregate error/abstention and intervals, weighted loss, and deployment-prevalence sensitivity on the binary candidate-assertion frame: `P(accept) = sensitivity*(1-negative_prevalence) + false_acceptance*negative_prevalence`. Human-negative includes unsupported assertions where the source requires withholding; correct withholding outputs and source-unresolved decisions are reported separately, with their own population mass, never silently removed from the overall panel. Unknown prevalence gives a stated range, never an unweighted enriched accuracy advertised as population accuracy. Use stratified closure bootstrap CIs for weighted summaries, with degenerate rare-error limits disclosed; use conservative bounds from simultaneous stratum intervals where bootstrap degenerates. Register aggregate limits as false acceptance among all outputs ≤`0.02 * negative_prevalence` and positive nonacceptance ≤`0.05 * positive_answerable_prevalence`, while retaining the conditional ≤2% and coverage ≥95% gates in every cell. Compute aggregate upper bounds as nonnegative prevalence-weighted sums of simultaneous cell bounds; propagate uncertainty in prevalence using simultaneous prevalence intervals from the independent probability panel. Report both prevalence intervals and worst-case aggregate limits over them. Inadequate prevalence precision or an unsupported transport assumption blocks the aggregate claim, even when challenge accuracy is high.

Eligibility retains zero critical failures, answerable coverage ≥95%, and simultaneous one-sided 95% upper false acceptance ≤2%. Require that false-acceptance bound in **each** of six cells and each workflow, plus an upper bound ≤5% for nonacceptance of human-positive answerable groups (which also bounds false abstention). Use `m=42`: 36 conditional tests for three workflows × six cells × two rates, plus six two-sided exact negative-prevalence intervals from the independent probability panel. Allocate error probability `0.05/42` per interval so the aggregate inputs also have simultaneous 95% coverage. With n=500 per sign/cell, one false acceptance gives an exact upper bound of 1.793530%, below 2%; compute the exact c>0 limit for every observed count. Nonacceptance includes both rejects and abstentions. No negative or positive denominator may be borrowed from the 600-group panel or a different cell to reach its minimum. Additional cells/candidates require preregistered adjustment and reviewed capacity.

A workflow accepting everything has conditional false acceptance 100% on a nonempty human-negative pool and fails. A workflow abstaining on everything has zero answerable coverage and 100% positive nonacceptance and fails. Deterministic counterexamples must verify both, even with 99.5% natural positive prevalence. Score critical/false acceptance loss 10, false abstention/other error 1, correct outcome 0, with critical failures disqualifying absolutely. Rank eligible complete workflows by design-weighted human loss; report shared errors and 10,000 paired closure-bootstrap comparisons with familywise adjustment. Inconclusive differences retain the stronger eligible two-family source-verified workflow without declaring the cheap screener a winner. No eligible workflow means stop.

Only calibration may rank candidates or tune prompts/rubrics. Freeze the selected entire workflow and hashes before certification. Exposed calibration negatives are not final held-out proof. Pilot-certification and final audits cannot select configurations. Any protected exposure invalidates affected proof and goes to the independent steward; authors never inspect protected payloads for this documentation correction.

## Release, stopping, and requirement map

Release follows the [private HF design](HF_DATASET_STORAGE_DESIGN.md). Card/Croissant/RAI validation, field-level provenance/licence, exact/near deduplication, pinned build inputs/code/tools/configuration, clean-room hash comparison, same-artifact independent evaluation/review, version mapping and readback all remain required. Source changes and takedowns invalidate dependent exports and trigger suppression plus a new reviewed release/disposition. No bulk deletion is authorized.

| Documentation criterion | Sections and evidence | Remaining owner |
| --- | --- | --- |
| AC-01 | Standard evidence, IAA and contamination sections with primary links | Driver and non-author source/content critics verify interpretation. |
| AC-02 | Standard DoR/five stages/DoD, compact template, this filled plan | Driver validates completeness against the frozen checklist. |
| AC-03 | Authority mapping, preserved fields, freeze status, sampling, statistics and judge calibration | Source lead #10512; separate steward #10514; evaluator #10515. No seal or quality certification is claimed. |
| AC-04 | HF design's custody, capacity, permissions and version mapping | Release owner/operator verify authorized namespace, entitlement and grants before any transfer. |
| AC-05 | PROPOSED status in all documents; standard documentation closeout | Driver obtains distinct Sol content criticism, Opus agreement and exact-head CF, then same-head CI, merge, issue evidence and common cleanup. |

Stop on fabricated seal, source incompleteness, model-written Ukrainian, protected-data access, sample infeasibility, leakage, failed threshold/check, unsupported rights claim, or scope drift. This is content-fix round 1 after two independent initial critics. All known HIGH/MEDIUM findings block agreement until resolved; future execution evidence may remain UNKNOWN only with owner, resolving event and blocked operation. After two content-fix rounds with unresolved or new material classes, change approach with the driver without reducing thresholds or denominators. Retained W2 disagreement, ВТС admission, identity, PULS, full-scale resource and all original residuals stay with their existing lane owners. Current dataset transition remains blocked pending source-completion, valid gold and independent certification evidence. This documentation author delivers a pushed candidate only; independent unseen-checklist proof and approval remain the driver's responsibility.
