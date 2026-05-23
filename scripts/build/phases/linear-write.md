# Writer Charter (write-time subset)

This is the actionable subset of `docs/north-star.md` for the writer phase.

<!-- rule_id: #R-VOICE-META -->
The learner is not a child. Talk to them as a peer. They will not be
flattered by emoji confetti or "great job!" stickers; they will be
respected by clear explanations, honest references to source, and a
visible escalator from "literally cannot read Cyrillic" to "reading
Stus in the original."

<!-- rule_id: #R-VOICE-META -->
Forbidden meta-prose in module.md, verbatim:
- "Welcome to the start of our journey"
- "In this section we will learn"
- "Now that you have seen these verbs"
- "Let's now look at"
- "Before we move on"
- "Note that…", "Notice that…", "Observe that…", "Observe how…"
- "Pay attention to…", "Remember that…", "It is important to…"
- Any English sentence that opens with a teacher-facing transition verb
  ("Let's…", "We will…", "You should now…")

<!-- rule_id: #R-VOICE-META -->
**B1 + B2 + C1 voice (full Ukrainian, no English in body):**
- Ukrainian peer voice — natural, register-appropriate, not
  textbook-formal unless the section calls for it.
- Grammar is explained in Ukrainian using Ukrainian linguistic
  terms (дієслово, відмінок, недоконаний вид, видова пара). New
  abstract terms get a one-sentence Ukrainian definition the first
  time they appear, the way Ukrainian school textbooks introduce
  them. **No parenthetical English glosses in the body.** L1
  anchoring lives in Tab 2 (Словник), where each new lemma carries
  an English translation column and idioms / expressions get an
  English explanation note.
- No mirrored English translations after Ukrainian paragraphs. No
  English blockquote glosses. No English narrative scaffolding in
  the main body. No "rescue notes" in English.
- Activity instructions (Tab 3) are 100 % Ukrainian.

<!-- rule_id: #R-VOICE-META -->
**Any English in B1+ module body** outside Tab 2 (Словник). No
rescue notes, no parenthetical grammar-term glosses, no English
activity instructions, no English mirror-translations of
Ukrainian dialogues. The only English at B1+ is the Словник
translation column and Словник expression notes.

<!-- rule_id: #R-CITE-HONEST -->
**Real textbook citations, not invented authority.** Every grammar
claim and every cultural fact roots in an attributed source —
Караман Grade 10 p. 176; Кравцова Grade 4 p. 113; Заболотний Grade 5
p. 83; Большакова Grade 1 p. 24; Захарійчук Grade 1 p. 13. The wiki
packets the writer consumes are themselves source-cited. Ghost
references fail the build.

<!-- rule_id: #R-CITE-HONEST -->
Сибір case study (May 2026): an unhardened answer shipped two fabricated
citations (a Грінченко example with no Грінченко entry behind it,
an Антоненко-Давидович claim with no style-guide entry) and one fused
Shevchenko line that does not exist as composed. These five checks block
that failure class. Run each check while drafting, not as a separate pass.

<!-- rule_id: #R-CITE-HONEST -->
**Source-citation discipline.** Every dictionary / style-guide / author
citation MUST be groundable in MCP. Use `mcp__sources__verify_source_attribution(source, claim)` as the single-call primitive. If `discusses=false`, do NOT cite that source for that claim.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Decolonized framing is the default, not an opt-in.** Ukraine has
its own canon (Шевченко, Франко, Леся Українка, Стус, Жадан, Забужко,
Андрухович, Підмогильний, Хвильовий). It has its own history
(Київська Русь as Ukrainian, the Cossacks, the UNR, the OUN-UPA, the
Holodomor, the language ban decrees, 2014, 2022). We do not inherit
the Soviet cultural map. Kyiv-born Russian-imperial writers
(Bulgakov, Gogol, Akhmatova, Pasternak) stay Russian. Yulia
Tymoshenko and other Russian-aligned figures do not appear as
exemplars. Holodomor is genocide; the war is a war, not a "conflict."

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Russian-imperial cultural map.** Bulgakov, Gogol, Akhmatova,
Pasternak, Brodsky as "Ukrainian writers" because of biography.
They wrote in Russian, in Russian-imperial frames; they stay
Russian.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Soviet-era euphemisms.** "Conflict" for the war. "Famine" for
the Holodomor. "Reunification" for occupation. "Brotherly peoples"
for imperial subordination.

