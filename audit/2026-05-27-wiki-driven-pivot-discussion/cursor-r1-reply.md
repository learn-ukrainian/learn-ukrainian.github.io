# Cursor round 1 — V7.1 with structural refactor, not V8 plumbing

I've read the transcript, the pending V8 ADR, `linear-write.md`, cursor-tools wiring, and the m20 failure history. Below is a position, not a implementation plan.

---

## 1. V7.1 vs V8 — my pick

**Pick: V7.1, but only if it means a structural refactor, not another patch on the same hierarchy.**

Codex and Gemini treated "V8" as a new pipeline phase. That overstates the work. The end-state they converged on — renderer charter, layered vocab allowlist, wiki hard-reject upstream, ~9 surviving `#R-*` rules — does **not** require new phase routing to ship. It requires:

1. **Inverting prompt hierarchy** (renderer charter at the top, not buried at line 158)
2. **Deleting redundant rules** (PR #2260 already proved −118 lines is viable)
3. **One new gate** (wiki-bounded content lemmas — mostly an extension of existing `learner_state.py`)
4. **Wiki manifest fix** (vocab minimum as first-class obligation — codex's blind spot)

That is ~1–2 days, not two weeks. The extra ~10 days in the V8 ETA is optional separation (`v8-render-module.md`, `--writer v8-renderer` routing, `v8_build.py` fork) that pays off **later**, when track-specific prompts diverge (seminar vs A1).

**When V8-as-separate-file becomes worth it:** after m20 ships under V7.1, if you need (a) prompt-ceiling headroom without conditional blocks, (b) clean A/B without touching production prompt, or (c) seminar vs core prompts that would make `linear-write.md` an unreadable `{IF_SEMINAR}` soup.

**Concrete defense:** The failure mode is "wiki is LESSON SOURCE" competing with 17 `#R-*` rules and a 540-line prompt. Moving that sentence from §158 to §25 and deleting rules that trivialize under vocab-bounding fixes the cognitive architecture. A new filename does not.

**Staging I'd endorse:** V7.1 structural refactor + m20 pilot → extract `v8-render-module.md` only if B1+/seminar prompts need forked files.

---

## 2. Crowded failure surface — architecture or writing?

**Mostly a writing/hierarchy problem. Partially an architecture problem.**

The architecture problem is real but narrow:

- **One prompt serving A1, B1+, and seminars** with level-gated conditionals (`{IMMERSION_RULE}`, `{INLINE_ALLOWED_TYPES}`, corpus access tiers) creates genuine attention competition. That's a reason for * eventual * file split, not for delaying the renderer pivot.
- **130KB ceiling** — you cannot keep adding hardening rules. Trimming is mandatory either way.

The writing problem is the dominant one:

- `linear-write.md` already has the right contract at lines 158–184 (LESSON SOURCE, implementation map row-by-row). Pt 10 failed **with that text present**. The model obeyed `#R-CLEAN-TABLES`, `#R-PROSE-FLOOR`, dialogue floors — i.e. the **local, enumerable rules** — because those are easier to satisfy than "integrate wiki obligations into prose."
- PR #2260 removed 118 lines without breaking tests. More rules are redundant under vocab-bounding than codex/gemini counted.

**Verdict:** Aggressive V7.1 trimming + charter-first hierarchy ≈ same outcome as V8 for A1/A2. The "need new prompt file" argument is about **maintainability and ceiling**, not about whether the renderer model works.

---

## 3. B1+ scaling — does the vocab gate become a no-op?

**No. It changes character, not load.**

At B2 with ~3000 cumulative lemmas, the allowlist is large — but that's the point. The gate stops being "can you say `прокидатися`?" and becomes **"are you introducing lemmas outside wiki § Словниковий мінімум ∪ plan targets?"**

What shifts at B1+:

| A1 renderer job | B1+ renderer job |
|---|---|
| Methodological UK → EN teacher voice + UK target forms | Methodological UK → UK teacher register (no EN body text) |
| Compose English glosses | Glosses live in Tab 2 only; Tab 1/3/4 are 100% UK |
| Tight allowlist (~200 cumulative) | Wide allowlist (~3000) but **new-lemma introduction still bounded by wiki** |

The gate is **not** a no-op because:

1. **New vocabulary introduction** remains the control surface — wiki/plan declares what's *new this module*; cumulative covers what's *review*.
2. **Invention moves up-stack** — with 3000 lemmas available, the model has more room to compose sentences, but unsupported *content* lemmas still fail. The failure class shifts from "random A1 word" to "author slipped in an undeclared B2 lemma."
3. **Tolerance bands** (`max_unsupported_uk_words` in `learner_state.py`) need level calibration — m20's band of 80 is A1-appropriate; B1+ should be tighter on *new* lemmas, looser on function words.

**Risk codex/gemini underweighted:** at B1+, with a huge allowlist, the writer can produce **grammatically fine but pedagogically misaligned** prose — using lemmas the learner knows but not in the wiki's intended sequence. The vocab gate catches leakage; **wiki_coverage row-by-row** catches sequence drift. Both stay load-bearing.

---

## 4. Seminar scaling — wiki as "source of truth" is wrong framing

**The renderer architecture holds IF the wiki is treated as a verified contract, not as truth.**

For HIST/BIO/LIT/OES/RUTH, the wiki is itself an LLM research artifact (`wiki/pedagogy/...` compiled via Gemini). "Render the wiki faithfully" **launders upstream hallucination** unless verification happens **before** the writer runs.

**Additional verification seminars need (beyond A1):**

| Layer | A1 sufficiency | Seminar requirement |
|---|---|---|
| Wiki completeness | Section stubs, vocab count, L2 rows | + factual claim inventory, source registry per claim |
| Quote verification | Textbook chunk grounding | `verify_quote` on every attributed quotation; `search_literary` for primary sources |
| Attribution | `get_chunk_context` telemetry | `verify_source_attribution` for contested claims (dates, causation, biographical facts) |
| Bias | Decolonization bad-form pairs | Two-source rule already in prompt line 250 — must be **wiki-compile-time enforced**, not writer-time optional |
| External articles | Multimedia search attempt | Wiki must cite real URLs; `ext-article-N` stubs hard-reject |

**Architecture implication:** Seminars need a **wiki verification gate** (compile-time or pre-writer) that is stricter than A1's `wiki_completeness_check`. The writer renderer is the same; the **input contract quality bar** is higher.

Codex flagged this ("claim/evidence graph, two-source checks") but both agents deferred it to "pilot A1 first." I agree on sequencing, but the design should **not** assume seminar wikis are hand-curated SLOBs. They're frozen research snapshots that must pass verification before render.

---

## 5. Activities — same gate, different rule cluster

**The renderer framing is insufficient for activities. Same writer pass, separate composition rules.**

Wiki names formats (`Вправа 1: fill-in reflexive verbs`); the LLM still composes concrete items. That's **bounded composition**, not rendering.

What the vocab allowlist covers:
- All UK tokens in `sentence:`, `prompt:`, `options:`, `items:` fields
- Distractors in MCQ/select (the hardest case)

What it does **not** cover without extra rules:

| Gap | Needed rule/gate |
|---|---|
| Activity *type* and pedagogical goal | Wiki obligation → `wiki_coverage` (already patches `activities.yaml`) |
| Item *count* and difficulty split | Existing `{ACTIVITY_COUNT_TARGET}`, INLINE/WORKBOOK split |
| Distractor quality | Distractors must come from wiki bad-form pairs, L2 error table, or `<!-- bad -->` markers — **not invented Russianisms** |
| Schema shape | `#R-ACTIVITY-FIELDS` cluster (error-correction canonical fields, `items` not `questions`) — stays load-bearing |
| MCQ semantic validity | Gate can't check; reviewer/content-review must |

**Do not create a separate activity phase.** Do create an explicit **"Activity composition (bounded, not rendered)"** section in the prompt with 4–5 rules, parallel to the prose renderer charter. Same allowlist gate runs on `activities.yaml` — `learner_state.py` already scans artifacts.

**Blind spot from round 1/2:** Distractor generation under vocab bound. At A1 with 20 lemmas, MCQ options are nearly isomorphic. Wiki must supply **wrong-form inventory** (L2 error table + decolonization pairs) or activities will be thin/repetitive.

---

## 6. Cursor-specific — don't assume parity with codex-tools/gemini-tools

**Three concrete mismatches from m20 history and wiring:**

**1. Emission contract is fragile.**
`cursor-tools` directives explicitly say "emit fenced blocks, do NOT edit files." Composer-2.5 on m20 attempt #7 wrote artifacts to disk instead → empty stdout → hard fail before `python_qg`. Codex/claude-tools generally respect stdout fences. **Any writer prompt redesign must lead with the emission contract**, and cursor needs a post-writer fallback that reads disk if stdout is empty (or hard-fail fast with a cursor-specific lint).

**2. Tool-call budget and context pressure.**
The prompt is ~540 lines before wiki manifest, implementation map, knowledge packet, and learner state. Cursor with scoped MCP + mandatory `get_chunk_context` per plan reference + resources search + VESUM batch calls hits context and turn limits differently than codex-tools. Empirically: **codex-tools won m20 rounds**; cursor-tools m20 was never completed successfully as writer. Default reviewer model for cursor-tools is `grok-4.20-reasoning`, not the writer — the writer path is less battle-tested.

**3. Instruction-following under rule overload.**
Cursor (Composer-class models) appear **more susceptible to structural compliance** (tables, dialogue boxes, callouts) over integrative teaching — same "visible compliance tokens" pattern codex brain-picked. A charter-first V7.1 helps all writers; it helps cursor **disproportionately** because cursor seems to grab the nearest enumerable rule.

**What you might be wrong to assume:**
- cursor behaves like codex-tools on long tool-heavy prompts → **no**
- cursor-tools is production-ready for m20 anchor → **not yet proven**
- MCP integration story is identical → cursor gets materialized `.cursor/mcp.json`; agy-tools gets native `mcp_sources_*`; codex gets its own wiring. Test per adapter.

---

## 7. Blind spots — what round 1/2 missed

**1. `word_count` vs structural density (Pt 10 root cause).**
Renderer pivot doesn't fix this. If the writer renders wiki content into tables/dialogue/callouts (per `#R-CLEAN-TABLES`), prose word count drops and the gate fails anyway. V7.1/V8 must either (a) adjust word_count to count gate-visible UK surfaces, or (b) add a prose-floor rule that survives renderer framing. Neither codex nor gemini resolved this in the pivot discussion.

**2. Track-specific prompt forking timeline.**
One `linear-write.md` with `{LEVEL}` conditionals works for A1→B1. Seminars (100% UK, contested facts, literary quotes, no English gloss composition) will break a single prompt. Plan the fork now; don't wait for V8 plumbing to acknowledge it.

**3. Wiki compile verification ≠ writer verification.**
Both agents said "wiki is LLM-generated, don't trust it" but put all verification burden on the writer pass. For seminars, **verification must happen at wiki compile** or you're paying writer tokens to re-verify the same claims every build.

**4. Activity distractor supply chain.**
Under strict vocab bound, MCQ/error-correction activities need wrong forms pre-seeded in wiki (L2 table, bad-form pairs). If wiki doesn't carry enough distractors, activity generation fails silently into thin/repetitive items.

**5. cursor-tools production readiness.**
Integrated 2026-05-24; one failed m20 attempt; deferred behind brain-pick. Any architecture decision should not assume cursor is interchangeable with codex-tools until m20 ships under cursor-tools with stdout emission verified.

**6. B1+ simplifies the renderer in one dimension.**
Removing English body composition reduces a major creative surface. B1+ renderer is *easier* than A1 renderer for prose; *harder* for register consistency (methodological → teacher UK without EN scaffold). Neither agent discussed this asymmetry.

---

## Summary position

| Question | Answer |
|---|---|
| V7.1 vs V8 | **V7.1 structural refactor** (charter-first, aggressive trim, new vocab gate, wiki manifest fix). Extract V8 file later if tracks diverge. |
| Crowded surface | **80% writing/hierarchy, 20% eventual file split** for seminar vs core |
| B1+ gate | **Stays load-bearing** on new-lemma introduction; shifts from tight to wide allowlist |
| Seminars | **Renderer holds; wiki verification gate must be stricter upstream** |
| Activities | **Same allowlist gate + separate composition rule cluster** in one writer pass |
| Cursor | **Not parity with codex-tools**; emission contract + rule overload + unproven m20 |

The material end-state codex and gemini want is right. The two-week V8 plumbing timeline is not justified for the A1/A2 pilot — **unless** you want the filename separation for ceiling/tests/track forks from day one. I'd ship the contract change in V7.1, prove it on m20, then extract the file when seminar prompts force it.
