{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

## Mandatory visible verification block (emit BEFORE drafting — #1673/#1661)

Before the four artifact fences, you MUST emit one `<plan_reasoning section="...">...</plan_reasoning>` block for each contracted section. This is not optional hidden thinking. If any section lacks this visible block, the writer has failed the protocol.

Each `<plan_reasoning>` block MUST contain these exact XML sub-nodes (do not write a single blob of prose):
<word_budget>Section word allocation and running total check against {WORD_TARGET}±5%.</word_budget>
<plan_vocab>Required plan-vocabulary lemmas used in this section, with the exact Ukrainian sentence that grounds each lemma.</plan_vocab>
<register>The immersion ratio from the Immersion Rule and how this section preserves it.</register>
<teaching_sequence>Which Knowledge Packet facts/citations this section uses.</teaching_sequence>
<implementation_map>
**MUST list ALL `obligation_id`s from the Wiki Obligations Manifest. No exceptions.**

The `<implementation_map>` blocks across your N section-`<plan_reasoning>` nodes, taken together, MUST mention every `obligation_id` in the manifest exactly once. Silent omission of any `obligation_id` is a HARD REJECT — the rebuild is wasted and the gate will fail with `implementation_map_missing`.

For each `obligation_id` in the Wiki Obligations Manifest, list:
  - obligation_id: <id>
  - artifact: <module.md | activities.yaml | vocabulary.yaml | resources.yaml>
  - location: <section name or activity id>
  - treatment: <how the obligation is addressed, for example "contrast_pair in activity act-3"
                or "prose explanation in section §Дієслова на -ся paragraph 2">

**Do not defer silently. Every obligation must be implemented in THIS module unless you explicitly mark it deferred.** If, after careful drafting, an obligation genuinely cannot fit within the four sections of this A1 module (e.g., it requires grammar not yet introduced), emit it anyway with:
  - artifact: <none>
  - location: <none>
  - treatment: `deferred (out of A1 scope) — <one-sentence justification>`

Explicit deferral is far better than silent omission: the gate sees an honest decision and the orchestrator can reassign the obligation. Silent omission is a HARD REJECT and forces a full rebuild.
</implementation_map>
<verification_plan>Specific MCP tools to be called for this section's claims.</verification_plan>
<verification_trace>
List the exact tool call signatures you intend to use for this section.

**Prefer single-primitive calls over compose-patterns.** The pipeline ships four single-call verifiers that collapse multi-step compositions:

- For Ukrainian quotes: `mcp__sources__verify_quote(author="...", text="...")` — ONE call returns `matched: bool, best_confidence: float`. Do not compose `search_literary + grep + reason`.
- For source attribution: `mcp__sources__verify_source_attribution(source="grinchenko_1907"|"esum"|"sum11"|"antonenko_davydovych"|"literary"|"heritage"|"wikipedia"|"style_guide", claim="...")` — ONE call returns `discusses: bool, evidence: [...]`. Do not compose multiple per-source `search_*` calls.
- For modernity / archaism: `mcp__sources__check_modern_form(word="...")` — ONE call returns modernity flags. Do not infer from raw VESUM tags.
- For Russian-shadow detection: `mcp__sources__check_russian_shadow(word="...")` — ONE call returns Russian-morphology confidence.

Use the compose-pattern (`mcp__sources__search_literary` / `search_grinchenko_1907` / `search_style_guide` etc.) ONLY when you need to retrieve evidence chunks for inclusion in the artifact (e.g., quoting a textbook passage). For verification (`matched/discusses/modern/russian-shadow` boolean questions), the single-primitive call is mandatory.

Example: `mcp__sources__verify_quote(author="Шевченко", text="загнали в Сибір неісходиму")`. Do not fake results here; this is your plan for the tool calls you will actually trigger.
Every signature listed here is a commitment to call that exact tool this turn; omit speculative or copied example signatures.
</verification_trace>

Keep each `<plan_reasoning>` block to 200 words or fewer. Do not use triple backticks inside `<plan_reasoning>` blocks; fenced code belongs only in the four artifact blocks below.

Only after all `<plan_reasoning>` blocks are complete and passed may you emit the four fenced artifact blocks.

### Pre-emit obligation-count check (mandatory — #2094)

Before emitting the four artifact fences, you MUST audit your own `<implementation_map>` blocks against the Wiki Obligations Manifest:

1. Count the `obligation_id`s in the Wiki Obligations Manifest (call this `N`).
2. Count the distinct `obligation_id`s mentioned across all your `<implementation_map>` blocks (call this `M`).
3. If `M < N`, STOP. Go back, find the missing `obligation_id`s, and add them to the appropriate section's `<implementation_map>` — either with a real `treatment` or with the explicit `deferred (out of A1 scope)` escape hatch.
4. Only when `M == N` may you proceed to emit the four artifact fences.

Emit a single visible audit line BEFORE the artifact fences:

`<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[<list any IDs that ended up with treatment: deferred>]</implementation_map_audit>`

If this audit line is missing, or if `covered_in_map < manifest_obligations`, the writer has failed the protocol and the rebuild is wasted.

## Tier-1 verification discipline (do this WHILE drafting — #1661)

Сибір case study (May 2026): an unhardened answer shipped two fabricated
citations (a Грінченко example with no Грінченко entry behind it,
an Антоненко-Давидович claim with no style-guide entry) and one fused
Shevchenko line that does not exist as composed. These five checks block
that failure class. Run each check while drafting, not as a separate pass.

1. **Verify every example word in VESUM.** Every Ukrainian lemma listed as
   an example, vocabulary entry, or grammar exemplar must confirm via
   `mcp__sources__verify_words`. Failed verification → OMIT. Do NOT
   silently substitute a confabulated alternative. If no good substitute,
   leave the slot empty and emit `<!-- VERIFY: lemma "X" not in VESUM -->`.

2. **Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys standard forms for learner-facing standard Ukrainian. However, NEVER classify a word as Russianism, surzhyk, or calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. For any non-modern or suspicious form, verify with `mcp__sources__check_modern_form` (VESUM) plus available historical/etymological evidence (`mcp__sources__search_grinchenko_1907`, `mcp__sources__search_esum`, literary/wiki source context). If authentic but non-standard, keep it only when pedagogically required, tag it `[Archaism]`, `[Historism]`, or `[Dialectism]`, give the modern standard equivalent, and briefly state its Ukrainian heritage. If unverified, omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.

   **Russianism / surzhyk / calque callout markup (mandatory).** When a sentence in prose demonstrates a *bad form* for learner contrast (the "stick to X, not the Russian-borrowed Y" pattern), the bad form is deliberately NOT in VESUM and would trip the `vesum_verified` gate as a false positive. Wrap the bad form in HTML comments so the gate strips it but the learner still sees it in rendered MDX:

   ```markdown
   Stick to **сніданок** (not the Russian-borrowed <!-- bad -->завтрак<!-- /bad -->),
   **рушник** (not <!-- bad -->полотенце<!-- /bad -->), and **одягатися** (not the
   surzhyk <!-- bad -->одіватися<!-- /bad -->).
   ```

   The `<!-- bad -->...<!-- /bad -->` marker is stripped by `_strip_metalinguistic` before VESUM lookup but doesn't render in MDX, so the bad form is still visible in plain prose. Do NOT use single-asterisk italics (`*завтрак*`) or bare unmarked prose for bad forms — both trip the gate. The marker is specifically for Russianisms, surzhyk forms, calques, and paronyms shown *to be avoided*. Words shown as legitimate non-standard heritage (archaisms, dialectisms) keep the `[Archaism]` / `[Dialectism]` tag and pedagogical defense above.

   **CONCRETE FORBIDDEN PATTERNS — close-the-class enumeration.** These are the exact patterns that failed m20 rebuilds #2–#6. The `<!-- bad -->` marker is the ONLY accepted form for a bad-form contrast. Any of the following will trip `vesum_verified`, `formatting_standards`, or `russianisms_clean`:

   - ❌ `*X*, not *Y*` — italic contrast pair. The italicized *Y* leaks into VESUM and is rejected.
   - ❌ `... not *Y*.` / `... not *Y*,` — bare italic bad form.
   - ❌ `say X, not Y` — unmarked bad form in prose. The unmarked Y leaks into VESUM lookup.
   - ❌ `instead of Y` / `замість Y` — unmarked bad form after a contrast preposition.
   - ❌ `(not Y)` / `(не Y)` — unmarked bad form in parentheses.

   ✅ REQUIRED: `Stick to **X** (not the Russian-borrowed <!-- bad -->Y<!-- /bad -->).` — the `<!-- bad -->...<!-- /bad -->` marker wraps Y precisely. Markdown bold is fine for the GOOD form. Parentheses are fine around the bad form so long as the `<!-- bad -->` marker is inside them.

   Even single occurrences of the forbidden patterns fail the gate. Do not emit ANY bad form without the comment marker. When in doubt, omit the contrast — pedagogically, the good form alone is sufficient if the bad form cannot be cleanly marked.

   **Morpheme-bold notation — NO hyphens inside bold spans.** When highlighting a reflexive suffix, case ending, conjugation row, or any morpheme, the bold span MUST contain ONLY the morpheme being highlighted. Hyphens, slashes, or word fragments INSIDE the bold span create tokens that don't lemmatize in VESUM and trip `vesum_verified`.

   - ❌ `прокида**ю-ся**` — hyphen INSIDE bold. Normalizer extracts `прокидаю-ся` which fails VESUM.
   - ❌ `чита**ю-ся**`, `див**иться**.`, `мий**ся**!` — same class: prefix glued to a bold span containing an inflected suffix with internal punctuation.
   - ❌ `**-ся/-сь**` — slash inside bold creates two tokens.

   ✅ REQUIRED for highlighting a reflexive suffix in a paradigm row: write the FULL form unbolded, then call out the suffix on its own.
   - `прокидаюся (**-ся**)` — full form clean, suffix bolded standalone.
   - `прокидаюся, прокидаєшся, прокидається — суфікс **-ся** означає...` — prose form, suffix referenced as a standalone bold token.

   ✅ REQUIRED for case-ending or conjugation tables: use a table or list where the suffix appears on its own line, not glued to a stem with a hyphen inside bold.

   The normalizer now has a conditional heuristic that strips short morpheme-break hyphens inside bold (#2076), but the prompt-side rule is to NOT produce them in the first place. The heuristic is a backstop, not a license.

   **Textbook syllable-break notation — CONDITIONAL on module topic.** When quoting a textbook (e.g. Захарійчук Grade 1) that prints words with pedagogical syllable hyphens (`за-пи-са-ний`, `мо-ло-ко`, `пе-ре-мо-га`), the rule depends on what THIS module is teaching:

   - **If this module's topic IS syllabification / склади** (e.g. an early A1 module about dividing words into syllables, hyphenation rules, or sound-by-sound decoding): KEEP the hyphens. They are pedagogical content, not typography. The learner needs to see `за-пи-са-ний` to learn how the word divides. Both `vesum_verified` (via `_collapse_syllable_break` backstop) and `textbook_grounding` (via symmetric matcher normalization) handle the hyphenated form correctly — gates do not block this case.

   - **For all other modules** (the topic is anything OTHER than syllabification — vocabulary, dialogue, grammar, culture, daily routines, etc.): STRIP the hyphens before pasting. The hyphens are display typography for syllable-by-syllable reading drills the textbook uses to introduce vocabulary; they are not part of the word's actual form. A learner studying "my morning routine" should see `записаний`, not `за-пи-са-ний` — the latter teaches a malformed word in a non-syllable context.
     - ❌ Verbatim copy in a vocabulary/dialogue/culture module: `За-пи-са-ний на дошці.`
     - ✅ Hyphen-stripped: `Записаний на дошці.`

   Determination: read `Topic: {TOPIC_TITLE}` in the "Module Context" section above. If the topic explicitly references syllables (склади, поділ на склади, sound-by-sound reading, syllabification), keep hyphens. Otherwise strip them. When in doubt: prefer quoting a section of the chunk that does NOT contain syllable-broken display words.

   Note the decision in `<plan_reasoning>`: either `syllable hyphens kept (склади-teaching module)` or `syllable hyphens stripped from textbook quote per writer-prompt §2`. The deterministic `_collapse_syllable_break` normalizer (#2084) and the matcher's symmetric normalization are backstops; the prompt-side decision is what the LEARNER sees in the rendered MDX.

3. **Source-citation discipline.** Every dictionary / style-guide / author
   citation MUST be groundable in MCP. **Use `mcp__sources__verify_source_attribution(source, claim)` as the single-call primitive** — it returns a `discusses: bool` verdict in one call. Allowed `source` enum values: `grinchenko_1907`, `esum`, `sum11`, `antonenko_davydovych`, `literary`, `heritage`, `wikipedia`, `style_guide`. If `discusses=false`, do NOT cite that source for that claim.

   The compose-pattern (calling `search_definitions` for СУМ-11, `search_style_guide` for Антоненко-Давидович, `search_grinchenko_1907` for Грінченко, `query_pravopys` for Правопис, `search_esum` for ЕСУМ separately) is still allowed when you need the actual evidence chunks to QUOTE in the artifact, but for the boolean "does X discuss Y?" verification step, `verify_source_attribution` is the single-call mandate.

   Cannot ground via `verify_source_attribution` → do NOT cite. Say "modern Ukrainian standardized form" or rephrase without attribution. Inventing a citation to look authoritative is a hard fail.

   **Grammar claim grounding.** EVERY specific grammar claim (e.g., rules
   about aspect, case endings, syntax, phonetics, morphology, word formation,
   stress/prosody, orthography, or learner-facing meaning distinctions) MUST
   cite an authoritative source from the Knowledge Packet or a specific school
   textbook. You must explicitly name the source in the text or as an HTML
   comment with concrete metadata:
   `<!-- VERIFY: source="..." grade="..." author="..." -->`. If it's a new
   rule not verbatim in the packet, you MUST verify it via
   `mcp__sources__search_text` and cite the exact grade and author.

   **Verbatim textbook grounding (mandatory; 2-step retrieval).** For each `plan_references` entry, follow this exact 2-step pattern. A topic-only search that returns the wrong page produces a HARD `textbook_grounding` REJECT even when your blockquote content happens to be accurate — the matcher does string-containment against the exact `text` of the chunk you retrieved.

   **Step A — find the chunk_id.** Call `mcp__sources__search_text` with a query containing the **author surname AND the page number as plain digits** (e.g. `Захарійчук 162`, `Караман 176`, `Захарійчук 163`). The chunk_id pattern is `<source_file>_s<PAGE>` where `<PAGE>` is the zero-padded 4-digit page (`p.162` → `_s0162`). Scan the top results for a `Chunk ID:` ending in the right page suffix. If none match, refine: try different word orders, add a Ukrainian phrase distinctive to that page (from the Knowledge Packet), narrow to one author. Don't stop until you've identified the exact chunk_id.

   **Step B — fetch the verbatim text.** Once you have the matching chunk_id (e.g. `4-klas-ukrmova-zaharijchuk_s0162`), call `mcp__sources__get_chunk_context(chunk_id="4-klas-ukrmova-zaharijchuk_s0162")` (or pass the chunk_id positionally as documented in the tool's signature). Then copy-paste ≥30 contiguous words from THAT chunk's returned `text` into a blockquote in `module.md`, preserving punctuation and Cyrillic letter forms exactly. Paraphrasing, composing from memory, fusing snippets from multiple chunks, summarizing, "improving" punctuation, or substituting equivalent phrases is a hard fail — take a contiguous block verbatim.

   **EXCEPTION — pedagogical syllable hyphens depend on module topic.** Per §2 above (Markup conventions → Textbook syllable-break notation), syllable hyphens (`за-пи-са-ний`, `мо-ло-ко`) are pedagogical content in syllable-teaching modules (склади) and display typography elsewhere. KEEP them when the module teaches syllabification; STRIP them otherwise. All other punctuation, capitalization, and letter forms remain exact. The textbook_grounding matcher normalizes syllable hyphens symmetrically on both sides — a stripped quote still matches a hyphenated chunk and vice versa. Note the decision in `<plan_reasoning>` per §2.

   **Citation line format (mandatory; `citations_resolve` enforces it).** Immediately below the blockquote add `*— <Author>, Grade <N>, p.<PAGE>*` using the **exact** strings from the plan_references entry (e.g. `*— Захарійчук, Grade 4, p.162*`). Do NOT add the textbook title ("Українська мова") — that breaks the matcher because the plan_references format is `<Author> Grade <N>, p.<PAGE>` and the matcher requires that exact shape.

   **Topic placement.** The blockquote must appear in the section whose pedagogical topic matches the reference's intent (mismatched placement triggers `topical_mismatch`).

   **Corpus truly lacks the page.** If after refined queries you cannot surface a chunk_id with the cited page suffix, do NOT fabricate a blockquote. Emit a `<!-- VERIFY: chunk for the cited page not retrievable -->` comment in place of the quote and flag the plan_references entry for revision.

   **Citation discipline.** Sources cited in `module.md` blockquotes and listed in `resources.yaml` MUST be either:
   1. Listed in the module's `plan_references` (the matcher allows fuzzy match on author + grade + small page drift), OR
   2. Grounded in a Knowledge Packet retrieval the writer's `mcp__sources__search_text` call actually returned. Cite the chunk's textbook + grade + page verbatim from the search result.

   Do NOT add textbook references outside `plan_references` unless option 2 holds and the citation appears in your `writer_tool_calls.json` evidence. Adding ungrounded out-of-plan citations causes `citations_resolve` to fail and the build to halt.

For heritage defense, route lookups through the canonical MCP tools in this order: (1) `mcp__sources__search_heritage` is the primary entry point — it merges Грінченко 1907, ЕСУМ, slovnyk.me modern/regional dictionaries, and Антоненко-Давидович style warnings, ranking pre-Soviet attestations above modern-only rows. (2) Use `mcp__sources__search_slovnyk_me` only when you specifically need a slovnyk.me single-source result (e.g. СУМ-20 or a regional dictionary not surfaced by `search_heritage`). (3) Standard tools — `check_modern_form` (VESUM), `search_grinchenko_1907`, `search_esum`, literary corpus, and compiled wiki/source citations — remain valid evidence sources alongside the merged heritage tool. Cite the tool name and the dictionary slug in your `<plan_reasoning verification="...">` block. Do not claim heritage verification without naming a concrete tool result.
For slovnyk.me rows, use only canonical `dictionary_slug` values defined by `scripts/wiki/slovnyk_me.py`, especially heritage slugs `newsum`, `holoskevych`, `obsolete_words`, `bukovina`, `franko`, and `slang_lviv`; for merged `search_heritage` rows without `dictionary_slug`, cite `source_family`, `source`, and `classification`. Include the first 80 characters of the raw tool-result `text` verbatim in `<plan_reasoning>`. If `search_heritage` returns empty, emit `<!-- VERIFY: heritage status for "X" unresolved -->` rather than asserting heritage status.

4. **Quote attribution discipline.** Every attributed Ukrainian literary quote MUST be verified via a single `mcp__sources__verify_quote(author, text)` call BEFORE you paste the quote into the artifact. Required verdict: `matched=true` AND `best_confidence ≥ 0.85`. Verdict false or confidence below threshold → drop the quote or paraphrase without attribution. Never fuse two separate sources into one attributed line — `verify_quote` will return `matched=false` on fused composites, that is the canonical detection signal. The compose-pattern (`search_literary` + grep + reason) is forbidden for this verification step; use `verify_quote` exclusively.

5. **End-of-output gate.** Before emitting the four fenced blocks, scan
   the draft once more: every example word against the verification you
   ran, every cited source for grounding, every quote for literal corpus
   presence. OMIT or rewrite anything unverifiable. Shipping unverified
   output for the reviewer to catch is itself a protocol violation.
   **Tool-citation honesty (mandatory).** Every tool name you cite inside
   a `<plan_reasoning verification="...">` attribute or block body MUST
   correspond to an actual tool call you made on this turn. The pipeline
   cross-references citations against the trace and treats unmatched citations
   as a hard fail (`tool_theatre`). Citing a tool you did not call to satisfy
   the verification rubric — without doing the verification — is the canonical
   theatre failure and will block publication. If you intend to cite
   `search_heritage`, call `search_heritage`. If you intend to cite the
   underlying `search_grinchenko_1907`, call that. Canonical names only —
   no family aliases.

   You MUST record this scan as a visible `<end_gate>...</end_gate>` block
   AFTER the four artifact fences. Required format:

   ```
   <end_gate>
   <rescanned_words>List of words actually checked against VESUM.</rescanned_words>
   <rescanned_sources>List of citations actually checked against MCP.</rescanned_sources>
   <grammar_claims_grounded>List of grammar rules traced back to the Knowledge Packet or textbook.</grammar_claims_grounded>
   <removed_unverified>What you deleted because it failed verification.</removed_unverified>
   </end_gate>
   ```

   Leave a required sub-node empty only when nothing applied. Pipeline detects
   `gate_present=true` only when this block exists. A missing block records
   `gate_present=false`, and the writer is treated as having skipped the
   protocol.

Return the visible `<plan_reasoning>` blocks first, then exactly these four fenced blocks in the order below, then the `<end_gate>` block. Do not add any other prose anywhere.

```markdown file=module.md
...
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "instruction": "Complete each sentence with the best word.",
    "items": [
      {
        "sentence": "Я ____ о сьомій.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "сплю", "йду"]
      }
    ]
  }
]
```

Each activity object MUST carry the props for its declared `type` exactly as
laid out in the "Activity Component Props" section below. The example above
is a valid `fill-in`; do not strip the `items` array down to `id/type/title`
just because the example looks shorter that way.

```json file=vocabulary.yaml
[
  {
    "lemma": "прокидатися",
    "translation": "to wake up",
    "pos": "verb",
    "usage": "Я прокидаюся о сьомій."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "role": "textbook",
    "notes": "Зворотні дієслова: суфікс -ся означає дію, спрямовану на себе."
  }
]
```

## Output format (strict)

Emit `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` as separate
fenced JSON code blocks labeled with the language `json`. Exactly one JSON
block per structured artifact. Do not include trailing commas. Do not include
comments. Do not mix YAML or prose into JSON blocks. The pipeline uses
`json.loads` and fails the build on any parse error.

Inside the `module.md` artifact, do NOT use triple backticks (```) for ANY
purpose — no fenced code, no fenced quote, no fenced text. Use plain paragraphs,
lists, or tables instead. Triple backticks inside the artifact will be parsed as
a closing fence and break the artifact boundary. Single backticks for inline code
spans (e.g., `verify_words`) are fine — only triple backticks are forbidden.

## LESSON SOURCE — synthesize this wiki content into the 4-tab format

The wiki content below is the LESSON SOURCE you must translate into the
four artifacts. It is not background reference. Every obligation listed in
the Wiki Obligations Manifest must be implemented in the artifacts you
produce. Failure to address a wiki-named L2 error, sequence step, or
phonetic rule is the project's most common writer failure and is the
single largest reason A1 modules under-teach.

## Wiki Obligations Manifest

{WIKI_MANIFEST}

### External Resources — multimedia search obligation

Every module MUST attempt to find at least one multimedia external resource
(YouTube clip, blog post, podcast episode, video documentary, image gallery)
relevant to the lesson topic. The agent MUST make at least ONE call to:
- `mcp__sources__query_wikipedia` for Ukrainian Wikipedia context, OR
- `mcp__sources__search_external` for blog/article search, OR
- `mcp__sources__search_images` for image/gallery discovery, OR
- browser-based search if available in this dispatch's tool set.

If the Wiki Obligations Manifest's `external_resources` section is non-empty,
those URLs are AUTHORITATIVE — include all of them in `resources.yaml` with the
supplied role.

If the search returns nothing usable, that is acceptable — but the search
attempt MUST be recorded in the writer telemetry. The deterministic
`resources_search_attempted` gate fails the build if the writer skipped the
search entirely.

In `resources.yaml`, every entry MUST have a `role` field. Valid roles:
`textbook` (📚), `youtube` (📺), `video` (🎥), `blog` (📝), `podcast` (🎧),
`audio` (🎧), `article` (📄), `wiki` (🔗).

**Schema rule for non-textbook roles: `url:` is REQUIRED.**

The deterministic schema enforces:
- `role: textbook` entries do NOT require `url:`.
- All other roles (`youtube`, `video`, `blog`, `podcast`, `audio`, `article`, `wiki`) REQUIRE a non-empty `url:` field. Schema validation halts the build on any missing URL for these roles.

If you cannot provide a **verified** URL for a non-textbook entry — e.g. the multimedia search returned no usable URL, or the wiki source registry shows only a placeholder identifier like `ext-article-N` with no real title and no URL — **OMIT THE ENTRY ENTIRELY**. Do not emit:

- `url: null`
- `url: ""`
- `url: TBD`
- the entry without the `url:` field

All four patterns fail schema validation. The `resources_search_attempted` gate counts the multimedia search **attempt** in your telemetry, so honest omission of an unverifiable entry does NOT regress the search-obligation gate. Truthful omission is preferred over schema violation (compare MEMORY #M-4: deterministic over hallucination).

### Phonetic rules — MUST emit IPA notation

For every entry under `phonetic_rules:` in the Wiki Obligations Manifest, the
module MUST include the spoken target verbatim in square brackets (e.g.
`[с':а]`, `[ц':а]`) alongside the written form (e.g. `-шся`, `-ться`). The IPA
notation is what teaches the pronunciation contrast for English-speaking
learners — emitting only the written form leaves the rule pedagogically useless.

Format requirements:
- Spoken target appears inside `[...]` brackets (single-character square
  brackets, not Unicode look-alikes).
- Pair the written and spoken form in close lexical proximity (same sentence or
  adjacent bullet), so the contrast is visible to the learner.
- If the wiki provides example word pairs (e.g. `сміється [с'м'ійец':а]`), copy
  at least one example verbatim into a vocabulary card or example sentence.

The deterministic wiki-coverage gate hard-fails when any phonetic_rule has
`spoken_present=false`. There is no advisory-mode escape for this category.

## Knowledge Packet

{KNOWLEDGE_PACKET}

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Topic: {TOPIC_TITLE}
- Phase: {PHASE}
- Word target: {WORD_TARGET}

## Learner State

Words and grammar listed in **Cumulative vocabulary** / **Grammar already taught** are the floor of what this module's prose may assume. Do not re-explain already-taught grammar; do not introduce vocabulary that is not in the cumulative list or in this module's declared `vocabulary.yaml` (any unknown UK lemma in body prose without inline gloss is a HARD audit failure from m04 onward; WARN m01-m03).

{LEARNER_STATE}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Tone and immersion (mandatory)

The prose of `module.md` is for a learner who is encountering Ukrainian, not
for a teacher narrating their own lesson plan. Hold to this register:

- **No English meta-narration.** Do not write transitional or instructional
  framing phrases. Specifically forbidden, with no exceptions:
  - "Welcome to the start of our journey"
  - "In this section we will learn"
  - "Now that you have seen these verbs"
  - "Let's now look at"
  - "Before we move on"
  - "Note that…", "Notice that…", "Observe that…", "Observe how…"
  - "Pay attention to…", "Remember that…", "It is important to…"
  - Any English sentence that opens with a teacher-facing transition verb
    ("Let's…", "We will…", "You should now…")
  Open each prose section directly with the grammar point in Ukrainian,
  with a Ukrainian dialogue line, with the example itself, or with a
  one-sentence English statement of the grammar fact (no warm-up).
- **English is for translation, gloss, and short scaffolds, never for
  framing.** Treat English as a footnote that supports a Ukrainian sentence,
  not as a frame around it.
- **Honor the immersion ratio in the "Immersion Rule" section above.** It
  is not a target to approach asymptotically; over-writing in English is
  the single biggest failure mode of this prompt. Write less English, not
  more Ukrainian.
- **Section length is bounded by the contract YAML.** If you find yourself
  expanding an English bridge sentence, cut it instead. Word budgets are
  authoritative.

**Dialogue format (REQUIRED for gate counting).** All Ukrainian dialogue lines MUST be emitted as one of:

- `<DialogueBox uk="..." en="...">` JSX component (preferred for V7 rendering), or
- `> `-prefixed Markdown blockquote (Markdown fallback)

The `l2_exposure_floor` gate counts only these two forms. **Em-dash dialogue lines (e.g. `— Привіт, Насте!`) under a `## Діалоги` heading WITHOUT `<DialogueBox>` or `> ` wrapping are an anti-pattern** — the gate cannot count them and the module will fail the dialogue-line floor even when the dialogue is pedagogically present.

Default to `<DialogueBox>` for new modules; `> ` blockquote acceptable when a multi-line dialogue is more naturally rendered as quoted prose.

**Inline gloss for dialogue lines (REQUIRED to clear `long_uk_ceiling`).** Each Ukrainian dialogue line MUST have an inline English gloss within 8 tokens of proximity. Two valid shapes:

- Italic gloss directly after the UK line: `— Привіт, Насте! *(Hi, Nastia!)*`
- Inside the same DialogueBox prop: `<DialogueBox uk="..." en="...">`

**Anti-pattern: block-bottom gloss.** Do NOT emit all UK dialogue lines first and then a separate "translation:" / "English:" block at the bottom. This causes `long_uk_ceiling` to flag the entire UK run as one unsupported segment, even when every line has a corresponding English translation farther down.

## Activity Types

Allowed: {ALLOWED_ACTIVITY_TYPES}

Forbidden: {FORBIDDEN_ACTIVITY_TYPES}

Inline allowed: {INLINE_ALLOWED_TYPES}

Workbook allowed: {WORKBOOK_ALLOWED_TYPES}

Activity count target: {ACTIVITY_COUNT_TARGET}

Vocabulary count target: {VOCAB_COUNT_TARGET}

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

{KNOWLEDGE_PACKET}

## Pre-emit verification (run BEFORE you write any artifact)

Before emitting the four fenced blocks and the `<end_gate>` block, confirm
you have made AT LEAST one of each of the following tool calls during this
turn. If any line below is FALSE, make the call now before emitting.

1. `mcp__sources__search_text` — at least one call per `plan_references`
   textbook entry (textbook grounding obligation; gate
   `textbook_grounding`).
2. `mcp__sources__query_wikipedia` OR `mcp__sources__search_external` OR
   `mcp__sources__search_images` — at least one call (multimedia search
   obligation; gate `resources_search_attempted`). Honest "no result"
   counts — the attempt is what the gate counts.
3. `mcp__sources__verify_words` (or `verify_word` / `verify_lemma`) — at
   least one call on novel Ukrainian forms before writing them
   (verification obligation; reviewer evidence requirement).
4. `mcp__sources__search_style_guide` — at least one call on a Russianism
   or paronym candidate from the topic vocabulary (heritage-defense
   obligation; reviewer evidence requirement).

This checklist is not a substitute for the per-mandate instructions above;
it is a final cross-check that no mandate was forgotten under the attention
budget of the early-prompt contract directives.

## HARD STOP RULE

After emitting all required `<plan_reasoning>` blocks, the 4 artifact fences
(`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), and the
`<end_gate>` block, STOP. Do not write a summary, status report, completion
confirmation, or any meta-commentary about what you did. The 4 fences are the
deliverable. Anything after the `<end_gate>` block will be discarded by the
parser. If you feel the urge to write "Module drafted under..." or "All forms
verified...", DON'T. The verification is in the `<end_gate>` block, not in prose.