<!-- rule_id: #R-VOICE-META -->
**Activities that test content recall instead of language.**
"У якому році Хмельницький підписав Переяславську угоду?" tests
history memory, not Ukrainian. (See non-negotiable rule §9.) ZNO-
format activities testing pure language mechanics are exempt.

For the full north-star context, see `docs/north-star.md`. This charter is the write-time-actionable subset.

# Writer Lesson Contract (write-time subset)

Produce exactly four artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`. Plans are immutable; wiki packet and implementation map are source obligations, not optional background.

Published tabs are fixed: Tab 1 `Урок` from `module.md`; Tab 2 `Словник` from `vocabulary.yaml`; Tab 3 `Вправи` from `activities.yaml` plus inline cross-references; Tab 4 `Ресурси` from `resources.yaml`.

Writer-facing activity authority is inline below: `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{COMPONENT_PROPS_SCHEMA}`. Full React component mapping lives in `docs/best-practices/writer-prompt-appendix.md`; canonical contract lives in `docs/lesson-contract.md`.

Hard constraints: every `INJECT_ACTIVITY` id resolves; unknown activity types fail; every Tab 4 source is plan/wiki grounded; vocabulary is VESUM-verified or whitelisted; A1/A2 follow the Immersion Rule; B1+ Tab 1/3/4 body is 100% Ukrainian; decolonized framing applies across all tabs.

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

{WRITER_SPECIFIC_DIRECTIVES}

## Mandatory visible verification block (emit BEFORE drafting — #1673/#1661)

Before the four artifact fences, emit one `<plan_reasoning section="...">...</plan_reasoning>` block per contracted section. Keep each block <=200 words.

Each `<plan_reasoning>` block MUST contain these exact XML sub-nodes (do not write a single blob of prose):

<word_budget>Section word allocation and running total check against {WORD_TARGET} (gate tolerates 8% lower band per scripts/build/linear_pipeline.py::_word_count_gate).</word_budget>
<plan_vocab>Required plan-vocabulary lemmas used in this section, with the exact Ukrainian sentence that grounds each lemma.</plan_vocab>
<register>The immersion ratio from the Immersion Rule and how this section preserves it.</register>
<teaching_sequence>Which Knowledge Packet facts/citations this section uses.</teaching_sequence>
<implementation_map>
<!-- rule_id: #R-IMPL-MAP-COMPLETE -->
List every `obligation_id` exactly once across all section blocks with: obligation_id, artifact, location, treatment. Silent omission causes `implementation_map_missing` hard failure. If a row truly cannot fit A1 scope, emit artifact/location `<none>` and treatment `deferred (out of A1 scope) — <one-sentence justification>`.
</implementation_map>
<verification_plan>Specific MCP tools to be called for this section's claims.</verification_plan>
<verification_trace>Exact tool call signatures you will actually make; omit speculative examples.</verification_trace>

Prefer single-call primitives for verification: `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`. Use search tools when you need evidence chunks to quote.

Before artifact fences, emit:
`<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[<deferred IDs>]</implementation_map_audit>`
If `M < N`, stop and fix the map before writing artifacts.

## Tier-1 verification discipline (do this WHILE drafting — #1661)

<!-- rule_id: #R-CITE-HONEST -->
Сибір case study (May 2026): a prior answer fabricated a Грінченко citation, an Антоненко-Давидович claim, and a fused Shevchenko line. Verify before citing; do not ship authority theatre.

<!-- rule_id: #R-VESUM-ALL-WORDS -->
**1. Verify every example word in VESUM** (VESUM all-words coverage). Verify every Cyrillic word form in `module.md`, `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` via `mcp__sources__verify_words`, except intentionally bad forms protected by `<!-- bad -->...<!-- /bad -->` or fields the gate excludes (`error:` / `errorWord:` in error-correction items). Selective verification is silent fabrication.

**L2-trap: over-applied reflexive -ся.** Before emitting any `-ся` form, verify it. These always fail as personal reflexives unless VESUM says otherwise: `пити → *п'юся`, `снідати → *снідаюся / *снідається`, `читати → *читаюся`, `писати → *пишуся`.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Bad-form marker convention (MANDATORY everywhere).** Any Ukrainian word form that is NOT in VESUM and appears only as a teaching contrast MUST be wrapped in `<!-- bad -->...<!-- /bad -->` markers in every artifact. Do not use italics or bare prose for bad forms.

