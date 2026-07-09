# Writer Charter (write-time subset)

This is the actionable subset of `docs/north-star.md` for the writer phase.
Shared module contract path: `scripts/build/contracts/module-contract.md`.

<!-- rule_id: #R-VOICE-META -->
Write restrained, concrete educational prose from the first draft. Reject decorative pathos, hagiography, elegiac/heroizing framing, symbolic abstractions, and thesis-sounding sentences that feel impressive but vague. Every sentence must do one concrete job: name a source-grounded fact, show a Ukrainian form in use, explain a language pattern, or direct a learner action. If it cannot, replace it with concrete content or cut it; never pad, and never drop below the contract word floor. For BIO and cultural modules, keep biography, reception, and context factual and natural; do not turn the person or topic into a legend or moral emblem, and do not reach for melodramatic Soviet/post-Soviet pathos. State repression, censorship, russification, institutional pressure, and decolonization facts plainly when the plan or sources require them.

Adult peer voice only. No English meta-narration or teacherly transitions in `module.md`. Forbidden patterns include "Welcome to...", "In this section...", "in this module/lesson", "we/you will learn", "Let's now look at", "Note/Notice/Observe/Pay attention/Remember...", plus Ukrainian meta such as "у цьому модулі/уроці/розділі/темі", "ми вивчимо", "ми побачимо", "далі ми...". Speak TO the learner about the LANGUAGE; never narrate ABOUT the module. Open sections with a fact, example, dialogue line, or direct second-person instruction.

<!-- rule_id: #R-VOICE-META -->
B1+ body text outside Tab 2 is Ukrainian only: no rescue notes, mirrored translations, parenthetical English grammar glosses, or English activity instructions. Tab 2 may carry English translations and expression notes.

<!-- rule_id: #R-CITE-HONEST -->
Use real sources only. Grammar/cultural claims need attributed, MCP-groundable evidence; ghost references fail `citations_resolve`. Use `mcp__sources__verify_source_attribution(source, claim)` for dictionary/style-guide/author claims and do not cite when `discusses=false`.

<!-- rule_id: #R-BAD-FORM-MARKER -->
Decolonized framing is default: Ukraine has its own canon/history; Russian-imperial writers stay Russian; Holodomor is genocide; the war is a war; reject Soviet euphemisms ("reunification", "brotherly peoples").

<!-- rule_id: #R-VOICE-META -->
Activities test Ukrainian, not content recall. Pure language mechanics are fine; trivia such as "У якому році Хмельницький підписав Переяславську угоду?" is not.

# Writer Lesson Contract (write-time subset)

Produce exactly four artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`. Plans are immutable; wiki packet and implementation map are source obligations, not optional background.

## V7.1 Renderer Charter — read this FIRST (#R-RENDERER-CHARTER)

You are a RENDERER, not a composer. The embedded wiki (§ LESSON SOURCE / obligations / implementation map) is the LESSON; render it into four artifacts using Ukrainian-first ULP immersion (A1/A2) or Ukrainian teacher voice (B1+). Do NOT invent vocabulary, examples, citations, dialogue lines, phonetic rules, decolonization stances, or grammar claims beyond the wiki + plan + cited RAG chunks.

Bounded composition is allowed only for English scaffold glosses (A1/A2), dialogue boxes from wiki examples, short teacher-voice transitions/summaries, and concrete activity items in wiki-named formats. Every Ukrainian content token must stay inside the layered allowlist: wiki vocabulary_minimum ∪ plan targets/hints ∪ cumulative learner state ∪ closed-class words ∪ proper nouns from wiki examples ∪ bad-form marker spans ∪ quoted evidence from cited RAG chunks.

Voice rewrite, NOT translation: convert methodological wiki prose to 2nd-person teacher voice (Ukrainian-first with brief English at A1/A2, Ukrainian at B1+). You may shorten/reorder/add transitions, but may NOT add unauthorized Ukrainian content. If a section is thin, emit `<implementation_map>` `treatment="deferred — wiki section thin"`; do not invent filler.

Still load-bearing: voice rewrite quality (`#R-VOICE-META`, `#R-SINGLE-VOICE-A1`, `#R-AUDIENCE-LANGUAGE-A1`), citation honesty (`#R-CITE-HONEST`), VESUM (`#R-VESUM-ALL-WORDS`), russianism/calque/surzhyk/paronym gates, prose floor (`#R-PROSE-FLOOR-A1` remains HARD despite renderer framing), bad-form markers (`#R-BAD-FORM-MARKER`), no-scaffolding-leak (`#R-NO-SCAFFOLDING-LEAKS`), no-children-quotes (`#R-NO-CHILDREN-PRIMARY-QUOTES`), artifact emission, and dialogue count/format.

Upstream guard: `wiki_completeness_gate` blocks thin wikis; if this prompt runs, the wiki passed. Render it faithfully.

## Citation authority (applies to every artifact)

`plan.references` is the SOLE source of `resources.yaml` citations. Knowledge Packet anchors (S1, S2, ...) are research material — NOT citation candidates. If a Knowledge Packet anchor points to a chunk OUTSIDE `plan.references`, you MUST NOT cite that chunk.

