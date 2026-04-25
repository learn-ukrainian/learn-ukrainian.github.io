# Dimensional Review System — Design

> **Status:** DRAFT · 2026-04-18
> **Author:** Claude (lead dev), in dialogue with user
> **Scope:** Wiki review (net-new) first, then module review refactor.
> **Related:** `scripts/build/phases/v6-review.md` (current module review), `scripts/wiki/quality_gate.py` (current mechanical wiki gate).

## 1. Problem

Two distinct problems with the current review layer:

**Module review is dimensional but harmonized.** `v6-review.md` already scores 9 weighted dimensions (Plan adherence 15%, Linguistic accuracy 15%, Pedagogy 15%, Vocab 10%, Exercises 15%, Engagement 10%, Structural 5%, Cultural 5%, Dialogue 10%). One reviewer call produces all 9 scores in one response. Consequence: scores bleed, personas harmonize, low scores compensate via weighted average, and "aim for 9+/10" becomes an averaging game instead of a gate that every dimension must pass.

**Wiki review has no semantic layer at all.** `quality_gate.py` runs only mechanical checks (word count, AI-thinking leakage regex, fence wrapping, truncation). No LLM review of factual accuracy, source grounding, or Ukrainian-perspective framing. Wiki compiles via a prompt and ships if mechanical gates pass.

## 2. Principles (non-negotiable)

1. **Per-dimension minimum gates, no weighted averaging.** Each dimension has a threshold. ALL must pass or the artifact fails. No compensation.
2. **Specialist personas per dimension.** Not "act as a reviewer" — "act as [sharp specific role]". Personas versioned in code, not drifting in prompts.
3. **Evidence-first scoring.** Reviewer outputs concrete findings FIRST (cite location, quote text, specify issue). Score is derived from findings, not asked for directly. Kills sycophancy and inflation.
4. **Parallel calls with cached shared prefix.** Not multi-persona-in-one-call (harmonizes). Not sequential turns (too many turns). One cached prefix + N parallel dimensional calls = wall-clock ≈ one review.
5. **Reviewer-as-fixer per dimension + deterministic fix-merger.** Each dimensional reviewer outputs its own `<fixes>` block localized to its dimension (preserves proven reviewer-as-fixer contract from ADR-001 — "FROM SCRATCH" rewrites degraded 9.6→9.2→8.4, so we do NOT write a centralized generative patcher). A small deterministic fix-merger detects conflicts across dim outputs (same `find:` string, overlapping spans) and either auto-merges non-conflicts or escalates conflicts with a minimal repair prompt. **Previously this section proposed a single LLM patcher; that idea was rejected after Codex adversarial review (2026-04-18) — centralized generative rewrite was a reinvention of the FROM-SCRATCH pattern ADR-001 already ruled out. See App D for review log.**
6. **Cross-agent mandatory.** Writer ≠ reviewer, ever. Current policy (2026-04-18): writer = Gemini, reviewer assignment is **evidence-based not declared** — start with ADR-002 defaults (Codex for code/infra/contract-checking, Claude for content adversarial) and refine via seeded benchmark.
7. **Wiki has no engagement dimension.** Wiki is AI-consumption reference; the learner never reads it. Scoring it for engagement is category error.
11. **Ukrainian for artifact, English for reviewer instructions/schema.** Wiki + module content stay in Ukrainian (decolonization principle intact). Reviewer prompts, schemas, and structured output stay in English until we have local benchmark data showing Ukrainian-instruction parity. Rationale: UAlign and Indic-QA document English/Ukrainian performance gaps in low-resource-language reasoning; translate-test regularly outperforms direct multilingual prompting. This is a CAPABILITY hedge, not a decolonization retreat — the thing learners see remains Ukrainian. Revisit after seeded benchmark.
12. **Deterministic dimensions are code gates, not LLM gates.** Structural integrity (word count, section presence, markdown cleanliness) and citation-registry consistency (every `[S#]` has a corresponding sibling-YAML entry; every YAML entry is cited at least once) are DETERMINISTIC. They go to code, not LLM scoring. Reserve LLM-scored dims for genuinely subjective checks (register, pedagogy, engagement, linguistic accuracy, cultural framing).
8. **Humor is structural to Ukrainian culture, not decorative.** Ukrainian culture survives under empire and under war through irony, parody, and meme-fluent resistance. A curriculum that teaches Ukrainian without teaching humor doesn't teach Ukrainian. But humor-as-engagement means *humor-under-siege* — wit that knows the context, not cheerful escapism. A module pretending everything is fine while Kharkiv is under drone attack is its own form of imperial erasure.
9. **Genre-mixing happens at two levels.** *Within a work*: Shevchenko-style — satire + rage + pastoral + prophecy in one poem. *Across a life or module*: Zhadan-style — serious poetry + silly rock songs + radio conversation + rap video, all the same artist. A language module doesn't need humor on every page, but the module AS A WHOLE must refuse single-register monotony. Ukrainian culture doesn't live in one room.
10. **Ukrainian perspective is outward-facing, not only inward.** Decolonization isn't parochialism. Zhadan's ability to see Hungarian or Russian politics with artistic clarity is a Ukrainian quality as real as his ability to see Kharkiv. The cultural-accuracy reviewer rewards Ukrainian voices that look at the wider world with authority — not only voices that speak about Ukraine to itself.

## 3. Wiki review — 4 LLM dimensions + 2 code gates

Net-new layer. Runs after mechanical `quality_gate.py` passes, before wiki ships to pipeline consumers.

### 3a. Code gates (deterministic, no LLM)

Run BEFORE any LLM review. Hard fail aborts the LLM pass — cheap way to filter obvious defects.