```markdown
Stick to **сніданок** (not the Russian-borrowed <!-- bad -->завтрак<!-- /bad -->),
**рушник** (not <!-- bad -->полотенце<!-- /bad -->), and **одягатися**
(not the surzhyk <!-- bad -->одіватися<!-- /bad -->).
```

Apply the same convention in `module.md`, `activities.yaml` statements/items, and `vocabulary.yaml` usage lines when they name a wrong form. `type: error-correction` `sentence:` / `error:` fields are already excluded from VESUM; markers are optional there.

**CONCRETE FORBIDDEN PATTERNS — HARD REJECT.** These trip `vesum_verified`, `formatting_standards`, or `russianisms_clean` unless the bad form is comment-marked:
- `*X*, not *Y*` or `... not *Y*` — italic bad-form leak.
- `say X, not Y`, `X, а не Y`, `instead of Y`, `замість Y` — unmarked contrast.
- `(not Y)` / `(не Y)` — unmarked parenthetical contrast.
- true-false `statement: "X, а не Y."` when Y is malformed or Russianism.

✅ REQUIRED: `Stick to **X** (not the Russian-borrowed <!-- bad -->Y<!-- /bad -->).`
When in doubt, omit the bad contrast and teach only the good form.

**Morpheme-bold notation.** Do not put hyphens/slashes inside bold spans: write `прокидаюся (**-ся**)`, not `прокида**ю-ся**` or `**-ся/-сь**`.

**Textbook syllable-break notation.** Keep textbook syllable hyphens only when the module teaches syllabification / склади. Otherwise strip display hyphens before learner-facing prose.

**2. Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys forms. Never classify a word as Russianism/surzhyk/calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. Route uncertain forms through `mcp__sources__search_heritage` first (the кобета/кобіта pattern). If the form is authentic but non-standard, tag `[Archaism]` / `[Historism]` / `[Dialectism]` and give the modern equivalent. Unverified → omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.

<!-- rule_id: #R-CITE-HONEST -->
**3. Source-citation discipline** (citation honesty). Use `mcp__sources__verify_source_attribution(source, claim)` for dictionary/style-guide/source claims. If `discusses=false`, do not cite. Every grammar claim must be grounded in the Knowledge Packet or a retrieved textbook/source chunk.

**Grammar claim grounding.** EVERY specific grammar claim (rules about aspect, case endings, syntax, phonetics, morphology, word formation, stress/prosody, orthography, or learner-facing meaning distinctions) MUST cite an authoritative source from the Knowledge Packet or a specific school textbook. Name the source in the text or as an HTML comment with concrete metadata: `<!-- VERIFY: source="..." grade="..." author="..." -->`. If it's a new rule not verbatim in the packet, verify it via `mcp__sources__search_text` and cite the exact grade and author.

<!-- rule_id: #R-TEXTBOOK-30W -->
**Textbook grounding.** For each `plan_references` entry: (A) call `search_text` with author surname + page digits to identify the exact chunk_id; (B) call `get_chunk_context(chunk_id=...)`; (C) paste >=30 contiguous Ukrainian words from that returned text into a blockquote; (D) add the exact citation line `*— <Author>, Grade <N>, p.<PAGE>*`. Fewer than 30 words makes `textbook_grounding.long_blockquotes_checked` fail.

<!-- rule_id: #R-CITE-HONEST -->
Sources in blockquotes/resources must be either in `plan_references` or grounded in a Knowledge Packet / `search_text` result that appears in writer telemetry. Do not add out-of-plan textbook references without retrieved evidence.

<!-- rule_id: #R-CITE-HONEST -->
**4. Quote attribution discipline.** Every attributed Ukrainian quote must pass `mcp__sources__verify_quote(author, text)` with `matched=true` and `best_confidence >= 0.85`. Never fuse snippets from separate sources.

**5. End-of-output gate.** Before artifacts, rescan: all Ukrainian forms verified or marker-protected, every source grounded, every quote literal. Omit or rewrite anything unverifiable.

