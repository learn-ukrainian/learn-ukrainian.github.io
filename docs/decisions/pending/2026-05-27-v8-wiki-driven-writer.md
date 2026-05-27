# PENDING — V8 wiki-driven writer (LLM-as-renderer)

**Status:** PENDING — awaiting user approval. Synthesizes the 2026-05-27 codex+gemini discussion on `wiki-driven-writer-pivot` channel; both agents converged on V8 architecture by their second message with `[AGREE]` at the end of gemini's round-2 reply.
**Surfaced:** 2026-05-27 (Pt 11) — user directive after Pt 10's nearly-shippable m20 still tripped `word_count` (1058 < 1104) and PR #2372 ceiling-test failure exposed the writer prompt growing past 130KB despite the 4 hardening PRs (#2366, #2367, #2370, #2371). User reframed: *"the LLM should USE THE WIKI to BUILD the lesson. ... is this possible. how should we approach it?"*
**Scope (BLOCKING):** All future module builds. Does NOT block tech-debt PRs that don't touch the writer phase or the wiki-coverage gate.
**Issues:** new (to file once approved)
**Predecessor:** [`2026-05-18-wiki-obligation-emission-contract.md`](../2026-05-18-wiki-obligation-emission-contract.md) — V7 gave the writer an emission contract but kept it as "compose from inputs" framing. V8 changes the framing itself.

---

## TL;DR

Replace the V7 *LLM-as-Composer* writer phase with a V8 *LLM-as-Renderer* writer phase. The wiki (`wiki/pedagogy/{level}/{slug}.md`) becomes the **lesson spine**; the textbook RAG provides **authority/evidence** via wiki citations like `[S1], [S9]`; ULP provides the **pedagogical pattern** (7 practices, S1→S6 progression); the LLM's job collapses to **render + voice-rewrite + bounded glue**.

The 17 `#R-*` writer-prompt rules collapse to ~9 (the rest trivialize because the LLM can no longer invent vocab, examples, or claims). The 130KB writer-prompt ceiling stops being load-bearing. The `wiki_coverage` gate becomes the primary correctness enforcer.

Codex + gemini both agreed (after pushback rounds): **V8 new renderer contract**, NOT another V7 prompt patch. Pilot on m20 alone first.

---

## Why now

1. **PR #2372 / m20 has been the rolling proof-of-pipeline since 2026-05-12.** Pt 10's empirical refire (worktree `185032`) under the fully hardened pipeline scored 9.5/10 on LLM review + 6/7 step-5 vocab coverage, but failed `word_count` due to *structural-density shift* — the writer placed content into tables/callouts/dialogue boxes (per `#R-CLEAN-TABLES`) instead of prose. The gate counts prose only.
2. **The hardening rules themselves are growing the writer prompt past its ceiling.** PR #2372 caught this empirically: `test_a1_letter_module_writer_prompt_stays_under_ceiling` (130KB) fails. The 4-PR hardening (#2366–#2371) added the rules; the ceiling cannot accept more.
3. **Codex's brain-pick (audit/2026-05-27-codex-brain-pick-m20/) named the pattern**: "visible compliance tokens" — gates rewarded local knob-hitting (one callout for engagement_floor, 15 dialogue boxes for l2_exposure_floor) rather than integrated teaching. Each hardening rule tightens one knob; the failures move to the next.
4. **The wiki was deliberately built to be the lesson spine** (per `scripts/wiki/compile.py` defaulting to Gemini, with `[S1]…[S9]` chunk citations into `data/sources.db`). m20's wiki has 5 substantive sections × 21 vocab lemmas × 6 L2 error patterns × 3 decolonization bad-form pairs × 5 textbook exercises with chunk IDs — empirically rich enough to be a lesson spine.
5. **User direction 2026-05-27 evening**: pivot from "compose lesson" to "render wiki + cited RAG + ULP pattern".

---

## The 4-layer V8 architecture

