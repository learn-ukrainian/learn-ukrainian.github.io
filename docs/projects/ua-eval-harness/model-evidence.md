# UA Eval Harness — model evidence log

> Data-backed record of model behaviour for the #2156 Ukrainian calque/grammar eval harness.
> Rule: **data, not impressions.** Every row is tool-scored or tool-verified. Raw prompts/responses
> stay out of git (kept in local `.agent/tmp/`); this log carries only scores, findings, and provenance.

## Positioning — why a *calque-specific* eval harness (related work)

Confirmed with the UNLP maintainer (2026-07-04): **there is no dedicated evaluation harness for calque.**
The adjacent work covers different axes:

- **lang-uk Ukrainian LLM Leaderboard** (`huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard`):
  17 benchmarks — FLORES/WMT (translation), XLSum (summarization), Belebele/SQuAD (QA),
  MMLU/ARC/Winogrande/TriviaQA/ZNO (reasoning/knowledge), GSM8K (math), IFEval (instruction).
  **General Ukrainian capability — no calque, no grammar.** Runs local vLLM checkpoints via `lm_eval`;
  commercial API models (OpenAI/Anthropic/Google) are a roadmap TODO, not yet supported — which is why
  our Claude/GPT/Gemini lanes are absent from it.
- **Karpov & Chernodub, UNLP 2026** (`arxiv.org/abs/2606.09334`): general minimal-edit Ukrainian GEC;
  best config Gemini 3.1-Pro F₀.₅ = 69.22 (≈90% of fine-tuned SOTA 73.14). Calque is one subset of GEC, not the focus.
- **LanguageTool** Ukrainian module: rule-based, general grammar.

