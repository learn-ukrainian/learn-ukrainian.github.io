# QG Layer B entailment-gate design

**Version:** 2
**Date:** 2026-07-10
**Authors:** GPT-5.6 Sol (lead); revision panel: Codex/GPT-5.6, AGY/Gemini-3.5-Flash-High, and Claude-Infra
**Status:** Design only. No runtime or repository behavior changes are included in this revision.

Normative terms such as **MUST**, **MUST NOT**, and **AUDIT** are binding requirements for the proposed `v2b` gate.

## Changelog: version 1 → version 2

| Requirement | Version 2 change |
|---|---|
| **R1** | Replaces parallel candidate tuples with immutable `AnchorCandidate` records, stable event/output identities, diagnostic-only source indices, candidate/window hashes, and a complete-candidate-set invariant. |
| **R2** | Adds a normative `ordered_segment_spans` contract for ellipsized excerpts. Segments must be ordered, non-overlapping, raw-mappable, and confined to one captured output. Cross-event stitching is forbidden. |
| **R3** | Defines deterministic canonical-source identity, fail-closed deduplication and aggregation, and an exhaustive relation × reviewer-verdict decision table. Search-only verdicts remain `AUDIT` until a live search-coverage gate exists. |
| **R4** | Treats raw output as delimited untrusted data, adds deterministic injection screening, specifies support-span requirements, and adds adversarial injection and irrelevant-offset probes. |
| **R5** | Extends the Phase 0 label contract with expected Layer A decisions/reasons, complete candidate records, segment-level ground-truth offsets, scan completeness, candidate eligibility/error status, and `MIXED`. |
| **R6** | Restricts the first implementation PR to Phase 0 documentation, schema, annotation guidance, schema validation tests, and optionally adjudicated labels. Runtime behavior is explicitly out of scope. |

## 1. Current state

Issue #4797 separates grounding into two questions: provenance anchoring followed by claim entailment, while admissible grounding remains a hard precondition for live QG scoring. [#4797](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4797)

Layer A is implemented as the selectable `v2` gate. It:

