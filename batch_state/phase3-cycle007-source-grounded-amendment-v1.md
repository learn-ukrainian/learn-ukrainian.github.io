# Phase 3 Cycle 007 source-grounded restart amendment v1

Issue: `#6375`

Evaluation cycle: `phase3-v2-1-evaluation-cycle-007`

Status: proposed contract; private provider calls are blocked until the exact
amendment and implementation pass all pre-call gates below.

## Operator-authorized user outcome

Certify the frozen Phase 3 correction-protection evaluation over exactly
10,159 held-out rows while preventing Gemini and Grok from treating shared
Russian-influenced pre-training as Ukrainian linguistic authority. Every
decision must be tied to frozen evidence produced through the project's
`sources` MCP and existing immutable source provenance. Two independent model
labels, their agreement alone, or schema-valid output alone are not sufficient
proof.

## Why this is a new cycle

Cycle 006 stopped safely after Gemini sealed 41 of 204 packets (2,050 of
10,159 rows). Its prompt and label schema did not require source-evidence IDs,
so those labels cannot be mixed with source-grounded labels. Cycle 006 remains
immutable diagnostic history. Cycle 007 copies no provider output, label, raw
response, adjudication, or resolution and starts both model lanes at zero.

This amendment does not reroll or alter the held-out source universe, row
identity, row order, packet order, packet size, denominator, taxonomy, custody
boundary, or release policy.

## Frozen source universe

The sole held-out source remains the restored Cycle 005 custody package:

- custody receipt SHA-256:
  `7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726`
- label manifest SHA-256:
  `b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab`
- ordered lane/packet/row identity commitment:
  `331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419`
- lanes: 40 clean-label packets / 2,000 rows and 164 residual-label
  packets / 8,159 rows
- total: 204 packets / 10,159 rows
- packet size: 50, except the already-sealed final 9-row packet

Materialization preserves lane order, packet order, row order, unit ID,
unit SHA-256, and all source-bearing fields byte-for-value. The only row field
that changes is `evaluation_cycle_id`.

## Frozen Sources MCP evidence layer

Before either labeler runs, a local compile step builds one immutable private
evidence sidecar per packet and one text-free evidence manifest. It uses the
project's `sources` MCP at the reviewed local endpoint and records the exact
public Sources server code hash plus the local `sources.db` and `vesum.db`
hashes. A different server, source database, query plan, tokenizer, prompt, or
sidecar format invalidates the canary and all later labels.

The deterministic query plan is:

1. Preserve and hash each row's existing source provenance and source-bearing
   fields without printing them. Evidence channels are separate and explicit:
   `pravopys_2026_normative`, `pravopys_2019_comparison`, `vesum_attestation`,
   `antonenko_style`, `ua_gec_calque`, `heritage_attestation`,
   `ukrainian_corpus_occurrence`, `textbook_explanation`,
   `russian_shadow_suspicion`, and `source_metadata`.
   Each channel has a closed claim boundary; attestation or occurrence cannot
   satisfy a normative-rule claim.
2. Extract Ukrainian Cyrillic surface forms with one reviewed tokenizer whose
   code path and SHA-256 are frozen in the evidence manifest. Compound splitting
   is a versioned parser operation. Ambiguous tokenization or decomposition is
   recorded as unresolved and never silently drops or invents evidence.
   Deduplicate the resulting queries within the frozen source universe.
3. Batch-check every extracted form with `verify_words`, and run
   `check_modern_form` for every extracted form regardless of the VESUM batch
   result. Bind `is_modern_codified`, `has_archaic_form`, and
   `has_only_archaic_form` to same-row evidence IDs so archaic-only risk review
   is mechanically selectable.
4. For a VESUM miss, never infer that the form is Russian or invalid. Split
   supported compounds, then check `query_ulif`, the locally cached
   `query_slovnyk_me` evidence, and `query_grac` corpus attestation. Ambiguous
   or unavailable escalation remains unresolved.
5. Russianism/calque and heritage verification is an always-on parallel path
   for every row, not a path gated by VESUM absence or Russian-shadow
   suspicion. Query both
   `search_style_guide` and `search_text` with
   `source_file='antonenko-davydovych-yak-my-hovorymo'`, plus
   `search_ua_gec_errors` and `search_heritage`. The structured
   Антоненко-Давидович index, its prose surface, and UA-GEC are complementary;
   no incomplete surface substitutes for the others.
6. Use `check_russian_shadow` only as a suspicion flag. It can require review
   but can never independently reject or accept a row.
7. Within this frozen Phase 3 evaluation contract, the officially decided
   Pravopys 2026 edition is the sole current normative authority. This is a
   task-specific frozen source identity, not an unsupported inference from the
   general Sources MCP documentation. Its PDF SHA-256 is
   `e593956bfba6737d991a76fa86970db9c10a5cd7fd8895bae67f2b9a950c3a92`;
   the text-free Phase 3 context receipt SHA-256 is
   `5da6f60e1cf5527fd98e44b4396472d871d359cd6b9dc76e3806c73a15c2b827`;
   and the public source-universe schema requires both an official decision
   locator and official download locator for that edition. Bind those frozen
   Cycle 005 rows/PDF facts to relevant residual phenomena. The Sources MCP
   `query_pravopys` tool exposes Pravopys 2019 and is comparison-only within
   this evaluation; it cannot override the frozen 2026 decision. Ukrainian
   textbook explanations, VESUM attestation, heritage evidence, and corpus
   occurrences remain distinct non-normative channels.