| Layer | Role | Source | Authority |
|---|---|---|---|
| **Wiki** | Lesson spine: methodology, sequence (Steps 1-5 at A1), vocab minimum (with frequency stars), L2 error table, decolonization stance with bad-form pairs, textbook example formats | `wiki/pedagogy/{level}/{slug}.md` | Curated (Gemini-generated, human/agent-reviewed) — but NOT infallible. Must still be audited per #7 below. |
| **Textbook RAG** | Authority/evidence backing wiki claims; cited via `[S1]…[S9]` markers in wiki | `data/sources.db` chunks fetched on demand via `mcp__sources__get_chunk_context` / `verify_quote` | Source-of-truth for quotes; Grade 1-3 chunks ground examples but do NOT appear as verbatim quotes (existing `#R-NO-CHILDREN-PRIMARY-QUOTES`). |
| **ULP** | Pedagogical pattern (Anna Ohoiko's 7 practices, S1→S6 progression for A1/A2) | `docs/references/private/` ULP files; pattern summarized in `docs/best-practices/ulp-presentation-pattern.md` | Defines presentation shape only; never invents content. |
| **LLM (renderer)** | Render wiki + voice-rewrite (3rd-person methodological → 2nd-person teacher voice) + add English glosses + emit dialogue boxes / activities / vocab table / resources. ADDS NO vocab, examples, citations, dialogue lines, or claims not derivable from wiki + cited RAG. | claude-tools / codex-tools / gemini-tools / deepseek-tools | Bounded by the new vocab gate; structural rules stay load-bearing. |

---

## What the LLM still genuinely composes

Constrained creative work — bounded by the layered allowlist (see "Vocab gate" below):

1. **English glosses** — wiki is in Ukrainian. LLM (or `mcp__sources__translate_en_uk` for deterministic Balla EN-UK dict lookups) adds glosses to every published Ukrainian noun/verb/adjective.
2. **Dialogue boxes** — wiki has example sentences but not full 6-8 turn dialogues. LLM composes dialogues using ONLY allowed lemmas (see #5 below). Existing `l2_exposure_floor` (14-line minimum at A1) still applies.
3. **Section intros + transitions + closing summary** — bounded voice the wiki doesn't carry. Subject to `#R-VOICE-META` anti-meta-narration list.
4. **Activity drilldowns** — wiki names the exercise format (Вправа 1, 2, …); LLM generates concrete items drawing only from allowed lemmas.

---

## Vocab gate (new) — the layered allowlist

**Hard-reject content lemmas (after VESUM lemmatization) outside this allowlist:**

```
allowed_lemmas = (
    wiki.vocabulary_minimum_lemmas
    ∪ plan.targets.new_vocabulary
    ∪ plan.targets.vocabulary_hints
    ∪ cumulative_learner_state.taught_lemmas   # prior modules in the same level
    ∪ closed_class_function_words              # canonical list (і, та, але, бо, я, ти, у, на, в, з, що, як, де, ...)
    ∪ proper_nouns_in_wiki_examples            # surface-form match required
    ∪ bad_form_markers                         # words inside <!-- bad -->...<!-- /bad --> are exempt
    ∪ quoted_evidence_from_cited_rag_chunks    # words inside `> ` blockquotes citing wiki [S*] anchors
)
```

**Reject condition** (codex pushback accepted; gemini r2 conceded):

- Hard-fail on **unsupported content lemmas after normalization** (i.e., lemmas not in the allowlist).
- NOT a single-token hard-fail. Allow band-tolerated misses for tokenization edge cases (compound words, inflected proper nouns, hyphenated forms) — band thresholds picked per `scripts/config.py:488,493` precedent (m20's existing `learner_state` gate allows up to 80 unsupported Ukrainian words).
- Single content-lemma miss → fail ONLY if it's pedagogically meaningful (i.e., a noun/verb/adjective NOT in the allowlist).

**Why NO CEFR runtime permission** (Codex r2 → Gemini r2 conceded): allowing the writer to "draw from cefr_a1 lemmas via `query_cefr_level`" recreates writer invention through a side door. If a dialogue needs more vocab, **expand the wiki minimum first**, then re-build. The wiki is the contract; CEFR validates proposed wiki additions but does not silently authorize runtime extras.

---

## Wiki gate (upstream hard-reject)

Block module build BEFORE writer runs when wiki sections are thin:

```
v8_wiki_completeness_check(wiki_path):
    require wiki has:
        - non-empty methodology section
        - ≥3 sequence steps (A1/A2 → ≥5)
        - ≥3 L2 error rows in the typical-errors table
        - ≥1 decolonization bad-form contrast pair (for L1-Russian-substitutable topics)
        - ≥{20 at A1, 30 at A2, 50 at B1+, 100 at seminar} vocab lemmas in Словниковий мінімум
        - ≥3 textbook example exercises with chunk_id citations
    if any miss: hard-reject with diagnostic naming the missing section.
```

Failure mode: "Wiki section [X] is insufficient; improve wiki first." (Gemini r1 framing; codex r1 agreed.)

Wiki improvements via `scripts/wiki/compile.py --writer gemini` — cheap, unmetered, and decoupled from the writer phase.

---

## Rules that stay load-bearing (codex r2 detailed list, gemini r2 conceded most)

Keep:
- `#R-CITE-HONEST` — wiki is LLM-generated; writer must still `verify_source_attribution` / `verify_quote` before quoting wiki citations.
- `#R-VOICE-META` — anti-meta-narration phrase list remains essential for voice rewrite quality. The "Welcome to…", "In this section we will learn…" patterns are still tempting for the LLM.
- `#R-BAD-FORM-MARKER` — the `<!-- bad -->...<!-- /bad -->` convention is structural; survives the pivot unchanged.
- `#R-CLEAN-TABLES` — bold ONLY target Ukrainian forms; six-row conjugation tables. Structural.
- `#R-AUDIENCE-LANGUAGE-A1` — A1 explanations stay in English; Ukrainian appears only as target.
- `#R-NO-SCAFFOLDING-LEAKS` — no `Крок 5:`, no `[S1]`, no obligation IDs in published prose.
- `#R-NO-CHILDREN-PRIMARY-QUOTES` — Grade 1-3 chunks ground examples but never appear as published blockquotes.
- `#R-GRAMMAR-TERMS-A1` — proper grammatical terminology (noun, verb, reflexive) in English explanations.
- `#R-SINGLE-VOICE-A1` — one teacher voice across the module.
- Dialogue count + format rules (`l2_exposure_floor`, `<DialogueBox uk="..." en="...">`).
- Prose floor rule (existing `#R-PROSE-FLOOR-A1` from PR #2372 if approved, or replaced by gate-side word_count).
- Artifact emission contract (`<implementation_map>` etc.) — adapted for V8's wiki-1:1 obligations.

Trivialize but DO NOT remove (codex pushback on gemini's r1 "trivialize" framing):
- `russianisms_strict`, `paronym_clean`, `surzhyk_clean`, `calques_clean` — wiki is LLM-generated and might cite a chunk that contains Russianisms. The audit gates must run on the rendered output regardless. Their *fire rate* drops to near-zero, but they remain load-bearing.
- `published_quote_for_publishable_refs`, `chunk_context_for_all_refs`, `citations_resolve`, `ai_slop_clean`, `register_consistency` — same: necessary but rarely-firing.

---

## Voice rewrite — operational test

**Definition**: rewrite 3rd-person methodological Ukrainian → 2nd-person English teacher voice, WITH NO new Ukrainian content.

**Tests (in combination)**:

1. **Token-set diff (hard gate)**: every Ukrainian token in rendered module → wiki's Ukrainian token set ∪ allowlist. Existing `scripts/audit/checks/learner_state.py:97-110` mechanism extended for V8.
2. **Voice anchor lintable negatives**: the existing `#R-VOICE-META` forbidden-phrase list (with the full anchors `"Welcome to the start of our journey"`, `"In this section we will learn"`, etc.) becomes a deterministic post-emit grep.
3. **Voice-golden examples** (gemini r1 proposal): include 2-3 sample wiki-to-module before/after pairs in the prompt as a one-shot pattern (`Цей розділ вчить...` → `Now, try using...`). Used as prompt scaffolding, not assertion.
4. **LLM-as-judge** (only as a content-review pass, not a build gate): paragraph-by-paragraph judges "does this rendering preserve the wiki's pedagogical intent without inventing content?"

---

## Empirical test plan (m20 success criterion)

Pilot V8 on `a1/my-morning` alone first. Compare to Pt 10's worktree `185032` refire (the empirical pre-pivot baseline).

Success criteria for ship:
- `word_count` ≥ 1104 (gate threshold, 8% under 1200 target).
- 100% wiki obligations covered (every wiki vocab item, every L2 error row, every textbook exercise format appears in the rendered module).
- 14-line A1 dialogue floor satisfied (existing `l2_exposure_floor`).
- Zero unsupported content lemmas under the new bounded-lexicon gate (with allowlist).
- All existing structural gates pass (`engagement_floor`, `formatting_standards`, `vesum_verified`, the russianism/calque/surzhyk/paronym gates, `component_props`, `activity_schema`, `plan_reference_match`, `citations_resolve`, `ai_slop_clean`).
- Content-review explicitly says "integrated teaching" not "compliance-only padding".

Cap: 3 refires under V8 before either ship or escalate.

---

## Migration: V8 not V7.1

Both agents agreed by their second message:

- **V7.1 (modify the current `linear-write.md` writer prompt + add wiki-vocab-bound gate)** — Codex r1: *"Fast, but likely inherits the current prompt's crowded failure surface. … too many other obligations still compete."* Rejected.
- **V8 (new renderer phase with dedicated `v8-render-module.md` prompt)** — Codex r1: *"New writer phase whose inputs are: audited wiki contract, source registry, learner-state lexicon, ULP presentation policy, output schemas. Keep V7.1 only as a one-module shadow experiment on m20."* Gemini r2: *"The V8 path resolves the 'visible compliance tokens' issue by constraining the writer's domain to rendering and formatting, rather than pedagogical invention."* Accepted.

Pilot scope: m20 only. Keep V7 writer phase intact for all other modules until V8 ships clean on m20 + at least one other A1 module.

---

## Blind spots / risks

From the round-1 + round-2 discussion:

1. **Low variance** (gemini r1) — strict constraints might produce 50 modules that feel structurally identical. Mitigation: structural variation lives in WIKI (different exercise format counts, different sequence step counts per module), not in writer creativity.
2. **Wiki staleness** (gemini r1) — if the wiki isn't updated when a new textbook lands in `sources.db`, the renderer is blind to it. Mitigation: wiki freshness check + `scripts/wiki/compile.py` cron.
3. **Surzhyk-in-RAG laundering** (gemini r1) — if wiki cites a "bad" chunk, renderer faithfully reproduces it. Mitigation: russianism/surzhyk/calque/paronym audit gates stay on the rendered output (codex r1 pushback; gemini r2 conceded).
4. **Source-registry freshness, copyright/learner suitability of "quote chunks verbatim"** (codex r1) — Grade 1-3 chunks should ground examples but NOT appear as published quotes. Existing `#R-NO-CHILDREN-PRIMARY-QUOTES` stays.
5. **POS boundary problems** (codex r1) — tokenization of compound words, hyphenated forms, contractions. Mitigation: band-tolerated misses (no single-token hard-fail).
6. **Stress-mark enforcement from ULP** (codex r1) — A1 stress annotation is required pedagogically; V8 must still enforce. Existing stress dictionary + post-emit annotation.
7. **Activity item generation under strict vocab limits** (codex r1) — even with vocab bounding, generating 5-9 fill-in items under tight constraints requires careful prompt design. Iterate on the prompt.
8. **Seminar-track bias** (codex r1) — "wiki says it" is weaker for seminars where wiki content is itself contested (HIST, RUTH). For seminar tracks V8 may need a claim/evidence graph layer with two-source checks. Defer; pilot on A1/A2 first.
9. **Current manifest extraction** (codex r1, `scripts/build/phases/wiki_manifest.py:24`) — does not yet treat wiki vocab minimum as a first-class obligation. Implementation gap.

---

## Implementation outline (post-approval)

1. **New phase prompt**: `scripts/build/phases/v8-render-module.md` — replaces the composer framing while keeping the structural rules from §"Rules that stay load-bearing".
2. **Wiki contract validator**: new module `scripts/audit/wiki_completeness_gate.py` runs upstream of writer; hard-rejects on thin wiki.
3. **Layered vocab allowlist**: extend `scripts/audit/checks/learner_state.py` with the layered allowlist (current implementation already has `_extract_ukrainian_surfaces` + `_compare_to_cumulative` — extend the inputs).
4. **Wiki manifest extraction**: extend `scripts/build/phases/wiki_manifest.py` to make vocab minimum a first-class obligation.
5. **Phase routing**: extend `scripts/build/v7_build.py` (or fork as `v8_build.py`) to route a single module through the V8 renderer phase when configured via `--writer v8-renderer`.
6. **m20 pilot**: dispatch v8 build on `a1/my-morning`; review against success criteria above.
7. **Promote**: if pilot ships clean, port `a1/my-greeting-and-goodbye` (m1) as a second test.
8. **General rollout**: after 2 clean A1 modules, V8 becomes default for all A1/A2; B1+/seminar gets evaluated per track.

ETA: 2 weeks for V8-alpha + m20 pilot. Subsequent modules under V8 should each take 30-60 min (similar to V7) with significantly lower iteration count.

---

## Decision

**Status: PENDING — awaiting user sign-off.**

Decision options:

1. **Accept V8 pilot scope**: build V8-alpha + m20 pilot per the implementation outline above. Estimated 2 weeks.
2. **Stage V8 incrementally**: ship the wiki-vocab-bound gate first (1 week), then the new prompt + the rest of V8 (1 week). Same end-state, but earlier surface area for the gate.
3. **Reject V8**: continue with V7 + targeted prompt patches. Means continuing the trim-to-fit-ceiling cycle for each new hardening rule.
4. **Other**: capture user variation.

If approved, this decision supersedes the design framing in [`2026-05-18-wiki-obligation-emission-contract.md`](../2026-05-18-wiki-obligation-emission-contract.md) — but the deterministic `seed_implementation_map` infrastructure from that PR (#2153) carries forward into V8.

---

## Source documents

- Discussion transcript: [`audit/2026-05-27-wiki-driven-pivot-discussion/transcript.md`](../../../audit/2026-05-27-wiki-driven-pivot-discussion/transcript.md) (full codex + gemini round-1/2 messages)
- Codex brain-pick on m20 (the empirical failure trigger): [`audit/2026-05-27-codex-brain-pick-m20/turn-{1,2,3}-*.md`](../../../audit/2026-05-27-codex-brain-pick-m20/)
- Pt 10 handoff (the salad → near-shippable arc): [`docs/session-state/2026-05-27-pt10-phase2a-validates-only-word-count-gap.md`](../../session-state/2026-05-27-pt10-phase2a-validates-only-word-count-gap.md)
- V7 hardening PRs landed in Pt 9-10: #2366, #2367, #2370, #2371 (all merged). PR #2372 (Path B, ceiling fix) in flight under the current architecture.
- Predecessor ADR: [`2026-05-18-wiki-obligation-emission-contract.md`](../2026-05-18-wiki-obligation-emission-contract.md)
- Wiki source-of-truth example: [`wiki/pedagogy/a1/my-morning.md`](../../../wiki/pedagogy/a1/my-morning.md) (1888 words, 24KB, 5 substantive sections, [S1]…[S9] chunk citations, 21 vocab lemmas + 6 L2 errors + 3 bad-form pairs + 5 textbook exercise formats).
