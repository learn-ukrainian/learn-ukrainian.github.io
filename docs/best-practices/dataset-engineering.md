# Dataset engineering standard

Version: 0.2.0. Status: PROPOSED under [#10772](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10772). This proposal becomes binding only after designated Sol and Opus agreement and proper landing. It does not approve a dataset, a new architecture, paid execution, or publication. Existing stronger project gates remain prerequisites.

Use the [plan template](dataset-plan-template.md), the [word-card companion plan](../projects/open-model-data/WORD_CARDS_DATASET_ENGINEERING_PLAN.md), and the [private storage proposal](../projects/open-model-data/HF_DATASET_STORAGE_DESIGN.md). The smallest adequate implementation is a filled plan and evidence from existing builders and validators. This standard requires no new orchestration framework.

## Evidence and applicability

The cited work supports documentation and evaluation practices. It does not prescribe this project's sample sizes, accuracy thresholds, approval routes, or source rights.

| Evidence | Supported practice and boundary |
| --- | --- |
| [Gebru et al., Datasheets for Datasets](https://arxiv.org/abs/1803.09010) | Document motivation, composition, collection, processing, uses, distribution, and maintenance. A completed datasheet is disclosure, not measured quality. |
| [Pushkarna et al., Data Cards](https://arxiv.org/abs/2204.01075), [primary Google publication](https://research.google/pubs/data-cards-purposeful-and-transparent-dataset-documentation-for-responsible-ai/) | Explain upstream choices and their rationale for the people who use and maintain the data. |
| [HF Dataset Cards](https://huggingface.co/docs/hub/datasets-cards) | A repository README presents its card; YAML metadata describes language, licence, and dataset configuration. Discovery metadata cannot establish permission or correctness. |
| [Croissant core](https://docs.mlcommons.org/croissant/docs/croissant-spec.html) | Describe machine-readable distributions, record sets, fields, and their sources. Validate against a pinned specification and validator. |
| [Croissant-RAI](https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html) | Record collection, annotation, use, limitations, biases, sensitive information, and maintenance. Do not substitute a generated stub for substantive answers. |
| [NeurIPS checklist](https://neurips.cc/public/guides/PaperChecklist) | State claim limits, uncertainty, reproducibility, and ethical considerations with supporting evidence. It is a conference checklist, not project authorization. |
| [2026 Evaluations and Datasets reviewer guidelines](https://neurips.cc/Conferences/2026/EvaluationsDatasetsReviewerGuidelines), [2026 hosting requirements](https://neurips.cc/Conferences/2026/EvaluationsDatasetsHosting) | Dataset contributions require accessible data and Croissant core plus minimal RAI metadata; reviewers examine evaluative purpose and documentation. HF-hosted data must be public at submission; accepted datasets must be public by camera-ready. Private research release here does not claim conference compliance. The former 2025 Datasets and Benchmarks rules are historical lineage, not current policy. |

## Definition of Ready

Before an actual dataset-quality pilot, the accountable driver freezes a plan with all of the following information. Missing evidence blocks the relevant transition. An UNKNOWN denominator blocks representative sampling until the inventory owner resolves it.

- Intended use, prohibited use, named consumer, user-visible outcome, scope, non-goals, version, and acceptance-criterion IDs.
- Record definition and independent source-unit definition. Count source rows, identities, records, fields, and splits separately. Freeze the universe and each source/field/stratum denominator with checksums and a conservation equation.
- Source inventory with exact edition, snapshot/version, checksum, acquisition locator, authoritative facet, licence record, attribution, and separate internal-use and redistribution dispositions. Preserve field-level dependencies for mixed-source records. Authorized internal acquisition/use is already decided; public redistribution review is a separate requirement of this task.
- An independently human-labelled golden evaluation set, frozen and sealed before dataset-quality construction. Name its separate steward, human adjudicators, source evidence, protected membership/answer custody, access policy, isolation tests, and authenticated seal receipt. Authors receive no protected membership or answers. A hash without authority and access isolation is insufficient.
- Disclosed development and annotation-training data, sealed calibration data, independent pilot-certification inputs, and an untouched final release test. Keep all partitions disjoint across related identities. Calibration may select judges or rubrics; the final release test never selects either.
- A preregistered acceptance-sampling plan with acceptable/rejectable quality levels, producer/consumer risks, n/c, operating-characteristic probabilities, endpoint dependence and finite-population feasibility. Preserve separate quality estimation and simultaneous error bounds. Budget two human labels, blind dispute adjudication, agreement audits and fresh-pool capacity before ratification.
- A fixed rubric with error classes, critical failures, abstentions, missing-label handling, numeric acceptance thresholds, sample sizes, confidence levels, statistical methods, sampling strata, inclusion probabilities, and risk/precision rationale. Preregister these before looking at evaluation results. There is no universal accuracy cutoff.
- Pilot size, selection algorithm and steward-controlled private draw state for protected membership, required failure strata, independent units, and an accounting policy for excluded or withheld material. A pilot must test semantic adequacy as well as mechanics.
- Named accountable driver, source/inventory owner, extraction author, annotation lead, gold steward, independent evaluator, release owner, maintenance owner, and takedown owner. Record actual assigned identities before execution; a role name alone is not an assignment.
- Stop conditions, review-round limit, residual owner and concrete unblocking event, reproduction procedure, release target and visibility, existing prerequisite gates, and typed receipt locations/digests.

## Five stages and their transitions

The dataset pipeline is exactly **pilot → measured gate → scaled build → independent evaluation → publish**. Source completion and the admitted human-gold seal are entry prerequisites, not optional later stages. Existing source, identity, certification, review, and publication gates add conditions to these transitions.

| Stage | Entry and work | Measured exit and exact receipt |
| --- | --- | --- |
| Pilot | All applicable DoR entries and gold seal pass. Construct only the frozen pilot sample with pinned inputs/code/configuration. Use cited source extraction, with no invented Ukrainian. | Pilot artifact digest, source-unit/record/field counts and dispositions, source locators, reproducibility comparison, semantic review results, and pilot-selection receipt. A schema or successful transport alone does not pass. |
| Measured gate | Independently evaluate the frozen pilot implementation and artifact against preregistered pilot-certification inputs; apply any stronger existing pilot-certification requirement. | Signed pass/fail report with thresholds, counts, CIs, strata, disagreements, abstentions, contamination and access checks, artifact/code/input digests, and independent reviewer identity. Failure stops scale. |
| Scaled build | Pilot gate and every original prerequisite pass. Freeze selected judge/rubric/prompt/parser/tool versions; build from pinned sources with bounded resources and resume checks. | Full accounting, exact/near dedup report, provenance/licence validation, complete artifact/shard digests, build manifest, and independent clean-room hash comparison. These prove construction, not release quality. |
| Independent evaluation | Evaluator has the exact scaled release artifact and the untouched final human-labelled partition. Authors cannot inspect protected inputs, membership, or answers. | Same-artifact semantic results for every preregistered endpoint and stratum, uncertainty and failure report, isolation/access receipt, and release recommendation. A changed artifact or selection invalidates this proof. |
| Publish | Evaluation, original gates, same-artifact independent review, metadata validation, capacity/access checks, and release-specific authorization all pass. Private collaboration and public release have different permissions. | Versioned private HF tag plus resolved commit and content digests, release mapping, card, Croissant/RAI validation, changelog, access verification, maintenance/takedown assignment, and readback receipt. Public release also needs per-source redistribution review and current operator GO. |

A development fixture is not the first stage above. Engineering, synthetic unit tests, and explicitly uncertified mechanics fixtures may proceed where the current programme permits them. They cannot create accepted facts, training data, dataset exports, certification, or release claims. If an operation cannot be classified unambiguously, refuse it rather than rename it a fixture.

## Annotation reliability and judge selection

[Counting on Consensus](https://aclanthology.org/2026.lrec-1.347/) discusses metric assumptions, imbalance, missing labels, confidence intervals, and disagreement analysis. [Artstein and Poesio](https://aclanthology.org/J08-4004/) explain chance correction and task-dependent agreement measures. Neither supplies a universal passing coefficient.

Each evaluation report records:

1. Label/rating unit, independent sampling unit, annotators per unit, rubric version, label prevalence and each annotator's marginals. Preserve raw independent labels before adjudication.
2. Raw agreement and a justified statistic, such as nominal Krippendorff alpha for categorical labels with missing ratings. State distance function, implementation/version, eligible pairs, total sampled units, missing ratings, and abstentions. Report undefined coefficients as undefined, never perfect agreement.
3. A confidence interval with confidence level, estimator, seed, resample count, clustering and stratification. Resample independent source/lexeme families together, retaining all related records and paired judge predictions. Ordinary row bootstrap falsely multiplies evidence when records share sources or lexical identities.
4. Separate agreement among humans, each judge versus independent human labels, and agreement between models. Only the human comparison evaluates judge adequacy. Preserve adjudication records and report disagreement by source, field, and error class.
5. Error and abstention costs, comparison endpoints, multiple-comparison treatment, minimum observations per stratum, and disqualifying failures fixed before calibration. Select by measured human-label agreement and risk, never provider reputation. Model agreement is neither truth nor human validation.

Use the sealed calibration partition to rank complete acceptance workflows, including both model families, source tools, rules, combination logic and any screener. Single-judge ranking does not validate the combined workflow. Measure shared wrong decisions against independent source-grounded human truth. Define false acceptance conditional on human-confirmed negative candidate outputs. Register independent negative enrichment, minimum cells, inclusion probabilities, weights and natural prevalence. Report sensitivity, specificity, mistakes and abstentions separately, with appropriate CIs. Accept-all and abstain-all counterexamples must fail. Freeze the resulting selection before independent pilot certification and final evaluation. Disclose repeated calibration attempts. A final-test failure cannot become a prompt-tuning input for a re-test on the same set. Retire exposed cases to disclosed regressions and obtain fresh independently controlled final evidence under the stop policy.

Preserve original independent human labels. An independent blind dispute reader sees unlabelled, randomly ordered competing outcomes with authentic source evidence; audit random agreements too. Candidate agreement cannot determine gold truth.

[NIST acceptance sampling](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc21.htm) concerns lot disposition, not population estimation. Its [OC guidance](https://www.itl.nist.gov/div898/handbook/pmc/section2/pmc232.htm) supports explicit risk/n/c design. Report actual pass probabilities and exact nonzero-error checks rather than advertise a zero-error sample size without false-rejection risk.

For binary independent units, exact binomial bounds can quantify rare errors, including zero observed errors. [SciPy's exact interval documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html) identifies the Clopper-Pearson method. With zero errors in `n` independent units, the one-sided upper bound is `1 - alpha**(1/n)`. This formula does not establish independence, population coverage, or a simultaneous bound across many endpoints. Clustered or weighted estimates need a method justified for that design. A zero-width all-success bootstrap is not evidence of zero risk.

## Held-out isolation and contamination

Split before fitting transformations or selecting models, and keep test data out of those decisions, as explained in [scikit-learn's common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html). For datasets, also freeze source/author/book/lexeme-family split rules as applicable. Declare whether evaluation concerns known sources or genuinely unseen sources; a within-dictionary holdout cannot establish unseen-dictionary generalization.

Evaluation audit partitions are separate from consumer train/test splits and release coverage. Protected units retain ordinary release dispositions; excluding them to create a detectable release complement leaks membership. Protect membership, labels and draw state independently of normal release records. A small finite-source census means blind source-grounded verification of one exact artifact, not independent held-out or transfer evidence; it cannot silently waive disjoint selection/calibration/final proof.

Keep exact fingerprints and a preregistered near-duplicate method, normalization, similarity threshold, and manual adjudication for matches. Compare development, training, calibration, pilot-certification, and final partitions, including aliases, homographs, related source records, paraphrases, and derived records. Preserve source identity before normalization. Report overlap numerator, searched denominator, exclusions, unresolved matches, and tool versions.

[Oren et al., Proving Test Set Contamination in Black Box Language Models](https://arxiv.org/abs/2310.17623) provide a statistical detection method under explicit assumptions. Local overlap checks establish only what was compared. They cannot prove that an opaque pretrained model never saw a public dictionary, passage, or benchmark. Record pretrained exposure as UNKNOWN where evidence cannot resolve it. Keep protected answer content out of model prompts, logs, cards, and public receipts.

## Definition of Done

Dataset completion requires all applicable evidence below. A documentation PR can describe this contract without satisfying a dataset's DoD.

- Quality passes on the exact release artifact against the untouched sealed final set. Report each field/source stratum and the overall estimate with its weighting, denominator, uncertainty, critical failures, missing labels, and abstentions. Unsampled or underpowered strata remain unresolved. Do not export unresolved fields as accepted facts.
- Dataset card and substantive Croissant/RAI metadata validate against pinned versions. Include intended uses/non-uses, data structure, source lineage, licences, collection/annotation, limitations/biases, sensitive-data review, social impact, access, synthetic-data status and maintenance/takedown conditions. For the word-card proposal, facts are authentic-source-extracted with no model-written Ukrainian. State group-level error rates separately from record/field rates. No protected membership or private content enters public metadata.
- A separate clean-room rebuild from pinned source checksums, code SHA, configuration, dependencies, tool versions, serialization order, and random seeds reproduces hashes. Record both manifests and the comparison. Any nondeterministic external judge output is a pinned, provenance-bearing input to replay; replay equality does not prove that judge's correctness.
- Consumer split boundaries and protected audit partition boundaries, including applicable source/author/book/lexeme-family isolation, exact and near deduplication, and contamination controls pass. Every source unit has exactly one disposition; every exported assertion carries record- and field-level provenance/licence references, including derivations and suppressions.
- Private release has a tag, resolved commit, file digests, archived release mapping, changelog, and verified authorized readback. Git tags are mutable references, so retention and independent digest verification protect release identity.
- Same-artifact independent review and all project publication gates pass. Public release additionally requires source-specific redistribution/permission evidence and current operator GO. Authorized internal work does not wait on that future public decision.
- Verified access capability/entitlement supports the proposed least privilege; source licences and attribution survive private access conditions. Private-transfer authority/scope has a named owner and receipt; project dataset licence decisions remain separate.
- Maintenance and takedown owners monitor source changes, suppress affected access and derivatives, issue replacement versions, and retain audit history under approved retention. Old pinned commits can retain bodies after withdrawal. A conditional history/object/ref purge plan needs per-event operator authorization, retired-ref verification and honest client-copy residuals; see the storage runbook. Do not bulk-delete corpus or history without separate authorization.

## Receipts, stopping, and documentation closeout

A typed transition receipt records criterion/stage, PASS/FAIL/UNKNOWN, actor and independence, UTC time, input and artifact digests, code/configuration/tool versions, command, denominator, metric/CI, protected evidence locator, and receipt digest. Public receipts contain only safe metadata. Access-controlled receipts retain protected details separately. Transport, schema, local tests, CI, publication, and semantic certification remain distinct evidence types.

Missing seal, unsupported fact, leakage, wrong identity, invented Ukrainian, incomplete accounting, incompatible public redistribution, failed threshold, moved release reference, or a changed evaluated artifact blocks its transition. After two review rounds with material blockers, the driver changes approach without reducing the bar. A residual names its owner and event required to resolve it; unresolved relevant gates cannot be declared complete.

For #10772, AC-01 maps to Evidence, Annotation, and Contamination; AC-02 maps to DoR, Five stages, DoD, and the template; AC-03 maps to the companion plan; AC-04 maps to storage; AC-05 requires distinct Sol content criticism and Opus designated agreement, exact-head outside-family APPROVE before a PR, same-head green CI, confirmed merge, issue evidence, and common cleanup. Author self-checks do not satisfy independent documentation proof. The driver supplies the original checklist and unseen adversarial scenarios to the non-author reviewers.

## References

The primary publications and official specifications are linked beside their supported claims above. The filled plan's numerical examples are proposed project choices, not thresholds mandated by these references. Storage-specific official references and source-permission records are in the [HF design](../projects/open-model-data/HF_DATASET_STORAGE_DESIGN.md#references).
