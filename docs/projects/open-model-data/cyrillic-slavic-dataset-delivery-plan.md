# Cyrillic-Slavic Ukrainian dataset delivery plan

Status: canonical execution plan for epic [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423).
This document is the durable handoff for the dataset-delivery arc; it does not
authorize provider execution, model training, storage deletion, or publication
beyond the rights of the admitted sources.

<!-- BEGIN OUTCOME_FREEZE_V2 -->
OUTCOME_FREEZE_V2

User-visible outcome:
Deliver a versioned, reproducible, source-derived dataset that teaches models to produce and preserve proper modern Standard Ukrainian while resisting interference only from the exhaustive V1 allowlist of Slavic language classes written in Cyrillic. The dataset must also identify and protect legitimate historical material, especially the Old East Slavic / Kyivan Rus written-language continuum and Middle Ukrainian, instead of correcting it into modern Ukrainian.

Operational language and context boundary:
- Target: modern Standard Ukrainian.
- Exhaustive V1 modern contact/adversarial allowlist: Russian, Belarusian, Bulgarian, Macedonian, Serbian in Cyrillic, and Montenegrin in Cyrillic. No named class may be added without source-qualified domain review and a new outcome freeze.
- Historical/protected identity classes: Old East Slavic / Kyivan Rus written-language continuum, Middle Ukrainian, Old Church Slavonic or a source-qualified Church Slavonic recension, and source-attested Rusyn.
- Every span has separate language_identity, script_profile, context_role, period/region/register where applicable, identity_candidates, and scope_status fields. Script never proves language identity.
- Context roles: unmarked modern Ukrainian, quotation, code-switch, transliteration, metalinguistic example, name/title, dialect or regional form, historical text, and ambiguous/noisy text.
- Correction truth is eligible only when the exact span is independently adjudicated as unmarked modern Ukrainian and the contrasted contact class is in the exhaustive V1 allowlist. Unknown, mixed-identity, non-Slavic Cyrillic, Latin-script Slavic, transliterated, and other_or_unresolved_slavic_cyrillic spans route to out_of_scope_protected or abstain, never correction truth.

Historical non-erasure invariants:
For every historical/protected source span: historical_forms_protected=true; modern_correction_eligible=false; old_east_slavic_is_modern_russian=false; historical_ruskyi_auto_mapped_to_modern_russian=false; and no automatic mapping to any modern national successor language. A modern-context rule may apply only to a distinct span independently adjudicated as unmarked modern Ukrainian; it may never relabel a historical source span. Historical records retain period, region, register, recension/editorial layer, identity candidates, and an unresolved historical-Cyrillic route. Old Church Slavonic and later source recensions must be distinguished or explicitly mapped, not flattened.

Frozen source denominator:
Freeze a versioned source manifest with exact admitted units, hashes, admission cutoff, source/rights capability state, and later-addition policy; later sources require a new dataset version. Derive and freeze an atomic rule denominator R, its algorithm, merge/split rules, and rule-manifest hash before scale. Keep source_unit_disposition separate from coverage_cell_status. Freeze an applicability predicate and explicit required-cell manifest over language x context x phenomenon x role rather than an implicit full Cartesian product. Every frozen source unit is dispositioned exactly once as converted, supporting_only, protected, evaluation_only, rights_limited_locator_only, duplicate, non_rule_bearing, unresolved, or blocked_with_reason. Every required coverage cell is separately marked satisfied, not_applicable_with_evidence, coverage_blocked, or unresolved. An actual protected_case is distinct from not_applicable_with_evidence; N/A never satisfies protected-case coverage. Row count, storage size, schema validity, or model agreement cannot substitute for denominator closure.

Canonical product:
A source capability ledger; immutable claim-typed evidence records; frozen atomic rule cards; teaching cases containing correct production, correction, minimal contrast, protected, and adjudicated abstention roles; deterministic derived training/evaluation views; versioned source-identity splits; provenance and rights metadata; and a consumer reproduction receipt. Gold targets require source-qualified human adjudication against cited claim-appropriate evidence. Attestation alone cannot establish contextual correctness. Model proposals retain provenance and cannot become targets without human adjudication. A coverage_blocked cell is not an abstention teaching case.