- Uses a default `τ=0.75`.
- Returns `anchored`, `abstained`, similarity, one source index, and one normalized-output span.
- Explicitly reserves raw-output entailment for a future Layer B. [`grounding_gate_v2.py`](../../../scripts/audit/grounding_gate_v2.py#L2-L48)
- Extracts digit and proper-noun-like salients from the evidence excerpt and checks their alignment against a candidate raw-output window. [`grounding_gate_v2.py`](../../../scripts/audit/grounding_gate_v2.py#L51-L99)
- Scans at most the first 50,000 output characters. [`grounding_gate_v2.py`](../../../scripts/audit/grounding_gate_v2.py#L385-L400)

The current shadow snapshot at `τ=0.75` contains:

- 1,310 checked groundings.
- 736 v2-effective groundings.
- 140 exact-match abstain recoveries.
- A net gold-true recall gain of 72.
- 115 v1-accepted/v2-rejected regressions.
- 42 v2-incremental gold-false audit candidates.

A false fixture claim with genuinely present source text is not a Layer A false positive: Layer A establishes provenance, not whether the source supports the reviewer’s verdict.

### [R2] Quantified real-loss mechanism

A deterministic audit examined 69 similarity-relevant hard rejects from the 115 regressions. Triage classified 46 as correct tightening and 23 as possible real losses.

All **23/23 real losses**, approximately 20% of the full regression set, have the same structure:

- The evidence excerpt joins multiple genuine source fragments with `...` or `…`.
- The fragments occur in one captured output.
- The best fragment similarity is already `1.0`.
- Current Layer A collapses the fragments into one enclosing span, after which locality or alignment checks reject the candidate.

Therefore:

1. Lowering `τ` cannot recover these rows; their similarity is already `1.0`.
2. Ordered multi-span provenance is the structural recall lever.
3. Layer B cannot repair the loss unless Layer A first materializes the segments and permits the claim to reach Layer B.
4. Multi-span provenance does not itself prove entailment. Layer B must judge the claim against the raw source output, not the concatenated excerpt.

Two of the 23 rows also involve `коцюба`/`кочерга` lexical variation between claim and evidence. Multi-span anchoring is necessary but may not be sufficient for those rows; the lexical policy is specified in §3.1.

Corpus spot verification established:

| Fact group | Status |
|---|---|
| Franko, Vienna University, 1893, dissertation and doctorate | Verified in configured corpus sources |
| Lesya Ukrainka/Larysa Kosach, 1871–1913 | Verified in configured textbook sources |
| Skovoroda, return in late August 1744 | Present in captured fixture evidence, but not independently re-probed; it must not gate a content-fact decision until re-verified |

Exact multi-output abstains are currently recovered as provenance-effective while retaining an absent source index and span. [`llm_reviewer_dispatch.py`](../../../scripts/audit/llm_reviewer_dispatch.py#L1402-L1427) The current `AnchorResult` cannot expose all matching outputs, so it cannot support safe multi-source resolution. [`grounding_gate_v2.py`](../../../scripts/audit/grounding_gate_v2.py#L40-L48)

Existing tests correctly prove that a real but irrelevant excerpt may pass Layer A. Claim-to-source entailment belongs to Layer B. [`test_grounding_gate_v2.py`](../../../tests/test_grounding_gate_v2.py#L117-L128)

Fixtures currently label claim truth and fabrication class but do not label excerpt provenance, ground-truth offsets, source relation, or candidate completeness. [`vesnianky.json`](../../../tests/fixtures/qg_bakeoff/vesnianky.json) [`ahatanhel-krymskyi.json`](../../../tests/fixtures/qg_bakeoff/ahatanhel-krymskyi.json)

For seminar modules, invalid grounded fact checks make the factual sweep incomplete and cause terminal failure. [`qg_workflow.py`](../../../scripts/audit/qg_workflow.py#L1417-L1522) CLI success ultimately requires `terminal_verdict == PASS`. [`qg_workflow.py`](../../../scripts/audit/qg_workflow.py#L2162-L2168)

## 2. Design options

| Option | Shape | Advantages | Material problems | Disposition |
|---|---|---|---|---|
| A. Deterministic alignment only | Compare claim numbers, entities, negation, and tokens with raw output | Cheap, reproducible, strong on literal conflicts | Cannot reliably decide attribution, role swaps, scope, implicit inversion, or over-generalization | Reject as insufficient |
| B. LLM judge on every Layer A pass | Send every claim and raw output to one semantic judge | Broad semantic coverage and simple conceptual flow | Highest cost and latency; same-family self-approval risk; prompt-injection exposure; avoidable calls for literal conflicts | Reject as primary design |
| C. Hybrid staged | Source/error checks → deterministic conflicts → qualified cross-family judge for undecided rows | Preserves deterministic fail-closed behavior, covers semantic distortions, limits model spend, and exposes stage decisions | Requires richer Layer A records, structured judge contracts, labels, and calibration | **Recommend** |
| D. Two-cheap-model ensemble | Two inexpensive judges; accept only on agreement | Checks some stochastic errors | Doubles calls, retains correlated overlap bias, and raises audit volume; inexpensive models must first clear the labeled Ukrainian relation set | Retain only as a measured fallback experiment |

## 3. Recommendation: verdict-aware hybrid Layer B

### 3.1 B0 — candidate materialization [R1] [R2]

Layer A MUST return immutable records rather than parallel source-index and span arrays.

#### `AnchorSegment` contract

All offsets are half-open Unicode code-point offsets. Hashes use the UTF-8 encoding of the referenced text.

```text
AnchorSegment {
  segment_index: integer >= 0

  excerpt_normalized_start: integer >= 0
  excerpt_normalized_end: integer > excerpt_normalized_start

  output_normalized_start: integer >= 0
  output_normalized_end: integer > output_normalized_start

  output_raw_start: integer >= 0
  output_raw_end: integer > output_raw_start

  normalized_segment_sha256: 64 lowercase hexadecimal characters
  raw_segment_sha256: 64 lowercase hexadecimal characters
}
```

A segment is valid only when:

1. Its normalized-output span maps deterministically to its raw-output span.
2. Normalizing the raw span reproduces the normalized segment.
3. Its recorded hashes match caller-extracted text.
4. No normalization boundary is ambiguous.

An unmappable or ambiguous segment produces `AUDIT`, never a guessed raw span.

#### `AnchorCandidate` contract

```text
AnchorCandidate {
  schema_version: "qg-anchor-candidate.v1"

  candidate_id: stable SHA-256 identifier
  event_output_id: stable SHA-256 identifier
  canonical_source_id: stable SHA-256 identifier
  source_index: integer >= 0              # diagnostic only

  tool_identity: {
    raw_name: string
    canonical_name: string
  }

  query_identity: {
    canonical_json: string
    sha256: 64 lowercase hexadecimal characters
  }

  raw_output_sha256: 64 lowercase hexadecimal characters
  normalized_output_sha256: 64 lowercase hexadecimal characters

  output_capture_complete: boolean
  anchor_scan_complete: boolean

  match_type:
    "EXACT_CONTIGUOUS" |
    "FUZZY_CONTIGUOUS" |
    "ORDERED_EXACT_SEGMENTS"

  similarity: number in [0, 1]
  tool_query_matched: boolean

  eligibility:
    "ELIGIBLE" |
    "INADMISSIBLE_SOURCE" |
    "TOOL_ERROR" |
    "AMBIGUOUS_ERROR" |
    "INCOMPLETE_CAPTURE"

  error_status:
    "NONE" |
    "STRUCTURED_ERROR" |
    "AMBIGUOUS_STRING_ERROR" |
    "TRANSPORT_ERROR" |
    "TRUNCATED_OUTPUT"

  ordered_segment_spans: non-empty immutable tuple<AnchorSegment>
}
```

`source_index` MUST NOT participate in stable identity because event order can change across replay and sidecars.

`candidate_id` MUST cover:

- `event_output_id`;
- match type;
- every ordered segment span;
- raw and normalized output hashes;
- the candidate contract version.

`event_output_id` MUST be derived from a versioned canonical representation of:

- canonical tool identity;
- canonical query;
- structured status/error envelope;
- stable document/source identifiers, when the tool supplies them;
- raw-output hash;
- output-capture completeness.

Strings are hashed as captured UTF-8 bytes. Structured outputs require deterministic canonical JSON before hashing. Two records with the same `event_output_id` but different canonical identity material or raw bytes constitute an integrity failure and produce `AUDIT`.

#### Candidate-set result

```text
AnchorSetResult {
  schema_version: "qg-anchor-set.v1"

  decision: "ANCHOR" | "REJECT" | "AUDIT"
  reason: registered machine-readable reason

  candidate_set_complete: boolean
  candidate_count_before_dedup: integer >= 0
  candidates: immutable tuple<AnchorCandidate>
}
```

The following invariant is mandatory:

```text
decision == ANCHOR  =>  candidate_set_complete == true
```

Layer A MUST enumerate every qualifying candidate across every captured output. If repetition guards, scan caps, capture truncation, mapping failures, or resource bounds prevent complete enumeration, the result is `AUDIT`.

No implementation may return “the best four” candidates while silently discarding the rest. A later operational cap may limit Layer B to four distinct outputs, but a complete set exceeding that cap produces `AUDIT` before semantic judgment.

Exact multi-output abstains remain `AUDIT` until this contract is implemented end to end.

#### `ordered_segment_spans` [R2]

An ellipsized excerpt may become `ORDERED_EXACT_SEGMENTS` only when all of the following hold:

1. The excerpt contains an explicit `...` or `…` separator.
2. Every non-empty excerpt fragment is independently present after the approved formatting/Unicode normalization.
3. All segments belong to one `event_output_id`.
4. Segment order matches excerpt order.
5. Segment spans are non-overlapping in both normalized and raw output:
   `previous.end <= next.start`.
6. Every segment has a verified normalized-to-raw mapping.
7. Every digit and salient anchor is aligned within its own segment.
8. Every valid occurrence assignment is enumerated, or the row becomes `AUDIT`.

Cross-event stitching is forbidden. If an excerpt is supportable only by joining fragments from different event outputs, Layer A returns:

```text
REJECT / CROSS_EVENT_STITCH_FORBIDDEN
```

The implementation MUST NOT collapse ordered segments into an authoritative `(first_start, last_end)` span. An enclosing range may be derived for diagnostics, but it cannot replace the segment list.

The first `v2b` cut supports only `ORDERED_EXACT_SEGMENTS`. It does not introduce a lower threshold or fuzzy synonym replacement for ellipsized excerpts.

#### Lexical-variant policy [R2]

Layer A establishes faithful provenance for the reviewer’s excerpt. It MUST NOT treat synonyms as quotation-equivalent.

- Formatting, whitespace, casefolding, and approved Unicode normalization remain permitted.
- VESUM may prove that inflected forms share a lemma for deterministic claim analysis, but it does not prove synonymy.
- `коцюба` and `кочерга` MUST NOT be substituted for each other by the anchor matcher.
- If the excerpt matches raw output exactly but the claim uses a lexical variant, Layer B evaluates the claim against the raw output.
- If the excerpt itself differs lexically from the raw output, the first release rejects or audits it under existing Layer A rules.
- Any future lexical-equivalence feature requires a versioned, source-verified lexicon, labeled probes, and separate calibration.

The design therefore does not claim automatic recovery of all 23 rows until the two lexical-variation rows are adjudicated under this distinction.

#### Layer B source window

Each eligible candidate is converted into a separate immutable judge window:

```text
JudgeWindow {
  candidate_id: string
  canonical_source_id: string
  raw_output_sha256: string

  raw_window_start: integer >= 0
  raw_window_end: integer > raw_window_start
  raw_window_sha256: string

  logical_unit_kind:
    "FULL_OUTPUT" | "PARAGRAPH" | "SECTION" | "JSON_SUBTREE"

  logical_unit_complete: boolean
  contains_all_anchor_segments: boolean
}
```

Window selection rules:

1. Use the full raw output when it fits the prompt envelope.
2. Otherwise use the complete containing paragraph, section, or JSON subtree plus bounded adjacent context.
3. The window MUST contain every ordered anchor segment associated with that candidate.
4. A partial logical unit, missing segment, hash mismatch, or prompt-budget truncation produces `AUDIT`.
5. Layer B never judges the concatenated evidence excerpt in place of raw output.

### 3.2 B1 — deterministic source admissibility and tool-error gate [R1] [R3]

Before semantic judgment:

1. Preserve existing tool-theatre, source-depth, and source-type checks. Layer B cannot rehabilitate an inadmissible source. [`qg_workflow.py`](../../../scripts/audit/qg_workflow.py#L1417-L1469)
2. Inspect structured status and error envelopes before converting mappings or lists to flattened text.
3. Classify every candidate’s `eligibility` and `error_status`.
4. An all-error candidate set returns `REJECT`.
5. An ambiguous string that may be an error returns `AUDIT`.
6. An incomplete captured output or incomplete scan returns `AUDIT`.
7. A recognized error candidate alongside a complete valid candidate is recorded but excluded from semantic support aggregation; it does not invalidate the valid candidate by itself.
8. A source rejected by the existing admissibility gates remains non-supporting.

This closes the path where exact error boilerplate can satisfy provenance matching.

### 3.3 B2 — deterministic claim-vs-raw conflict screen

B2 operates on `fact_check.claim`, never on `evidence_excerpt`.

For each eligible candidate, it may return:

```text
ENTAILS             # only for explicitly whitelisted structured schemas
CONTRADICTS
TOOL_ERROR
UNDECIDED
```

High-certainty `CONTRADICTS` cases include incompatible:

- numbers, dates, percentages, and units;
- named entities;
- explicit polarity or negation;
- attributed actors;
- subject/object roles where the structure is explicit;
- structured field values.

Free-text token overlap MUST NOT produce `ENTAILS`. Deterministic entailment is permitted only for a versioned allowlist of structured tool schemas whose field semantics directly express the claim.

For Ukrainian morphology:

- Batch surface forms through `scripts.verification.vesum.verify_words()` and use returned lemma/POS/tags. [`vesum.py`](../../../scripts/verification/vesum.py#L52-L102)
- Reuse the existing chunked lookup pattern rather than suffix heuristics. [`content_lexicon_reconciler.py`](../../../scripts/lexicon/content_lexicon_reconciler.py#L178-L190)
- Missing data, incompatible analyses, absent proper-noun coverage, or mere synonymy produces `UNDECIDED`.
- VESUM failure must never be converted into an invented equivalence.

### 3.4 B3 — qualified cross-family entailment judge [R4]

Run one tool-disabled, structured-output judge over residual candidates after B1 and B2.

#### Input contract

```json
{
  "schema_version": "qg-layer-b-judge-input.v1",
  "fact_checks": [
    {
      "fact_check_id": "stable-id",
      "claim": "claim text",
      "reviewer_verdict": "CONFIRMED",
      "candidate_sources": [
        {
          "candidate_id": "sha256-id",
          "canonical_source_id": "sha256-id",
          "tool": "query_wikipedia",
          "status": "completed",
          "raw_output_sha256": "sha256",
          "window_start": 1200,
          "window_end": 2410,
          "window_sha256": "sha256",
          "logical_unit_complete": true
        }
      ]
    }
  ]
}
```

The evidence text itself is supplied only through the untrusted-data blocks defined below.

#### Output contract

```json
{
  "schema_version": "qg-layer-b-judge-output.v1",
  "fact_checks": [
    {
      "fact_check_id": "stable-id",
      "source_relations": [
        {
          "candidate_id": "sha256-id",
          "relation": "ENTAILS",
          "support_spans": [
            {
              "start": 147,
              "end": 284,
              "role": "SUPPORTS"
            }
          ],
          "confidence": "high",
          "prompt_injection_observed": false
        }
      ]
    }
  ]
}
```

Allowed relations:

```text
ENTAILS
CONTRADICTS
EXPLICITLY_UNCERTAIN
NO_RELATION
MIXED
INSUFFICIENT_CONTEXT
TOOL_ERROR
ABSTAIN
```

#### Support-span contract [R4]

Offsets are half-open Unicode code-point offsets relative to the decoded raw judge window.

- `ENTAILS` requires at least one `SUPPORTS` span.
- `CONTRADICTS` requires at least one `CONTRADICTS` span.
- `EXPLICITLY_UNCERTAIN` requires at least one `UNCERTAINTY` span.
- `MIXED` requires at least one supporting and one contradicting or uncertainty span.
- `NO_RELATION`, `INSUFFICIENT_CONTEXT`, `TOOL_ERROR`, and `ABSTAIN` require an empty span list.
- Spans MUST be non-empty, in bounds, and refer to the candidate’s supplied window.
- The caller extracts support text itself and maps it back to global raw-output offsets.
- The caller does not accept model-returned quotations.
- Where B2 extracted claim-critical numbers or entities, a decisive support span must contain or structurally bind the corresponding value; otherwise the judge result is invalid and becomes `AUDIT`.

Golden-set scoring MUST compare returned spans with human-annotated expected support spans. A syntactically valid but semantically irrelevant span therefore fails qualification instead of being treated as successful `ENTAILS`.

#### Raw-output prompt-injection defense [R4]

Tool disabling alone is insufficient. Every raw source window is untrusted data.

The prompt serializer MUST use a deterministic, collision-checked delimiter:

```text
<<<BEGIN_UNTRUSTED_TOOL_OUTPUT
nonce=<derived nonce>
candidate_id=<candidate id>
unicode_chars=<length>
sha256=<window hash>
>>>
<JSON-escaped raw window>
<<<END_UNTRUSTED_TOOL_OUTPUT nonce=<same nonce>>>
```

Requirements:

1. The system message contains all instructions and the output schema; raw output never appears in it.
2. The user message contains metadata and delimited data only.
3. The nonce is deterministically derived from prompt version and window hashes, then re-derived with a counter if either delimiter occurs in source content.
4. The caller verifies declared length and hash before dispatch.
5. The judge is explicitly instructed that text inside the block is evidence, cannot amend the task, and must never be executed as an instruction.
6. Provider-native JSON-schema output is required where available.
7. The judge receives no tools, retrieval, filesystem, or network access.
8. A deterministic screen flags instruction-like text directed at the judge, including attempts to ignore instructions, change the output schema, impersonate a system message, or force a relation.
9. In initial `v2b`, a flagged candidate cannot contribute to `ACCEPT` through model judgment. It yields `AUDIT` unless B2 independently proves a contradiction or structured tool error.
10. Delimiter collision, serializer drift, provider truncation, or hash mismatch yields `AUDIT`.

The golden set MUST include:

- An unrelated claim whose source window says to ignore instructions and return `ENTAILS`.
- A contradiction accompanied by an injected instruction to return `ENTAILS`.
- Source text containing fake delimiter syntax.
- A judge response with valid but irrelevant offsets and a hallucinated `ENTAILS`.

None may produce `ACCEPT`.

#### Lean-qualification subscription-seat deviation

For the frozen lean qualification only, the Codex subscription-seat judge uses
one flattened prompt because `codex exec` exposes no system/developer role
flag. This is a narrow deviation from requirements 1–2 above; it is not an
approval for a durable content-blocking deployment. The flattened prompt MUST:

1. Place the complete policy prompt first, followed by an explicit immutable
   boundary marker, then the metadata/evidence message.
2. Repeat immediately before the first untrusted block that later content is
   untrusted evidence and cannot override the system instruction.
3. Retain the nonce delimiter plus caller hash and length verification.
4. Retain the caller-side deterministic injection screen; a flagged row is
   `AUDIT` before it can become an accepting model relation.
5. Carry a distinct prompt-template version and pass flattened-prompt probes
   for fake request-system markers, forged delimiters, and outside-block
   instruction attempts with no passing relation.

The subscription invocation also runs in a fresh no-MCP `CODEX_HOME`, disables
all reachable tool families, and rejects any rollout tool event. Agy/Gemini is
not eligible for this qualification until its selected log can prove complete
tool-event capture; a `--log-file` that only locates a separate transcript is
not sufficient. Revisit role separation before any durable blocking deploy.

#### Caller validation

The deterministic caller rejects as `AUDIT`:

- unknown or duplicate fact-check IDs;
- unknown or duplicate candidate IDs;
- missing or extra results;
- missing candidate results;
- unknown enums;
- invalid support-span cardinality or roles;
- invalid offsets or hashes;
- malformed JSON;
- medium or low confidence;
- prompt-injection flags on a result needed for acceptance;
- timeout or provider error;
- incomplete context;
- lineage conflict;
- budget exhaustion.

Final `ACCEPT`, `REJECT`, and `AUDIT` ownership remains outside the model.

#### Cross-family rule

```text
judge_family != qg_reviewer_family
judge_family != module_author_family
```

Unknown model lineage produces `AUDIT`. A qualified route must have separately cleared the labeled Ukrainian relation set. Current source code includes Gemini and Claude frontier route examples, but no specific model string is normative. [`llm_reviewer_dispatch.py`](../../../scripts/audit/llm_reviewer_dispatch.py#L41-L52)

If no qualified third-family route is available, the row remains `AUDIT`.

### 3.5 B4 — canonical-source aggregation [R3]

#### Canonical source identity

A `canonical_source_id` is derived from:

1. Canonical tool identity.
2. Stable corpus document ID, URL/revision, or equivalent source identifier when supplied.
3. Stable section/item identity when supplied.
4. Query mode and logical source unit.
5. Identity-contract version.

When a tool exposes no stable document identity, `event_output_id` becomes the canonical source identity with `identity_strength=EVENT_OUTPUT_ONLY`.

Deduplication is allowed only when candidates have identical:

- canonical source identity material;
- raw-output hash;
- capture-completeness flags;
- logical-unit identity;
- relevant ordered segment spans.

Under uncertainty, retain both candidates. If retaining both exceeds capacity, return `AUDIT`. Never deduplicate merely because normalized text is equal.

The following always produce `AUDIT`:

- one canonical ID mapping to inconsistent identity material;
- an apparent hash collision;
- a dedup operation that would hide differing raw bytes;
- identity uncertainty that prevents preserving all candidates.

#### Candidate and source aggregation

Within one canonical source:

- Repeated identical candidates may be deduplicated under the rules above.
- `NO_RELATION` alongside exactly one decisive relation does not change that relation.
- `ENTAILS` plus `CONTRADICTS` becomes `MIXED`.
- A decisive relation plus `EXPLICITLY_UNCERTAIN` becomes `MIXED`.
- Any supplied `MIXED` remains `MIXED`.
- `INSUFFICIENT_CONTEXT` or `ABSTAIN` makes the fact-check aggregate `AUDIT`; an undecided candidate might conceal material disagreement.
- Recognized structured `TOOL_ERROR` candidates are excluded only when at least one eligible non-error candidate exists.
- An all-error set aggregates to `TOOL_ERROR`.
- An unknown relation becomes `AUDIT`.

Across canonical sources, apply the same rules. Thus:

- One or more `ENTAILS`, with all other eligible sources `NO_RELATION`, aggregates to `ENTAILS`.
- One or more `CONTRADICTS`, with all others `NO_RELATION`, aggregates to `CONTRADICTS`.
- Entailment plus contradiction aggregates to `MIXED`.
- Any unresolved eligible source forces `AUDIT`.

## 4. Decision-metric specification [R3]

Layer B decides whether captured raw evidence supports the reviewer’s verdict. It does not determine global fixture truth.

### Exhaustive relation × verdict mapping

`A` = `ACCEPT`, `R` = `REJECT`, `U` = `AUDIT`.

| Aggregate relation | `CONFIRMED` | `REFUTED_BY_CONTRADICTION` | `CONTESTED` | `UNATTESTED_AFTER_SEARCH` | `UNVERIFIED_INSUFFICIENT_SEARCH` |
|---|---:|---:|---:|---:|---:|
| `ENTAILS` | A | R | R | U | U |
| `CONTRADICTS` | R | A | R | U | U |
| `EXPLICITLY_UNCERTAIN` | R | R | A | U | U |
| `NO_RELATION` | R | R | R | U | U |
| `MIXED` | R | R | U | U | U |
| `INSUFFICIENT_CONTEXT` | U | U | U | U | U |
| `TOOL_ERROR` | R | R | R | U | U |
| `ABSTAIN` | U | U | U | U | U |

Any unmapped verdict, relation, or combination defaults to `AUDIT`.

`CONTESTED + MIXED` remains `AUDIT` in the initial release. The current fact-check schema has one `grounding` object, so multi-document contestation cannot yet demonstrate that the reviewer actually cited both sides. [`qg_schema.py`](../../../scripts/audit/qg_schema.py#L626-L653) Initial acceptance of `CONTESTED` is limited to a single admissible source explicitly marking the issue uncertain.

`UNATTESTED_AFTER_SEARCH` always returns `AUDIT` from `v2b` until a separate live search-coverage gate proves the required source set and queries were completed. It cannot bypass entailment merely because the prompt requests a search list.

### Layer A × Layer B composition

| Layer A outcome | Layer B | Fact-check decision | Module consequence |
|---|---|---|---|
| Hard provenance reject, including cross-event stitching | Not run | `REJECT` | Terminal content failure |
| Incomplete candidate set, incomplete scan/capture, ambiguous mapping, or internal error | Not run | `AUDIT` | Incomplete and non-shippable |
| Unique or complete multi-candidate anchor | Expected verdict-relative relation | `ACCEPT` | Eligible for live-admissible scoring |
| Unique or complete multi-candidate anchor | Decisive wrong relation or `NO_RELATION` | `REJECT` | Terminal content failure |
| Unique or complete multi-candidate anchor | Abstain, invalid judge result, lineage conflict, insufficient context, injection risk, or budget failure | `AUDIT` | Incomplete and non-shippable |
| Search-only verdict without live coverage gate | Not applicable | `AUDIT` | Incomplete and non-shippable |

### Module-level metric

Emit:

```text
fact_checks_total
fact_checks_accept
fact_checks_reject
fact_checks_audit
coverage_missing
layer_a_rejects
layer_a_audits
layer_a_multispan_candidates
layer_b_deterministic_rejects
layer_b_llm_calls
layer_b_llm_errors
layer_b_injection_audits
layer_b_cost_usd
```

Module status:

- `PASS`: every factual claim has exactly one fact-check decision, every decision is `ACCEPT`, and every search-only verdict has passed a future live search-coverage gate.
- `FAIL_CONTENT`: at least one `REJECT`.
- `NEEDS_AUDIT`: no reject exists, but at least one `AUDIT`, missing/duplicate coverage item, infrastructure failure, or budget failure exists.
- Both non-pass statuses map to `terminal_verdict=FAIL`.

Scoring retains:

- `model_judgment`: the reviewer’s unmodified verdict.
- `live_admissible`: credits the verdict only when both Layer A and Layer B accept it.

This extends the current scoring split that neutralizes inadmissible positive verdicts while preserving raw judgment. [`qg_bakeoff.py`](../../../scripts/audit/qg_bakeoff.py#L1941-L1986)

### Capacity envelope

Proposed incremental per-module limits:

```text
max_layer_b_calls = 1
max_layer_b_distinct_outputs = 4
max_layer_b_prompt_tokens = 10,000
max_layer_b_completion_tokens = 800
max_layer_b_cost_usd = 0.25
```

These are qualification targets, not permission to truncate:

- Count the complete serialized prompt, including delimiters and schemas.
- If a complete candidate set or complete logical units do not fit, return `AUDIT`.
- The Layer B allowance is separate from and additive to existing module and batch budgets.
- Any final values require measured Phase 1 data.

At the currently configured example prices, 10,000 input and 800 output tokens correspond to approximately $0.0205 for the Gemini profile and $0.21 for the Claude spot-audit profile. The fact-check schema allows up to 40 rows, so large modules may legitimately audit rather than receive incomplete evidence. [`qg_schema.py`](../../../scripts/audit/qg_schema.py#L684-L690)

## 5. Failure-mode analysis

| Failure class | Required handling |
|---|---|
| Fabricated excerpt value | Layer A digit/salient alignment rejects it. |
| Real excerpt, altered claim value | B2 compares claim-side values with raw output and rejects. |
| Meaning inversion | Explicit polarity conflicts reject in B2; implicit inversion goes to B3. |
| Attribution or role swap | B2 handles structured roles; otherwise B3 with required support spans. |
| Over-generalization | Scope and quantifier changes go to B3; overlap alone never accepts. |
| Ellipsized genuine excerpt | Layer A records ordered same-output spans; Layer B judges the claim against raw output. |
| Cross-event joined excerpt | Layer A hard-rejects `CROSS_EVENT_STITCH_FORBIDDEN`. |
| Lexical variant | No synonym substitution in Layer A; claim-side semantics go to B3. |
| Tool error as evidence | B1 uses structured status before flattening; all-error evidence rejects. |
| Missing contradictory candidate | Complete-candidate invariant forces `AUDIT`. |
| Wrong normalized/raw mapping | Segment-level hashes and round-trip mapping force `AUDIT`. |
| Dedup hides disagreement | Exact canonical identity is required; uncertainty retains both or audits. |
| Prompt injection | Delimited untrusted data, deterministic screening, structured output, and injection probes prevent acceptance. |
| Valid but irrelevant support offset | Span-role contract and annotated overlap tests fail qualification. |
| Judge timeout or malformed result | `AUDIT`. |
| Search-only verdict without coverage proof | `AUDIT`. |

Layer B does not decide global source authority or retrieve better evidence. It evaluates the relation between the captured admissible source output and the reviewer’s verdict.

## 6. Test plan

### Existing Layer A probes that remain load-bearing

The current suite must remain green, including:

- Fabricated excerpt and digit mismatch.
- Ambiguous boilerplate.
- Insufficient evidence mass.
- Ordered ellipsis within one output.
- Rejection of cross-event stitching.
- Real-but-irrelevant excerpt passing Layer A.
- Tool/query as a soft provenance signal.
- Default v1 and explicit v2 wiring.
- Gold-false claim with genuinely present excerpt.
- Candidate truncation and pathological repetition failing closed.

[`test_grounding_gate_v2.py`](../../../tests/test_grounding_gate_v2.py)

### Phase 0 contract tests [R5] [R6]

The first PR’s validation tests must prove that the label schema:

1. Accepts a valid contiguous candidate.
2. Accepts a valid ordered multi-segment candidate.
3. Requires stable event/output, raw-output, normalized-output, and segment hashes.
4. Requires complete candidate records keyed by event/output identity.
5. Rejects `expected_layer_a_decision=ANCHOR` when the candidate set is incomplete.
6. Rejects overlapping or out-of-order segments.
7. Rejects segments spanning different event outputs.
8. Rejects invalid normalized-to-raw round trips.
9. Treats source index as diagnostic rather than identity.
10. Rejects inconsistent canonical-source identity.
11. Accepts `MIXED` as a human source relation.
12. Requires eligibility and error status for every candidate.
13. Requires `qualification_eligible=false` for a partial label pilot.
14. Rejects unknown decision, reason, relation, and status enums.

These are schema/data tests only. They must not change Layer A runtime behavior.

### Future Layer B golden probes [R2] [R4]

At minimum:

1. `franko-1893-vienna`: positive ordered multi-span.
2. `lesya-1871-1913`: positive ordered multi-span.
3. `zhnyvarski-boroda`: positive ordered multi-span.
4. Adversarial cross-event join: must not anchor.
5. Ellipsized row with claim-side lexical variation.
6. Real excerpt, wrong claim digit.
7. Real excerpt, wrong person or place.
8. Explicit negation inversion.
9. Subject/object or attribution swap.
10. `some` → `all`, local → national, possible → certain.
11. Raw error string cited as support.
12. Unique anchor with decisive entailment.
13. Multi-source entailment plus neutral.
14. Multi-source entailment plus contradiction → `MIXED`.
15. Multi-source set containing an undecidable eligible source → `AUDIT`.
16. `REFUTED_BY_CONTRADICTION` accepted only on contradiction.
17. `CONTESTED` accepted only on explicit uncertainty in the initial release.
18. Search-only verdict → `AUDIT` without live coverage proof.
19. Unicode, whitespace, stress-mark, and normalization mapping.
20. Window missing required context → `AUDIT`.
21. Invalid offsets, missing rows, extra rows, malformed enum, or malformed JSON.
22. Timeout, provider error, lineage conflict, or budget skip.
23. VESUM unavailable or ambiguous → undecided.
24. Injection instruction attempting to force `ENTAILS`.
25. Fake delimiter injection.
26. Valid but irrelevant support offsets.
27. Combined module aggregation: any reject or audit prevents terminal pass.
28. Cost cap checked before any logical-unit truncation.

## 7. Rollout

### Phase 0 — labels and contracts [R5]

The versioned sidecar schema is `qg-layer-b-labels.v2`.

Normative shape:

```yaml
schema_version: qg-layer-b-labels.v2
dataset_id: string
source_artifacts:
  - artifact_sha256: sha256
    fixture_set_sha256: sha256

qualification_eligible: false
qualification_blockers:
  - string

cases:
  - case_id: string
    artifact_sha256: sha256
    fixture_id: string
    fact_check_id: string
    fact_check_index: integer

    claim: string
    evidence_excerpt: string
    claim_is_true: boolean
    expected_reviewer_verdict: enum

    expected_layer_a_decision: ANCHOR | REJECT | AUDIT
    expected_layer_a_reason: registered enum
    anchor_scan_complete: boolean
    candidate_set_complete: boolean

    candidates_by_event_output_id:
      "<event-output-sha256>":
        - candidate_id: sha256
          canonical_source_id: sha256
          source_index: integer
          tool_identity: object
          query_identity: object
          raw_output_sha256: sha256
          normalized_output_sha256: sha256
          output_capture_complete: boolean
          anchor_scan_complete: boolean
          match_type: enum
          similarity: number
          eligibility: enum
          error_status: enum
          ordered_segment_spans:
            - segment_index: integer
              excerpt_normalized_start: integer
              excerpt_normalized_end: integer
              output_normalized_start: integer
              output_normalized_end: integer
              output_raw_start: integer
              output_raw_end: integer
              normalized_segment_sha256: sha256
              raw_segment_sha256: sha256
          expected_source_relation:
            ENTAILS | CONTRADICTS | EXPLICITLY_UNCERTAIN |
            NO_RELATION | MIXED | TOOL_ERROR |
            INSUFFICIENT_CONTEXT
          expected_support_spans:
            - start: integer
              end: integer
              role: SUPPORTS | CONTRADICTS | UNCERTAINTY

    expected_aggregate_relation: enum
    expected_fact_check_decision: ACCEPT | REJECT | AUDIT
    context_sufficient: boolean
    failure_class: registered enum

    corpus_verification_status:
      VERIFIED | FIXTURE_ATTESTED | UNVERIFIED | NOT_APPLICABLE

    annotators:
      - string
    adjudication:
      status: AGREED | ADJUDICATED | UNRESOLVED
      adjudicator: string | null
      note: string
```

Required Layer A reason vocabulary includes at least:

```text
ANCHORED_CONTIGUOUS
ANCHORED_ORDERED_SEGMENTS
PRESENT_MULTI
ABSENT
FUZZY_AMBIGUOUS
OUTSIDE_SCAN
RAW_MAPPING_AMBIGUOUS
CROSS_EVENT_STITCH_FORBIDDEN
INCOMPLETE_CAPTURE
INCOMPLETE_CANDIDATE_SET
TOOL_ERROR
INSUFFICIENT_MASS
BELOW_TAU
DIGIT_NOT_ALIGNED
SALIENT_NOT_ALIGNED
```

Annotation procedure:

1. Freeze artifact and fixture hashes.
2. Label claim truth separately from provenance.
3. Enumerate every matching output before choosing a decision.
4. Record exact normalized and raw spans for every excerpt segment.
5. Confirm all multi-span fragments belong to one event output.
6. Record scan and capture completeness independently.
7. Classify candidate eligibility and structured/ambiguous errors.
8. Judge the claim against raw output, not against the excerpt.
9. Record expected support spans for decisive relations.
10. Use two annotators; adjudicate every disagreement.
11. `UNRESOLVED` cases remain qualification blockers.
12. Independently re-probe any fixture-only fact before it gates a content decision.

Human-label the union of:

- All 234 v1-reject/v2-effective recoveries.
- All 115 regressions.
- All 159 abstains.
- All 42 gold-false incremental candidates.
- All 76 currently unlabeled recoveries.
- A stratified control sample from both-gates-accept and both-gates-reject rows.

These categories overlap and must be treated as a set union. Counts derive from the 2026-07-09 effective shadow baseline (`audit/2026-07-09-qg-shadow-baseline/baseline-effective-tau075.md`, local evidence artifact); re-derive from the artifact at labeling time rather than trusting these numbers. *(Editorial citation added by the committing reviewer, 2026-07-10.)*

### First PR scope [R6]

The first PR MUST contain only:

- `docs/projects/ua-eval-harness/layerb-entailment-gate-design.md`
- A versioned JSON Schema, such as `schemas/qg-layer-b-labels.v2.schema.json`
- A Layer B annotation guide.
- Schema validation tests.
- The required golden-case skeletons.
- Optionally, the adjudicated label union.

It MUST NOT modify:

- `grounding_gate_v2.py`;
- `AnchorResult` or grounding behavior;
- gate flags;
- scoring;
- shadow execution;
- judge prompts or routes;
- budgets or caches;
- `groundings[]`;
- generated audit, status, review, or telemetry artifacts.

A partial annotation pilot is allowed only when:

```text
qualification_eligible = false
```

and explicit blockers identify the missing union or adjudication. It cannot authorize Phase 1 qualification.

### Phase 1 — separate implementation and offline shadow

After Phase 0 is complete, separate reviewed PRs may implement candidate materialization and Layer B shadow execution.

Replay all 1,310 stored groundings and publish by seat, fixture, verdict, and failure class:

- Layer A decision and reason.
- Candidate-set completeness.
- Ordered segment records.
- B1 and B2 outcomes.
- Judge relation, confidence, injection signal, and span validity.
- Final accept/reject/audit.
- False accept, false reject, and audit rates.
- Live-admissible deltas.
- Calls, tokens, cost, and latency.
- Multi-source and canonical-identity distributions.

Keep v1 and Layer-A-only columns unchanged for comparison.

### Phase 2 — qualification thresholds

Blocking thresholds:

- 100% on adversarial digit, name, inversion, over-generalization, error, multi-span, cross-event, injection, and offset probes.
- Judge relation agreement at least 90% overall and 85% in every failure class. [#4797 qualification note](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4797#issuecomment-4919012040)
- Zero observed unsafe accepts and a one-sided 95% upper confidence bound no greater than 1%.
- At least 95% recall on human-admissible expected relations.
- Audit rate no greater than 15% on unique anchors and 25% overall.
- `p95` incremental spend no greater than $0.25 per module.
- No existing Layer A probe regression.
- Human audit of every Layer A regression and newly accepted Layer B row.
- No candidate-set, identity, span, delimiter, or hash-integrity failure.

### Phase 3 — canary

Introduce separate flags such as:

```text
grounding_gate_version=v2b-shadow
grounding_gate_version=v2b
```

Canary requirements:

- No invalid fact checks or required ungrounded findings.
- No missing claims.
- Two consecutive green runs.
- Re-run after any prompt, gate, schema, model, route, fixture, scorer, delimiter, or label change.
- Evidence no older than seven days. [`calibration_criteria.md`](calibration_criteria.md#L109-L139)
- One module each from FOLK, BIO, and HIST.
- `CONTESTED + MIXED` remains audit-only until an independently reviewed multi-grounding contract exists.

### Phase 4 — cutover and operations

Cut over only after Phase 2 and two consecutive Phase 3 runs pass.

After arming:

- Any unsafe false accept automatically disarms Layer B.
- More than 15% terminal failures over 30 consecutive live passages pauses the lane.
- Track provider errors, audit rate, injection audits, relation distribution, candidate completeness, cost variance, and window failures.
- Maintain a one-step rollback to Layer-A-only and invalidate Layer B cache rows. [`calibration_criteria.md`](calibration_criteria.md#L153-L161)

Cache identity MUST include:

- raw-output and judge-window hashes;
- ordered segment spans;
- candidate and canonical source identities;
- judge prompt/delimiter version;
- judge model and family;
- Layer A version and `τ`;
- Layer B rules version;
- VESUM data version;
- sidecar schema and label-set hashes.

## 8. Remaining questions for later phases

1. Which qualified three-family route matrix clears the labeled Ukrainian relation set within the cost ceiling?
2. Which structured tool schemas are safe for deterministic `ENTAILS`, rather than deterministic rejection only?
3. Should the search-coverage gate ship before or alongside active `v2b`?
4. How should source authority be represented once multi-document `groundings[]` is designed?
5. What per-class corpus size is required to establish the 1% unsafe-accept confidence bound?
6. Does the proposed 10,000-token envelope preserve complete logical units across all target tools, or must limits become tool-schema-specific?
7. Should future source-level contestation distinguish contradiction within one document from disagreement across independent documents?
