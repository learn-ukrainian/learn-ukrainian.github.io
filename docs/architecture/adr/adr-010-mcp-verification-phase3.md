# ADR-010: MCP verification layer — Phase 3 architectural redesign

**Status**: PROPOSED
**Date**: 2026-05-11
**Deciders**: Krisztian (pending), Claude (Opus 4.7 xhigh, this draft)
**Related**:
- #1657 (parent EPIC — "MCP verification-layer improvements, 3-phase plan")
- #1877, #1878 (Phase 2 remaining sub-issues — `verify_quote`, `verify_source_attribution`)
- #1879, #1880 (Phase 2 in-flight PRs at draft time — both OPEN, not yet merged)
- #1658, #1659, #1660, #1669, #1679 (Phase 1, closed 2026-05-04/05)
- #1807 (codex-tools writer treating `<verification_trace>` as prose — downstream symptom of Phase 2/3 gap)
- #1663 (Антоненко-Давидович 46% coverage gap — informs `completeness_note` design)
- #1662 (ЕСУМ vols 2–6 backfill — informs completeness)
- ADR-009 (timeout unification — orthogonal but format-sibling)

## Context

The MCP `sources` server at `.mcp/servers/sources/server.py` currently registers **31 tools** (`grep -c 'name="' .mcp/servers/sources/server.py` returns 31 as of HEAD `3e7b8b5e27`). Phase 1 of EPIC #1657 closed in early May: rename `search_etymology` → `search_grinchenko_1907`, ship `sovietization_risk` on СУМ-11 rows, and rewrite tool descriptions to surface known coverage gaps. Phase 2 added `check_modern_form` + `check_russian_shadow` (closed), with `verify_quote` and `verify_source_attribution` open in PRs #1880 and #1879.

Phase 3 is the architectural lift the EPIC body explicitly defers to a separate ADR (this one):

> Phase 3 designed via separate ADR before implementation.

The EPIC proposes three sub-topics: (a) `verify_external(claim, source_hint)` as a server-side Tier-2 ladder, (b) a unified structured-verdict envelope across all `verify_*` and `check_*` tools, (c) per-dimension review bundles `review_dim_russicism`, `review_dim_naturalness`, etc. that compose the underlying primitives.

The pressure for this work is real. The V7 reviewer prompt at `scripts/build/phases/linear-review-dim.md` (Tier-1 audit section, lines 39–79) asks the LLM to compose 4–6 MCP calls per dimension per claim and reason about the joint outcome. Under length pressure the prompt skips calls, hallucinates verdicts when calls return empty, and fabricates citations to sound authoritative — exactly the failure mode #1807 documents and the Сибір case study (May 2026) caught only via manual review. Phase 2 collapses three of those compositions into single primitives. Phase 3 is the question: how much further should we collapse, and where does collapsing stop working?

The 5 QG dimensions enforced by `scripts/common/thresholds.py:49-55` are: `pedagogical`, `naturalness`, `decolonization`, `engagement`, `tone`. Not all five are equally amenable to server-side bundling, and treating them uniformly is the first design trap to avoid.

## Decision

Phase 3 ships **three asymmetric tracks**, not a uniform redesign:

1. **`verify_external` ships, but narrowly scoped and renamed** — a hard-coded Tier-2 ladder over a curated allowlist of public sources, not a generic web-fetch. The name `verify_external` collides with the existing `search_external` (server.py:197, the internal external-articles corpus); rename the new tool **`verify_web_claim(claim, claim_type, source_hint=None)`** to avoid that collision.

2. **The structured envelope ships, but as an additive opt-in** — define `VerificationVerdict` as the canonical response shape for **new** `verify_*` / `check_*` / `review_dim_*` tools. Existing tools migrate opportunistically (each next-touch PR, not a single migration PR), and tools whose semantics fundamentally don't fit (`search_text`, `search_sources`, `search_literary`) stay on a per-chunk envelope rather than being forced into a per-claim envelope.