Cycle007 isolation:
Cycle007 remains evaluation-only and deny-listed from training truth. Freeze the deny-list over row IDs, exact example/source units, document/work/edition groups, labels, case-specific sidecars, prompts, paraphrases, and synthetic siblings. Prohibit evaluation-example and annotation derivation while allowing only shared abstract rule concepts or authority-only citations whose exact held-out spans and annotations are not exposed. Any uncertain lineage is excluded from training views.

Non-goals:
No general C2 knowledge corpus; no Latin-script Slavic interference program; no non-Slavic Cyrillic program; no model training in this epic; no preference optimization; no mass Gemini/Grok labeling; no provider output promoted to gold; no model-performance learning curve; no prompt-baseline or dataset-backed model-behavior claim as an epic completion gate; no publication of source text beyond rights; no automatic modernization of historical, dialectal, quoted, named, transliterated, or metalinguistic spans.

Role map:
One accountable orchestrator owns sequencing and disposition. Source/rights owners establish capabilities. Source-qualified human adjudicators establish gold against claim-appropriate evidence. Ukrainian language lanes may propose and independently review mappings but are not truth by themselves. Independent builders implement deterministic artifacts. An evaluation steward freezes held-out partitions before any rule/case derivation and withholds held-out labels from builders. A cross-family reviewer gates every consequential PR. Models may propose candidates but cannot author gold labels.

Independent held-out evaluation:
Freeze document/source-identity splits, exact and near-duplicate policy, required-cell construction rules, and per-required-cell held-out requirements before rule or case derivation. Keep held-out text, labels, annotations, and case-specific derivatives unavailable to builders. Report dataset integrity and coverage per language, context, phenomenon, and role. Hard global failures are any split leakage, unsupported gold label, destructive edit of a protected case, provenance/rights loss, denominator drift, integrity corruption, or Cycle007 derivative entering training truth. Model training and behavior comparison remain separately authorized after DATASET_READY and cannot close this epic.

Stop, residual, and scale policy:
Global stop conditions are denominator drift, leakage, protected-span damage, rights/provenance integrity corruption, or Cycle007 contamination. Lane-local stop conditions are unresolved rights, incomplete sources, or insufficient evidence; disjoint safe lanes may continue, while affected required cells remain coverage_blocked or unresolved. Never lower a gate, synthesize authority, or silently expand scope. Scale only after a source-qualified pilot passes; measure a deterministic coverage-yield curve of newly satisfied source-backed atomic coverage versus duplicate/derivative volume, never a model-performance learning curve.

Completion vocabulary:
INVENTORIED means the frozen source universe is disposition-complete, with blocked and unresolved counts still explicit. PILOT_VALIDATED means the source-qualified pilot, split firewall, and held-out protection/integrity gates pass. DATASET_PARTIAL means reproducible admitted rows exist but at least one frozen required source unit/cell, right, or integrity requirement remains blocked or unresolved. DATASET_READY means the frozen required denominator is covered with zero unresolved or blocked required cells, zero unknown required rights, zero exclusion gaming, all admitted targets human-adjudicated and source-traceable, all views split-safe and reproducible, and the consumer receipt independently reproduces the dataset. Protected, evaluation-only, rights-limited, duplicate, and non-rule-bearing units remain denominator-visible. BLOCKED means a named global stop condition prevents safe progress. TRAINING_VALIDATED is outside this epic and cannot be claimed here.

Legacy and policy disposition:
The new epic remains a child of open-model-data stream epic #6321. Issue #6375 is superseded for dataset delivery only after a machine-readable handoff receipt validates the controlling outcome SHA, old/new issue IDs, public artifact SHAs, exact text-free Cycle007 state including labeling still OFF and zero provider-derived training labels, residual counts, blockers, owners, and receiving-epic acceptance. Completed historical issues remain closed. Issue #6958 remains open until its machine-readable Wikipedia teaching/gold/training ineligibility field and fail-closed selection gate land; the successor epic pins that policy to the exact merged artifact/check SHA rather than relying on a mutable issue number. The approximately 81 GiB Cycle007 expansion may be reclaimed only through a separate compact-migration child with exact round-trip proof, a recoverable backup, and explicit operator authorization before deletion.
<!-- END OUTCOME_FREEZE_V2 -->