8. Give every immutable result a content-derived evidence ID using canonical
   JSON over exactly: evidence schema, channel, source identity and version,
   locator, query SHA-256, status, supports value, retrieval SHA-256, parser ID
   and version, row identity, and optional phenomenon ID. Status is one of
   `attested`, `not_found`, `ambiguous`, `incomplete`, `parse_error`, or
   `unavailable`; support is a closed claim-boundary value. Negative evidence
   IDs are valid references but never count as sufficient positive support.
   Sidecars may contain private text, but public receipts contain only counts,
   hashes, tool names, source versions, and pass/fail facts.

Network fallbacks are disabled during evidence compilation. Missing,
conflicting, truncated, unparseable, or unavailable source evidence is marked
unresolved; it is never normalized into positive evidence.

## Model contract

Gemini and Grok receive the same immutable row packet and the same immutable
evidence sidecar, but never see each other's labels. Their prompts state that
the evidence sidecar and Ukrainian sources are authoritative over model
memory. Both harnesses must resolve the `sources` MCP before the public canary;
the canary must prove an actual source-tool round trip, not merely a configured
server name.

Every clean label adds one sorted, unique `evidence_ids` array at label level.
Every residual phenomenon adds its own sorted, unique `evidence_ids` array;
there is no shared row-level shortcut for a multi-phenomenon label. The
validator requires every ID to exist for that exact row and, for residual
labels, that exact phenomenon. It rejects cross-row, cross-phenomenon,
invented, duplicate, or out-of-order IDs. An `agree`,
`positive`, `acceptable_control`, or `protected` decision requires sufficient
normative or attestation evidence under the frozen query plan. If evidence is
missing or conflicting, the only valid outcome is the existing uncertainty
path (`reject_insufficient_locator_evidence`, `abstention`, or
`disagreement`, as appropriate). Models emit only the closed label schema;
they do not rewrite Ukrainian text or author free-form explanations.

Provider tool-call telemetry and source responses remain private. A sanitized
receipt binds their hashes and records only the resolved server, tool names,
counts, success state, and whether a required source escalation occurred.

## Comparison, review, and shared-error defense

Deterministic comparison runs over all 10,159 dual labels. A matching pair is
not automatically final when its evidence is risky.

The following consensus rows receive source-authority review in full:

- any VESUM miss or archaic-only form;
- any UA-GEC, Russian-shadow, or style-guide warning;
- any heritage/source conflict, missing normative rule, or unresolved source
  result;
- any model decision that cites insufficient, missing, foreign-row, or
  non-normative evidence;
- every synthetic Russianism/Surzhyk and source-conflict negative control.

In addition, a deterministic SHA-256-ranked sample audits the otherwise clean
consensus population: all consensus rows after the risk-trigger population
above is excluded. The pre-label seed is
`SHA256("phase3-cycle007-consensus-audit-v1\n" || custody_sha256 ||
manifest_sha256 || ordered_identity_commitment_sha256)`. Each row rank is
`SHA256(seed || lane || unit_id || unit_sha256)`.

The sampler first unions the ten highest-ranked available rows from every
nonempty clean-label decision-code stratum and every nonempty residual
`(phenomenon_id, phenomenon_decision_code)` stratum. A row may satisfy several
residual strata but appears once in the audit. If this union exceeds 600, the
sample expands to the full union. Otherwise the sampler fills to 600 from the
remaining population by global row rank. If the population contains fewer
than 600 rows, it audits the whole population. Empty and smaller-than-ten
strata contribute all available rows. The population definition, exclusions,
seed, ranks, stratum membership, and selected identity commitment are sealed
before source-authority audit begins.

The audit accepts zero unsupported acceptance, incorrect positive, or
Russian/Surzhyk-as-standard finding. One such finding is a terminal semantic
stop: the affected stratum expands to full review, the root cause is corrected,
and any invalidated model or audit work is rerun. This 600-row zero-failure
sample uses the zero-event one-sided 95% bound
`1 - 0.05 ** (1 / audited_population_count)`; at 600 audited rows this is below
0.5% for an otherwise unobserved shared-error rate. The receipt records the
actual audited count and computed bound. Risk-triggered rows are reviewed at
100% and are not included in that estimate.

Model disagreements go to a fresh source-qualified adjudicator that sees both
candidate labels, the same evidence sidecar, and no unrelated model outputs.
The live risk-trigger review, clean-consensus sample audit, and disagreement
adjudication are executed locally by a human operator/source-qualified advisor
or an Anthropic-family source-qualified lane with Sources MCP. Google and xAI
families are prohibited from those roles, including a fresh Gemini or Grok
session. The accountable root owns routing and receipt verification but does
not inspect private text. The adjudicator may select an existing candidate
only when the cited source evidence supports it. Otherwise it emits an
unresolved request. The operator or a designated source-qualified advisor
resolves only explicit unresolved requests, with a source-bound decision
receipt. No majority vote, model agreement, same-family recheck, or
source-blind operator choice can override conflicting evidence.