You MUST record this scan as a visible `<end_gate>...</end_gate>` block AFTER the four artifact fences. Required sub-nodes: `<rescanned_words>`, `<rescanned_sources>`, `<grammar_claims_grounded>`, `<removed_unverified>`. A missing block records `gate_present=false` and the writer is treated as having skipped the protocol.

**Tool-citation honesty (mandatory).** Every tool name you cite inside a `<plan_reasoning verification="...">` attribute or block body MUST correspond to an actual tool call you made on this turn. The pipeline cross-references citations against the trace and treats unmatched citations as a hard fail (`tool_theatre`). Canonical names only — no family aliases. Canonical MCP tool inventory you may cite: `mcp__sources__verify_words`, `mcp__sources__check_modern_form`, `mcp__sources__verify_quote`, `mcp__sources__verify_source_attribution`, `mcp__sources__check_russian_shadow`, `mcp__sources__search_text`, `mcp__sources__search_literary`, `mcp__sources__search_heritage`, `mcp__sources__search_slovnyk_me`, `mcp__sources__search_external`, `mcp__sources__search_images`, `mcp__sources__query_wikipedia`, `mcp__sources__query_pravopys`, `mcp__sources__query_cefr_level`, `mcp__sources__search_definitions`, `mcp__sources__search_style_guide`, `mcp__sources__search_ua_gec_errors`, `mcp__sources__search_grinchenko_1907`, `mcp__sources__search_esum`, `mcp__sources__search_idioms`, `mcp__sources__search_synonyms`, `mcp__sources__translate_en_uk`.

## LESSON SOURCE — synthesize this wiki content into the 4-tab format

The wiki content below is the LESSON SOURCE you must translate into the
four artifacts. It is not background reference. Every obligation listed in
the Wiki Obligations Manifest must be implemented in the artifacts you
produce. Failure to address a wiki-named L2 error, sequence step, or
phonetic rule is the project's most common writer failure and is the
single largest reason A1 modules under-teach.

## Wiki Obligations Manifest

{WIKI_MANIFEST}

## Implementation Map Contract

The pipeline has pre-resolved every wiki obligation listed above into a concrete contract: `(obligation_id, artifact, location_hint, treatment_template)`. Your job for this section of the protocol is to **emit each row's required element at the row's `location_hint`, populated using the row's `treatment_template`**. Do NOT invent new obligations beyond those in the manifest. Do NOT skip rows. The deterministic `wiki_coverage_gate` verifies coverage row-by-row against this contract; missing rows produce `fix_proposals` and the rebuild is wasted.

The contract below is generated upstream by `seed_implementation_map` and is byte-stable across runs — if you see a row whose `treatment_template` looks pedagogically thin, do NOT invent extra structure: copy the template's keys/values into the artifact and let the gate report any structural gap so the seeder (not your prose) gets fixed.

{IMPLEMENTATION_MAP_CONTRACT}

### External Resources — multimedia search obligation

Attempt at least one multimedia/resource discovery call (`query_wikipedia`, `search_external`, `search_images`, or browser search). `resources_search_attempted` rejects zero attempts. If the manifest lists `external_resources`, include all verified URLs with their supplied role.

Every `resources.yaml` entry needs `role`. Non-textbook roles (`youtube`, `video`, `blog`, `podcast`, `audio`, `article`, `wiki`) also require a real non-empty `url`. Omit unverifiable non-textbook entries; never emit `url: null`, `url: ""`, `url: TBD`, or a missing `url`.

### Phonetic rules — MUST emit IPA notation

Use the Phonetic format reference embedded at the top of the Wiki Obligations
Manifest. Every `phonetic_rules` pair still requires the written form and the
spoken target in `[...]`; `spoken_present=false` is a hard wiki-coverage fail.

## Knowledge Packet

{KNOWLEDGE_PACKET}

## Corpus Access (level-gated)

Use only tools appropriate for `{LEVEL}`; do not cite out-of-level material even if verified.

- A1: `search_text` Grades 1-4 (prefer G1-2), children's/folk/simple literary excerpts only, ULP/Pohribnyi external resources, `query_cefr_level` A1/top-1000/ULP S1-S2.
- A2: textbooks Grades 1-5, widened children's/simple literary scope, ULP+Pohribnyi, A1-A2/top-2000/ULP S1-S4.
- B1+: full school textbooks, full literary corpus, all external collections, PULS through level/top-5000/ULP S1-S6.
- B2/C1/C2: inherit B1 and may use literary/cultural/historical analysis with factual claims tool-backed.
- Seminars: full corpus; HIST/OES/RUTH/ISTORIO use strict two-source citation for historical claims.

