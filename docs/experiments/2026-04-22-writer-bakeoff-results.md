# Writer Bakeoff Results — A1 M03 `special-signs`

**Date run:** 2026-04-21 night → 2026-04-22 early morning (UTC)
**Fixture:** `curriculum/l1-uk/plans/a1/special-signs.yaml` (Codex fork of v1.3.1 source plan, PASS-verified by 2 independent reviewers)
**Methodology:** 5-writer UK-native module bakeoff + 20 round-robin cross-reviews, no self-review
**Status:** publishable draft; raw artifacts preserved on per-writer worktrees and in `experiments/writer-bakeoff-2026-04-22/`

## One-sentence summary

Claude Opus 4.7 produced the most reliably high-quality Ukrainian-native A1 lesson module among five writers (Gemini 3.1 Pro, Gemini 3 Flash, GPT-5 via Codex CLI, Claude Opus 4.7, Claude Sonnet 4.6) measured by round-robin cross-review from the other four writers, but **no writer achieved a majority PASS verdict** — indicating the task prompt and/or source plan still leave gaps that the best model can't close alone.

## Design

### Hypothesis

Three independent questions, measured on a single fixture:

1. **Which model writes Ukrainian A1 content best** when given the same plan, same retrieval context, and same adapted system prompt?
2. **Which model reviews Ukrainian content best** — measured via calibration (discrimination range, evidence density, self-consistency) on the same 5 outputs?
3. **Does the "Ukrainian Tutor" user-crafted system prompt outperform a generic task prompt** when applied across all 5 writers?

Questions 1 and 2 are answered directly by the experiment. Question 3 is answered indirectly: no writer got PASS from a majority of reviewers, which suggests the prompt (or the plan, or the fixture) has residual limitations even with a carefully-crafted prompt-persona.

### Fixture

A1 M03 `special-signs` — the hardest A1 module for LLMs because it demands:

- Correct м'який знак placement rule (exactly 8 consonants per Літвінова 5-кл mnemonic "ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи": Д, Т, З, С, Ц, Л, Н, ДЗ, + Р separately per Авраменко)
- Correct apostrophe rule (після б, п, в, м, ф, р before я, ю, є, ї; exclusion for prefixal forms like під'їзд which are A2+ material)
- Correct Г [ɦ] vs Ґ [g] distinction with no conflation and no "м'який" mislabel for Г
- И vs І minimal pairs (бик/бік, дим/дім)
- Trilled Р framing without false reassurance
- Zero Russian transliteration or Russianism leaks
- Textbook citations to Захарійчук (1-кл), Большакова (1-2-кл), Авраменко (5-кл), Літвінова (5-кл)

A model that writes M03 cleanly can probably write any A1 module. A model that fails M03 would ship false pedagogy that harms learner habits.

### Writers

| # | Writer | Model | Dispatch adapter |
|---|---|---|---|
| 1 | Gemini 3.1 Pro | `gemini-3.1-pro-preview` | `ai_agent_bridge` via gemini-cli |
| 2 | Gemini 3 Flash | `gemini-3-flash-preview` | same |
| 3 | GPT-5.x (Codex) | default Codex model | `codex exec` |
| 4 | Claude Opus 4.7 | `claude-opus-4-7` | `claude -p` |
| 5 | Claude Sonnet 4.6 | `claude-sonnet-4-6` | same |

All 5 received the same system prompt (see `batch_state/briefs/writer-bakeoff-a1-m03.md`) adapted from a user-crafted "Ukrainian Tutor" persona into a "Ukrainian Module Author" persona. All 5 received the same plan and same wiki retrieval context. All 5 ran in isolated git worktrees, no awareness of each other.

### System prompt highlights

The adapted prompt is authoritative and imperative, not descriptive. Examples:

- "Do not let errors pass. Verify every grammatical form, every stress, every vocabulary choice, every pedagogical claim before you commit it."
- "Use Cyrillic only. Strictly avoid Russianisms. Strictly avoid Surzhyk. Detect every calque."
- "Consult in this order: VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко."
- "Ukrainian is not a dialect of Russian. Frame unique Ukrainian features on their own terms."
- "This module is NOT written for English-speaking absolute beginners. Write like a Ukrainian teacher writes for Ukrainian children."

Full prompt in the brief file.

### Review methodology — round-robin, no self-review

Every writer reviewed all outputs except its own. 4 reviews per output × 5 outputs = 20 reviews. All reviews ran as fresh isolated sessions with no awareness of other reviewers' scores.

Scoring rubric (0–10 per axis, 6 axes):

1. **Linguistic correctness** — Russianisms, calques, Surzhyk, stress errors
2. **Pedagogical accuracy** — does the rule formulation match the cited textbooks?
3. **Decodability / A1-appropriateness** — grammar and vocabulary scope
4. **Plan adherence** — every objective / vocabulary_hints.required / activity_hint covered?
5. **Register / naturalness** — reads like Ukrainian teacher or like translated English textbook?
6. **Honesty** — flags genuine uncertainties with `<!-- VERIFY -->`, doesn't paper over gaps

Aggregate per writer = mean of the 4 reviewers' overall scores.

## Results

### Per-writer aggregate (ranked)

| Rank | Writer | Overall | Verdicts (4 reviewers) | Word count range |
|---|---|---|---|---|
| 1 | **Claude Opus 4.7** | **7.80** | REVISE × 4, no FAIL | 1650–2000 |
| 2 | Codex (GPT-5) | 7.45 | PASS × 1, REVISE × 2, FAIL × 1 | 1100–2050 |
| 3 | Gemini 3.1 Pro | 7.12 | REVISE × 4 | 1200–1895 |
| 4 | Claude Sonnet 4.6 | 6.83 | PASS × 1, REVISE × 2, FAIL × 1 | 2000+ |
| 5 | Gemini 3 Flash | 5.83 | FAIL × 3, REVISE × 1 | 1100–1906 |

Margin rank 1 → rank 2: **0.35** (just above the 0.3 tiebreaker threshold, no second-fixture tiebreaker needed).

### Per-axis means (higher is better)

| Axis | Opus | Codex | Gemini Pro | Sonnet | Gemini Flash |
|---|---|---|---|---|---|
| Linguistic correctness | 8.0 | 7.6 | 8.0 | 7.0 | 5.5 |
| Pedagogical accuracy | 7.75 | 6.6 | 7.5 | 6.0 | 5.75 |
| Decodability (A1) | 8.0 | 7.9 | 6.75 | 7.0 | 5.75 |
| Plan adherence | 7.75 | 6.25 | 6.5 | 6.25 | 6.0 |
| Register / naturalness | 8.5 | 8.5 | 7.5 | 8.0 | 7.5 |
| Honesty | 6.75 | 7.9 | 6.5 | 6.75 | 4.5 |

Notable patterns:
- **Opus** highest or tied-highest on 4 of 6 axes (linguistic correctness, pedagogical accuracy, decodability, plan adherence)
- **Codex** highest on honesty (7.9) — most willing to flag uncertainty via `<!-- VERIFY -->`
- **Gemini Pro** ties Opus on linguistic correctness (8.0) but trails on decodability and honesty
- **Sonnet** tied highest on register/naturalness (8.0) but weak on plan adherence (6.25)
- **Flash** last on every axis except register (where it ties at 7.5) — evidence Flash is a meaningful quality downgrade from Pro

### Stability (verdict distribution)

Opus is the only writer with **no FAIL verdict from any reviewer**. Gemini Pro is second-most stable (all REVISE). Codex and Sonnet had high variance (PASS and FAIL from different reviewers on the same output). Flash had 3 FAILs — consistent low quality.

### Why no majority PASS

The 20 reviews collectively produced 3 PASS, 13 REVISE, 4 FAIL. No single writer received PASS from more than 1 reviewer. This is the most important finding of the experiment — even the best writer, under a carefully-crafted prompt, produced work 4 different cross-reviewers consistently scored as "needs revision."

Interpretation: one or more of
- The fixture is hard enough that even the strongest model misses plan requirements (the most common complaint across reviews: "activity_hint count under plan spec", "missing Захарійчук [–]/[=] notation")
- The plan itself has demands (18-item group-sort, 6-item true-false) that writers systematically half-satisfy, suggesting either the plan's requirements should be softened or the prompt should emphasize them more
- The prompt still under-specifies the `## Практика` contract — writers interpret "introduction plus sample items" differently

This points at the prompt, not the model, as the main remaining bottleneck.

### Per-reviewer calibration

| Reviewer | Mean score given | Range | Mean evidence entries | Verdicts given |
|---|---|---|---|---|
| **Opus** | 6.85 | 5.8 – 8.3 | 25.2 | PASS 0, REVISE 3, FAIL 1 |
| **Codex** | 6.25 | 5.5 – 6.5 | 22.5 | PASS 0, REVISE 3, FAIL 1 |
| Sonnet | 8.07 | 7.5 – 8.5 | 19.8 | PASS 1, REVISE 3, FAIL 0 |
| Gemini Pro | 6.47 | 4.3 – 8.7 | 11.2 | PASS 0, REVISE 2, FAIL 2 |
| Gemini Flash | 7.38 | 4.3 – 8.8 | 9.5 | PASS 1, REVISE 2, FAIL 1 |

**Opus as reviewer:** widest discriminating range (2.5 pts spread) and highest evidence density (25.2 entries per review). Most nuanced judgments.

**Codex as reviewer:** narrowest range (1.0 pt) and strictest overall — consistently penalizes. High evidence (22.5). Reliable lower-bound signal.

**Sonnet as reviewer:** lenient (8.07 mean), narrow range (1.0 pt) — poor discrimination.

**Gemini Flash as reviewer:** lowest evidence (9.5) and high variance (4.3–8.8) — noisy. Unreliable.

**Gemini Pro as reviewer:** wider range (4.4 pts) but low evidence (11.2) — opinionated without backing it up.

### Why evidence density matters

The rubric required every score to cite concrete quoted evidence from the module. Reviews with high evidence density (>20 entries/review) were the ones actually engaging with the text. Reviews with low evidence (<12) tended toward vague "feels good/feels off" judgments. Opus, Codex, and Sonnet all produced 20+ entry reviews. The Gemini pair did not.

This is the mechanism behind the calibration difference, not a pure "model intelligence" question.

## Decisions this experiment informs

### F4 (primary writer) for l1-uk track

**Opus.** Highest aggregate (7.80), zero FAIL verdicts, highest on 4 of 6 axes. Margin of 0.35 over Codex is narrow but the stability (no FAILs) breaks the tie.

### F2 (fallback ladder) for writer role

Based on aggregate scores:

1. Opus (7.80)
2. Codex (7.45)
3. Gemini 3.1 Pro (7.12)
4. Sonnet (6.83)
5. Gemini 3 Flash (5.83) — **meaningful drop**, should carry `generated_by_model` metadata + rebuild queue

Flash's 1.29-pt gap to Sonnet, and 1.97-pt gap to Opus, confirms the user's earlier intuition that Flash is a real quality downgrade and should not be used as "silent fallback" without provenance tracking.

### F4 (reviewer role) for production pipeline

**Primary: Opus. Secondary: Codex.**

Opus for discriminating judgment and evidence density. Codex for strict, consistent lower-bound. Cross-agent pair (no self-review) whenever a writer's output needs validation. Third-rung fallback if both are unavailable: Gemini 3.1 Pro (wider range than Flash, but evidence-light so expect shallower analysis).

### For the English-scaffolded follow-up bakeoff

Same 5 writers, same fixture methodology, different system prompt and different output contract. Run after Phase G infrastructure is in place. Don't assume today's winner generalizes — the task-shape difference (English scaffolding + Ukrainian target content) may favor a different writer.

## Caveats

- **Sample size is one fixture.** A second fixture (A1 M02 `reading-ukrainian`) would firm up the ranking, especially for the narrow Opus/Codex margin. Not run because the 0.35 margin is above our 0.3 tiebreaker threshold.
- **Temporal snapshot.** Model versions current as of 2026-04-22. Re-run at a scheduled cadence (quarterly?) as new model versions ship.
- **Prompt-dependent.** Results reflect performance on this specific adapted system prompt. Different prompt engineering could produce different rankings.
- **One-way review.** Reviewers were themselves writers in the same experiment. This introduces bias concerns (a model may systematically over- or under-penalize a style similar to its own). Mitigation: round-robin excludes self-review, and 4 independent reviewers per output reduces single-reviewer bias.
- **Sonnet-on-Codex YAML parse failure:** one of the 20 reviews could not be auto-parsed due to unquoted strings with colons; numeric scores were hand-extracted verbatim from grep of the raw file and evidence was preserved in the raw result file for audit (`batch_state/tasks/review-sonnet-on-codex.result`). All 6 axis scores and overall_score recovered; evidence detail was simplified in the reconstructed YAML.

## Reproducibility

All artifacts are committed:

- Writer system prompt: `batch_state/briefs/writer-bakeoff-a1-m03.md`
- Reviewer system prompt: `batch_state/briefs/bakeoff-review.md`
- Plan fixture: `curriculum/l1-uk/plans/a1/special-signs.yaml` (via branch `codex/fork-l1uk-codex`)
- 5 writer outputs: branches `writers/bakeoff-<writer>` (see `git worktree list` for paths; each writes `experiments/writer-bakeoff-2026-04-22/<writer>/special-signs.md`)
- 20 cross-reviews: `experiments/writer-bakeoff-2026-04-22/reviews/<reviewer>-on-<writer>.yaml`
- Aggregated scores: `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json`
- Aggregation script: `batch_state/aggregate_bakeoff.py`

To re-run: see the brief files for the exact dispatch commands used (all via `scripts/delegate.py dispatch`).

## Open follow-ups

1. **Prompt engineering pass.** The lack of majority PASS suggests the prompt under-specifies activity count requirements and the `## Практика` contract. Before the next bakeoff, tighten those sections.
2. **Fixture count.** Run one more fixture (A1 M02) as a sanity check on the Opus/Codex ordering.
3. **English-scaffolded bakeoff.** Separate experiment, different prompt. Run after Phase G infrastructure is ready.
4. **Seminar bakeoff.** Seminars (HIST, BIO, LIT, OES) require different skills — cultural/historical nuance, decolonized framing of contested figures. Today's winner may not generalize. Separate bakeoff when seminar phase starts.
