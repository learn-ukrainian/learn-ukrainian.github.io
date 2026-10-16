# Dataset plan template

Version: <version>. Status: PROPOSED until designated approval and landing.
Issue/parent/stream: <links>. Approved programme and precedence: <links/clauses>.
Standard: [dataset engineering](dataset-engineering.md). All blanks block their gate.

## Outcome and responsibility

- Intended use and named consumer: <use, consumer, user-visible outcome>.
- Non-use and non-goals: <unsupported claims, prohibited uses, scope>.
- Driver / source-inventory owner / extraction author: <named assignees>.
- Annotation lead / separate gold steward / independent evaluator: <assignees>.
- Release / maintenance / takedown owners: <assignees and succession>.
- Acceptance criteria and existing stronger prerequisites: <frozen IDs/hash>.

## Inputs and denominators

- Record, source unit, independent cluster, identity and field definitions: <each>.
- Frozen universe, source/field/stratum counts and dispositions: <manifest/digest>.
- Unknown denominator: <owner, event, blocked operation; never an invented total>.
- Sources: <edition/snapshot/checksum, locator, facet, provenance/licence record>.
- Rights: <internal-use disposition; separate redistribution/permission evidence>.
- Mixed fields and derivatives: <field-level licence, attribution, dependencies>.
- Splits: <source/author/book/lexeme boundaries, applicability, weights>.
- Exact/near dedup and contamination: <algorithm, threshold, scope, unresolveds>.

## Human gold and measurement

- Gold prerequisite: <independent human source labels, frozen before quality pilot>.
- Seal: <authority/signature, manifest SHA, UTC date, isolation/access receipts>.
- Custody: <separate control, denied author membership/answers, alias closure>.
- Disclosed development/training: <manifest, disjointness, no final-test use>.
- Sealed calibration: <n/units/strata, candidate judges/rubrics, selection rule>.
- Pilot-certification inputs: <separate n/units/strata, evaluator and custody>.
- Untouched final release test: <separate n/units/strata, evaluator and custody>.
- Rubric and critical failures: <fixed version, error/abstention costs>.
- Numeric thresholds: <overall and per field/source, sample-size/precision rationale>.
- IAA: <statistic, prevalence/marginals, raw agreement, human adjudication>.
- Denominators: <all sampled, missing labels/abstentions, eligible label pairs>.
- CIs: <method/confidence, seed/resamples, clusters, multiplicity, rare errors>.
- Freeze selection before evaluation: <judge/prompt/parser/config/tool digests>.

## Stage receipts

| Stage | Prerequisite and measured pass/fail | Artifact and typed receipt |
| --- | --- | --- |
| Pilot | <DoR, source completion, admitted seal; n/selection/semantic check> | <digests, counts, locators, comparison> |
| Measured gate | <independent pilot certification plus original gates> | <pilot/code/input digests, metrics/CIs/verdict> |
| Scaled build | <all prerequisites; complete accounting/reproduction> | <shard/build/dedup manifests, clean-room hashes> |
| Independent evaluation | <frozen artifact; untouched final test passes> | <same-artifact results, uncertainty, isolation> |
| Publish | <review, metadata, access/capacity, release authorization> | <private tag+commit/digests, readback, release map> |

## Release, stopping, and completion

- Card/Croissant/RAI: <substantive fields, pinned validators and receipts>.
- Rebuild: <pinned sources/code/config/tools/seeds, clean-room command/comparison>.
- Visibility/access: <private default, namespace verified, gold separately isolated>.
- Public-only conditions: <per-source redistribution review and current operator GO>.
- Capacity/retention: <measured bytes/versions/reserve, overage stop, release archive>.
- Maintenance/takedown: <source-change trigger, access suppression, replacement>.
- Stop/residual: <failures, two-round limit, owner and exact unblocking event>.
- DoD: <untouched-test semantic proof, same-artifact review, release/hygiene evidence>.
- Receipt schema: <criterion, status, actor/time, inputs/artifact/code, metric/CI, digest>.
- Documentation approval: <Sol/Opus, exact-head CF, CI, merge and cleanup receipts>.
