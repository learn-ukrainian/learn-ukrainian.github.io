# Cyrillic-Slavic Ukrainian dataset delivery plan

Status: canonical execution plan for epic [#7423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7423).
This document is the durable handoff for the dataset-delivery arc; it does not
authorize provider execution, model training, storage deletion, or publication
beyond the rights of the admitted sources.

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
`data/projects/open_model_data/evidence/phase3_cyrillic_slavic_predecessor_handoff_v1.json`
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

For every mandatory source family, each frozen unit appears exactly once:

`input_total == converted + not_rule_bearing + duplicate_representation + evaluation_only + superseded_or_historical + blocked_with_reason`

`blocked_with_reason` blocks `SOURCE_COVERAGE_READY` and dataset completion.
Rights limitation is a capability tag, not a disposition escape. Every
independently confirmed non-evaluation rule-bearing unit links bidirectionally to
an immutable evidence/rule artifact and at least one permitted consumer view:
`supervised_pair`, `preference`, `protection`, `filtering`, `review`,
`automatic`, or `research_only`.

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

Before derivation, the held-out steward freezes source partitions, required
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

The accountable orchestrator owns scope, sequencing, integration, verification,
issue truth, and final disposition, but is not the Ukrainian-language authority.
The following decision roles remain separate across the program:

1. scope/circularity critic;
2. Ukrainian source reviewer;
3. rule author/extractor;
4. held-out steward;
5. held-out label reviewer;
6. scorer;
7. outsider reproducer;
8. cross-family code/infra reviewer;
9. Ukrainian-capable disposition auditor;
10. Ukrainian-capable textbook non-hit auditor.

One continuing identity may hold at most one role for the program. A provider or
model switch does not create a new independent role. Ukrainian claims require a
language-qualified review lane and source-backed verification; model agreement is
never evidence of authority.

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