**Our niche:** a dedicated **calque** evaluation harness (F/Calque-first, G/* adjacent), UA-GEC-backed,
CC-BY-4.0 attribution propagated. Maintainer explicitly welcomed UA-GEC F/Calque gold-subset use
("use it however you'd like"). Target venue: **UNLP 2027** (2026 deadline passed).

## Gemma 4 baseline (2026-07-04)

**Why Gemma 4 is the anchor model:** it sits on the public leaderboard (`gemma-4-26B-A4B-it` = **#1**,
avg rank 1.59) **and** is open-weights (Apache 2.0) **and** cheap-to-free on OpenRouter (see Cost note) →
it bridges the public leaderboard and our harness with one shared, top-ranked, reproducible model. Runs as both a *subject*
(evaluate its Ukrainian) and a candidate *reviewer* (#4309) — tested separately, no assumption that
leaderboard rank implies judge quality.

- **Lane:** `opencode` → OpenRouter. IDs: `openrouter/google/gemma-4-31b-it` (Dense),
  `openrouter/google/gemma-4-26b-a4b-it` (MoE, ~4B active/token).
- **Test:** the 3-profile UK-writing bakeoff (`BRIEF.md`, same brief the 5 fleet candidates used in #4330/#4335)
  scored with `scripts/audit/probe_uk_writing_score.py` (VESUM validity + russian-shadow + immersion).

### Deterministic writing scores

| Model | A2 (Eng-support) | B2 (pure) | Seminar | Russicisms | Notes |
|---|---|---|---|---|---|
| **gemma-4-31b-it** (Dense) | 100% | 100% | 100% | 0 | paid but negligible (see Cost note); terse (under word targets); 1 Latin-script leak `zimy` in S3 |
| **gemma-4-26b-a4b-it** (MoE, LB #1) | 98.0% | 98.4% | 99.0% | 1 (S1) | truncated to S1 only on first run (MoE-reasoning output cap); slightly lower cleanliness |

**Finding:** 31B (Dense) ≥ 26B (MoE) on our task, consistent with Dense-beats-MoE-on-quality. Both are
**near commercial-fleet parity** (codex/agy/claude were ~100% VESUM / 0 russicisms in #4335) — strong for open weights.

### Seminar fact-check (31B) — the harness thesis, demonstrated

31B scored **deterministically perfect** on the seminar profile, yet its «Веснянки» passage is
**factually flawed** when checked against the sourced facts established in #4335 (uk.wikipedia + VESUM):

- **«гаї — символічні дерева, прикрашені стрічками»** — fabrication/conflation. *Гаївки* derive from
  *гай* = **grove** (place of performance), not decorated ribbon-trees. (Flag for tool-verification;
  contradicts the sourced etymology.)
- **melody «світлість та піднесення»** — **wrong**. Веснянки are archaic, narrow-range, piercing-*гукання*
  (sourced #4335). The identical error cursor made.
- **«перемагають zimy»** — Latin-script leak (`zimy` for `зими`), also caught deterministically.

**→ Surface-clean ≠ factually-accurate.** A model that is #1-adjacent on general Ukrainian and passes
every VESUM/russicism check still fabricates folk-culture specifics and inverts the musicology — visible
only to fact-verification. This is exactly the gap the calque/fact harness exists to fill, and prime
UNLP-2027 evidence.

### Calque probe — operational finding for #4306

An initial 20-item calque probe pulled the *shortest* raw `F/Calque` rows from `ua_gec_errors`; these are
context-stripped word-forms (`рожі→мармизи`, `вдів→одягнув`) that aren't clean standalone calques →
**not test-usable**. Lesson for **#4306: the F/Calque gold subset needs curation (context, length,
clarity filters), not raw extraction.** (Russian-first counts: F/Calque = 2397 total, 871 `source_lang=ru`.)

### Per-run log

| task_id | model | lane | mode | result | finding | op-failure |
|---|---|---|---|---|---|---|
| gemma4-smoke | gemma-4-31b-it | opencode/OR | calque probe (1) | correct («на протязі»→протягом/упродовж) | — | — |
| gemma4-31b-write | gemma-4-31b-it | opencode/OR | write 3-profile | VESUM 100/100/100, 0 russ | seminar folk-fact errors | terse |
| gemma4-26b-write | gemma-4-26b-a4b-it | opencode/OR | write 3-profile | truncated (S1 only) | — | MoE-reasoning output cap |
| gemma4-26b-write2 | gemma-4-26b-a4b-it | opencode/OR | write 3-profile (retry) | VESUM 98/98.4/99, 1 russ (S1) | — | — |
| gemma-smoke2 | gemma-3-27b-it (last-gen) | opencode/OR | calque probe (1) | correct («приймати участь»→брати участь) | — | `:free` variant errored server-side |

**Provenance caveat:** OpenRouter may serve quantized weights and we do not replicate the leaderboard's
exact `(reasoning)(0-shot)` config — results are labelled **"via OpenRouter,"** never claimed identical to
the leaderboard's local vLLM run. Bit-exact reproduction (if ever needed) = self-host the Apache-2.0 HF
checkpoint locally; costs compute, not OpenRouter credit.

### Cost note (corrected 2026-07-05)

OpenRouter pricing (verified 2026-07-05 via `GET /api/v1/models`), per **million** tokens (prompt/completion):

| endpoint | prompt | completion | notes |
|---|---|---|---|
| `gemma-4-31b-it` | $0.12 | $0.35 | **default pin** — paid but negligible (a module review = fractions of a cent) |
| `gemma-4-31b-it:free` | $0 | $0 | genuinely free, but **rate-limited (per-min + per-day) and less stable** — `gemma-3-27b-it:free` already "errored server-side" in the per-run log above |
| `gemma-4-26b-a4b-it` | $0.06 | $0.33 | MoE, cheaper still |
| `gemma-4-26b-a4b-it:free` | $0 | $0 | free MoE, same rate-limit caveat |

**The lane is NOT literally "free"** — the earlier "free on OpenRouter" claim was wrong. The default is the
**paid** `-it` endpoint (stable, effectively-free at our volume); the `:free` endpoint is reachable via
`--model` for high-volume / non-critical bursts. Still a strong **offload from the metered Claude/Codex
lanes**. Any real spend is only corpus-scale throughput (#4311).

### Applied-use probes (2026-07-05, user-run) — role calibration

Beyond the deterministic writing scores, four applied probes fixed Gemma's actual fleet role:

| probe | result | verdict |
|---|---|---|
| Bridge smoke (`ask-gemma`) | returned `GEMMA_OK` | ✅ lane wired end-to-end |
| **Seminar review** | correctly BLOCKED seeded russicisms/calques, Latin-letter leakage, and imperial/decolonization framing | ✅ usable for cheap **surface review** |
| **Seminar writing** | fluent Ukrainian, but **added unsupported details / inferences outside the supplied source packet** | ❌ **not** a production autonomous seminar writer |
| **Wiki packet** (fully-supplied source records) | concise markdown + YAML, **no invented sources, every factual sentence cited** | ✅ promising for **source-constrained** wiki drafting |

**Current read (authoritative role):** usable NOW for **(a) cheap surface review** and **(b) source-constrained
wiki drafting**. **Not** a sole seminar writer and **not** a sole factual reviewer yet. For seminar / factual
modules, use it **only behind a non-Gemma source/factual gate.** This supersedes the blunt "fabricates facts
→ never a fact-checker" framing: the failure mode is **over-generation beyond the source packet**, which a
full source packet + a non-Gemma verification gate contains.

## Harness experiment: opencode vs Hermes for tooled fact-checking (2026-07-05, #2156 step 1)

**Question:** which harness grounds gemma-4-31b's seminar fact-checking better? Same prompt, same model,
same `sources` MCP server — the «Веснянки» passage with 2 planted fabrications (the model's own, from the
bakeoff above) + 3 true claims.

| | opencode (sources+lightpanda MCP) | hermes -z (sources MCP) |
|---|---|---|
| runtime | ~3 min | ~11 min |
| tool telemetry | 7 `tool_use` NDJSON events (wikipedia, definitions, heritage, search_text ×2, literary, гаївки follow-up) | real retrieval (verbatim Grade-6 textbook quotes in our MCP's source-label format) but **0 calls captured** — `-z` one-shot fires no usable per-run hook telemetry (filed #4390) |
| true claims | 3/3 CONFIRMED with real citations (its decomposition folded «пагорби» into the ritual claim) | 3/4 — its decomposition split «пагорби» into a standalone claim and left that true claim UNVERIFIED |
| fabrication: «гаї» ribbon-trees | withheld ✓ (honest UNVERIFIED: "no tool evidence for прикрашених стрічками") | **CONFIRMED ✗** — rationalized from the word «гаївки» while itself noting the detail was never found |
| fabrication: melody «світлість та піднесення» | withheld ✓ | withheld ✓ |

**Verdict: opencode is the reviewer transport** (speed, per-run observability — a tool-theatre gate is
impossible without it — and calibration: hermes-gemma endorsed a fabrication WITH tools available, the
exact confident-fabrication failure the harness exists to catch). Hermes remains the V7 writer transport.

**Both harnesses stopped short of active refutation** — the refutation evidence was one section-read away
(uk.wiki «Веснянки» §2: «Мелодії веснянок побудовані на багаторазовому повторенні однієї-двох поспівок у
межах невеликого діапазону»), but both settled for `summary` mode. → the tooled-reviewer design (brief v2,
fleet-reviewed by codex/cursor/agy 2026-07-05) makes deep-reads a deterministic post-parse gate, not prompt
prose, and requires grounding excerpts to substring-match captured tool payloads (anti-fabricated-grounding).

**Etymology nuance for the gold sheet:** ЕСУМ marks the *гаївка* etymology «неясне» (гоголь-bird / гай /
ягли-просо theories; the гай derivation is called «непереконлива» in the *ягілка* entry). Correct verdicts:
the «гаї» decorated-tree *ritual* claim → REFUTED-as-unattested; the *etymology* → CONTESTED (present both,
never assert one). This distinction is now first-class in the reviewer's verdict taxonomy.

## Live «Веснянки» proof — the tooled reviewer end-to-end (2026-07-05, #2156 design D6)

First live runs of the full merged machinery (PR #4401 transport/telemetry + PR #4414 contract/gates +
PR #4418 live-proof fixes): `build_reviewer_prompt` → `FRONTIER_OPENCODE_ROUTE` (gemma-4-31b + sources MCP,
MCP fail-fast) → NDJSON telemetry → theatre/budget/deep-read/grounding gates → verdict taxonomy.

**Run 2 scorecard (post-fixes) vs the D6 criteria:**

| criterion | result |
|---|---|
| «гаї» fabrication | ✅ `UNATTESTED_AFTER_SEARCH` + a **critical `UNATTESTED_FACT` finding** + `evidence_gaps` entry — the step-1 honest-withhold is now a first-class labeled verdict |
| melody fabrication | ❌ **CONFIRMED on a real-but-irrelevant excerpt** («Весну зустрічали радісно й пишно…» = festive greeting ≠ melodic characterization). Claim↔evidence semantic alignment is model judgment — un-gateable by construction (deepseek's #4418 review, vector (a)) |
| true claims | ✅ all CONFIRMED with section-depth wiki quotes; search protocol followed (grinchenko in the mix) |
| coverage | ✅ 8/8 claims enumerated after the #4418 prompt mandate (run 1 silently skipped the melody claim) |
| telemetry/gates | ✅ 4 tool calls captured; theatre/budget/deep-read all functioned; round-trip preserved grounding |
| grounding gate calibration | ⚠️ run 1 exposed the transport-`tool_call_id` false-negative (fixed in #4418); run 2 exposes **quote abridgment** — the model ellipsizes excerpts («Весня́нки**...** назва…») → 4/7 legit groundings fail the literal substring check (#4416 item 3, now P1) |

**The finding that frames step 3:** tools + deterministic gates shrank the fabrication surface at the
cheap tier — ungrounded gemma asserted both fabrications (step 1); tooled-and-gated gemma correctly
UNATTESTED one and emitted a critical finding — but still rationalized the other into CONFIRMED with an
irrelevant real quote. Whether a stronger tooled model closes that alignment gap (and whether tooling
lifts cheap→frontier on exactly this axis) is the step-3 bakeoff's central measurement, scored with the
locked asymmetric constants (`qg_factcheck_scoring.py`: CONFIRMED-on-fabricated = −100 fatal).