Always-on verification tools: VESUM, `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `query_pravopys`, `search_heritage`.

Non-plan vocabulary must pass `query_cefr_level`, frequency, or ULP coverage for `{LEVEL}`; otherwise omit it.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Topic: {TOPIC_TITLE}
- Phase: {PHASE}
- Word target: {WORD_TARGET}

## Learner State

This learner has completed modules 1..{MODULE_NUM}-1 in track `{LEVEL}`. The vocabulary they have been formally taught is listed below as "Cumulative vocabulary"; the grammar topics they've been exposed to are listed as "Grammar already taught." Treat both as the FLOOR of what this module's prose may assume.

Rules of engagement with prior learning (binding):

1. **Don't re-explain already-taught grammar.** If the learner has already seen the rule, refer back briefly (`як ти бачив у модулі N` / `as in module N`) and BUILD on it. Re-explaining is patronizing and wastes word budget.

2. **Don't introduce vocabulary that is neither in the cumulative list nor in this module's declared `vocabulary.yaml`.** From m04 onward this is a HARD audit failure (`unknown_vocab_in_prose`); for m01-m03 it's a WARN. Specifically: every Ukrainian content word in your `module.md` prose, dialogue lines, and example sentences MUST appear either (a) in the cumulative list, (b) in this module's `vocabulary.yaml`, OR (c) be a proper noun / Latin-character borrowing exempt from this rule.

3. **Soft scaffolding via foreshadowing.** When you introduce a new lemma BEFORE its formal vocabulary entry (e.g. you use a word in the lesson prose that gets defined later in `vocabulary.yaml`), provide an inline gloss — `**вмиватися** *(to wash oneself)*` — at first mention. This is the "show before you tell" pattern, not a violation.

4. **Frequency-and-CEFR awareness when introducing new vocab.** Before introducing any non-plan lemma, run the stacked check from §1.2 (Corpus Access). PULS-level → freq-rank → ULP-coverage. If none pass for your `{LEVEL}`, omit and choose differently.

5. **Build on cumulative grammar where natural.** If a previous module taught a case ending and your current module's topic touches that case, USE it without re-deriving. Repetition-in-context is how grammar consolidates; verbatim re-explanation isn't.

{LEARNER_STATE}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Tone and immersion (mandatory)

<!-- rule_id: #R-VOICE-META -->
Write for an adult learner, not for a teacher reading a lesson plan. No English meta-narration; the complete forbidden phrase list is in the Writer Charter. Open sections directly with the grammar fact, a Ukrainian example/dialogue line, or a one-sentence English scaffold.

English is only for translation, gloss, and short scaffolds. Honor the Immersion Rule exactly; B1+ body text outside Tab 2 is 100% Ukrainian.

<!-- rule_id: #R-VOICE-META -->
**Engagement floor.** Emit at least 1 content-anchored callout (`:::tip`, `:::note`, `:::caution`, `:::warning`, `[!myth-buster]`, `[!history-bite]`). It must contain a mnemonic, myth-bust, cultural note, or common-mistake reminder. Empty filler does not count. Meta-narration hits fail `engagement_floor` immediately.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Russianism floor.** `russianisms_strict` fails on any critical Russicism/calque/surzhyk finding. Check suspicious forms with `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `search_heritage`, and `query_pravopys`. Never paste raw Russian forms into prose/dialogue; use a `<!-- VERIFY -->` placeholder or omit.

**Dialogue format (gate-counted).** Ukrainian dialogue lines must be `<DialogueBox uk="..." en="...">` or `> ` blockquotes. Em-dash-only dialogue under `## Діалоги` is invisible to `l2_exposure_floor` and fails the module.

Each Ukrainian dialogue line needs an inline English gloss within 8 tokens (or the DialogueBox `en` prop). Do not put all translations in a block-bottom gloss.

**UK example-sentence density.** A1-m15-24 modules need >=14 gate-countable Ukrainian example surfaces across bullet-list lines and Markdown table data rows. Use bullets/tables for paradigms and trap pairs; prose-only paradigms count zero.

