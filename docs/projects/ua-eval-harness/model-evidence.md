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
avg rank 1.59) **and** is open-weights (Apache 2.0) **and** free on OpenRouter → it bridges the public
leaderboard and our harness with one shared, top-ranked, reproducible model. Runs as both a *subject*
(evaluate its Ukrainian) and a candidate *reviewer* (#4309) — tested separately, no assumption that
leaderboard rank implies judge quality.

- **Lane:** `opencode` → OpenRouter. IDs: `openrouter/google/gemma-4-31b-it` (Dense),
  `openrouter/google/gemma-4-26b-a4b-it` (MoE, ~4B active/token).
- **Test:** the 3-profile UK-writing bakeoff (`BRIEF.md`, same brief the 5 fleet candidates used in #4330/#4335)
  scored with `scripts/audit/probe_uk_writing_score.py` (VESUM validity + russian-shadow + immersion).

### Deterministic writing scores

| Model | A2 (Eng-support) | B2 (pure) | Seminar | Russicisms | Notes |
|---|---|---|---|---|---|
| **gemma-4-31b-it** (Dense) | 100% | 100% | 100% | 0 | free on OpenRouter; terse (under word targets); 1 Latin-script leak `zimy` in S3 |
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

### Cost note

31B is **free** on OpenRouter and near commercial-parity on UA writing → a lane that can **offload work
from the metered Claude/Codex lanes**, not a place to spend. Any future spend is only for corpus-scale
throughput (#4311) if free-tier rate limits bind.