## Frozen contract

| Field | Value |
| --- | --- |
| Parent epic | #7423 |
| Controlling outcome SHA-256 | `890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47` |
| Contract state | `V2_REVIEWED_ACTIVE` |
| Ukrainian-domain review | `APPROVE` — Gemini 3.7 Flash High |
| Scope/circularity review | `APPROVE` — GPT-5.6 Sol red-team |
| Previous contract | `V1_SUPERSEDED_NOT_ACTIVE` |

The frozen outcome is:

> Deliver a versioned, reproducible, source-derived dataset that teaches models to produce and preserve proper modern Standard Ukrainian while resisting interference only from an exhaustive V1 allowlist of Cyrillic-written Slavic contact classes. It must identify and protect historical language—especially the Old East Slavic / Kyivan Rus written-language continuum and Middle Ukrainian—instead of modernizing or relabeling it.

The SHA above is the controlling identity from the reviewed epic contract. Any
material change to the outcome, language boundary, denominator, role map,
evaluation design, stop policy, or completion terms invalidates this plan and
requires a new domain review and an independent scope/circularity review before
implementation continues. The receipt in
`data/projects/open_model_data/reference/phase3_cyrillic_slavic_predecessor_handoff_v1.json`
binds the predecessor state to this identity.

## Product boundary

The target is modern Standard Ukrainian. The modern Cyrillic-written contact
allowlist is exhaustive for this dataset version:

1. Russian.
2. Belarusian.
3. Bulgarian.
4. Macedonian.
5. Serbian written in Cyrillic.
6. Montenegrin written in Cyrillic.

The following are protected historical or regional identities and are not
modern correction targets by identity alone:

- Old East Slavic / the Kyivan Rus written-language continuum;
- Middle Ukrainian;
- Old Church Slavonic, or a source-qualified Church Slavonic recension;
- source-attested Rusyn.

The dataset must represent these dimensions independently for every span:

- `language_identity`;
- `script_profile`;
- `context_role`;
- `scope_status`;
- period, region, register, and recension/editorial layer where applicable.

Script is not language identity. Unknown, mixed-identity, non-Slavic Cyrillic,
Latin-script Slavic, transliterated, and unresolved spans are protected,
out-of-scope, or abstained; they are never silently converted into correction
truth. A span is correction-eligible only when it is independently adjudicated
as unmarked modern Ukrainian and the source-backed rule applies to that span.

### Historical non-erasure invariants

Every historical/protected span must enforce all of these invariants:

- `historical_forms_protected=true`;
- `modern_correction_eligible=false`;
- `old_east_slavic_is_modern_russian=false`;
- `historical_ruskyi_auto_mapped_to_modern_russian=false`;
- no automatic mapping to any modern national successor language.

Modern correction may apply only to a distinct span independently adjudicated as
unmarked modern Ukrainian. It may never relabel, normalize, or erase a
historical source span. Mixed Middle Ukrainian/Church Slavonic material and
recension/editorial layers remain representable without a forced single label.

### Explicit non-goals

- general C2 knowledge or a general historical-language corpus;
- Latin-script Slavic or non-Slavic Cyrillic interference programs;
- model training, preference optimization, model downloads, or model-performance learning curves;
- mass Gemini/Grok labeling or provider output promoted to gold;
- automatic modernization of historical, dialectal, quoted, named, transliterated, metalinguistic, or exercise/distractor spans;
- publication beyond source rights;
- changing the frozen taxonomy, denominator, packet size, validators, endpoints, or custody controls inside this dataset version.