3. **`review_dim_*` ships for two dimensions only — `naturalness` and `decolonization`.** The other three QG dims (`pedagogical`, `engagement`, `tone`) have no algorithmic substrate and a server-side bundle would be cargo-culted. Those dims stay as model-side reasoning over the existing primitives. This is the most opinionated piece of this ADR — `review_dim_*` is a real architectural primitive only where the underlying evidence can be deterministically computed.

### Concrete surface

```
.mcp/servers/sources/server.py        New tools registered:
                                        verify_web_claim
                                        review_dim_naturalness
                                        review_dim_decolonization

.mcp/servers/sources/envelope.py      NEW. Pydantic models for VerificationVerdict,
                                      EvidenceItem, CompletenessNote. JSON-schema
                                      export for CI validation.

.mcp/servers/sources/web_ladder.py    NEW. Curated allowlist + per-source fetcher
                                      + claim-type-aware cache TTL.

scripts/audit/check_mcp_envelopes.py  NEW. CI test: every new verify_*/check_*/
                                      review_dim_* response validates against its
                                      declared output schema.

scripts/build/phases/linear-review-dim.md
                                      Reviewer prompt updates: for DIM in
                                      {naturalness, decolonization}, the four-step
                                      audit collapses to a single review_dim_*
                                      call. For the other three DIMs, the existing
                                      composition stays.
```

### Track 1 — `verify_web_claim`

**Input shape**:

```python
verify_web_claim(
    claim: str,                      # what to verify, in Ukrainian or English
    claim_type: Literal[             # determines ladder + cache policy
        "historical_fact",           # → Wikipedia + ukrlib + linguistics-blog allowlist
        "orthography_rule",          # → Pravopys 2019 (already in MCP) + slovnyk.me
        "source_attribution",        # → already covered by verify_source_attribution; reject here
        "current_event",             # → REJECT. Out of scope. Current events belong in WebSearch.
        "biographical",              # → Wikipedia + Encyclopedia of Ukraine when ingested
    ],
    source_hint: str | None = None,  # optional bias to a specific allowlisted source
    confidence_threshold: float = 0.7,
)
```

**Hard-coded Tier-2 ladder** (not learned routing — too small a domain to justify training):

| `claim_type`         | Ladder order                                                                  |
|----------------------|-------------------------------------------------------------------------------|
| `historical_fact`    | `query_wikipedia` → `search_literary` (already-ingested) → ukrlib.com.ua HEAD |
| `orthography_rule`   | `query_pravopys` (local) → slovnyk.me orthography → web allowlist             |
| `biographical`       | `query_wikipedia` → e-ushe.org (Encyclopedia of Modern Ukraine, when ingested) |
| `source_attribution` | reject; use existing `verify_source_attribution`                              |
| `current_event`      | reject; out of scope (volatile, no canonical caching strategy)                |

The allowlist is checked into `web_ladder.py` and lives alongside the code. Adding a new source is an explicit PR + ADR addendum — not a runtime config. This is intentional: a verification tool whose source list can drift at runtime cannot be reasoned about by reviewers.

**Caching**:

- `historical_fact`, `biographical`, `orthography_rule` → 30-day TTL (already the policy for `query_wikipedia`).
- Hash key: `sha256(claim_normalized + claim_type + source_hint)` — claim normalization reuses the same NFKD/case/quote/whitespace pipeline `verify_quote` introduced (PR #1880 establishes this normalization; reuse don't reinvent).
- Cache backend: same SQLite cache table `query_wikipedia` uses today (`data/sources.db`).

**Output**: `VerificationVerdict` envelope (Track 2). When sources disagree, return all hits sorted by ladder priority with per-hit confidence; never collapse to a single answer.

**Auth/rate-limit**: per-host token bucket in `web_ladder.py`. Default: 1 request / source / second. Wikipedia and slovnyk.me already have user-facing rate-limit conventions documented; copy theirs. No API keys committed — sources requiring keys are rejected from the allowlist outright.

**Why not generic web-fetch**: a generic `verify_external(claim, any_url)` looks more flexible but is the wrong abstraction. The reviewer doesn't need flexibility — it needs reliability. A 30-source allowlist verified against in 6 lines of code is auditable; a generic fetcher is a recurring source of "the model cited a 2023 Medium post" failures. The user-side Tier-2 escalation (Explore + WebFetch) keeps its niche for genuinely novel claims; `verify_web_claim` handles the long tail of canonical-source verification.

### Track 2 — `VerificationVerdict` envelope

**Canonical shape** (pydantic, in `envelope.py`):

```python
class EvidenceItem(BaseModel):
    raw_text: str                          # verbatim quote from the source
    source: str                            # canonical source slug ("sum11", "grinchenko_1907", "wikipedia", "ukrlib", ...)
    edition: str | None = None             # e.g. "1970-1980" for СУМ-11, "1907" for Грінченко
    year: int | None = None
    url: str | None = None                 # for live sources
    chunk_id: str | None = None            # for FTS5-indexed sources
    confidence: float                      # 0.0–1.0, per-evidence
    sovietization_risk: int | None = None  # 0/1/2 from #1659, when applicable
    modernity_status: Literal[             # from check_modern_form, when applicable
        "modern_codified", "archaic_only", "has_archaic_form", "unknown"
    ] = "unknown"

class CompletenessNote(BaseModel):
    """When a source's coverage is partial, document the gap.
    Example: search_style_guide returns "Антоненко-Давидович indexed 279/600+ entries"."""
    indexed: int
    canonical_estimate: int | None
    fallback_route: str | None             # human-readable next-step

class VerificationVerdict(BaseModel):
    result: Literal["verified", "not_verified", "disagreement", "out_of_scope"]
    confidence: float                      # 0.0–1.0, aggregate over evidence
    evidence: list[EvidenceItem]           # always present, possibly empty
    completeness_note: CompletenessNote | None = None
    schema_version: Literal["v1"] = "v1"   # for migration management
```

**Migration strategy** — opportunistic, not big-bang:

| Cohort                                      | Migration trigger                  | Envelope status     |
|---------------------------------------------|------------------------------------|---------------------|
| New tools (`verify_web_claim`, `review_dim_*`) | Phase 3 ships them with envelope from day 1 | Required            |
| In-flight Phase 2 (`verify_quote`, `verify_source_attribution`) | Add envelope BEFORE these merge if cheap, otherwise migrate in immediate follow-up | Strongly preferred  |
| Already-shipped `verify_*` / `check_*` (`verify_word`, `verify_words`, `verify_lemma`, `check_modern_form`, `check_russian_shadow`) | Migrate in next PR that touches the tool for any reason | Opportunistic       |
| `search_*` (chunk-returning) tools          | Stay on per-chunk envelope (each chunk already carries `source`, `confidence_score`, `sovietization_risk` for sum11) | NOT migrated to per-claim envelope |
| `query_*` (live single-source) tools        | Wrap response in envelope on next touch | Opportunistic       |

**Why opportunistic**: a single migration PR touching 31 tools is impossible to review, breaks every consumer at once, and produces a 5000-line diff. Per-tool migration produces small, reviewable PRs and keeps the system shippable throughout.

**Schema enforcement**:

- pydantic at runtime in MCP handlers (handler returns `VerificationVerdict(...)`, server serializes to JSON).
- JSON-schema export in `scripts/audit/check_mcp_envelopes.py` — for every tool declared envelope-compliant, the CI script invokes the handler with a fixture input and validates the response. New tool with envelope but no fixture → CI fail.
- The envelope's `schema_version` field allows additive evolution: v1 is locked once ACCEPTED; new fields require v2 + dual-emit during transition.

**What stays on raw output** (`search_text`, `search_literary`, `search_sources`, `search_external`, `search_images`): these are retrieval-style tools that return ranked chunks, not verification verdicts. Forcing a `result: verified` field on a retrieval call is a category error. Their per-chunk metadata (`source`, `chunk_id`, `confidence_score`, `sovietization_risk`) already covers the spirit of the envelope; locking that as a separate `ChunkEnvelope` typed dict is fine but not required as Phase 3 scope.

### Track 3 — `review_dim_*` for naturalness + decolonization only

For each of the 5 QG dims, we ask: **is there an algorithmic substrate, or is this model-judgment territory?**

| Dim             | Algorithmic substrate available?                                                                                          | Ship `review_dim_*`? |
|-----------------|---------------------------------------------------------------------------------------------------------------------------|----------------------|
| `pedagogical`   | Partial: `query_cefr_level` per vocab item. But "scope appropriate for A2" is a judgment call, not a query.               | No                   |
| `naturalness`   | Yes: `check_russian_shadow` per token + `search_style_guide` per collocation + `verify_quote` per cited line + `check_modern_form` per lemma. All four are deterministic. | **Yes**              |
| `decolonization`| Yes: `sovietization_risk` per СУМ-11 citation + pre/post-Soviet attestation via `search_grinchenko_1907` + `search_heritage` for flagged archaisms. All deterministic. | **Yes**              |
| `engagement`    | None. Whether a dialogue is engaging is a model/human judgment.                                                            | No                   |
| `tone`          | None. Register-detection has weak signals but no source-of-truth tool.                                                     | No                   |

This is the most opinionated decision in the ADR and the place the user explicitly asked for pushback. The EPIC body lists `review_dim_russicism` and `review_dim_naturalness` as examples — both fit Track 3. But generalizing to "ship `review_dim_*` for every dim" would produce three near-empty bundles (`pedagogical`, `engagement`, `tone`) that do nothing the model isn't already doing better, while creating maintenance burden and a misleading API surface.

#### `review_dim_naturalness(content, level)`

**Bundle**:

1. Tokenize content into Ukrainian word forms (re-use logic from existing scripts/wiki tokenizer).
2. For each token: `check_russian_shadow(token, threshold=0.7)`. Aggregate hits with confidence ≥ 0.7.
3. Extract bigram/trigram collocations: `search_style_guide(collocation)` for each. Aggregate hits.
4. Find quoted spans (`"..."` / `«...»`): `verify_quote(author, quoted_text)` if author tag present.
5. For each non-bracketed Ukrainian lemma: `check_modern_form(lemma)`. Flag `archaic_only` lemmas without `[Archaism]` markup.

**Return shape** (envelope-conformant):

```python
VerificationVerdict(
    result="not_verified" if findings else "verified",
    confidence=...,
    evidence=[
        EvidenceItem(raw_text="кафедра приймає участь", source="antonenko_davydovych", ...),
        EvidenceItem(raw_text="вірний", source="russian_shadow_check", confidence=0.91, ...),
        ...
    ],
    completeness_note=CompletenessNote(
        indexed=279,
        canonical_estimate=600,
        fallback_route="ukrlib.com.ua/books/printit.php?tid=4002",
    ),
)
```

**No `fixes_suggested` field.** Fix generation requires module-wide context (what word does this clause want, given the lesson topic). Server-side fix proposals are brittle ("`приймати участь` → `брати участь`" is fine in isolation, but the module's surrounding sentence may need the whole clause restructured). The LLM composes fixes from the structured findings — that is the right division of labor and aligns with #M-4 (deterministic tooling for evidence, LLM for composition).

#### `review_dim_decolonization(content)`

**Bundle**:

1. For each СУМ-11-style definitional quote in content: `search_definitions(headword)` and surface `sovietization_risk`.
2. For each citation of a pre-Soviet source (Грінченко, ЕСУМ): `search_grinchenko_1907` / `search_esum` to confirm the citation exists (catches the Грінченко fabrication failure from the Сибір case study).
3. For each `[Archaism]` / `[Historism]` / `[Dialectism]` tag: `search_heritage(form)` to validate heritage classification.
4. Soviet-era keyword regex (already in `linear-review-dim.md` rule C) over module-narration text outside quoted definitions.

Same envelope shape as naturalness, no `fixes_suggested`, same rationale.

### Interaction with reviewer-as-fixer (#M-4 rule 4)

`#M-4` (deterministic over hallucination) requires that every verifiable claim is tool-backed. `review_dim_*` is exactly that pattern: the reviewer's evidence rows are now MCP-tool outputs, not model recall. The prompt simplifies from "compose 4 tool calls per finding" to "call `review_dim_naturalness`, paraphrase the structured findings into evidence_quotes, score from balance of evidence." Fix proposals stay model-side, where they need module context to be useful.

## Alternatives considered

- **Ship `verify_external` as a generic web-fetch wrapper (`claim, any_url`)** → rejected. Flexible-but-unreliable beats reliable-but-narrow only when the consumer can validate; reviewers under length pressure can't. The Сибір failure mode was the model citing plausible-looking sources without authority; a generic fetch tool makes that easier, not harder. The curated allowlist is the constraint that makes the tool trustworthy.

- **Skip Track 1 (`verify_web_claim`) entirely, strengthen per-dim tools instead** → considered seriously. Argument: Tier 2 is rare enough that user-side Explore + WebFetch is fine for the long tail, and the dim tools cover the high-volume cases. Counter-argument: the EPIC body documents repeat user-side escalation (~14 calls in the Сибір case) and #1807 attests the model skips Tier 2 under length pressure. A narrow `verify_web_claim` for canonical-source claims (Wikipedia + Pravopys + ukrlib) recovers the highest-value Tier 2 cases without scope-creep. Net: ship narrow, defer generic.

- **Big-bang envelope migration across all 31 tools in a single PR** → rejected. Unreviewable, breaks all consumers simultaneously, and the existing per-tool ad-hoc shapes are not actively harmful enough to justify a 5000-line diff. Opportunistic migration is slower but ships.

- **Ship `review_dim_*` for all 5 dimensions for symmetry** → rejected. Asymmetric APIs are uglier than symmetric ones but more honest. A `review_dim_engagement` bundle would either be a one-line LLM judgment wrapper (no value over the existing prompt) or would invent fake signals (e.g. "average sentence length") that don't actually measure engagement. The two-of-five split tells the reviewer prompt clearly: for these two dims you have a tool, for the other three you still compose model judgment over primitives.

- **Have `review_dim_*` emit `fixes_suggested` (find/replace pairs)** → rejected for Phase 3. Server has token-local view; module rewriting is a clause/sentence-level transformation that needs surrounding context. Leave fix generation to the LLM with the full module in context. Revisit if real-world telemetry shows the LLM consistently failing to compose fixes from structured findings.

- **Unify `search_*` retrieval tools into the same envelope as `verify_*`** → rejected as category error. Retrieval returns ranked chunks for the LLM to read; verification returns a verdict for the LLM to act on. Two response shapes for two intents.

- **Bake the curated web allowlist into a runtime YAML config** → rejected. A YAML in CI is editable in a PR; a runtime config drifts and bypasses ADR-level review. Hard-coded module is the friction we want.

## Consequences

**Positive**:
- Reviewer prompts for `naturalness` and `decolonization` collapse from ~30 lines of audit composition (current `linear-review-dim.md` Tier-1 audit block, §A–E) to a single call + paraphrase step. Length-pressure failure mode (#1807) goes from "skip tool calls" to "fail loudly when the tool returns disagreement."
- Tier-2 escalation has a server-side path for the canonical-source long tail; user-side Explore/WebFetch becomes the genuinely-novel-claim escape hatch, not the default.
- Structured envelope makes downstream consumers (writer prompts, audit scripts, the Monitor API) parse one shape, not 31.
- Schema-versioned envelope allows additive evolution without breaking consumers.

**Negative / risks**:
- `verify_web_claim` is a new external-network dependency in the MCP server. If Wikipedia rate-limits, builds slow. Mitigation: SQLite cache with 30-day TTL covers the vast majority of repeat queries; live failures degrade gracefully to `result="out_of_scope"` rather than crashing.
- Two of five dims having `review_dim_*` is structurally asymmetric. Maintainers will be tempted to "complete the set." This ADR has to be load-bearing against that temptation — the asymmetry is the point.
- Opportunistic envelope migration means the codebase spends months in mixed state (some tools enveloped, some not). Consumers must tolerate both shapes during transition. Mitigation: envelope ships with `schema_version="v1"`; absence of `schema_version` in a response = legacy, treat accordingly.
- `review_dim_naturalness` runs O(N tokens) `check_russian_shadow` calls per module. At ~5000 words/module this is ~5000 sequential SQLite + pymorphy3 calls. Need to confirm latency is acceptable (or batch internally — likely a `check_russian_shadow_batch` follow-up).

**Migration cost**:
- New code: `envelope.py` (~120 LOC), `web_ladder.py` (~300 LOC), 2 × `review_dim_*` handlers (~200 LOC each), `check_mcp_envelopes.py` (~150 LOC), schema-version test cases. Approx 1000 LOC + tests.
- Reviewer prompt updates: `scripts/build/phases/linear-review-dim.md` Tier-1 audit block conditionally collapses for `naturalness` and `decolonization`; ~50-line edit.
- Per-existing-tool envelope migration is its own per-PR cost (~50-100 LOC each) but spread over months.

## Open questions (raised here, resolved during implementation)

1. Does `verify_web_claim` need `claim_type="terminology"` for verifying a Ukrainian linguistic term (e.g. "is `сурогат-мова` a real linguistic-literature term")? Likely yes, ladder = `query_wikipedia` → linguistics-blog allowlist. Defer until first concrete need.
2. Does `review_dim_naturalness` need a "literary register" mode (where archaism rate is expected high) vs default (where archaism is a problem)? Probably yes via `level` parameter. Spec out during implementation.
3. Should the envelope's `evidence` list have an enforced maximum length (truncate long matches)? Yes — propose 20 items; revisit on telemetry.
4. Are `verify_quote` and `verify_source_attribution` migrating to the envelope BEFORE PRs #1879/#1880 merge, or in immediate follow-ups? Recommend: follow-ups, to avoid stalling the in-flight PRs.

## Verification

- **Implementation gate**: This ADR moves to ACCEPTED only after Krisztian sign-off. Implementation issues filed AFTER ACCEPTED, not bundled in this PR.
- **CI**: `scripts/audit/check_mcp_envelopes.py` enforces envelope shape on every new envelope-compliant tool. New tool with envelope ⟹ new fixture, or CI fails.
- **Telemetry**: writer/reviewer JSONL events `reviewer_dim_evidence` already emit per-dim evidence — extend to surface `review_dim_*` tool invocation when it fires, for measurable rollout.
- **Revisit trigger**: if `review_dim_naturalness` latency exceeds 30s/module after batching, or if `verify_web_claim` cache-miss rate stays above 30%, this ADR is candidate for amendment. If a sixth QG dimension gets added (per future curriculum work), revisit Track 3's two-of-five split.

## History

| Date       | Event                                                                                |
|------------|--------------------------------------------------------------------------------------|
| 2026-05-04 | Phase 1 closes — #1658, #1659, #1660, #1669 land                                     |
| 2026-05-05 | Phase 1 deprecation alias removed (#1679)                                            |
| 2026-05-11 | Phase 2 in flight — PRs #1879 (`verify_source_attribution`), #1880 (`verify_quote`) open |
| 2026-05-11 | This ADR drafted (Claude Opus 4.7 xhigh, headless dispatch)                          |
| TBD        | ADR ACCEPTED → implementation issues filed                                           |
| TBD        | Track 1 (`verify_web_claim`) ships → re-evaluate generic Tier-2 escape hatch         |
| TBD        | Track 2 envelope migration ≥75% of `verify_*` / `check_*` tools → consider freezing `v1` |
