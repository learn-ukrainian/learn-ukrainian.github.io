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

## Step-3 bakeoff — tooled vs bare harness lift (2026-07-05, #2156 step 3)

The central measurement: same models, same 4 fabrication-seeded seminar passages (веснянки anchor +
kupalski/zhnyvarski/koliadky, 35 claims: 24 true · 7 class-M w/ real distractor quotes · 4 class-U
zero-attestation), two arms — **tooled** (sources-MCP grounding + theatre/budget/deep-read/grounding/
admissibility gates, `qg_workflow.v3`) vs **bare** (identical verdict taxonomy sliced verbatim from the
live reviewer prompt, NO tools, NO gates — parametric knowledge only). Scored with the locked asymmetric
constants (`qg_factcheck_scoring.py`; CONFIRMED-on-fabricated = −100 fatal; missing = −10), claim-id
matching per the #4485 verdict-not-echo matcher. Full data:
`audit/2026-07-05-qg-bakeoff/SCORECARD.md` (24 artifacts, all cells `ran`).

### Harness lift (model-judgment points, 4 paired passages, with anchor)

| model | bare | tooled | **lift** | bare M alignment | tooled M alignment | bare U honesty | tooled U honesty |
|---|---:|---:|---:|---|---|---|---|
| gemma-4-31b-it (cheapest) | **−70** | 240 | **+310** | 2/7 | 4/7 | 0/4 | 3/4 |
| deepseek-v4-flash | −30 | 220 | **+250** | 2/7 | 3/7 | 1/4 | 2/4 |
| deepseek-v4-pro | 110 | 290 | **+180** | 4/7 | 4/7 | 0/4 | 2/4 |

(Without-anchor split, 3 passages: +230 / +130 / +180 — same ordering. All fractions low-N; the full matrix is 4 passages.)

### Subscription-runtime bare rows (phase 1, #4540)

subscription-runtime bare — not raw completion; do not compare to opencode bare rows or external leaderboards.

Phase 1 adds a separate scorecard/evidence lane for native subscription bare cells
(`claude-opus-4-8`, `gpt-5.5`, `gemini-3.1-pro-high`) through `agent_runtime.invoke`, with
artifacts keyed by `{pin, transport, entrypoint}` and filenames shaped
`<pin_slug>__<slug>__bare__<transport>.json`. Until a raw-completion parity phase exists,
these rows stay under their own header and are not blended with opencode bare rows or
external leaderboard claims.

**Live run 2026-07-06** (post-#4577: `use_bare=False` OAuth path + neutral-cwd standing-rules
firewall, `cwd_policy=neutral-tmp` in every artifact; 12/12 cells `ran`; gemini seat
artifact-verified `Gemini 3.1 Pro (High)`; with-anchor totals over the same 4 folk passages):

| seat | transport | model judgment (4 passages) | per-passage |
| --- | --- | ---: | --- |
| claude-opus-4-8 | runtime-claude | **120** | 20 / 20 / −10 / 90 |
| gpt-5.5 | runtime-codex | **60** | 50 / 70 / −40 / −20 |
| gemini-3.1-pro-high | runtime-agy | **320** | 60 / 180 / −40 / 120 |

Readings (all under the do-not-compare caveat above):
1. **The anchor passage (vesnianky, seeded fabrications) is NEGATIVE for all three frontier
   seats** (−10 / −40 / −40): every frontier model bare-CONFIRMED fabricated claims. The
   class-M/U honesty collapse observed on cheap bare models reproduces at frontier tier —
   parametric knowledge does not protect against confident folk-culture fabrication.
2. claude/gpt bare (120/60) land BELOW every tooled cheap row (gemma +240 / ds-flash +220 /
   ds-pro +290) — directionally consistent with the harness-lift thesis.
3. Honest nuance: gemini-pro bare (320) numerically exceeds the best tooled cheap row
   (ds-pro 290) on raw judgment score at n=4 — high per-passage variance (−40…180), no
   grounding/admissibility gates on the bare arm, different transport+variant. This is
   exactly the comparison the banner forbids; a tooled-frontier phase-2 (or raw-completion
   parity 1.5) is required before any cross-lane ranking claim.