Cycle007 remains evaluation-only. Its rows, sidecars, prompts, labels,
paraphrases, synthetic siblings, and source/example identities are denied from
training truth. Shared abstract rule concepts or authority-only citations may be
reused only when no exact Cycle007 span or derivative is used; uncertain lineage
is excluded.

## Frozen product and denominators

The product is a source capability ledger, immutable claim-typed evidence,
frozen atomic rule cards, source-qualified teaching cases, deterministic
derived training/evaluation views, source-identity splits, provenance/rights
metadata, and an independently reproduced consumer receipt. It is not complete
because a row count, schema, transport, model agreement, or CI run looks good.

Before scale, freeze all of the following:

- the versioned source-unit manifest, hashes, admission cutoff, and rights capabilities;
- the atomic rule denominator `R`, derivation algorithm, merge/split rules, and manifest hash;
- the applicability predicate and required coverage-cell manifest;
- separate source-unit dispositions and coverage-cell statuses;
- per-required-cell construction and held-out requirements;
- source/document identity partitions and exact/near-duplicate policy;
- the Cycle007 deny-list and evaluator custody boundary.

For every mandatory source family, each frozen source unit appears exactly once:

`input_total == converted + supporting_only + protected + evaluation_only + rights_limited_locator_only + duplicate + non_rule_bearing + unresolved + blocked_with_reason`

Source-unit dispositions remain separate from coverage-cell statuses. Every
required coverage cell is separately marked `satisfied`,
`not_applicable_with_evidence`, `coverage_blocked`, or `unresolved`.
Independently confirmed non-evaluation rule-bearing units link bidirectionally
to immutable evidence/rule artifacts and to reviewed deterministic
training/evaluation views, with protection and abstention behavior explicit.
Later consumer shapes are governed by child contracts.

An actual protected case is distinct from
`not_applicable_with_evidence`; N/A cannot satisfy protection coverage.
Attestation alone cannot establish contextual correctness. Gold targets require
source-qualified human adjudication against claim-appropriate cited evidence.
Models may propose candidates, but cannot author gold.

## Case and evaluation contract

The canonical case roles are:

- correct modern production;
- source-backed correction;
- minimal contrast;
- actual protected historical/context span;
- adjudicated abstention;
- `not_applicable_with_evidence`;
- coverage-blocked/unresolved.

Before derivation, the evaluation steward freezes source partitions, required
coverage strata, clean-modern controls, thresholds, rights/role contracts, and
the near-duplicate policy. Rule authors see only steward-cleared development
material; they never see held-out text, labels, locators, fingerprints,
derivatives, public-canary patterns, or near-neighbours. Any leakage, uncertain
lineage, protected-span damage, denominator drift, or rights/provenance
corruption is a terminal global stop.

Global stops apply to the whole epic. Lane-local stops (for example, unresolved
rights or insufficient source evidence in one contact class) keep the affected
cells blocked while disjoint safe lanes may continue. No lane may hide a blocked
cell by changing its applicability or denominator.

Scale is governed by a deterministic coverage-yield curve: newly satisfied
source-backed atomic coverage compared with duplicate/derivative volume. It is
not governed by a model learning curve or a fixed row quota.

## Roles and evidence

The role map is:

- one accountable orchestrator owns scope, sequencing, integration, verification, issue truth, and final disposition;
- source/rights owners establish source capabilities and rights boundaries;
- source-qualified human adjudicators establish gold against claim-appropriate cited evidence;
- Ukrainian language lanes may propose and independently review mappings but are not truth by themselves;
- independent builders implement deterministic artifacts;
- an evaluation steward freezes held-out partitions before any rule/case derivation and withholds held-out labels from builders;
- a cross-family PR reviewer gates every consequential PR.

Independence-sensitive review and steward roles must not self-review their own
artifacts. Ukrainian claims require a language-qualified review lane and
source-backed verification; model agreement is never evidence of authority.

## Ordered issue DAG

Every child issue carries the controlling SHA, its role, denominator, explicit
dependencies, non-goals, acceptance evidence, and global/lane-local stop policy.
Native child links on GitHub are authoritative; the table below is the durable
human-readable projection.

