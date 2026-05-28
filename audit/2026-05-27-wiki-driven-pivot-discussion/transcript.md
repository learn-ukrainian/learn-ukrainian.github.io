# Wiki-driven writer pivot discussion — full transcript (2026-05-27 Pt 11)

## user round 0 (post) — 2026-05-27T20:57:18.369516+00:00

# Wiki-driven writer architecture pivot — design discussion

## Where we are (2026-05-27 Pt 11)

After 4 PRs of writer-prompt hardening (#2366, #2367, #2370, #2371) and a 5th in-flight (#2372 — failing CI on the 130KB writer-prompt ceiling test), Phase 2a refire #2 produced a nearly-shippable m20 but still tripped `word_count` (1058 < 1104 min). Codex's brain-pick (turns 1-3 saved at `audit/2026-05-27-codex-brain-pick-m20/`) called the pattern "visible compliance tokens" — gates rewarded local-knob-hitting rather than integrated teaching.

The user is pivoting: **reframe the LLM from "compose lesson from inputs" to "render the WIKI as a lesson, using the wiki's cited RAG chunks as evidence, applying ULP's pedagogical pattern."** The wiki was deliberately built (via `scripts/wiki/compile.py` defaulting to Gemini) to be the lesson spine — citing textbook chunks as [S1], [S2], ...

## Proposed architecture

| Layer | Role | Source |
|---|---|---|
| **Wiki** | Lesson spine — methodology, sequence, vocab list (with frequency stars), L2 error patterns, decolonization stance, textbook example formats | `wiki/pedagogy/{level}/{slug}.md` |
| **Textbook RAG** | Authority/evidence backing wiki claims (every wiki section cites chunks like [S1]…[S9]) | `data/sources.db` chunks fetched on demand via `mcp__sources__get_chunk_context` / `verify_quote` |
| **ULP** | Pedagogical pattern — the 7 practices + S1→S6 progression for A1/A2 | `docs/references/private/` ULP files; pattern summarized in `docs/best-practices/ulp-presentation-pattern.md` |
| **LLM (writer)** | Render wiki + voice-rewrite (methodological Ukrainian → 2nd-person teacher voice) + emit dialogue boxes / activities / vocab table / resources — but invents no vocab, examples, or claims | claude-tools / codex-tools / gemini |

The **wiki for `a1/my-morning`** has 5 substantive sections (Методичний підхід, Послідовність введення Steps 1-5, Типові помилки L2 with 6-row table, Деколонізаційні застереження incl. concrete bad-form pairs, Словниковий мінімум with ★ frequencies, Приклади з підручників with chunk-cited exercises). Each maps 1:1 to a lesson section. The wiki provides the substantive content; the LLM provides the voice + structural rendering.

## The new writer rule (one rule replacing the current 17)

> Your job is to RENDER the wiki below as a learner-facing `module.md` + `vocabulary.yaml` + `activities.yaml`. You may rewrite the voice from methodological-Ukrainian to teacher-to-learner-second-person. You may add English glosses. You may add structural scaffolding (headings, tables, dialogue boxes, activity items). You may NOT introduce vocabulary, examples, citations, dialogue lines, or claims not derivable from the wiki or its cited RAG chunks. Every Ukrainian noun/verb/adverb in your output must trace back to the wiki's vocabulary minimum or examples section. For evidence, fetch the wiki's cited RAG chunks ([S1], [S2], ...) via MCP and quote them — do not paraphrase.

## What the LLM still genuinely composes (and gates that stay load-bearing)

1. **English glosses** — wiki is Ukrainian. LLM (or Balla EN-UK dict deterministic) adds glosses.
2. **Dialogue boxes** — wiki has *example sentences*, not full *dialogues*. LLM composes 6-8 turn dialogues using ONLY wiki vocab.
3. **Section intros + transitions + closing summary** — bounded voice the wiki doesn't have.
4. **Activity drilldowns** — wiki gives example formats; LLM generates items drawing only from wiki vocab/examples.

Gates that stay load-bearing: `engagement_floor`, `l2_exposure_floor`, `formatting_standards`, `wiki_coverage` (newly load-bearing as the 1:1 enforcer), `vesum_verified` (trivial when vocab is wiki-bounded).

## Gates that trivialize (LLM constrained to wiki content)

`russianisms_strict`, `paronym_clean`, `surzhyk_clean`, `calques_clean`, `published_quote_for_publishable_refs`, `chunk_context_for_all_refs`, `citations_resolve`, `ai_slop_clean`, `register_consistency`, the entire scope-creep / hallucination class. The writer can't invent a Russianism if it can't invent vocab.

## Questions for codex + gemini

1. **Is this architecturally sound?** Does the 4-layer split (wiki spine + RAG evidence + ULP pattern + LLM renderer) hold up at A1/A2 / B1+ / seminar tracks? Where are the gaps?

2. **The new writer rule (the single charter quoted above) — does it overconstrain?** Will the LLM be able to compose pedagogically-strong dialogues with vocab strictly bounded to the wiki minimum (10-20 lemmas at A1)?

3. **The wiki-vocab-bound gate** — every Ukrainian word in module.md must lemmatize to a vocab entry in wiki § Словниковий мінімум OR appear in a wiki example sentence. Is this enforceable? What's the right reject condition (single word miss vs threshold)?

4. **Wiki gaps**: when the wiki is too thin (a section is a stub, or examples are insufficient), what's the failure mode? Hard reject (block module build until wiki improved)? Soft warn (LLM may bridge minimally)?

5. **Dialogue composition under wiki-vocab constraint**: at A1, the wiki vocab minimum is 10-20 lemmas. A 6-turn dialogue with full sentences likely needs more. Should we expand the vocab gate to "wiki vocab minimum + UK function words + level-appropriate cefr_a1 lemmas via `query_cefr_level`"? Or just expand the wiki vocab minimum itself?

6. **Voice rewrite drift**: "rewrite methodological Ukrainian → 2nd-person English teacher voice" is fuzzy. What's the right operational definition + test? Sample-pair golden examples in the prompt?

7. **Existing writer prompt rules** — which of the 17 `#R-*` rules become redundant under wiki-driven? Which stay relevant (likely: `#R-CLEAN-TABLES`, `#R-CITE-HONEST`, `#R-BAD-FORM-MARKER`, `#R-PROSE-FLOOR-A1`, `#R-AUDIENCE-LANGUAGE-A1`)?

8. **Empirical test plan**: how do we validate this changes the outcome on m20? Re-fire under new prompt, then compare against Pt 10 refire (worktree 185032). What's the success criterion?

9. **Migration path**: do we ship this as V7.1 (modify current writer prompt + add wiki-vocab-bound gate) or as V8 (full new pipeline)? V7.1 is faster but risks bringing in residual V7 framing; V8 is cleaner but takes longer.

10. **Blind spots**: what are we missing? What kills this architecture in practice?

## Constraint

This is analysis-only discussion. Do not propose code changes; propose design directions and counter-arguments. Round limit 2.


## codex round 1 (reply) — 2026-05-27T21:02:19.465813+00:00

Scope note: the pending A1 shape-contract and writer-split cards overlap this discussion but do not block a read-only design answer.

My position: **architecturally sound direction, but not sound as the “one rule replaces 17” version.** Treat this as “wiki becomes the primary content contract,” not “wiki removes the need for prompt/gate discipline.”

**Option A: V7.1 patch.** Fast, but likely inherits the current prompt’s crowded failure surface. `linear-write.md` already says the wiki is “LESSON SOURCE” and every obligation must be implemented, with deterministic row checks (`scripts/build/phases/linear-write.md:158`, `scripts/build/phases/linear-write.md:184`). The failure is not absence of that idea; it is that too many other obligations still compete.

**Option B: V8 wiki-renderer. Recommended.** New writer phase whose inputs are: audited wiki contract, source registry, learner-state lexicon, ULP presentation policy, output schemas. Keep V7.1 only as a one-module shadow experiment on m20.

Key points by question:

1. The 4-layer split holds for A1/A2 if the wiki is promoted from “context” to an audited contract. It is weaker for B1+/seminars unless wiki claims become a claim/evidence graph with source priority and two-source checks. Seminar tracks are bias-sensitive; “wiki says it” is not enough.

2. The single charter overconstrains A1 dialogue if interpreted literally. m20’s current structural floor is 14 dialogue lines (`scripts/config.py:488`), and the prompt asks writers to emit 15 for margin (`scripts/build/phases/linear-write.md:331`). A 10-20 lemma wiki minimum alone will not support natural 6-8 turn dialogue plus questions.

3. The vocab-bound gate is enforceable, but only with a layered allowlist. Existing learner-state code already extracts Ukrainian surfaces and compares them to cumulative + declared vocab (`scripts/audit/checks/learner_state.py:97`, `scripts/audit/checks/learner_state.py:110`). Reject on unsupported **content lemmas** after lemmatization, but allow closed-class function words, proper nouns, bad-form markers, source quotes, and already-taught cumulative vocab. Single-token hard fail is too brittle.

4. Wiki gaps should hard-reject content generation. The writer may bridge voice, headings, English glosses, transitions, and activity packaging. It should not bridge missing examples, missing L2 error rows, missing source evidence, or thin decolonization stance. Current wiki coverage is hard-fail (`scripts/config.py:420`; `scripts/audit/wiki_coverage_gate.py:317`).

5. Expand the wiki/plan lexicon, not ad hoc CEFR permission. m20 already has plan `targets.new_vocabulary` and `vocabulary_hints` (`curriculum/l2-uk-en/plans/a1/my-morning.yaml:43`, `curriculum/l2-uk-en/plans/a1/my-morning.yaml:60`), while the wiki has a fuller minimum (`wiki/pedagogy/a1/my-morning.md:58`). CEFR can validate, but should not silently authorize extra writer invention.

6. Voice rewrite needs operational tests: A1 explanation prose in English, Ukrainian only as target forms, no Ukrainian metalanguage to the learner (`scripts/build/phases/linear-write.md:306`, `scripts/build/phases/linear-write.md:309`), no writer scaffolding leaks (`scripts/build/phases/linear-write.md:315`). Golden before/after pairs are useful, but lintable negatives matter more.

7. Rules that stay load-bearing: citation honesty, bad-form marker, A1 audience language, no scaffolding leaks, clean tables, dialogue format, prose/word floor, artifact fence format, tool telemetry. Rules that become lighter but not removable: russianism/surzhyk/calque/paronym gates. The wiki itself is generated by Gemini (`wiki/pedagogy/a1/my-morning.md:8`), so it cannot be trusted as a final language authority without checks.

8. Empirical test on m20: preflight wiki source resolution; generate from the V8 renderer; pass `word_count` at or above 1104 minimum for target 1200 (`scripts/build/linear_pipeline.py:6968`); hit 100% mandatory wiki obligations; pass dialogue/example floors; no unsupported content lemmas except allowlisted classes; content review must say the result teaches integrated routine/reflexive grammar, not just visible compliance tokens.

9. Migration: ship as **V8 design with a V7.1 shadow pilot**. If V7.1 means “edit current 500-line prompt again,” I expect more prompt-ceiling and contradiction failures. If it means “route one m20 build through a separate renderer prompt while leaving pipeline wiring intact,” that is a useful experiment.

10. Blind spots: source-registry freshness, copyright/learner suitability of “quote chunks verbatim,” POS boundary problems, stress-mark enforcement from ULP, activity item generation under strict vocab limits, and seminar-track bias. Also current manifest extraction covers sequence steps, L2 errors, phonetic rules, bans, and resources, but not the wiki vocab minimum as a first-class obligation (`scripts/build/phases/wiki_manifest.py:24`, `scripts/build/phases/implementation_map.py:12`).

So: adopt the pivot, but make the wiki renderer a new constrained contract, not a softer prose instruction pasted into V7. [DISAGREE]

## gemini round 1 (reply) — 2026-05-27T21:02:19.470459+00:00

# Wiki-driven writer architecture pivot — Design Analysis (Round 1)

The proposed pivot from **LLM-as-Composer** to **LLM-as-Renderer** is a significant architectural correction that addresses the "visible compliance tokens" problem (Code 1-3). By making the Wiki the lesson spine and the LLM a constrained rendering engine, we move the pedagogical burden from a non-deterministic writer to a deterministic, human-curated (or Wiki-agent-curated) knowledge base.

## 1. Architectural Soundness
The 4-layer split (Wiki/RAG/ULP/LLM) is sound across all tracks. It effectively separates **Authority** (RAG), **Sequence** (Wiki), **Pattern** (ULP), and **Voice** (LLM). For A1/A2, this fixes the "hallucinated textbook" issue. For Seminar tracks, it prevents "hallucinated history" by forcing 1:1 adherence to wiki-compiled facts.

## 2. Overconstraint & Pedagogical Strength
The "no invention" rule (no new vocab/examples) is a necessary discipline but poses a risk to **Dialogue Composition**. At A1, a 6-8 turn dialogue with only 15 lemmas can feel robotic. However, ULP Practice 4 (teach-by-immersion) suggests that dialogues are artifacts to be encountered; they don't need to be complex if the goal is phonetics and basic reflexives. The constraint forces *better* wiki preparation rather than *cleverer* writing.

## 3. Wiki-vocab-bound gate
Enforcing lemmatization of every word to a wiki entry is feasible using the `verify_words` (VESUM) tool.
- **Enforcement**: Reject on a single word miss (hard-fail). This forces the writer to stick to the SLOB (Slovnykovyi Minimum).
- **Nuance**: We must allow **Latin-character names** (exempt) and **canonical function words** (see Q5).

## 4. Wiki Gaps
Thin wiki sections should trigger a **Hard Reject** (Block module build). If the wiki is a stub, the LLM "bridging" will inevitably lead back to hallucination/Russianism contamination. The failure mode must be: "Wiki section [X] is insufficient; improve wiki first."

## 5. Dialogue composition & Vocab Expansion
We MUST expand the vocab gate to **"Wiki vocab minimum + UK function words + level-appropriate CEFR lemmas"**. A1 cannot function without basic pronouns, prepositions, and conjunctions that might not be the "focus" of the morning-routine wiki.
- **Expansion Source**: `query_cefr_level(level='a1')` + a hardcoded "Global Function Word List" (e.g., *і, та, але, бо, я, ти, у, на, в*).

## 6. Voice rewrite drift
"Methodological Ukrainian → 2nd-person English teacher voice" needs a **One-Shot Pattern**.
- **Definition**: Transform "Цей розділ вчить..." (Wiki) to "Now, try using..." (Module).
- **Test**: Comparison against a `voice_golden_examples` set in the prompt.

## 7. Redundant vs. Relevant Rules
- **Redundant**: `#R-TEXTBOOK-30W` (handled by Wiki-RAG 1:1 mapping), `#R-CITE-HONEST` (mostly trivialized).
- **Relevant**: `#R-VOICE-META` (still need to avoid "Welcome to this lesson"), `#R-BAD-FORM-MARKER` (still need the `<!-- bad -->` syntax for contrast pairs), `#R-CLEAN-TABLES` (structural formatting), `#R-AUDIENCE-LANGUAGE-A1` (immersion logic).

## 8. Empirical Test Plan
1. Re-fire `m20` under V8-alpha prompt.
2. **Success Criterion**: `word_count` passes (>1104) WITHOUT "compliance-only" filler; zero unknown_vocab_in_prose violations; all dialogue lines grounded in `wiki/my-morning.md`.

## 9. Migration Path: V8
This is a V8 change. The shift from "searching for grounding" to "rendering a manifest" is too deep for V7.1. We should ship a clean `scripts/build/phases/v8-render-module.md` prompt.

## 10. Blind Spots
- **Low Variance**: Constraints might produce 50 modules that feel identical in structure.
- **Wiki Staleness**: If the wiki isn't updated when a new textbook is added to `sources.db`, the writer is blind to it.
- **Surzhyk in RAG**: If the Wiki cites a "bad" textbook chunk, the Renderer will faithfully reproduce it unless the Reviewer (Blue Team) catches it.

[DISAGREE]

## codex round 1 (reply) — 2026-05-27T21:04:15.026951+00:00

My round-2 position is closer to convergence on **V8**, but I still have substantive objections.

I accept Gemini’s V8 conclusion and hard-reject stance for thin wiki sections. The existing V7 prompt already says the wiki is the “LESSON SOURCE” and row-by-row obligation source, not background (`scripts/build/phases/linear-write.md:158`, `scripts/build/phases/linear-write.md:184`). Since that did not prevent visible-compliance failure, this should be a new renderer contract, not another V7 prompt patch.

Pushback on Gemini: “Reject on a single word miss (hard-fail).” I disagree. The current learner-state gate extracts Ukrainian surfaces and compares them to cumulative plus declared vocab (`scripts/audit/checks/learner_state.py:51`, `scripts/audit/checks/learner_state.py:104`, `scripts/audit/checks/learner_state.py:110`), but it has calibrated tolerance, and m20’s band allows up to 80 unsupported Ukrainian words (`scripts/config.py:488`, `scripts/config.py:493`). A single-token hard fail will mostly punish tokenization, inflection, names, bad-form contrasts, and quoted evidence. The right reject condition is: hard-fail unsupported **content lemmas after normalization** outside wiki vocab/examples + plan vocab + cumulative learner state + closed-class function allowlist; single misses should fail only if they are pedagogically meaningful content lemmas or Russianism/calque risks.

Pushback on Gemini: “MUST expand … with level-appropriate CEFR lemmas.” I still disagree with CEFR as an open runtime permission. That recreates writer invention through a side door. For m20, the plan already gives target and hint vocab (`curriculum/l2-uk-en/plans/a1/my-morning.yaml:47`, `curriculum/l2-uk-en/plans/a1/my-morning.yaml:60`) and the wiki gives a richer minimum (`wiki/pedagogy/a1/my-morning.md:58`). If dialogues need more, expand the wiki/plan lexicon before render. CEFR can validate proposed additions, not silently authorize them.

Pushback on the root proposal: “quote cited RAG chunks — do not paraphrase.” That cannot be blanket policy. V7 already forbids Grade 1-3 textbook blockquotes in adult A1 while still requiring chunk retrieval for grounding (`scripts/build/phases/linear-write.md:127`, `scripts/build/phases/linear-write.md:129`, `scripts/build/phases/linear-write.md:313`). The renderer should quote only adult-appropriate publishable sources; children’s textbook chunks should ground examples and resources, not appear verbatim in learner prose.

Rules I would keep load-bearing: citation honesty, chunk retrieval telemetry, bad-form marker syntax, A1 audience language, single teacher voice, no scaffolding leaks, clean tables, dialogue count/format, prose/word floor. Those are not redundant: they encode output shape and learner-facing constraints (`scripts/build/phases/linear-write.md:303`, `scripts/build/phases/linear-write.md:307`, `scripts/build/phases/linear-write.md:310`, `scripts/build/phases/linear-write.md:316`, `scripts/build/phases/linear-write.md:321`, `scripts/build/phases/linear-write.md:327`, `scripts/build/phases/linear-write.md:331`).

Empirical success criterion for m20: V8-alpha renderer passes word count using the existing 8% lower tolerance (`scripts/build/linear_pipeline.py:6968`, `scripts/build/linear_pipeline.py:6973`), passes 100% wiki obligations under hard-fail behavior (`scripts/audit/wiki_coverage_gate.py:317`, `scripts/audit/wiki_coverage_gate.py:318`), meets the 14-line A1 dialogue floor (`scripts/config.py:489`), and has zero unsupported content lemmas under the new bounded-lexicon gate. Human/content review should specifically compare against Pt 10 for “integrated teaching” rather than more gate-visible padding.

So: V8 wiki-renderer pilot, yes. “One rule replaces 17,” single-token hard fail, and broad CEFR unlock, no. [DISAGREE]

## gemini round 1 (reply) — 2026-05-27T21:04:15.030449+00:00

I have reviewed Codex's Round 1 response and my own. We are converging on the **V8 wiki-renderer** architecture, but Codex correctly identified flaws in both the user's premise ("one rule replaces 17") and my Round 1 proposal regarding vocab expansion.

**1. Concession to Codex on Q5 (Vocab Expansion)**
In Round 1, I proposed bridging the dialogue vocabulary gap by using `query_cefr_level` and a hardcoded function word list. Codex is correct: this is a runtime hallucination vector. We should strictly rely on `scripts/audit/checks/learner_state.py` mechanisms. The permitted vocabulary for the writer must be strictly defined as `(Wiki SLOB ∪ plan.targets.new_vocabulary ∪ cumulative_vocabulary)`. Ad-hoc CEFR permission subverts the deterministic curriculum progression.

**2. Concession to Codex on Q7 (Gate Trivialization)**
In Round 1, I claimed `#R-CITE-HONEST` and Russianism gates would trivialize. Codex rightly points out that the wiki itself is an LLM-generated artifact (`wiki/pedagogy/a1/my-morning.md:8` shows it was generated by `gemini-3.1-pro-preview`). Treating the wiki as infallible would simply launder hallucinations upstream. The writer must still run `check_russian_shadow` and `verify_quote` on the wiki's pedagogical claims. The structural rules (`#R-VOICE-META`, `#R-BAD-FORM-MARKER`, `#R-CLEAN-TABLES`) and verification gates MUST remain load-bearing.

**3. Refining the V8 Contract**
Based on our shared analysis, the architecture should move forward as Option B (V8 wiki-renderer), structured as follows:
*   **The Prompt**: Replaces the composer framing but KEEPS the structural and verification rules.
*   **The Vocab Gate**: Hard-rejects any content lemma not found in the layered allowlist (Wiki + Plan Targets + Cumulative Learner State).
*   **The Wiki Gate**: Hard-rejects the build upstream if the wiki sections are thin, preventing the writer from attempting to "bridge" missing content.

The V8 path resolves the "visible compliance tokens" issue by constraining the writer's domain to rendering and formatting, rather than pedagogical invention, without sacrificing necessary LLM-auditing rigor.

[AGREE]