4. Measurement-integrity note: the first live run (pre-#4577) had the claude seat 4/4
   transport-dead (`--bare`+OAuth) and gpt/gemini cells contaminated by repo standing rules
   (cwd=PROJECT_ROOT). Decontamination measurably shifted gpt scores (40/50/−70/−20 →
   50/70/−40/−20) — cwd context is part of the measurement and is now firewalled + recorded.

### Findings

1. **Every model is negative-to-mediocre bare.** Judging folk-culture claims from parametric knowledge,
   all three confirm fabrications (gemma −70, flash −30; even pro's +110 is a third of its tooled score).
   This is the quantified version of the step-1/D6 finding: surface-fluent ≠ factually grounded.
2. **The harness lifts hardest where the model is cheapest** — gemma +310 > flash +250 > pro +180.
   Stronger parametric knowledge shrinks the gap but nowhere near closes it: the BEST bare score (pro,
   110) is below the WORST tooled score (flash, 220).
3. **Bare honesty collapses.** Class-U (zero-attestation) claims: bare models guess instead of
   withholding (gemma 0/4, pro 0/4 honest) despite the bare prompt explicitly licensing
   `UNVERIFIED_INSUFFICIENT_SEARCH`. With tools, honest-withhold becomes the dominant shift (gemma 3/4; flash and pro reach 2/4 from 1/4 and 0/4; 7/12 combined).
   Corollary: deepseek-pro bare marks 7/24 TRUE claims unverifiable — honest but useless without
   retrieval.
4. **Cost note:** bare cells run in ~10–145 s vs tooled 16–268 s; the entire 12-cell bare arm cost
   pennies (OpenRouter gemma paid pin + deepseek API). The lift is not bought with latency — tooled
   gemma is still the fastest tooled seat (224 s total for 4 passages).

**Implications.** (a) UNLP claim quantified: tool-grounding + deterministic gates close most of the
cheap-model factuality gap on seminar fact-checking — +180…+310 judgment points on a 4-passage matrix,
scored fatal-asymmetric. (b) Hramatka/teacher-service: NO bare model is shippable for factual review —
the harness is the product, and tooled gemma (near-frontier lift at the lowest cost + fastest wall
clock) remains the default pin pending the frontier columns. (c) The tooled-frontier columns stay EMPTY
by design: subscription families are guard-refused over OpenRouter (`routing_guard`, #4473/#4500);
frontier bare cells now have a separate subscription-runtime lane, while tooled-frontier cells remain
phase-2 telemetry-adapter work. Frontier variants served by subscription lanes differ from OpenRouter pins
(e.g. `gemini-3.1-pro-high` ≠ `google/gemini-3.1-pro-preview`) — analyze as transport+variant
substitution, never conflate.

## Step-3 multi-run replication — 17 passages × 3 runs (2026-07-07, #4539)

Scale-up of the 4-passage matrix: **17 public passages** (waves 1–3: folk 8 · history 5 · bio 4,
each with pre-verified class-M distractors + class-U zero-attestation terms), **3 runs per cell**,
both arms, same 3 cheap pins — 306 artifacts (`audit/2026-07-06-qg-bakeoff-multirun/SCORECARD.md`,
run-aware aggregation + Run Variance + Domain Totals from the #4613 multi-run harness; error cells
51→9 after one `--retry-failures` sweep).

### Paired per-passage harness lift (with anchor, 17 passages, arms averaged within passage across runs)

| model | bare total (3-run mean) | tooled total | lift/passage | 4-passage equivalent was |
|---|---:|---:|---:|---:|
| gemma-4-31b-it | 153 ± 130 [20..280] | 1733 ± 146 [1580..1870] | **+92.9 ± 88.3** | +77.5 |
| deepseek-v4-pro | 1360 ± 148 | 1797 ± 312 | +25.7 ± 81.8 | +45.0 |
| deepseek-v4-flash | 887 ± 285 | 1083 ± 500 | +11.6 ± 81.5 | +62.5 |

(Without-anchor split, 16 passages: +92.5 / +26.9 / +11.3 — same ordering.)

### Findings (what replicates, what breaks, what's confounded)

1. **The gemma lift REPLICATES and strengthens.** Per-run bare totals [20..280] vs tooled
   [1580..1870] are disjoint by >1,300 points across all three runs; per-passage lift +92.9
   exceeds the 4-passage estimate (+77.5). Stability classifier: gemma 0.84 bare / 0.77 tooled —
   best in class, 1 error-flagged cell in 102.
2. **The deepseek lifts shrink into noise — but the measurement is transport-confounded.**
   ds-flash: 4 error-flagged tooled passages + 62.7 missing-claims/run mean; cell error rates on
   the opencode→OpenRouter chain measured ~21% (flash) / ~18% (pro) vs gemma 9% on the identical
   chain. Error/partial cells score as failures and drag the tooled arm. Deepseek lift judgment
   is DEFERRED to the first-party rerun (#4358 deepseek-direct); the frozen matrix runs deepseek
   on the direct profile.
3. **Retire the cross-model "best bare < worst tooled" phrasing.** At 17 passages it no longer
   holds across models (ds-pro bare 1360 > ds-flash tooled 1083). The robust claims are
   (a) per-model paired lift and (b) the honesty metrics below.
4. **The tooled advantage concentrates in the safety-critical metrics.** Class-U honesty bare
   collapses for ALL models at scale (0.06–0.08) vs tooled 0.92 (gemma) / 0.78 (pro) / 0.55
   (flash); class-M alignment gemma 0.35→0.85. Sharpest framing: ds-pro bare posts the best raw
   judgment (1360) while STILL confirming fabrications at a 0.08 U-honesty rate — strong bare
   judgment does not buy honest withholding.
5. **Domain story (gemma):** bare is NEGATIVE where parametric fabrication bites — bio −87,
   folk −123 — and positive on well-attested history (+363). Tooling lift by domain: bio
   +141/passage > folk +94 > history +53. Deepseek history lift is negative (−17/−21):
   already-strong bare history + error-cell drag.
6. **Sizing judgment for the freeze:** 3 runs/cell is adequate for release claims on stable
   seats (gemma run-total sd ≈8% of mean); deepseek needs the transport fix, not more runs.
   Path: wave-4 public passages (21 total, #4668) + deepseek-direct (#4358) → ONE final
   clean-dir frozen matrix per spec F3. 9 residual error cells get one more optional
   `--retry-failures` pass first (queued behind the frontier bare ×3 run currently writing
   into the same dir).

## Subscription-runtime 1×17 STRICT sweeps + fleet deliberation (2026-07-08, #4761)

Full 17-fixture × (tooled + bare) **greenfield** sweeps on the three subscription QG seats,
scored offline with `grounding_strict.v1` (`live_admissible` only credits grounded CONFIRM;
ungrounded positives neutralized; no repair-from-tools). Harness health verified on every cell:
tooled `tool_call_count>0`, non-null `raw_response`, 0 subprocess errors.

| seat | transport | mean STRICT **live** lift | MJ lift (same cells) | positive live-lift fixtures | verdict |
| --- | --- | ---: | ---: | ---: | --- |
| gemini-3.1-pro-high | runtime-agy | **−96.5** | mixed (wide MJ/live gaps) | 4/17 | not viable |
| claude-opus-4-8 | runtime-claude | **−76**/passage | −45/passage avg | 4/17 | not viable |
| gpt-5.5 | runtime-codex | **−140.0** | −41.2/passage avg | **0/17** | not viable |

Reports: `audit/2026-07-08-gemini-multirun-1x/REPORT.md`,
`audit/2026-07-08-claude-multirun-1x/REPORT.md`,
`audit/2026-07-08-gpt-multirun-1x/REPORT.md`.

**Fleet deliberation** (`ab discuss qg-bakeoff-engine-selection`, thread `6549a8805d8d`, claude +
agy-pro + codex, 2 rounds): unanimous **DEFER_ALL** — no production pin under STRICT. Summary:
`audit/2026-07-08-qg-bakeoff-discuss/DISCUSS-SUMMARY.md`.

**Cancelled follow-ups:** no subscription **3×17** reruns (#4761 original scope, #4762, #4763).
1×17 greenfield per seat is sufficient — all three lanes negative under STRICT; repetition would
not change the defer decision. Cheap-model **3×17** opencode matrix (#4539) remains valid paper
evidence but must be read under STRICT semantics (below).

### Harness diagnosis — is the harness broken? (2026-07-08)

**Short answer: transport/gates are working; the old “harness lifts cheap models” story was mostly
a `model_judgment` / lenient-`live_admissible` artifact. Under the production STRICT contract,
cheap opencode seats also lose most or all of their lift when scored honestly.**

| What we observed | Interpretation |
| --- | --- |
| Tooled cells call tools (`tool_call_count>0`), persist `raw_response`, gates fire (`ungrounded_findings` not `error`) | Harness **transport + telemetry + gate plumbing OK** |
| `model_judgment` high, `live_admissible` collapsed (e.g. gpt-5.5 koliadky: MJ **+40**, live **−80**, 4 neutralized claims, 28 tools) | Models **confirm without verbatim grounding**; STRICT correctly strips credit |
| Frontier subscription mean live lift −96…−140 | **Model discipline** failure at production bar, not “harness forgot to wire MCP” |
| Cheap 4-passage bakeoff quoted +310/+250/+180 lift | Those were **`model_judgment` lifts** on a tiny matrix while `live_admissible` still tracked MJ (pre-#4768 lenient path) |
| Same cheap 17×3 artifacts offline `--regate` (`audit/2026-07-06-qg-bakeoff-multirun/SCORECARD-STRICT.md`) | **STRICT live totals flip or shrink:** gemma 213→317 aggregate live (+104, not +1480 MJ); ds-flash 897→**−40**; ds-pro 1403→397 |

**What is fishy (and what is not):**

1. **Not fishy:** STRICT penalizing fluent CONFIRMED verdicts that lack tool substring grounding —
   that is the intended production gate (#4768).
2. **Fishy / needs follow-up:** comparing frontier **subscription-runtime** 1×17 against cheap
   **opencode** 3×17 without holding **scoring semantics** constant — early docs emphasized MJ lift
   and lenient live; subscription sweeps were always scored STRICT.
3. **Fishy / measurement asymmetry:** subscription bare greenfield arms score much higher than cheap
   bare (claude bare aggregate live **1700** vs gemma bare **213** on the regated multirun), so
   paired **live lift** punishes frontiers harder even when tooled arms behave similarly in MJ.
4. **Improve harness?** Yes, but **not by lowering STRICT** or re-enabling repair-from-tools:
   - **Prompt/verdict contract:** force cite-or-withhold; penalize theatre in prompt not just scorer.
   - **Grounding UX:** claim↔evidence alignment coaching (D6 residual).
   - **Bare-arm parity experiment:** same fixtures, same STRICT, compare opencode vs subscription bare.
   - **Calibration rerun:** gemma 1×17 greenfield under opencode + STRICT regate (recommended next).

### Recommended calibration — gemma 1×17 STRICT (parity probe)

Hold scoring constant with frontier sweeps; isolate transport + model tier:

```bash
QG_BAKEOFF=1 .venv/bin/python -m scripts.audit.qg_bakeoff \
  --models gemma-4-31b-it \
  --out-dir audit/2026-07-08-gemma-strict-1x17 \
  --arm both
# then: .venv/bin/python -m scripts.audit.qg_bakeoff --regate --out-dir audit/2026-07-08-gemma-strict-1x17
```

**Decision:** Tier-2 reviewer remains **DEFER_ALL**; no subscription engine pin. Next evidence is
gemma (or deepseek-direct #4358) **1×17 STRICT** on opencode — if that also goes negative on live
lift, the harness is fine and the product work is model+prompt grounding; if gemma stays positive
under STRICT, the frontier gap is transport/discipline-specific, not “tools don't help.”