| Gate | Check | Enforcement |
|---|---|---|
| **Structural integrity** | word count ≥ level minimum; required sections present (короткий зміст, основний зміст, etc.); no `## Джерела` bibliography section (handled by sibling YAML); markdown well-formed | `scripts/wiki/quality_gate.py` (extend) |
| **Citation registry consistency** | every inline `[S#]` ref resolves to a `sources:` entry in sibling YAML; every YAML `sources:` entry is cited at least once; no orphans either direction | new check in `quality_gate.py` — leverages existing `sources_schema.py` |

### 3b. LLM dimensions (4, subjective)

| # | Dimension | Persona | Agent assignment | Min score | Notes |
|---|---|---|---|---|---|
| # | Persona | Primary | Fallback | Min score | Notes |
|---|---|---|---|---|---|
| 1 **Factual accuracy** | "You are a Ukrainian studies fact-checker. You flag any claim about Ukrainian grammar, phonetics, history, or culture that cannot be verified." | Gemini (MCP via bridge, native Ukrainian) | Claude (MCP via bridge) / Codex (MCP after #1325) | TBD (seeded benchmark) | Requires live MCP access (VESUM, Wikipedia, Антоненко-Давидович). Codex joins fallback pool once #1325 lands — until then, Codex cannot serve this dim. |
| 2 **Source grounding (qualitative)** | "You are an editorial integrity checker. Every substantive claim must trace back to its cited source's actual content. You identify claims that outrun what their sources say." | Codex (contract-checking, literal-minded) | Claude / Gemini | TBD (seeded benchmark) | Quantitative citation-registry consistency is the §3a code gate. LLM only evaluates whether cited source actually supports the claim. |
| 3 **Ukrainian perspective / decolonization + outward clarity** | "You are a Ukrainian cultural editor. You flag framing that treats Ukrainian as 'like Russian but X', Soviet-inherited historical framing, dismissal of Ukrainian agency. You reward confident outward-looking framing." | Claude (cultural nuance) | Gemini | TBD | Both native-approximating agents are capable. Codex unsuitable — too literal for cultural framing judgment. |
| 4 **Register / naturalness** | "You are a Ukrainian language editor. You flag translationese, calques, machine-translated phrasing, register mismatches." | Gemini (native-approximating, MCP for style guide) | Claude / Codex (after #1325) | TBD | ADR-002: Codex for code/infra, content agents for content. Codex as last-resort fallback when primary + secondary unavailable. |

Wiki reviewer ignored dimensions: engagement (N/A), dialogue (N/A), exercise quality (N/A), plan adherence (wiki has no plan contract), pedagogical quality (wiki isn't pedagogy).

**All agent assignments above are DEFAULTS pending seeded benchmark (§7).** Primary/fallback ordering is informed by Gemini's peer-reviewer evidence (concrete linguistic catches) and ADR-002 specialization. Benchmark will freeze or adjust. **Primary+fallback pattern is a resilience requirement per user direction 2026-04-18**: if primary agent is rate-limited or unavailable, orchestrator falls back automatically so the review pipeline doesn't stall.

## 4. Module review — 7 LLM dimensions + 2 code gates (refactor)

Module review keeps the content of all 9 current dimensions but splits them: 2 go to code gates (deterministic), 7 go to parallel dimensional LLM review. Current `v6-review.md` becomes the per-dimension prompt template source.

### 4a. Code gates (deterministic)

| Gate | Check | Source |
|---|---|---|
| **Structural integrity** | word count ≥ `word_target`; required sections present; no meta-narration ("Content notes:"); markdown clean; no dangling sentences | extend `scripts/audit_module.py` / config.py `AUDIT_THRESHOLDS` |
| **Plan-adherence quantitative** | required `vocabulary_hints` present in prose; `activity_obligations` count matches markers; section word budgets within ±10% | extend `plan_validator.py` / `audit_module.py` |

### 4b. LLM dimensions (7, subjective)

All agent assignments are **DEFAULTS pending seeded benchmark** (§7). Primary+fallback pattern: orchestrator uses primary; falls back to alternate(s) if primary is rate-limited/unavailable. Resilience requirement per user 2026-04-18.

| # | Dimension | Primary | Fallback | Min score |
|---|---|---|---|---|
| 1 | Plan adherence (qualitative) | Codex (contract-checking) | Claude / Gemini | TBD |
| 2 | Linguistic accuracy | Gemini (native + MCP) | Claude (MCP) / Codex (MCP after #1325) | TBD |
| 3 | Pedagogical quality | Gemini | Claude | TBD |
| 4 | Vocabulary coverage (qualitative) | Codex | Gemini / Claude | TBD |
| 5 | Exercise quality | Codex (logic-focused) | Claude / Gemini | TBD |
| 6 | **Engagement & tone** | Claude | Gemini | TBD |
| 7 | Cultural accuracy + outward clarity | Claude | Gemini | TBD |

**Linguistic accuracy rationale:** Gemini's peer-reviewer evidence (task `gemini-linguistic-review-view-2026-04-18`) showed 3 concrete linguistic catches requiring native Ukrainian understanding + live MCP lookup: `рахувати` vs `вважати` Russianism, `путь` gender contamination, "по суботам" calque. These require semantic judgment Codex as-is cannot provide. Codex joins fallback pool after #1325 (adapter MCP fix) ships.

**Dialogue quality:** folded into engagement dim — "mixed-register, non-transactional, named-speakers" checks fit naturally there. Separate dim removed to cut review count.

### 4c. Why thresholds are "TBD"

Codex review (2026-04-18) correctly flagged that my 8.0/8.5/9.0 thresholds were guesses. Proper thresholds set from **seeded benchmark score distributions**: plant known defects at known severity, measure score distributions on clean vs defective artifacts, set thresholds at the separation point. Until that data exists, there are no numbers. See §7.

## 5. Engagement personas (module only, per level)

Sharp, specific, level-matched. Verified cultural references only. No invented historical figures. Do NOT reference Tymoshenko or Bulgakov. Personas carry Ukrainian humor-DNA (irony, meme-fluency, willingness to roll eyes at solemnity) alongside whatever emotional core the level calls for — no persona is purely earnest, because the real reader isn't.

- **A1–A2:** "You are 17, London-raised, your babusya speaks Ukrainian but you grew up in English. You're doing this module on your phone between classes. You scroll Телебачення Торонто shorts when you're bored and you've seen your cousins repost tractor-stealing-tank memes for three years now. You cried at Шевченко's 'Садок вишневий' once and you won't admit it. You wanted this to feel like a door opening into your grandmother's world — warm, witty, specific. You don't want 'beautiful language' platitudes; you want to find out what your family actually jokes about."
- **B1–B2:** "You are 34, your new partner is Ukrainian, they fled from Kharkiv. You want to understand their family's jokes — and you want to know why everyone suddenly goes quiet at certain news. You're doing this module at 10pm after work, tired. You don't want the module to pretend there's no war, and you don't want it to drown in grief either — you want Ukrainian the way Ukrainians actually carry it: serious and sometimes funny, Zhadan-style. Show you know the difference between cheerful-imperial-erasure and real warmth-under-siege."
- **C1–C2:** "You are a lifelong learner who just finished Plokhy's *Gates of Europe*, listens to Hrytsak's lectures on YouTube, and was recently ambushed by *Zaporozhets za Dunayem* — you loved that it wasn't strictly opera. You've worked through Zabuzhko in the original; Andrukhovych is in your rotation; Pidmohylny is next. You carry Zhadan's *Інтернат* and his band's catchier songs at the same time, and you don't think that's a contradiction. You will roll your eyes at childish examples AND at humorless rigor. Rigor is fine. Warmth is essential. Genre-mixing is a gift. Outward clarity is a mark of a serious culture."
- **Seminar (HIST, BIO, LIT, ISTORIO, OES, RUTH):** "You are 19, a Ukrainian-American history student. You already know the basic chronology; spare you the encyclopedia voice. You want Plokhy's narrative drive, Hrytsak's synthesis, Zhadan's willingness to be funny next to being serious. You want stakes named out loud. You want this material to see the wider world clearly, not be provincial about Ukraine. If the text is one-note solemn for ten pages, you close the tab."

Persona evaluation output is FORCED to include:
- 2+ friction moments (cite location, quote text, explain why stopping)
- 2+ delight moments (cite location, quote text, explain why continuing)
- 1+ observation on register-mixing: does the module refuse single-register monotony across its span? (explicit question, not optional)
- 1+ observation on humor-fit: where does the module miss a natural humor opportunity? where does it force humor that doesn't land?
- Net score derived from friction:delight ratio + register-mixing observation + humor-fit observation

No free-floating number. No "10/10 engaging!" without concrete evidence.

## 5.3 Rubric details — engagement dimension (module dim 6)

The current `v6-review.md` dim 6 rubric is defensively framed ("deduct for formulaic openers, gamified language, generic enthusiasm"). The new rubric is affirmative.

**REWARD for (affirmative engagement signals):**
- **Narrative drive** — does a section tell a story, or just list facts? (Plokhy test)
- **Intellectual warmth** — does the writer think *with* the learner, or at them? (Hrytsak test)
- **Genre-mixing within the module** — does prose + example + cultural fragment + humor + folk reference co-exist across the module's span? Does the module refuse single-register monotony from beginning to end? (Shevchenko + Zaporozhets test)
- **Humor that knows the context** — irony, wordplay, self-deprecating observation, meme-literate aside when level-appropriate. NOT chipper Western-sitcom humor. The kind of humor that coexists with grief, not the kind that dodges it.
- **Multi-modal texture** — references to song, dance, spoken idiom, folk ritual, contemporary music or meme culture when natural to the topic
- **Cultural specificity** — concrete Ukrainian detail, not generic "beautiful language" enthusiasm

**DEDUCT for:**
- **Single-register monotony** — one tone from start to finish, whether earnest-pedagogical, academic-cold, gamified-chipper, or even consistently-witty. The failure is the monotony.
- **Cheerful-imperial-erasure** — tone that pretends the war isn't happening, or treats Ukrainian culture as a happy tourism brochure. Cheerfulness divorced from reality is its own form of violence.
- **Reverential monotone** — treating Ukrainian as museum artifact, not as living culture that can laugh at itself.
- **Forced humor / Western-sitcom register** — jokes that land as sitcom Westernism, not Ukrainian irony. Better no humor than fake humor.
- **Missed obvious humor opportunities** — teaching *дружина* without any marriage irony; teaching *бути* without the folk philosophical weight; reading as if the writer has never been to a Ukrainian wedding.
- **Generic enthusiasm** — "beautiful language," "incredibly rich culture," empty filler.

## 5.4 Rubric details — cultural accuracy dimension (module dim 8, wiki dim 3)

The current `v6-review.md` dim 8 covers decolonization at a high level ("never 'like Russian but...'", factually correct claims, respectful representation). Augment with the outward-clarity refinement.

**REWARD for:**
- Decolonized framing — Ukrainian on its own terms, never "like Russian but..."
- Factually correct cultural/historical claims
- **Outward clarity** — Ukrainian voices / references that look at the wider world with authority and precision (Zhadan-on-Hungary test). Ukrainian culture as a clear-sighted perspective on the world, not only a subject inspected from outside.
- **Confidence, not defensiveness** — Ukrainian literature on the same plane as European literature, not presented as downstream-of-Russia or "finally free-from-Russia." Both framings still center Russia.
- **Naming the enemy when the topic requires it** — Shevchenko named the tsar; Zhadan names Putin; the curriculum shouldn't be mealy-mouthed about Russian colonial violence when the subject is occupation, deportation, Holodomor, war. Soft evasion IS a decolonization failure.

**DEDUCT for:**
- "Like Russian but..." or "east Slavic languages (including Russian)..." framing when the sentence is about Ukrainian specifically
- Soviet-inherited chronology, "common Rus' origin" framing that treats Russia as the continuation of Kyivan Rus'
- Tourist-brochure Ukraine — "interesting to outsiders" framing
- Soft-provincial voice that hesitates to look beyond Ukrainian borders or to comment on global/regional matters
- Naming-the-wrong-enemy — using "conflict" where "invasion" is accurate, "tension" where "occupation" is accurate
- Invented historical figures or uncritical reference to contested figures (Bulgakov as "Ukrainian", Tymoshenko as neutral political shorthand). Always verify via `mcp__sources__query_wikipedia` before naming.

## 5.5 Engagement — decomposed checks + Zhadan as calibration (NOT as gate)

**CORRECTION 2026-04-18:** Earlier version of this doc proposed "Would this land for a Zhadan reader?" as a literal pass/fail gate. Codex review caught the error: `scripts/config.py:391` shows A2/B1 prioritize clear high-comprehension Ukrainian with strict simplicity constraints, NOT literary performance. A Zhadan-flavored gate would penalize correct beginner plainness. The "Zhadan north-star" is a **calibration artifact for prompt writers**, not a scoring rubric applied to modules.

**The actual engagement dim does these concrete checks, level-calibrated:**

| Check | A1-A2 weight | B1-B2 weight | C1-C2 weight | What it detects |
|---|---|---|---|---|
| **Anti-boilerplate specificity** | high | high | high | Does the module use specific Ukrainian cultural details, not generic "beautiful language" platitudes? |
| **Narrative drive** | medium | high | high | Do sections tell a story / have arc, or just list facts? |
| **Tonal variation across sections** | low-medium | medium-high | high | Does the module refuse single-register monotony across its span? (module-wide, not paragraph-wide) |
| **Humor handling** | low (simplicity wins) | medium | high | Where humor appears, is it Ukrainian-native register (not Western-sitcom)? Are natural humor opportunities missed? Level A1-A2: low weight because simplicity dominates. Higher levels: meme-fluency and irony expected. |
| **War-context honesty** | medium | high | high | If the topic touches contemporary life, does the module acknowledge reality without melodrama AND without chipper erasure? ("місто аптек, місто блокпостів" register). |
| **Outward clarity** | N/A | medium | high | Does the text see beyond Ukraine's borders with authority? N/A at A1-A2 (too advanced). |
| **Anti-chipperness** | high | high | high | Detection: self-congratulatory openers ("Welcome to A2!"), gamified language ("You have unlocked..."), generic enthusiasm. Deduct. |

**Each check produces its own sub-score.** Final engagement score is the worst sub-score at that level's weighted thresholds — not an average. Sub-scores are more diagnostic than a single engagement number.

**"Zhadan-fit"** is used in ONE specific sub-check at C1+/seminar only: does the module's register sit in the space a Zhadan-reading Ukrainian would recognize as alive? That single sub-check can reference the Холодна Гора calibration artifact. It does NOT drive the A1-B2 evaluation.

**Calibration limit (unchanged):** The reviewer can apply the structural checks above. It cannot judge "this tried to sound like Zhadan and failed in a Ukrainian-native-ear way." Native ear (the native reviewer / user) remains the final tonal calibrator. The reviewer is a first-line filter.

## 5.5-legacy (deleted)

~~"Would this module land for a reader whose literary home is Zhadan?"~~ This framing is deleted from the scoring rubric per Codex review 2026-04-18. Preserved in App D as calibration-artifact history.

**Historical foundation:** **Shevchenko** as the lineage anchor. Every Ukrainian agrees he's awesome to read because he (a) proved Ukrainian can bear literature equal to any language by *doing it*, (b) wrote in the rhythm of the real language (коломийковий meter, folk song cadence, dumy structure), and (c) refused single register — satire + rage + pastoral + prophecy in one poem. He is the foundational proof that Ukrainian engagement is genre-mixed.

**Contemporary embodiment:** **Serhiy Zhadan** as the living synthesis. Novelist + poet + rock frontman + radio host + collaborator with rap bands + front-line volunteer in Kharkiv. Proves every principle: narrative drive, genre-mixing within a work AND across a life, intellectual warmth, humor-under-siege, cultural specificity, outward clarity. If the engagement reviewer's taste had a single name, it would be his.

**Humor touchstones (contemporary):**
- *Телебачення Торонто* — satirical YouTube "broadcasting from Toronto." The name is itself the joke; irreverent remove from performative seriousness. Reference-safe.
- *Наші без раші* (YouTube) — per user, funny; I haven't verified the register myself. Reference with user or native-speaker calibration.
- Zhadan's band (*Жадан і Собаки* / *Жадан і ...*) — ska/punk/folk-rock, politically sharp, willing to be silly. The "300 китайців у Будапешті" song (user's example) is a case in point: a Ukrainian writer in Kharkiv seeing Orbán's Hungarian golden-visa scheme clearly enough to turn it into catchy satire. Outward clarity + humor + music, all at once.

**Calibration limit (honest):** The reviewer prompt can encode structural tests — monotone register, missing cultural weight, forced cheerfulness, cheerful-imperial-erasure of the war context, provincial-inward-only framing. It CANNOT catch "this tried to sound like Zhadan and failed in a Ukrainian-native-ear way." That requires a native tonal ear. the native reviewer or the user is the only reliable final calibrator on "did this land." The reviewer is a first-line filter, not a substitute for native judgment.

## 6. Execution pattern

### 6a. Unified runtime — single orchestrator, single invocation path

**CORRECTION 2026-04-18 (Codex review finding #3):** Earlier version proposed mixing `delegate.py dispatch` for Codex and `ask-claude` for Claude. `docs/agent-runtime-guide.md:11` requires unified entrypoint — different paths mean different timeout/retry/rate-limit/parsing semantics inside one review gate. All dimensional calls go through `scripts/agent_runtime/` adapters. One orchestrator (new `scripts/wiki/review_orchestrator.py` for wiki; `scripts/build/phases/review_orchestrator.py` for module).

### 6b. Prewarm + fan-out (corrected caching math)

**CORRECTION 2026-04-18 (Codex review finding #1):** Earlier version claimed "fire N calls in parallel with cached prefix." Wrong. Anthropic prompt cache entries only become available AFTER the first response begins ([Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)). True simultaneous fan-out misses the cache on every call.

**Correct pattern (when multiple Claude dims on one artifact):**
1. Build shared prefix once.
2. **Prewarm:** fire one Claude dim call. Wait for response to begin (cache entry becomes available).
3. **Fan-out:** fire remaining Claude dim calls. They hit the cache.
4. **Wall-clock:** prewarm time + (max of remaining calls). Roughly 1.5× one call instead of 1× one call. Still cheaper than full sequential.

**Cost math (Sonnet-class, 10K prefix + 500 suffix per dim, 4 dims):**
- Sequential with prewarm + cache: ~$0.0525 input
- True parallel without caching: ~$0.126 input (2.4× more)
- Our pattern: sequential-with-prewarm, accept the small latency hit.

**For wiki specifically:** Only 1 LLM dim runs on Claude (decolonization). No caching benefit applies. Claude cache economics is NOT the justification for the wiki design. Justification is agent-fit, not cache math.

**For Codex:** **No caching in current invocation path.** OpenAI API supports GPT-5-Codex caching, but this repo's runtime (`agent-runtime-guide.md:57`) uses per-message fresh-session policy with no cached-input tier in `cost_rates.yaml:15`. Treat Codex cost as N × full prefix until measured on the exact path we ship. **Codex dim assignment must be justified by agent-fit, not cache economics.**

### 6c. Reviewer-as-fixer per dimension + deterministic fix-merger

**CORRECTION 2026-04-18 (Codex review finding #4):** Earlier version proposed a single LLM patcher that integrated findings from all dims and produced one coherent fix batch. This is a reinvention of the FROM-SCRATCH rewrite pattern that ADR-001 already rejected (degraded 9.6→9.2→8.4).

**Correct pattern:**

1. **Each dimensional reviewer outputs its own `<fixes>` block** (preserves ADR-001 reviewer-as-fixer contract). Each reviewer's fixes are LOCAL to its dimension — surgical find/replace, no cross-dimensional interpretation.
2. **Fix-merger (deterministic, code only — no LLM)**:
   - Collect all `<fixes>` from all dims
   - Group by `find:` string
   - **Non-conflicts** (unique `find:` strings): apply sequentially
   - **Conflicts** (same `find:` string, different `replace:` values): either (a) both replacements can be applied non-destructively (rare — triggers priority rule: linguistic > factual > register > engagement), or (b) genuine conflict — fail the artifact with "review conflict" flag for human/next-round attention
   - **Span overlaps** (find-strings partially overlap): treat as conflicts
3. **Re-review:** after merger applies fixes, run dimensional reviewers again on the patched artifact. Max 2 rounds. Score must go UP (per ADR-001 principle — if patches degrade scores, the reviewer's fix suggestions were wrong).
4. **No centralized LLM patcher anywhere in this flow.** The merger is a Python function, not a prompt.

### 6d. Per-dimension gate logic

```
for dim, score, min_score in dimensional_results:
    if score < min_score:
        artifact.fail_reason = f"{dim} below threshold ({score} < {min_score})"
        artifact.status = "NEEDS_FIXES"
        break  # one failure = fail, no compensation
```

No weighted average. No overall score. Each dimension stands alone.

## 7. Two-phase evaluation: pilot + seeded benchmark

**CORRECTION 2026-04-18 (Codex review finding #6):** Earlier version proposed "scrappy pilot OR formal A/B" as either-or. Codex correctly pointed out: pilots on real content cannot measure recall (missed errors are invisible). Seeded defects are necessary to measure recall, precision, and stability before freezing agent splits or thresholds. Corrected plan: pilot first for prompt shape, seeded benchmark second for agent assignment and threshold calibration. Both, not either.

### 7a. Phase 1 — prompt-shape pilot (fast, qualitative)

Goal: get a prompt that produces structured, evidence-first output that a human reader can act on.

1. Pick ONE dimension (start with source-grounding — most tractable, output clearly checkable).
2. Write the reviewer prompt. Output schema: JSON with `findings[]` (each with `location`, `quote`, `issue`, `severity`), `<fixes>` block, score.
3. Run on 2-3 real wiki artifacts via default-agent choice.
4. Iterate prompt until output is structured, grounded in evidence, no hallucinated findings.
5. Move to next dim.

Expected cost: ~30 min / dim, 4 dims × 4-5 iterations ≈ 20-50 calls total. Trivial.

### 7b. Phase 2 — seeded benchmark (empirical, freezes assignments and thresholds)

**Runs AFTER prompt shape is stable (Phase 1 done).** Freezes the reviewer-agent matrix and per-dim thresholds based on data.

1. **Build a seeded benchmark corpus.** 5 wiki artifacts. For each artifact: produce 3 versions — (a) clean baseline, (b) lightly defective (2-3 planted errors), (c) heavily defective (8-10 planted errors across dims). Errors documented: type, severity, location. Label ground truth.
2. **Planted error taxonomy** (per dim):
   - Factual: wrong date, wrong etymology, wrong grammatical claim
   - Source grounding: unsourced claim, overclaim-beyond-source, misattribution
   - Decolonization: "like Russian but", Soviet-inherited framing, centered-on-Russia phrasing
   - Register: translationese, calque, register mismatch (journalistic in pedagogical)
3. **Run each candidate agent** (Claude, Gemini, Codex) on each dimension across clean + light + heavy versions.
4. **Measure per (dim, agent):**
   - **Recall**: caught planted errors / total planted errors
   - **Precision**: true-positive findings / all findings (needs inspecting flagged items on clean baseline — false positives are findings on clean content)
   - **Stability**: rerun 3× — do scores and findings remain consistent?
   - **Cost**: actual tokens × per-token cost on the exact invocation path we ship (not theoretical pricing)
5. **Threshold derivation:** score distributions on clean vs. defective artifacts determine per-dim min score. Threshold set at the separation point where defective artifacts reliably fall below.
6. **Agent assignment:** highest F1 at acceptable cost wins the dim. Ties broken by cost.

### 7c. Ground truth alternative: the native reviewer annotation (small sample)

If user/the native reviewer bandwidth permits: have her mark errors independently on 2-3 real Gemini-written wikis. Compare reviewer findings vs her annotations. Provides validation against native-expert judgment, not just our planted taxonomy. Smaller sample, higher signal.

### 7d. Budget

- Phase 1: ~50 calls total, ~1 day
- Phase 2: 5 artifacts × 3 versions × 3 agents × 4 dims × 3 reruns ≈ 540 calls, bounded over 1-2 nights
- the native reviewer validation: 3 artifacts, ~1 week real-world turnaround depending on her schedule

**Do not freeze agent assignments or thresholds before Phase 2 completes.**

## 8. Rollout — canary, not hard-gate day one

**CORRECTION 2026-04-18 (Codex review finding #10):** Earlier version hard-gated the wiki rebuild on the new dimensional review from day one AND included a "backfill existing compiled wikis" step that referenced files that don't exist (the wiki was deleted; rebuild is net-new). Both fixed below.

### Phase 1 — Pre-rebuild prompt hygiene (code gates ready)
1. **Fix compile prompts** (`scripts/wiki/prompts/compile_*.md`): enforce Ukrainian-only output explicitly, strip `## Джерела` section from emit. Delegable to Codex (task #9). Small.
2. **Extend `quality_gate.py`** with the two code gates from §3a (structural integrity, citation-registry consistency). No LLM involved. Also small.
3. **Write one dimensional reviewer prompt** via Phase 7a pilot pattern. Start with source-grounding (most tractable).

### Phase 2 — Shadow-mode dimensional review during rebuild
Rebuild the wiki with fixed compile prompts AND run dimensional review **in shadow mode** — reviewer runs, logs findings, but does NOT gate the artifact. All findings logged to `wiki/.reviews/` with agent attribution and timestamp. Rebuild proceeds; quality data accumulates.

Rationale: same-day cutover of compile prompts + hard review gate makes failures unattributable (writer regression vs reviewer false positive). Shadow mode separates those.

### Phase 3 — Seeded benchmark (per §7)
During shadow-mode run: also execute the seeded benchmark. Now have real rebuild output AS WELL AS labeled defective corpus for measurement.

### Phase 4 — Freeze assignments + thresholds, promote to hard gate
With Phase 2 + 3 data:
1. Pick agent per dim by F1 + cost.
2. Set thresholds from score distributions.
3. Promote dimensional review from shadow to hard gate for wiki.
4. Re-process any wiki artifacts from Phase 2 that now fail new thresholds.

### Phase 5 — Module refactor (mirrors Phase 1-4)
After wiki is hard-gated:
1. Fix module compile prompts where needed (`v6-review.md` split into per-dim prompts).
2. Module dimensional review runs in shadow mode on next module build batch.
3. Seeded module benchmark (3 modules × 3 versions).
4. Freeze + promote to hard gate.

### Phase 6 — Monitoring and tuning (ongoing)
1. Emit per-dim scores as JSONL events (`{"event": "dim_score", "dim": "linguistic", "score": 8.7}`).
2. Dashboard in Monitor API: per-dim score distributions per track.
3. Threshold tuning: if a dim consistently bottlenecks real output, raise it. If it always passes, lower it to reduce noise.

### Removed: "backfill" step
Previous version included "run new review on existing compiled wikis, patch worst offenders." There are no existing compiled wikis in production (user confirmed 2026-04-18 — "we deleted them, we are rebuilding them"). Step removed.

## 9. Open questions (post-Codex-review, still genuinely open)

Previous versions of this section had 5 questions — 4 have been resolved by the 2026-04-18 adversarial reviews + consultations. Remaining:

1. **Ukrainian-artifact / English-instruction split: OK permanent or revisit.** Per §2 principle 11, reviewer prompts stay in English until benchmark proves parity. Include this as a dimension of Phase 2 seeded benchmark: run same reviewer prompt in English-instructions-vs-Ukrainian-instructions on the same artifacts. Measure recall/precision delta. If Ukrainian-instructions match English-instructions, we can flip; if gap persists, English-instructions remain permanent.
2. **Engagement dim level-calibration weights (§5.5 table).** The weights I assigned by level (high/medium/low for each sub-check) are my best guesses informed by config.py A2/B1 simplicity priorities. User or the native reviewer should review before freezing — they know the real pedagogical priority curve better than I do.
3. **Fix-merger conflict resolution priority rule.** I proposed "linguistic > factual > register > engagement" as tiebreaker when two dims' fixes touch the same span. This is a guess. Real priority should come from user judgment about which kind of error is "worst" to ship.
4. **Orchestrator availability detection.** Primary+fallback pattern requires detecting when primary is unavailable (rate limit, error, timeout). Needs a clean signal from `scripts/agent_runtime/` — how is availability exposed? Design detail to resolve during Phase 1 Step 2.

### Resolved by adversarial reviews + consultations (2026-04-18)

- ~~Option A vs B for fix-conflict~~ → Resolved: reviewer-as-fixer per dim + deterministic fix-merger (not a single LLM patcher). §2 principle 5, §6c.
- ~~Ground-truth source for A/B~~ → Resolved: pilot + seeded benchmark (both), with the native reviewer as supplementary validation. §7.
- ~~Patcher agent~~ → N/A. No LLM patcher. Fix-merger is deterministic code.
- ~~Min-score thresholds~~ → Deferred to Phase 2 seeded benchmark data.
- ~~Cost at scale~~ → Clarified: Codex has no caching in current CLI invocation path; Claude uses prewarm + fan-out pattern; real numbers come from Phase 2 measurement.
- ~~CodexAdapter tool access~~ → Resolved: fix adapter (#1325 delegated to Codex) to make Codex a viable fallback reviewer. Primary/fallback pattern per user's resilience requirement.

## 10. Not in scope

- Real-learner engagement measurement (simulated student personas only; real engagement needs real users).
- Review-score tuning via ML (simple thresholds are fine until we have enough production data).
- Replacing `quality_gate.py` mechanical checks (those stay; dimensional review runs after them).
- Audit gates (`config.py` thresholds on word count, activity count, vocab) — independent system, already works.

---

## Appendix A — Files to create

```
docs/design/dimensional-review.md               # this doc
scripts/wiki/prompts/review_factual_accuracy.md  # dim 1 (filename matches JSON "dimension" field)
scripts/wiki/prompts/review_source_grounding.md  # dim 2
scripts/wiki/prompts/review_ukrainian_perspective.md  # dim 3
scripts/wiki/prompts/review_register.md          # dim 4
scripts/wiki/review.py                           # orchestrator (no LLM patcher — deterministic fix-merger per §6c)
scripts/build/phases/review/plan_adherence.md
scripts/build/phases/review/linguistic_accuracy.md
scripts/build/phases/review/pedagogical_quality.md
scripts/build/phases/review/vocabulary_coverage.md
scripts/build/phases/review/exercise_quality.md
scripts/build/phases/review/engagement.md
scripts/build/phases/review/structural_integrity.md
scripts/build/phases/review/cultural_accuracy.md
scripts/build/phases/review/dialogue_quality.md
scripts/build/phases/review/patcher.md
```

## Appendix B — Persona source of truth

All personas live in a single file: `scripts/build/phases/review/personas.py` (dict literal). Updates require PR. Referenced by ID from prompt files. No persona text duplicated across files.

## Appendix C — Fact corrections for persona writing

### Political figures
- **Yulia Svyrydenko** — current PM of Ukraine (appointed 2025-07-17 by Zelensky). Second female PM in Ukrainian history. Safe to reference positively.
- **Yulia Tymoshenko** — do NOT reference in personas or examples. User framing: Russian-aligned. Avoid entirely.
- **President = highest Ukrainian leader.** Not the PM. Don't conflate.

### Literary figures — who belongs in Ukrainian personas
**Reference these as Ukrainian literary touchstones:**
- **Oksana Zabuzhko** — contemporary literary philosopher, demanding prose. Strong fit for advanced-learner personas.
- **Yuri Andrukhovych** — contemporary novelist/essayist, Bu-Ba-Bu poetry group. Literary ambition signal.
- **Valerian Pidmohylny** — Executed Renaissance modernist. Doubles as a decolonization reference (killed by Soviet regime 1937).
- **Serhiy Zhadan** — contemporary poet/novelist, respected.
- **Mykola Khvylovy** — Executed Renaissance prose stylist, "Away from Moscow!" polemic.
- **Vasyl Stus** — dissident poet, died in Soviet camp 1985.
- **Lesya Ukrainka, Ivan Franko, Taras Shevchenko** — canonical, safe, appropriate for beginner-to-intermediate cultural references.

**Do NOT reference as "Ukrainian" canon or as aspirational reading for Ukrainian learners:**
- **Mikhail Bulgakov** — born in Kyiv but Russian-imperial writer. *The White Guard* / *Days of the Turbins* portray Ukrainian forces as bandits; defended tsarist / White Russian cause during 1918-19 Ukrainian revolution. Since 2022, being actively removed from Ukrainian cultural canon. Invoking him implies Soviet-inherited framing of "Kyiv-born = Ukrainian culture" — exactly the decolonization failure the cultural-accuracy reviewer exists to catch. Lesson 2026-04-18: I referenced him in this doc's C1-C2 persona; user caught it.
- **Nikolai Gogol (as "Ukrainian")** — more nuanced, but do not reference uncritically. Wrote in Russian, imperial career, complex legacy. If invoked at all, frame as Russian-language author with Ukrainian roots, not as Ukrainian writer.
- **Anna Akhmatova, Boris Pasternak, etc.** — Russian canonical figures. Not Ukrainian even if they had biographical ties to Ukrainian territory.

### Historical figures
- **Do NOT invent historical figures.** Always verify via `mcp__sources__query_wikipedia` or authoritative sources before naming anyone. 2026-04-18 lesson: fabricated "Hetman Tymoshenko" — does not exist.
- Real Ukrainian hetmans to reference safely: Bohdan Khmelnytsky, Ivan Mazepa, Petro Doroshenko, Pavlo Polubotok. Always verify spelling/dates/context before invoking.

### Contemporary humor touchstones (level C1+ and seminar)

Safe to reference as signals of contemporary Ukrainian humor register:
- **Serhiy Zhadan** — poet + novelist + rock frontman + radio host + hip-hop collaborator in 2025. Calibration artifacts, in priority order for future prompt writers:
  - **PRIMARY: *Холодна Гора* (2025, hip-hop, Kharkiv under daily strikes).** The single best contemporary sample of the register this curriculum is trying to honor. The war is atmosphere not foreground ("місто аптек, місто блокпостів" — one line, two city-realities); class specificity is moral weight (khrushchevka, stepfather at factory, mom named Надія, fake-Armani tracksuits, paracetamol, marshrutka, FC Metalist); register mixing at the micro-level (literary + street argot + folk proverb + profanity + poetic abstraction within four lines); and the thesis line **"виросту, вивчусь — дам усім пизди"** — grow up, STUDY, then payback. Education-as-weapon delivered in working-class rage-teen voice. Form meets audience: Zhadan doing rap because Kharkiv kids listen to rap, under bombardment, in 2025. If a reviewer prompt writer reads only ONE Zhadan text, read this one.
  - **SECONDARY: *300 китайців у Будапешті* (2010s, rock satire).**
 Five perspectives in under three minutes (tender narrator → grotesque migrant fever-dream of Budapest → cynical Ukrainian smuggler voice → post-arrival criminal economy), hyper-specific proper nouns doing double duty as rhythm and political inventory (Ikarus bus, Мівіна, "майже ще не вживаними польськими гандонами"), the "300" echoing Maoist cultural revolution, and the four-geography gaze (Ukraine / Hungary / China / EU underworld) delivered through rock. The humor is never cheerful; the crooked smile of the exhausted smugglers ("криво посміхаючися кожному китайцю") is the tone. **This is the best concrete sample of "Zhadan register" on the page.** Future prompt writers calibrating the engagement reviewer should re-read it. Not to copy the style into learner modules — the register is wrong for pedagogy — but to remember what "serious + funny + specific + multi-register + outward-looking" actually *sounds like*. Zhadan is the contemporary north-star for this curriculum's engagement taste.
- **Телебачення Торонто** — satirical YouTube "broadcasting from Toronto" (the name is the joke — ironic remove from performative seriousness). Reference-safe for irreverent contemporary register.
- **Наші без раші** — per user, funny YouTube. Not yet verified by lead dev; reference with user or the native reviewer calibration.

### Outward clarity — a decolonization refinement

Decolonization is NOT parochialism. A fully decolonized Ukrainian curriculum presents Ukrainian culture as a *clear-sighted perspective on the world*, not only as a subject for outsiders to learn about. Ukrainian voices that see other societies accurately (Zhadan on Hungary, Stus on Russia, Plokhy on global history) are expressions of Ukrainian cultural confidence. The engagement and cultural-accuracy reviewers should reward this outward-facing standing, not only inward-facing self-description.

### General principle
**This curriculum's cultural references must be Ukrainian on Ukraine's own terms.** "Kyiv-born" is not the same as "Ukrainian writer." Russian-imperial figures with biographical ties to Ukraine are Russian-imperial figures. Do not silently inherit the Soviet cultural map that treats Ukrainian heritage as a subset of Russian heritage. When in doubt, pick a figure whose Ukrainian identity is uncontested.

### Humor posture — structural, not decorative
Ukrainians survive empire and war through irony, parody, meme-fluent resistance. A curriculum that teaches Ukrainian without teaching humor doesn't teach Ukrainian. But humor here means humor-under-siege — wit that knows the context. Chipper "everything is fine" register while Kharkiv is under drone attack is imperial erasure. The right register is Zhadan's: serious and sometimes funny, never cheerful-oblivious, never relentlessly solemn. **Note per Codex review 2026-04-18:** this posture is a calibration principle for prompt writers and module authors. It is NOT a hard gate applied to beginner modules where simplicity legitimately dominates. See §5.5 for level-calibrated decomposition.

## Appendix D — Codex adversarial review log (2026-04-18)

Codex ran adversarial review on the v1 of this doc on 2026-04-18 PM (task-id `design-review-dimensional-2026-04-18`). Full response preserved in agent-bridge message #368. Ten findings, all accepted after evidence evaluation. Key structural changes driven by the review:

| Finding | Severity | Change to doc |
|---|---|---|
| #1 Claude parallel cache math wrong | major | §6b rewritten to prewarm + fan-out pattern. Corrected cost math. Wiki no longer claims cache justification (only 1 Claude dim). |
| #2 Codex caching claim mixed billing models | major | §6b clarifies: no caching in current CLI-fresh-session path. Cost as N × full prefix. Agent-fit drives Codex assignment, not cache economics. |
| #3 Invocation path drift | major | §6a requires unified runtime via `scripts/agent_runtime/` adapters. No `delegate.py` or direct-API bypass. |
| #4 Single patcher reinvents FROM-SCRATCH rewrite | blocker | §2 principle 5 + §6c rewritten to reviewer-as-fixer per dim + deterministic fix-merger (code, no LLM). Preserves ADR-001. |
| #5 Agent assignments are hypotheses + factual wiki dim assumes tool access Codex doesn't have | major | §3 + §4 tables: all agent assignments marked "default pending benchmark"; factual/linguistic dims deferred until `CodexAdapter:135` tool_config question is resolved; dialogue dim folded into engagement. |
| #6 Pilot can't measure recall | major | §7 rewritten to pilot + seeded benchmark (both, not either-or). |
| #7 Ukrainian-only reviewer instructions is a risk | major | §2 new principle 11: Ukrainian for artifact, English for reviewer instructions until benchmarked. |
| #8 Zhadan north-star as gate punishes beginner plainness | major | §5.5 rewritten: Zhadan is calibration artifact, NOT scoring gate. Decomposed into concrete checks with per-level weights. "Zhadan-fit" sub-check only at C1+. |
| #9 Arbitrary thresholds + deterministic dims shouldn't be LLM-scored | major | §3a + §4a: structural integrity + citation-registry consistency moved to code gates. Thresholds deferred to seeded benchmark. |
| #10 Rollout hard-gates rebuild day one + references obsolete backfill | blocker | §8 rewritten to canary/shadow-mode rollout. Backfill step deleted. |

**Codex verdict:** PROCEED WITH FIXES. Architecture direction sound (per-dim gates, evidence-first, semantic wiki review layer). Fixes are execution/rollout level.

**Lead-dev judgment on the review:** 10 findings, 10 with strong evidence (repo paths, ADR references, real mechanisms, peer-reviewed papers). Zero manufactured findings. User's bar was "don't accept anything without strong arguments backed with real sources and truth" — the review meets it.

**Files updated as a result of this review:**
- `docs/design/dimensional-review.md` (this file)
- `docs/session-state/current.md` (captures policy changes for next session)
- `memory/MEMORY.md` (fact corrections)
- Tasks updated: #4 demoted, #5 re-scoped, #10 marked complete, new tasks for adapter audit likely needed