## Privacy, storage, and fleet boundary

Held-out rows, private prompts, evidence sidecars, source responses, provider
outputs, labels, and raw telemetry remain on the local machine in a mode-0700
operator-owned package with mode-0600 files. They never go to a VPS, Git,
GitHub, stdout, argv, controller logs, or public review artifacts.

The two VPSes may receive only public code, synthetic fixtures, tests, and
review briefs. Their Cycle 007 work is limited to public materializer proofs,
synthetic test execution, prompt/contract criticism, and exact-head
cross-family code review. Public-only agents may perform those tasks; they may
not receive held-out or source-response content.
The local package receives an incremental, hash-verified Google Drive backup
before the first private provider call and after each completed stage. Cycle
006 and Cycle 007 are preserved separately; no cleanup is authorized until
Cycle 007 certification and backup verification are complete.

## Roles

- Accountable Sol root: scope, sequencing, privacy-safe monitoring,
  integration, and final disposition.
- Ukrainian source-authority reviewer: verifies the query hierarchy, source
  roles, evidence sufficiency, and Russianism/Surzhyk protections.
- Independent scope/circularity critic: verifies the denominator, fresh-label
  boundary, audit independence, stop policy, and absence of circular proof.
- Implementation workers: public tooling and synthetic fixtures only.
- Independent cross-family reviewer: exact-head code and infrastructure gate.
- Gemini and Grok: independent first-pass labelers using identical frozen
  source evidence.
- Fresh source-qualified adjudicator: disagreement and risk-review lane.
- Runtime independent source auditor: local human or Anthropic-family
  source-qualified lane; owns the 100% risk review and clean-consensus sample
  audit and is disjoint from both first-pass model families.
- Operator or designated source-qualified advisor: explicit unresolved
  decisions only.

## Pre-call gates

No private provider call is allowed until all are true:

1. This amendment's SHA-256 and the audit seed/selection algorithm are frozen.
2. A Ukrainian source-authority reviewer and a distinct scope/circularity
   critic approve this exact amendment; material findings are reconciled and
   re-reviewed.
3. The evidence compiler proves 204 sidecars / 10,159 rows, exact identity
   preservation, source-version bindings, deterministic cache reuse, no
   network fallback, and fail-closed behavior for every missing/conflicting
   source family.
4. The materializer proves 204 packets / 10,159 rows, zero copied labels or
   provider artifacts, transaction rollback, and correct 0700/0600 custody.
5. Synthetic tests prove evidence-ID omission, invention, cross-row reuse,
   reordering, hash drift, insufficient-source acceptance, Russian-shadow-only
   rejection, VESUM-miss condemnation, source-server unavailability, partial
   seals, stop idempotence, and private-value non-disclosure all fail closed.
6. Exact-head CI and an independent cross-family review approve all public
   execution modules and proofs.
7. Public Gemini and Grok canaries each make a real `sources` MCP call, cite
   valid evidence IDs, reject a Russian/Surzhyk trap for the right sourced
   reason, preserve a heritage false-positive control, and emit the exact
   bound schema without private data. These canaries use dedicated public
   synthetic fixtures disjoint from both the private 10,159-row denominator
   and its frozen negative controls.
8. A text-free preflight binds the reviewed code, amendment, source database,
   prompts, evidence manifest, audit seed, canary receipts, and fresh Google
   Drive backup receipt.

## Stop policy

For each provider work unit (one Gemini chunk or one Grok packet), one
structural retry is permitted only when attempt 1 has no extractable,
schema-valid result. A schema-valid result that fails identity, evidence, or
semantic validation is terminal and receives no provider retry. Any other
structural, source-binding, privacy, provider, or audit failure writes one
text-free terminal stop and blocks every later paid or adjudication stage.
No chunk-size,
validator, taxonomy, source hierarchy, audit threshold, or custody change is
allowed inside a live run.

## Completion terms

Certification requires:

- exactly 204 packets and 10,159 unique rows with two fresh, independently
  sealed, source-bound first-pass labels;
- 10,159/10,159 valid evidence sidecars and zero invalid or foreign evidence
  references;
- deterministic comparison over the full denominator;
- 100% review of every risk-triggered consensus row and all disagreements;
- completion of the frozen 600-row clean-consensus audit with zero terminal
  findings, or the expanded/all-population sample required by the frozen
  algorithm;
- source-bound resolution of every explicit unresolved request;
- zero missing, invalid, partial, duplicate, unbound, source-unsupported, or
  unresolved rows;
- zero active provider runtime directories and no provider stop;
- final text-free receipts binding the exact code, source versions, manifests,
  reviews, outputs, denominator, and residual zero.

No merge, publication, training-data release, threshold change, or policy
change is authorized by this amendment.