| Stage | Issue | Depends on | Owned outcome | Terminal evidence |
| --- | --- | --- | --- | --- |
| P0 | #7424 | — | publish this contract, stream pointer, and predecessor handoff | merged plan, validated receipt, predecessor disposition |
| P1 | #7425 | #7424 | freeze source, rights, language, and applicability universe | frozen unit and required-cell manifests |
| P2 | #7426 | #7425 | freeze atomic rule, evidence, adjudication, and case contracts | frozen `R`, authority rules, fail-closed validators |
| P2 | #7427 | #7425, #7426 | freeze held-out splits and Cycle007 lineage firewall | split and deny-list custody proof |
| P3 | #7428 | #7425–#7427 | build six modern Cyrillic contact channels | source-qualified modern cell dispositions |
| P3 | #7429 | #7425–#7427 | build historical protection channels | non-erasure, period, region, and recension proof |
| P4 | #7430 | #7426–#7429 and merged #6958 | construct the smallest source-qualified pilot | reproducible pilot with all applicable case roles |
| P5 | #7431 | #7430 | independently validate pilot and issue scale GO/NO-GO | exact GO/NO-GO and residual map |
| P6 | #7432 | #7431 GO | scale by coverage yield without denominator revision | yield curve and closure/residual receipt |
| P7 | #7433 | #7432 | reproduce consumer views and certify state | `DATASET_READY`, `DATASET_PARTIAL`, or `BLOCKED` receipt |
| parallel | #7434 | #7424 and Cycle007 custody identities | compact Cycle007 storage safely | exact round-trip and recoverable backup; deletion separately authorized |

Critical path:

`#7424 → #7425 → #7426 → #7427 → (#7428 || #7429) → #7430 → #7431 → #7432 → #7433`

`#6958` is a binding admission dependency, not a duplicate child. It must mark
Wikipedia Foundry views ineligible for teaching, gold, and training and enforce
that policy fail-closed before #7430. #7434 is parallel custody work and is not
a semantic dataset gate.

## Completion vocabulary

Use these exact statuses; do not collapse them:

- `INVENTORIED`: source universe disposition-complete, with blocked/unresolved counts visible.
- `PILOT_VALIDATED`: source-qualified pilot, split firewall, and held-out protection/integrity gates pass.
- `DATASET_PARTIAL`: reproducible rows exist but required denominator, rights, or integrity gaps remain.
- `DATASET_READY`: frozen required denominator covered; zero blocked/unresolved required cells; zero unknown required rights; no exclusion gaming; every admitted target human-adjudicated/source-traceable; every view split-safe/reproducible; consumer reproduction passes.
- `BLOCKED`: a named global stop prevents safe progress.
- `TRAINING_VALIDATED`: outside this epic and forbidden as a completion claim.

No intermediate child may claim `DATASET_READY` or `TRAINING_VALIDATED`.

## Transfer and anti-misdirection instructions

An agent taking over this epic starts from the epic and this document, then:

1. verify the controlling outcome SHA and current `origin/main` identities;
2. read the exact child issue and native dependency links before dispatch;
3. freeze the task's denominator, non-goals, role, held-out boundary, and stop/residual policy in its issue/brief;
4. use only its owned paths and a dispatch worktree;
5. record model/provider proposals separately from human-adjudicated gold;
6. run deterministic validators before any provider or training authorization;
7. report counts, booleans, hashes, statuses, and named residual owners—not source text;
8. stop on any global tripwire, and keep lane-local blockers visible without shrinking the denominator;
9. close an issue only after every acceptance criterion has typed evidence and all remaining scope is transferred;
10. never treat `TRAINING_VALIDATED`, model agreement, storage size, row totals, or schema validity as a substitute for the stated completion gates.

The public predecessor receipt binds #6375 to #7423 and records the exact
text-free Cycle007 state. #6375/Cycle007 is historical evidence, not the active
milestone. The predecessor closes only after that receipt is merged and validated;
any genuine residual is owned by #6958 or #7434 as mapped in the receipt.