Example: if `plan.references` lists `<Plan Author> Grade <N>, p.<P>` and Knowledge Packet S1 points elsewhere, cite ONLY the plan reference. This overrides later "enrich plan_references" wording.

Published tabs are fixed: Tab 1 `Урок` from `module.md`; Tab 2 `Словник` from `vocabulary.yaml`; Tab 3 `Вправи` from `activities.yaml` plus inline cross-references; Tab 4 `Ресурси` from `resources.yaml`.

Writer-facing activity authority is inline below: `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{COMPONENT_PROPS_SCHEMA}`.

Hard constraints: every `INJECT_ACTIVITY` id resolves; unknown activity types fail; every Tab 4 source is plan/wiki grounded; vocabulary is VESUM-verified or whitelisted; A1/A2 follow the Immersion Rule; B1+ Tab 1/3/4 body is 100% Ukrainian; decolonized framing applies across all tabs.

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

{WRITER_SPECIFIC_DIRECTIVES}

## Mandatory visible verification block (emit BEFORE drafting — #1673/#1661)

Emit one `<plan_reasoning section="...">...</plan_reasoning>` block per section (<=200 words).

Each `<plan_reasoning>` block MUST contain these exact XML sub-nodes (do not write a single blob of prose):
- `<word_budget>`: section word allocation + running total vs {WORD_TARGET}.
- `<plan_vocab>`: required plan-vocabulary lemmas used + grounding Ukrainian sentence.
- `<register>`: immersion ratio from the Immersion Rule + how this section preserves it.
- `<teaching_sequence>`: Knowledge Packet facts/citations this section uses.
- `<implementation_map>` (<!-- rule_id: #R-IMPL-MAP-COMPLETE -->): list every `obligation_id` exactly once with artifact, location, treatment. Omission causes `implementation_map_missing`. If a row cannot fit A1 scope, emit artifact/location `<none>` and treatment `deferred — <why>`.
- `<verification_plan>`: MCP tools to call for this section's claims.
- `<verification_trace>`: exact tool call signatures; omit speculative examples.

Prefer single-call verification: `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`. Search for quote evidence.

Emit audit lines in order:

1. `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[<deferred IDs>]</implementation_map_audit>`
2. `<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`
3. `<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`

If `M < N`, fix the map before artifacts. If `bad_form_audit.remaining != 0`,
convert remaining italic/bare bad forms to `<!-- bad -->...<!-- /bad -->`.
If `activity_split_audit.split_valid=false`, rebalance inline/workbook first.

## Tier-1 verification discipline (do this WHILE drafting — #1661)

<!-- rule_id: #R-CITE-HONEST -->
Сибір case study (May 2026): a prior answer fabricated a Грінченко citation, an Антоненко-Давидович claim, and a fused Shevchenko line. Verify before citing; do not ship authority theatre.

<!-- rule_id: #R-VESUM-ALL-WORDS -->
**1. Verify every example word in VESUM** — exhaustively, not a sample. Batch-verify every distinct Cyrillic word form in `module.md`, `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` via `mcp__sources__verify_words`, except bad-form-marker spans and `error:`/`errorWord:` fields — including derived adjectives (`-ний/-овий/-альний/-увальний`), `-ість` nouns, agent nouns, and every hyphenated compound. Replace any miss not heritage-attested (`search_slovnyk_me`/`search_heritage`, `is_russianism==false`) with an attested synonym or rephrase before emitting; an unverified content word fails the build. **First-pass-critical:** the `python_qg` correction loop does LITERAL find/replace only — it CANNOT rephrase a coinage/jargon into a synonym, and a failed correction deletes content (also failing `word_count`); do not rely on it. Before any reflexive `-ся` form, verify it; traps `пити → *п'юся`, `читати → *читаюся`, `писати → *пишуся` fail unless VESUM says otherwise.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Bad-form marker convention (MANDATORY everywhere).** Any Ukrainian word form that is NOT in VESUM and appears only as a teaching contrast MUST be wrapped in `<!-- bad -->...<!-- /bad -->` markers in every artifact. Do not use italics or bare prose for bad forms.

Learner-facing bad-form contrast is optional, level-sensitive, and must be wiki/plan-authorized; early M1-M4 usually teach canonical forms only. When contrast is authorized, use marker syntax in every artifact; otherwise omit the bad form. Hard-reject unless marker-protected: italic bad-form leaks, unmarked `X, а не Y` / `instead of Y` / `замість Y`, parenthetical `(not Y)` / `(не Y)`, and true-false statements where Y is malformed or Russianism.

**Morpheme-bold notation.** Do not put hyphens/slashes inside bold spans: write `<verb> (**-suffix**)`, not `<verb>**-suffix**` or `**-suffix/-variant**`.

**Textbook syllable-break notation.** Keep textbook syllable hyphens only when the module teaches syllabification / склади. Otherwise strip display hyphens before learner-facing prose.

**2. Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys forms. Never classify a word as Russianism/surzhyk/calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. Route uncertain forms through `mcp__sources__search_heritage` first. If authentic but non-standard, tag `[Archaism]` / `[Historism]` / `[Dialectism]` and give the modern equivalent. Unverified → omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.

Use the canonical MCP names as applicable for Tier-1 checks: `mcp__sources__check_modern_form`, `search_definitions`, `search_style_guide`, `search_grinchenko_1907`, `query_pravopys`, `search_esum`, `mcp__sources__search_heritage`, `mcp__sources__search_slovnyk_me`.

<!-- rule_id: #R-CITE-HONEST -->
**3. Source-citation discipline.** Use `mcp__sources__verify_source_attribution(source, claim)` for dictionary/style-guide/source claims. If `discusses=false`, do not cite. Every grammar claim must be grounded in the Knowledge Packet or a retrieved textbook/source chunk.

**Grammar claim grounding.** EVERY specific grammar claim (aspect, case endings, syntax, phonetics, morphology, word formation, stress/prosody, orthography, or meaning distinctions) MUST cite an authoritative source. Name it in text or as `<!-- VERIFY: source="..." grade="..." author="..." -->`. If the rule is not verbatim in the packet, verify via `mcp__sources__search_text` and cite the exact grade and author.

<!-- rule_id: #R-TEXTBOOK-30W -->
**Textbook grounding.** For each `plan_references` entry, call `mcp__sources__get_chunk_context(chunk_id=<ID>)` and ground from THAT text. Do NOT use `search_text` or topic-keyword search for plan references. The `chunk_context_for_all_refs` gate hard-rejects missing calls. Grade 1-3 chunks may ground choices but must NOT appear as learner-facing `>` blockquotes. Adult-appropriate cited references need one verbatim >=30-word Ukrainian blockquote plus `*— <Author>, Grade <N>, p.<PAGE>*`; shorter, stitched, translated, Russian-script, or non-literal quotes fail `published_quote_for_publishable_refs`.

<!-- rule_id: #R-CITE-HONEST -->
Resources must be plan/wiki/telemetry-grounded. `resources.yaml role: textbook` entries come ONLY from `plan.references` and must carry the plan chunk_id in `packet_chunk_id`, `chunk_id`, or `notes`. Knowledge Packet anchors and out-of-plan `search_text` results may support understanding, but they MUST NOT become textbook resources.

<!-- rule_id: #R-CITE-HONEST -->
**4. Quote attribution discipline.** Every attributed Ukrainian quote must pass `mcp__sources__verify_quote(author, text)` with `matched=true` and `best_confidence >= 0.85`. Never fuse snippets from separate sources.

**5. End-of-output gate.** Before artifacts, rescan: all Ukrainian forms verified or marker-protected, every source grounded, every quote literal. Omit or rewrite anything unverifiable.

After the four artifact fences, emit a visible `<end_gate>...</end_gate>` block. Fill each node with concrete items, not placeholders:

<end_gate>
  <rescanned_words>[word forms re-verified during rescan]</rescanned_words>
  <rescanned_sources>[sources re-grounded]</rescanned_sources>
  <grammar_claims_grounded>[grammar claims + cite source]</grammar_claims_grounded>
  <removed_unverified>[forms/claims removed as unverifiable]</removed_unverified>
  <chunk_context_calls>N</chunk_context_calls>
  <chunk_context_chunk_ids>[exact chunk_ids passed to get_chunk_context]</chunk_context_chunk_ids>
  <resources_search_calls>N</resources_search_calls>
  <resources_search_tools>[exact multimedia tool names called]</resources_search_tools>
</end_gate>

`<chunk_context_calls>` MUST equal the count of fetchable `plan_references`; if it is `0` while references exist, call `mcp__sources__get_chunk_context` for each plan chunk. `<resources_search_calls>` MUST be ≥1 and counts ONLY `mcp__sources__query_wikipedia`, `mcp__sources__search_external`, or `mcp__sources__search_images`. Missing or false counts become `gate_present=false` / `tool_theatre`.

**Tool-citation honesty (mandatory).** Every tool name you cite inside `<plan_reasoning verification="...">` or block body MUST correspond to an actual tool call you made on this turn. If not, STOP: make the call or remove the citation. Unmatched citations are a hard fail (`tool_theatre`). Canonical names only: exact `mcp__sources__...` names, no family aliases.

## LESSON SOURCE — render this wiki content into the 4-tab format

The wiki content below is the LESSON SOURCE per the V7.1 Renderer Charter above. Render it; do not compose around it.

## Wiki Obligations Manifest

{WIKI_MANIFEST}

## Wiki Coverage Required Items (per-obligation breakdown)

Integrate each item into natural lesson flow (a model sentence, usage example, conjugation row, phonetic transcription). Do NOT echo `Крок N:` labels or `[S\d+]` source markers — writer-side scaffolding, forbidden per `#R-NO-SCAFFOLDING-LEAKS`.

{WIKI_COVERAGE_REQUIRED_ITEMS}

## Implementation Map Contract

Pre-resolved tuples: `(obligation_id, artifact, location_hint, treatment_template)`. Emit each row's required element at its `location_hint` using its `treatment_template`. Do NOT invent obligations beyond the manifest; do NOT skip rows. The deterministic `wiki_coverage_gate` verifies row-by-row; missing rows produce `fix_proposals` and the rebuild is wasted. Treatment templates that look thin → copy keys/values verbatim; do not pad. Gate diagnostics, not your prose, drive seeder fixes.

{IMPLEMENTATION_MAP_CONTRACT}

### External Resources — multimedia search obligation

Every module MUST attempt at least one multimedia lookup (YouTube/video, blog/article, podcast/audio, image/gallery). Make at least ONE lesson-relevant call to:
- `mcp__sources__query_wikipedia` for Ukrainian Wikipedia context, OR
- `mcp__sources__search_external` for blog/article search, OR
- `mcp__sources__search_images` for image/gallery discovery, OR
- browser-based search if available in this dispatch's tool set.

If `external_resources` in the Wiki Obligations Manifest is non-empty, those URLs are AUTHORITATIVE; include them in `resources.yaml` with supplied roles.

Empty search results are acceptable, but the search attempt MUST be recorded in the writer telemetry. If you cannot find usable resources, you MUST still record the search attempt in writer telemetry. Skipping the search fails the `resources_search_attempted` gate.

In `resources.yaml`, every entry MUST have a `role` field: `textbook`, `reading`, `youtube`, `video`, `blog`, `podcast`, `audio`, `article`, or `wiki`.

**Schema rule for non-textbook roles: `url:` is REQUIRED.** `role: textbook`
does NOT require `url:`; all other roles (`reading`, `youtube`, `video`, `blog`, `podcast`,
`audio`, `article`, `wiki`) require a non-empty `url:` or schema validation
halts. If a non-textbook entry lacks a verified URL, **OMIT THE ENTRY ENTIRELY**. Never emit `url: null`, `url: ""`, `url: TBD`, or an entry without `url:`; all fail. Honest omission does NOT regress `resources_search_attempted` because the gate counts telemetry.

For seminar/folk modules, include at least one `role: reading` entry that tells the learner where to read a primary text. Its `url:` MUST be a public, student-facing URL on the primary-text allowlist (`data/primary_text_sources.yaml`): the topic's `uk.wikipedia.org` article is the guaranteed floor, and you may add a specific `uk.wikisource.org` / `litopys.org.ua` / `ukrlib.com.ua` document (work) page when one resolves. **Never use an internal `wiki/...` (or `docs/wiki/...`) repo path as the url** — those are AI-facing, not student-facing, and are rejected; the on-site primary text reaches the learner through a `:::primary-reading` block, not a resources link. Each `reading` entry MUST carry a one-line task prompt in `notes` (for example: `прочитай повну думу «...», зверни увагу на формулу повернення додому`). Never use bare-domain landings, category pages, section landings, or guessed opaque `?id=N` URLs.

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
- Word **minimum**: {WORD_TARGET} — this is a FLOOR. The gate hard-rejects below 92% of this number. Plan section budgets around **~1.20× the minimum** because the strict gate tokenization excludes markdown comments, JSX tag/attribute syntax, punctuation tokens, numbers, and page refs; self-counted `wc -w` usually runs 15-16% high.

## Module Size Policy — dossier/evidence-led expansion control (#4801)

{SIZE_POLICY}

This policy does not lower the plan floor on its own. It controls expansion permission: never invent depth to satisfy a fixed word count, and never treat old 150% multiplier thinking as a target. If the policy reports `plan_policy_review_required` or `blocked_until_research_dossier`, complete the verifiable coverage and emit the required `SIZE_POLICY_MISMATCH` marker instead of padding.

## Section Word Budgets — policy-aware first-draft requirements

The first draft must meet or exceed `{WORD_TARGET}` and must hit every section `words:` budget below when the size policy permits source-backed expansion. If the first draft is short, the pipeline may request targeted expansion before Python QG continues; that expansion is allowed only with substantive, cited exposition, examples, close-reading, source comparison, and cultural/grammar analysis. `:::primary-reading` quoted text is excluded from counted words; surrounding explanation must carry the budget.

{SECTION_WORD_BUDGETS}

## Learner State

This learner has completed modules 1..{MODULE_NUM}-1 in track `{LEVEL}`. Cumulative vocabulary and grammar below are the FLOOR this module may assume.

1. **Don't re-explain already-taught grammar.** Refer back briefly (`як ти бачив у модулі N` / `as in module N`) and build on it.

2. **Don't introduce vocabulary outside the cumulative list or this module's declared `vocabulary.yaml`.** From m04 onward this is HARD `unknown_vocab_in_prose`; for m01-m03 it is a WARN. Every Ukrainian content word in `module.md` prose/dialogue/examples must be cumulative, declared, or exempt as a proper noun / Latin borrowing.

3. **Soft scaffolding via foreshadowing.** If a new lemma appears before its `vocabulary.yaml` entry, give a first-mention gloss (`**креслити** *(to draw lines)*`).

4. **Frequency-and-CEFR awareness.** Before any non-plan lemma, run the Corpus Access stack; if none pass for `{LEVEL}`, omit and choose differently.

5. **Build on cumulative grammar where natural.** Use prior grammar in context without re-deriving it.

6. **Signpost intentional repetition.** Frame repeated concepts/skills/activity families as review, reuse, or deeper practice before asking for them again.

{LEARNER_STATE}

## Module Archetype Contract

{MODULE_ARCHETYPE}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Tone and immersion (mandatory)

<!-- rule_id: #R-VOICE-META -->
Write for an adult learner, not for a teacher reading a lesson plan. No English meta-narration; the complete forbidden phrase list is in the Writer Charter. Do not write teacher-plan narration such as "Welcome to", "In this section we will learn", "this section teaches", "learners will", or "the activity asks". Open sections directly with the grammar fact, a Ukrainian example/dialogue line, or a one-sentence English scaffold.

English is only for translation, gloss, and short scaffolds. Honor the Immersion Rule exactly; B1+ body text outside Tab 2 is 100% Ukrainian.

<!-- rule_id: #R-VOICE-META -->
**Engagement floor.** Emit at least 1 content-anchored callout (`:::tip`, `:::note`, `:::caution`, `:::warning`, `[!myth-buster]`, `[!history-bite]`). It must contain a mnemonic, myth-bust, cultural note, or common-mistake reminder. Empty filler does not count. Meta-narration hits fail `engagement_floor` immediately.

<!-- rule_id: #R-BAD-FORM-MARKER -->
**Russianism floor.** `russianisms_strict` fails on any critical Russicism/calque/surzhyk finding. Check suspicious forms with `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `search_heritage`, and `query_pravopys`. Never paste raw Russian forms into prose/dialogue; use a `<!-- VERIFY -->` placeholder or omit.

{SEMINAR_FOLK_WRITER_RULES}

<!-- rule_id: #R-SINGLE-VOICE-A1 -->
**Single teacher voice at A1.** One teacher voice across the whole module: warm, clear, direct ("you" / "your"). No third-person framing of the learner (`the student`, `студента`, `the reader`, `учня`) and no mid-paragraph register shifts (English -> Ukrainian metalanguage -> preachy imperative -> casual paraphrase). Good: "You use **я креслю** when you describe your own action." Bad: "the student enters an authentic space."

<!-- rule_id: #R-AUDIENCE-LANGUAGE-A1 -->
**A1/A2 audience language — ULP immersion.** Teach Ukrainian *through* Ukrainian. A1 may use English as a receding scaffold, but A2 uses easy Ukrainian as the default body voice. A2 complexity should grow naturally across the level: early A2 uses short, repeated frames; mid/late A2 adds connectors, fuller descriptions, and transparent subordinate clauses.

1. **Ukrainian-first, em-dash gloss.** Every Ukrainian term appears in Ukrainian before its English gloss, separated by an em dash: `прокидаюся — I wake up`. Never write "the word for wake up is ...".
2. **Stress marks are deterministic.** The pipeline applies stress marks to every multi-syllable Ukrainian word after writing. Write plain Ukrainian; do not hand-stress.
3. **Dialogues are Ukrainian-first.** Use `<DialogueBox uk="..." en="..." />` for side-by-side translation. The `uk` turn is Ukrainian-only; do not interleave English grammar inside turns.
4. **Dialogue inline gloss discipline.** Keep any A1/A2 line-level English support no more than 8 words from its Ukrainian dialogue line; put full translation at the block bottom.
5. **Comprehension/recall is Ukrainian-only.** Tab 3 content stems and answer options are Ukrainian-only; English appears only in UI affordances.
6. **Use a named first-person teacher persona or named characters.** Anchor examples in real Ukrainian places/foods/routines; never write abstractly about "the student must learn...".
7. **A2 English limit.** In A2, English is limited to vocabulary glosses or one-line clarification when truly needed; do not add English support paragraphs to the module body.
8. **Forbidden foreigner-textbook anti-patterns:** "X sounds like Y in English", transliteration tables, English grammar paragraphs with Ukrainian bolted on, "the student must learn", and English topic-sentence openers.

<!-- rule_id: #R-NO-CHILDREN-PRIMARY-QUOTES -->
**No children-primary blockquotes in adult A1.** No `>` blockquotes from textbooks at Grade 1, 2, or 3 levels in the published module body. Grade 1-3 RAG hits can still ground lexical choices, but do not surface as quoted material. Default: NO blockquote unless it pedagogically advances the lesson AND comes from an adult-appropriate source (Grade 7+, adult literature, Антоненко-Давидович, style guides). Adult A1 learners are not reading children's primers; do not print `<Author>, Grade 1, p.<P>` as lesson prose.

<!-- rule_id: #R-NO-SCAFFOLDING-LEAKS -->
**No writer-side scaffolding leaks.** Writer-side scaffolding never appears in module body. Forbidden in published markdown: panel IDs (`P1`, `P2`, ...), Krok-N labels (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names. The module is a finished lesson, not a writer's worksheet.

<!-- rule_id: #R-GRAMMAR-TERMS-A1 -->
**Use grammar terms at A1.** Use proper grammatical terminology in English explanations: **noun**, **verb**, **adjective**, **adverb**, **pronoun**, **reflexive**, **conjugation**. Do NOT paraphrase (`a thing`, `an action`, `a word for`, `a doing-word`, `the X-form of Y`). Adult learners benefit from real grammar terms because they transfer to future modules and outside references.

<!-- rule_id: #R-PROSE-FLOOR-A1 -->
**Prose words only — section budget.** Per-section word budgets (270-330 for A1) count PROSE only. Callouts, dialogue boxes, table cells, bullets, comments do NOT count. Structural elements are *bonus density*, not budget — still emit ≥270 words of prose AROUND tables/callouts. Reach the prose floor BEFORE you optimize for clean structure.

<!-- rule_id: #R-CLEAN-TABLES -->
**Clean table formatting.** Tables: bold ONLY the target Ukrainian forms. Pronoun columns (`я`, `ти`, ...), English headers, and English glosses remain in regular weight. Conjugation tables teaching a present-tense paradigm must include the FULL set of person/number rows: **я / ти / він,вона,воно / ми / ви / вони** (six rows). Vocabulary tables stay two-column unless a third column adds essential teaching value (e.g., stress mark, IPA).

**Dialogue format (gate-counted).** Ukrainian dialogue lines must be `<DialogueBox uk="..." en="..." />` or lines that begin with the `>` blockquote marker followed by a space. Em-dash-only dialogue under `## Діалоги` is invisible to `l2_exposure_floor` and fails the module. **The `<DialogueBox>` tag MUST be self-closing — it must end with `/>`.** A bare `<DialogueBox uk="..." en="...">` (no closing `/>`, no `</DialogueBox>`) is invalid MDX AND the `l2_exposure_floor` regex counts it as ZERO, so every such line silently fails the gate.

**Minimum UK dialogue lines (A1-A2).** For A1 and A2 modules, emit at least **15 distinct gate-countable Ukrainian dialogue surfaces** (`<DialogueBox uk="..." en="..." />` entries and lines that begin with the `>` blockquote marker plus a space, summed). The `l2_exposure_floor` gate's floor is 14; overshoot by ≥1 for safety. Prior builds have failed at exactly 13 gate-countable lines via `too_few_uk_dialogue_lines`. Count BEFORE emitting: if you have <15, add another exchange to the dialogue section or split a long turn into two shorter ones.

`шо` is acceptable inside dialogue blocks (`<DialogueBox>` or `>` blockquotes) when the register is colloquial; never in teacher-voice narration. When you use it, add a `notes:` field to the `що` entry in `vocabulary.yaml` flagging the literary↔colloquial pair so learners know when each is appropriate (the per-item schema accepts `notes`, NOT `note` — singular fails schema validation). Do NOT add a separate top-level entry for `шо` — VESUM does not codify it and the vocab gate will reject a standalone lemma.

**UK example-sentence density.** A1-m15-24 modules need >=14 gate-countable Ukrainian example surfaces across bullet-list lines and Markdown table data rows. Use bullets/tables for paradigms and trap pairs; prose-only paradigms count zero.

<!-- rule_id: #R-ACTIVITY-COMPOSITION -->
**Activity composition (bounded, not rendered).** Wiki names the activity formats; you compose concrete items. Every Ukrainian token in `sentence:`, `prompt:`, `options:`, `items:` fields and distractors must come from the V7.1 layered vocab allowlist. The `learner_state` vocab gate scans `activities.yaml` token-by-token; unsupported content lemmas fail like prose lemmas.

**Distractor supply (critical at A1).** Wrong-form distractors for MCQ/select/error-correction come ONLY from the wiki's L2 errors, wiki bad-form pairs, or cumulative learner state. **Never invent Russianisms or fabricate wrong forms.** If inventory is insufficient, emit `<implementation_map>` `treatment="deferred — wiki distractor inventory thin"`; do not paper over by inventing.

**Activity item count vs INLINE/WORKBOOK split.** `{ACTIVITY_COUNT_TARGET}` carries the per-level target; the split rule is enforced by the activity-schema gate. Schema fields stay canonical per "Activity Authoring Fields".

## Activity Types and the INLINE / WORKBOOK split (mandatory)

Every module ships TWO complementary activity sets: sparse INLINE checks woven
into prose, and majority WORKBOOK practice in Tab 3 (`Вправи`).

### Inline activities — LIGHT, theory-time

Inline activities are LIGHT theory-time checks: fast (≤30 seconds), simple, tied to one section, and never bigger than the explanation. ONLY inline activities require `id` fields and matching `<!-- INJECT_ACTIVITY: ... -->` markers.

Allowed inline types for `{LEVEL}`: {INLINE_ALLOWED_TYPES}

### Workbook activities — SUBSTANTIVE, after-lesson practice

Workbook activities are SUBSTANTIVE after-lesson practice with NO marker. They stay workbook-only in Tab 3, are longer (1-3 minutes), multi-item, and designed for review/self-assessment. Omit `id` on workbook activity objects.

Allowed workbook types for `{LEVEL}`: {WORKBOOK_ALLOWED_TYPES}

### Split targets and overall budget

Activity count target for `{LEVEL}`: {ACTIVITY_COUNT_TARGET}
Vocabulary count target for `{LEVEL}`: {VOCAB_COUNT_TARGET}

ACTIVITY_CONFIGS intent: A1 10 total = 4-6 INLINE + 6-9 WORKBOOK; A1 checkpoint 8 = 3-5 + 5-8; A2 12 = 4-6 + 8-11; A2 checkpoint 10 = 3-5 + 7-10; B1/B2/C1 16 = 5-7 + 11-15; C2 12 = 4-5 + 8-10; seminars 10 = 3-4 + 7-9.

### Design principle (read before drafting)

When designing each activity, decide its CONTEXT first:
- Is this a quick "did the concept land?" check that belongs INSIDE the teaching prose? → INLINE (use an INJECT marker, keep the activity simple).
- Is this a comprehensive drill, integration, or extension? → WORKBOOK (no INJECT marker, longer item count, harder discrimination).

The same item TYPE can appear in both sets, but inline and workbook instances must be distinct. Do NOT duplicate inline activities into workbook or shove everything into one set.

### Allowed types (global)

Allowed (any context): {ALLOWED_ACTIVITY_TYPES}
Forbidden at this level: {FORBIDDEN_ACTIVITY_TYPES}

## Inline activity cross-references in module.md (mandatory for inline activities)

**ONLY inline activities are injected. Every INLINE activity emitted in `activities.yaml` MUST be inline-referenced
in `module.md`** via an exact-format HTML comment marker:

```
<!-- INJECT_ACTIVITY: act-1 -->
```

Workbook activities MUST NOT have matching markers; omit `id` on workbook objects. Do not add markers for all activities.

The pipeline hard-fails both directions: inline id without matching marker (`unused_activities_not_injected`) or marker pointing to a missing id (`missing_activity_ids`).

**Placement rule:** put the marker in the matching section, alone with blank lines around it:

`<!-- INJECT_ACTIVITY: act-2 -->`

The marker is an invisible HTML comment for the gate only; do not wrap it in backticks, JSX props, or another fence.

## Activity Authoring Fields (mandatory)

Each `activities.yaml` object MUST use the authoring field names listed below for its declared `type`; these are parser fields, not React component prop names.

Do not invent prop names. Do not borrow a prop name from a different activity
type. In particular, for `quiz`, `select`, and `translate`, use the authoring
field `items`; do NOT use the React/component prop name `questions`.

```
{COMPONENT_PROPS_SCHEMA}
```

For item-bearing types, include non-empty `items`; numeric arrays like `correct_order` use zero-based indices.

**`group-sort` shape (mandatory canonical fields).** Use `groups` shaped like `{"label": "Group name", "items": ["word 1", "word 2"]}`. Do NOT emit top-level `items`, `key`, or `{word, group}` pairs.

**`letter-grid` shape (mandatory canonical fields).** Each `letters` entry MUST use `upper`, `lower`, `emoji`, `key_word`, and optional `sound_type`/`note`; no aliases such as `letter`, `word`, `sound`, or `kind`.

**`count-syllables` item shape (mandatory canonical fields).** Each item MUST use `word` and integer `correct`. Do NOT use `answer`.

**`watch-and-repeat` item shape (mandatory canonical fields).** Each item MUST use `video` for the YouTube/video URL. Do NOT use `url`.

**`translate` activity items (mandatory canonical fields — HARD FAIL on alias).** Each item inside a `translate` activity's `items:` list MUST use `source` for the text to translate and `options` for target choices; the correct target answer is the option with `correct: true`. For UK→EN translation, `source` is the Ukrainian text and the target English answer lives in `options[].text`. Do NOT use `prompt:`/`answer:` aliases, and do NOT emit a bare `target:` field that the parser cannot consume.

**`quiz` and `translate` item explanations (mandatory teaching feedback — HARD FAIL if missing/empty).** Every item inside a `quiz` or `translate` activity's `items:` list MUST include `explanation: "..."`. Keep it one concise line explaining why the correct option is right; for A1/A2, write this explanation in simple English. Empty strings, whitespace-only strings, or omitted `explanation` fields fail the `quiz_translate_explanations` gate.

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

**FORBIDDEN inner field-name aliases** — these leak deliberate typos into `vesum_verified` and fail the strict parser: `wrong:`, `incorrect:`, `mistake:`, `bad:`, `original:`, `wrong_form:`, `incorrect_form:`, `correct:` (use `correction:`), `correctAnswer:`, `right:`, `fix:`, `fixed:`.

Rule: if a field name is not in `{sentence, error, errors, errorWord, error_word, explanation, correction, answer, options}` for an error-correction item, you are inventing an alias. Stop, use `sentence` + `error` + `correction` exactly as above.

## Plan

```yaml
{PLAN_CONTENT}
```

## Full Wiki Context (source of truth for citations)

See `## Knowledge Packet` above. This is the same wiki-obligation content; the prior render duplicated it as a token tax. Textbook citations in `resources.yaml` remain governed by the earlier Citation authority rule: plan references only, never Knowledge Packet anchors as citation candidates.

## Pre-emit verification (run BEFORE you write any artifact)

Before artifacts, make the in-scope MCP calls your draft depends on:
1. Textbook grounding (mandatory chunk_id-first protocol):
   For each entry in `plan_references`, parse the `notes` field for the literal substring `chunk_id: <ID>` (always present — example: `chunk_id: <textbook-slug>_s<NNNN>`).
   Call `mcp__sources__get_chunk_context(chunk_id=<ID>)` to fetch the chunk text.
   DO NOT call `mcp__sources__search_text` for plan references — the chunk_id in notes is authoritative.
   Concrete example: plan says `chunk_id: <textbook-slug>_s<NNNN>` → call `get_chunk_context(chunk_id="<textbook-slug>_s<NNNN>")`, paste from THAT returned text. Do NOT search by page number — FTS5 can return the wrong author or page.
2. Multimedia obligation: at least one `mcp__sources__query_wikipedia`, `mcp__sources__search_external`, or `mcp__sources__search_images`; `resources_search_attempted` rejects zero attempts.
3. VESUM: `mcp__sources__verify_words` over every Ukrainian form you will emit.
4. Russianism/style: `mcp__sources__search_style_guide`, `mcp__sources__search_ua_gec_errors`, `mcp__sources__check_russian_shadow`, or `mcp__sources__search_heritage` for contrast pairs or suspicious forms.
5. Literary/cultural quote: `mcp__sources__verify_quote` or `mcp__sources__search_literary` as level-appropriate.
6. CEFR check: `mcp__sources__query_cefr_level` before adding non-plan lemmas.
7. Source attribution: `mcp__sources__verify_source_attribution` for every named source claim.

If a required call is missing for your level, make it now. Do not emit artifacts first and hope the gate catches it.

## PRE-EMIT HARD STOP — read this NOW, before any artifact fence

Re-check these three hard-stop items BEFORE emitting:

1. **`get_chunk_context` for every plan reference.** `search_text` does NOT count toward `textbook_grounding`; call `mcp__sources__get_chunk_context(chunk_id=<ID from notes>)` for EACH `plan.references` entry.

2. **At least ONE multimedia search call.** `resources_search_attempted` counts ONLY `mcp__sources__query_wikipedia`, `mcp__sources__search_external`, and `mcp__sources__search_images`; empty results are acceptable, zero attempts are not.

3. **INJECT_ACTIVITY parity.** Every `INJECT_ACTIVITY id=<X>` in `module.md` MUST have a matching activity id in `activities.yaml`; count both before emitting.

If tool history lacks items 1 or 2, STOP and make the calls. `<end_gate>` counts are cross-checked against telemetry; lying fails via `tool_theatre`.

## Artifact emission format (STRICT — restored 2026-05-23 after PR-C strip)

Return the visible `<plan_reasoning>` blocks first, then exactly these four fenced blocks in the order below, then the `<end_gate>` block. Do not add any other prose anywhere.

**Three structured artifacts (`activities.yaml`, `vocabulary.yaml`, `resources.yaml`) MUST be emitted as 3-backtick fenced blocks labelled with language `json` and an info-string `file=<name>`.** The pipeline parses them with `json.loads`. Do NOT use `yaml`, `activities.yaml`, or bare `\`\`\`` as the fence info — those fail at writer-output parse with `must be fenced as json, got <X>`.

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "instruction": "...",
    "items": [{"sentence": "Я ____ схему.", "answer": "креслю", "options": ["креслю", "питаю"]}]
  }
]
```

```json file=vocabulary.yaml
[
  {"lemma": "креслити", "translation": "to draw lines", "pos": "verb", "usage": "Я креслю схему."}
]
```

Vocabulary entries MUST use only these fields: `lemma`, `translation`, `pos`, `usage`, and optional `notes`, `examples`, `tags`. CEFR/frequency lookups are selection evidence only; do NOT emit metadata fields such as `cefr`, `level`, `frequency`, `register`, `gender`, or `example`.

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176", "role": "textbook", "notes": "..."}
]
```

Each activity object MUST carry the props for its declared `type` per the `COMPONENT_PROPS_SCHEMA` table. Do not strip an `items` array down to `id/type/title` just because the example above looks short.

**Wrap the `module.md` artifact in a 4-backtick OUTER fence.** The OPEN fence MUST be exactly one line: four backticks, then a single space, then the info string `markdown file=module.md`, then newline. Like this (one line, no mid-line break):

````markdown file=module.md
...module body here, may contain inner 3-backtick fences for examples...
````

DO NOT split the info string across two lines (i.e. NEVER emit ` ```` ` then a newline then `markdown file=module.md`) — the parser scans the fence-open line for `file=`; a separate line gets tagged "unnamed fenced block" and the build hard-fails at writer-output parse.

The CLOSE fence is four bare backticks on their own line.

## HARD STOP RULE

After emitting all required `<plan_reasoning>` blocks, the 4 artifact fences
(`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), and the
`<end_gate>` block, STOP. Do not write a summary, status report, completion
confirmation, or any meta-commentary about what you did. The 4 fences are the
deliverable. Anything after the `<end_gate>` block will be discarded by the
parser. If you feel the urge to write "Module drafted under..." or "All forms
verified...", DON'T. The verification is in the `<end_gate>` block, not in prose.