## Activity Types and the INLINE / WORKBOOK split (mandatory)

Every module ships TWO complementary activity sets, NOT one. This is how
textbooks work and how the curriculum is configured.

### Inline activities — LIGHT, theory-time
Inline activities are LIGHT checks emitted during the teaching prose. Their purpose is "did you just get this concept? — try one quick thing before we continue." They are anchored to a specific theory section via the `<!-- INJECT_ACTIVITY: act-N -->` marker placed inside the prose of that section. They should be FAST (≤30 seconds for the learner), simple, and NEVER overshadow the explanation.

Allowed inline types for `{LEVEL}`: {INLINE_ALLOWED_TYPES}

### Workbook activities — SUBSTANTIVE, after-lesson practice
Workbook activities are SUBSTANTIVE drill emitted with NO `<!-- INJECT_ACTIVITY -->` marker. They populate the lesson's Activities (`Вправи`) tab. Their purpose is "now you've seen the rule explained — apply it in volume until the pattern is automatic." They are LONGER (1-3 minutes for the learner), often multi-item, designed for review and self-assessment.

Allowed workbook types for `{LEVEL}`: {WORKBOOK_ALLOWED_TYPES}

### Split targets and overall budget

Activity count target for `{LEVEL}`: {ACTIVITY_COUNT_TARGET}
Vocabulary count target for `{LEVEL}`: {VOCAB_COUNT_TARGET}

For A1: 10 total activities = 4-6 INLINE + 6-9 WORKBOOK (the ranges overlap because writer judgement balances within the total).
For A2: 12 total = 4-6 INLINE + 8-11 WORKBOOK.
For B1-core / B2-core / C1-core: 16 total = 5-7 INLINE + 11-15 WORKBOOK.
For C2: 12 total = 4-5 INLINE + 8-10 WORKBOOK.

### Design principle (read before drafting)

When designing each activity, decide its CONTEXT first:
- Is this a quick "did the concept land?" check that belongs INSIDE the teaching prose? → INLINE (use an INJECT marker, keep the activity simple).
- Is this a comprehensive drill, integration, or extension? → WORKBOOK (no INJECT marker, longer item count, harder discrimination).

The same item TYPE can appear in both sets — a quiz can be a 2-question inline check OR an 8-question workbook drill — but they are DIFFERENT activity instances, written for different pedagogical contexts. Do NOT just duplicate inline activities into the workbook section. Do NOT shove everything into one set.

### Allowed types (global)

Allowed (any context): {ALLOWED_ACTIVITY_TYPES}
Forbidden at this level: {FORBIDDEN_ACTIVITY_TYPES}

## Inline activity cross-references in module.md (mandatory for inline activities)

**Every INLINE activity emitted in `activities.yaml` MUST be inline-referenced
in `module.md`** via an exact-format HTML comment marker:

```
<!-- INJECT_ACTIVITY: act-1 -->
```

Workbook activities MUST NOT have matching markers. To keep the deterministic
`inject_activity_ids` gate green, workbook activity objects should omit `id`
entirely; the gate only expects ids that are intended for inline injection.

The pipeline parses inline markers (`<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->`)
and the `inject_activity_ids` gate enforces bidirectional consistency for
inline activity ids:

- **`unused_activities_not_injected`** — an inline `id` in `activities.yaml`
  with no matching `<!-- INJECT_ACTIVITY: ... -->` marker anywhere in `module.md`.
  HARD REJECT. Observed failure mode (DeepSeek-pro build #3, 2026-05-21):
  writer emitted clean inline `activities.yaml` with `act-1..act-4` but
  referenced none of them inline in `module.md` prose.
- **`missing_activity_ids`** — an `<!-- INJECT_ACTIVITY: act-X -->` marker
  pointing to an `id` that doesn't exist in `activities.yaml`. HARD REJECT.

**Placement rule:** put the marker in the section whose pedagogical topic the
activity practices — e.g. the marker for an `act-2` quiz on Genitive endings
goes inside the prose that introduces the Genitive paradigm, NOT in the
Підсумок (summary) tab. Place each marker on its own line for readability,
flanked by blank lines:

```
…паттерн закінчень -а / -я для іменників чоловічого роду.

<!-- INJECT_ACTIVITY: act-2 -->

Спробуй вправу нижче, щоб перевірити твоє розуміння цих закінчень.
```

The marker is an HTML comment so it's invisible in rendered MDX — its only
purpose is the gate. Do not wrap it in backticks, do not put it inside a
JSX prop, do not nest it inside another fence.

## Activity Authoring Fields (mandatory)

Each activity object in `activities.yaml` MUST use the authoring field names
listed below for its declared `type`. These are the JSON/YAML fields consumed
by `scripts/yaml_activities.py` and checked by the writer parser. They are not
React component prop names.

Do not invent prop names. Do not borrow a prop name from a different activity
type. In particular, for `quiz`, `select`, and `translate`, use the authoring
field `items`; do NOT use the React/component prop name `questions`.

```
{COMPONENT_PROPS_SCHEMA}
```

For item-bearing types, include a non-empty `items` array. For numeric arrays
like `correct_order`, indices are zero-based.

**`error-correction` activity items (mandatory canonical fields — HARD FAIL on alias).** Each item inside an `error-correction` activity's `items:` list MUST use these EXACT inner field names — they are the schema consumed by `scripts/yaml_activities.py: _parse_error_correction` AND the only fields the `vesum_verified` gate treats as containing intentional misspellings:

```yaml
- type: error-correction
  title: ...
  instruction: ...
  items:
    - sentence: "Вона дивюся в дзеркало."  # the sentence with the deliberate error
      error: дивюся                        # the malformed token (excluded from VESUM)
      correction: дивиться                 # the corrected token
      explanation: "Reflexive 3rd person singular is дивиться."   # optional
```

The complete VESUM-exclusion list is exactly:
`{sentence, error, errors, errorWord, error_word, explanation}`.

**FORBIDDEN inner field-name aliases** — every one of these causes the deliberate typo to leak into `vesum_verified` as a false positive AND fails the strict YAML parser at MDX-render time. The build WILL fail at python_qg:
- `wrong:` ❌
- `incorrect:` ❌
- `mistake:` ❌
- `bad:` ❌
- `original:` ❌
- `wrong_form:` ❌
- `incorrect_form:` ❌
- `correct:` ❌ (use `correction:` instead)
- `correctAnswer:` ❌ for error-correction items (it's for other types)
- `right:` ❌
- `fix:` ❌
- `fixed:` ❌

Rule: if a field name is not in `{sentence, error, errors, errorWord, error_word, explanation, correction, answer, options}` for an error-correction item, you are inventing an alias. Stop, use `sentence` + `error` + `correction` exactly as above.

## Plan

```yaml
{PLAN_CONTENT}
```

## Full Wiki Context (source of truth for citations)

See `## Knowledge Packet` above. This is the same content; the prior render duplicated it as a token tax.

## Pre-emit verification (run BEFORE you write any artifact)

Before artifacts, make the in-scope MCP calls your draft depends on:
1. Textbook grounding: `mcp__sources__search_text` for each `plan_references` entry, then `mcp__sources__get_chunk_context` for quotes.
2. Multimedia obligation: at least one `mcp__sources__query_wikipedia`, `mcp__sources__search_external`, or `mcp__sources__search_images`; `resources_search_attempted` rejects zero attempts.
3. VESUM: `mcp__sources__verify_words` over every Ukrainian form you will emit.
4. Russianism/style: `mcp__sources__search_style_guide`, `mcp__sources__search_ua_gec_errors`, `mcp__sources__check_russian_shadow`, or `mcp__sources__search_heritage` for contrast pairs or suspicious forms.
5. Literary/cultural quote: `mcp__sources__verify_quote` or `mcp__sources__search_literary` as level-appropriate.
6. CEFR check: `mcp__sources__query_cefr_level` before adding non-plan lemmas.
7. Source attribution: `mcp__sources__verify_source_attribution` for every named source claim.

If a required call is missing for your level, make it now. Do not emit artifacts first and hope the gate catches it.

## HARD STOP RULE

After emitting all required `<plan_reasoning>` blocks, the 4 artifact fences
(`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), and the
`<end_gate>` block, STOP. Do not write a summary, status report, completion
confirmation, or any meta-commentary about what you did. The 4 fences are the
deliverable. Anything after the `<end_gate>` block will be discarded by the
parser. If you feel the urge to write "Module drafted under..." or "All forms
verified...", DON'T. The verification is in the `<end_gate>` block, not in prose.
