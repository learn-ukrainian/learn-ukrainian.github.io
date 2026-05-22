{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Writer Prompt

Write the A1 module using the plan and contract below. Produce exactly four
authoring artifacts: `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml`.

{WRITER_SPECIFIC_DIRECTIVES}

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

   **Coverage requirement (#2026-05-20).** "Every example word" means
   EVERY Cyrillic word form that appears in your module.md prose,
   vocabulary.yaml entries (lemma AND usage fields), activities.yaml
   prompts/answers, and resources.yaml notes — not a selected sample.
   Build the `verify_words` list by iterating your full draft, not by
   recalling salient words. The deterministic `vesum_verified` gate WILL
   find the words you skipped — selective verification is the same
   failure class as silent fabrication.

   **L2-trap: over-applied reflexive -ся.** Common writer failure mode is
   emitting reflexive forms (`-ся`) of TRANSITIVE verbs that are NOT
   reflexive in standard Ukrainian. The verb is intransitive-reflexive
   ONLY if its `-ся` form is in VESUM. Examples that ALWAYS fail:
   - `пити → *п'юся` (WRONG — `пити` is transitive: `Я п'ю каву`)
   - `снідати → *снідаюся / *снідається` (WRONG — intransitive but not reflexive: `Я снідаю`)
   - `читати → *читаюся` (WRONG — transitive: `Я читаю книгу`)
   - `писати → *пишуся` (WRONG; impersonal `пишеться` exists in passive sense, but `*пишуся` as personal reflexive does not)

   Before emitting any `-ся` form, verify via `mcp__sources__verify_word`.
   If `verify_word` returns NOT FOUND for the `-ся` form, the verb is NOT
   reflexive — emit the non-reflexive form instead. Do not invent
   reflexive forms by analogy from English "myself / oneself" — Ukrainian
   reflexive morphology is lexicalized per verb.

2. **Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys standard forms for learner-facing standard Ukrainian. However, NEVER classify a word as Russianism, surzhyk, or calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. For any non-modern or suspicious form, verify with `mcp__sources__check_modern_form` (VESUM) plus available historical/etymological evidence (`mcp__sources__search_grinchenko_1907`, `mcp__sources__search_esum`, literary/wiki source context). If authentic but non-standard, keep it only when pedagogically required, tag it `[Archaism]`, `[Historism]`, or `[Dialectism]`, give the modern standard equivalent, and briefly state its Ukrainian heritage. If unverified, omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.

   **Bad-form marker convention (MANDATORY everywhere).** Any Ukrainian word form that is NOT in VESUM — intentional misspellings, Russianisms, Surzhyk, calques, archaisms appearing only for teaching contrast — MUST be wrapped in `<!-- bad -->...<!-- /bad -->` markers wherever it appears in the output, regardless of which artifact. The bad form is deliberately NOT in VESUM and would trip the `vesum_verified` gate as a false positive; the marker lets the gate strip it while the learner still sees the form in rendered MDX.

   ```markdown
   Stick to **сніданок** (not the Russian-borrowed <!-- bad -->завтрак<!-- /bad -->),
   **рушник** (not <!-- bad -->полотенце<!-- /bad -->), and **одягатися** (not the
   surzhyk <!-- bad -->одіватися<!-- /bad -->).
   ```

   Apply this same convention in ALL writer artifacts:
   - **module.md prose:** `**дивитися → я дивлюся**, not <!-- bad -->дивюся<!-- /bad -->`.
   - **activities.yaml `true-false` `statement:` fields:** any negative example named in a true statement must be marker-wrapped. WRONG: `statement: "правильно: X, а не Y."`. RIGHT: `statement: "правильно: X, а не <!-- bad -->Y<!-- /bad -->."`
   - **activities.yaml `match`, `fill-in`, `multiple-choice`, `order`, `pair-up`, etc. items:** any wrong form named as a contrast — if it is not a structural field like `error:` that the gate already skips — MUST have markers.
   - **vocabulary.yaml `usage:` field:** usually exemplifies the correct form, so markers should not normally be needed. If a usage line names a wrong form for teaching, marker it.
   - **resources.yaml `title:` / notes:** out of scope; do not marker.

   **Exception:** `type: error-correction` activity items already have `sentence:` / `error:` fields fully excluded from VESUM lookup; markers are optional there but harmless.

   **True-false anti-pattern:** statements that say `X, а не Y` / `X, not Y` MUST marker the Y form when Y is a malformed, Russianism, Surzhyk, or other non-VESUM teaching contrast. Do not leave Y bare just because the statement's `answer: true`.

   The `<!-- bad -->...<!-- /bad -->` marker is stripped by `_strip_metalinguistic` before VESUM lookup but doesn't render in MDX, so the bad form is still visible in plain prose. Do NOT use single-asterisk italics (`*завтрак*`) or bare unmarked prose for bad forms — both trip the gate. The marker is specifically for Russianisms, surzhyk forms, calques, and paronyms shown *to be avoided*. Words shown as legitimate non-standard heritage (archaisms, dialectisms) keep the `[Archaism]` / `[Dialectism]` tag and pedagogical defense above.

   **CONCRETE FORBIDDEN PATTERNS — HARD REJECT, close-the-class enumeration (#2094, #2095).** These are the exact patterns that failed m20 rebuilds #2–#17. The `<!-- bad -->` marker is the ONLY accepted form for a bad-form contrast.

   **Silent emission of any italic-wrapped bad form is a HARD REJECT — the rebuild is wasted and `vesum_verified` will fail.** Yesterday's m20 build #17 emitted `❌ *Я дивюся* → ✅ **Я дивлюся**` and `not the L2 trap form ❌ *Я користуювася*` — both patterns the writer KNEW the rule for (the same writer used `<!-- bad -->` markers correctly in the same module for завтрак / полотенце / одіватися). Inconsistent application of this rule is the same failure class as silent obligation omission, and it now carries the same HARD REJECT consequence.

   Any of the following will trip `vesum_verified`, `formatting_standards`, or `russianisms_clean`:

   - ❌ `*X*, not *Y*` — italic contrast pair. The italicized *Y* leaks into VESUM and is rejected.
   - ❌ `... not *Y*.` / `... not *Y*,` — bare italic bad form.
   - ❌ `say X, not Y` — unmarked bad form in prose. The unmarked Y leaks into VESUM lookup.
   - ❌ `true-false statement: X, а не Y.` — unmarked YAML negative example. The unmarked Y leaks into VESUM lookup unless marker-wrapped.
   - ❌ `instead of Y` / `замість Y` — unmarked bad form after a contrast preposition.
   - ❌ `(not Y)` / `(не Y)` — unmarked bad form in parentheses.

### Pre-emit bad-form audit (mandatory — #2095)

Before emitting the four artifact fences (after the `<implementation_map_audit>` line from #2094), you MUST self-audit your draft across `module.md`, `activities.yaml`, and `vocabulary.yaml` for any unmarked or italic-wrapped bad-form pattern:

1. Scan your draft for any of: `❌ *X*`, `*X*, not *Y*`, `... not *Y*.`, `... not *Y*,`, `say X, not Y`, `X, а не Y`, or `X, not Y` inside YAML `statement:` / item strings.
2. For EVERY match, the bad form `X` or `Y` MUST be wrapped in `<!-- bad -->X<!-- /bad -->` markers, NOT in `*italic*` and NOT bare prose. The Russianism, surzhyk, calque, or L2-trap form is the load-bearing case.
3. If your scan finds zero italic-bad-form patterns, you may proceed. If your scan finds any, STOP, replace them with `<!-- bad -->` markers, and re-scan.

Emit a single visible audit line BEFORE the artifact fences (after the `<implementation_map_audit>` line):

`<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`

If this audit line is missing, or if `remaining > 0`, the writer has failed the protocol and the rebuild is wasted. Mechanical consistency on this rule unlocks all m20 ship velocity.

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

   **MANDATORY WORD-COUNT SELF-CHECK (≥30 words).** Before emitting each textbook blockquote, count the Ukrainian word tokens you pasted. The `textbook_grounding` gate runs `long_blockquotes_checked` against a HARD floor of 30 contiguous words — fewer than 30 produces a HARD REJECT even when retrieval + attribution were perfect. Observed failure mode (DeepSeek-pro build #3, a1/my-morning, 2026-05-21): writer pasted *"Уранці Євген устав із ліжка САМ. ... Після сніданку САМ помив посуд."* (24 words, correctly attributed to Захарійчук Grade 1 p.52) and the gate still rejected. If your draft block hits a comma at word ~24 and stops, KEEP READING the chunk body and KEEP COPYING the next sentence until your contiguous span passes 30 words. Trim trailing partial sentences only AFTER you've cleared the floor. The retry path is expensive — get it right on the first emit.

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

### Additional MCP tools — surface and use

The verification discipline above covers the load-bearing checks. The pipeline
also exposes these tools; use them when their evidence is relevant:

- `mcp__sources__search_literary` — primary literary sources (125K chunks: chronicles, poetry, prose, legal texts). Use at b1+ for full access; at a1/a2 use only the level-curated subset per §1.1 of the Corpus Access section.
- `mcp__sources__search_idioms` — Frazeolohichnyi (25K idioms). Use when prose needs a natural Ukrainian idiom rather than an English-calque construction.
- `mcp__sources__search_definitions` — СУМ-11 (127K entries; 7,152 flagged for Soviet ideological framing). **Use with caution**: every result row carries `sovietization_risk` (0/1/2). Risk ≥ 1 → do NOT reproduce the definition verbatim; paraphrase neutrally OR query `search_grinchenko_1907` / `search_heritage` for a pre-Soviet alternative. Issue #1659.
- `mcp__sources__search_grinchenko_1907` — Hrinchenko historical dictionary (67K entries, 1907). Pre-Soviet usage attestation. Use when you need to show that an "unusual-looking" UK form is authentic UK heritage, NOT a Russianism.
- `mcp__sources__search_esum` — ESUM etymological dictionary (vol. 1 indexed; vols. 2-6 in `data/processed/esum_vol{2..6}.jsonl`). Cognate maps, Proto-Slavic forms, borrowing chronology.
- `mcp__sources__search_synonyms` — Ukrajinet WordNet (122K synsets, auto-translated from English WordNet — caveat #1657). Use sparingly; cross-check with `search_style_guide` or native Ukrainian context before substituting.
- `mcp__sources__translate_en_uk` — Балла EN→UK (79K entries). Use when you have an English source and need the canonical UK translation, especially for vocabulary-yaml `translation:` fields.
- `mcp__sources__query_pravopys` — Правопис 2019 orthography rules. The authoritative reference for spelling (м'який знак, апостроф, capitalization, hyphenation). Cite when emitting any rule about Ukrainian orthography.
- `mcp__sources__query_cefr_level` — PULS CEFR vocabulary (5.9K words tagged A1-C1). The vocab-level check from §1.2.

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
3-backtick fenced JSON code blocks labeled with the language `json`. Exactly
one JSON block per structured artifact. Do not include trailing commas. Do
not include comments. Do not mix YAML or prose into JSON blocks. The pipeline
uses `json.loads` and fails the build on any parse error.

**Wrap the `module.md` artifact in a 4-backtick OUTER fence.** The OPEN
fence MUST be exactly one line — four backticks, then a single space,
then the info string `markdown file=module.md`, then newline. Like this
(everything between the two `<<<` markers is one line, with no
mid-line break):

```
<<<````markdown file=module.md<<<
```

DO NOT split the info string across two lines (i.e. NEVER emit
` ```` ` followed by a newline followed by `markdown file=module.md`).
The parser scans the fence-open line for the `file=` label; if that
label is on a separate line, the block is tagged "unnamed fenced block"
and the build hard-fails at writer-output parse.

The CLOSE fence is four bare backticks on their own line: ```` (no
indentation, no trailing text).

The 4-backtick wrapper lets you include 3-backtick code blocks INSIDE
module.md for verb conjugation tables, code-style examples, or any prose
that benefits from a fenced block — those inner 3-backtick fences will be
treated as content. CommonMark fence semantics: an N-backtick open is
closed only by ≥N backticks. So a 4-backtick outer permits 3-backtick
inner fences to pass through. Use 4 backticks for module.md OUTER even if
you don't need inner fences — uniform protocol is safer than per-module
choices.

Triple-backtick `module.md` outers are still accepted for backward
compatibility, but they fail HARD as soon as the writer includes any
nested triple-backtick line. Default to 4-backtick.

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

## Corpus Access (level-gated)

Your `{LEVEL}` from Module Context determines which MCP tools are in-scope. Tools NOT in your level's row are OUT OF SCOPE — do not call them and do not cite them. This gating exists because lower-level modules need register discipline; an A1 module quoting Stus is a register break even if the quote is verified.

| {LEVEL} | Textbooks | Literary | External | Vocab-level check | Always-on |
|---|---|---|---|---|---|
| **a1** | `search_text` (Grades 1-4 only — prefer G1-2 when satisfying `plan_references`; G3-4 only when the topic explicitly requires it) | `search_literary` filtered to children's literature, folk songs, fairy-tale openings, iconic phrases — query with collection filter `tag:a1-curated` (see §1.1) | ULP only: `search_external(collections=["ulp_blogs","ulp_youtube","pohribnyi_pronunciation"])` | `query_cefr_level` → stacked: PULS A1 → ubertext-freq top-1000 → ULP S1-S2 (see §1.2) | VESUM tools, `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `query_pravopys` |
| **a2** | `search_text` (Grades 1-5) | `search_literary` filtered to `tag:a2-curated` (widens to add simple Stefanyk passages, Hlibov full, simple Lesya for children) | ULP + Pohribnyi (same as a1) | `query_cefr_level` → PULS A1+A2 → top-2000 → ULP S1-S4 | (same) |
| **b1** | `search_text` (full Grades 1-11) | `search_literary` (FULL corpus — chronicles, poetry, prose, legal texts) | All 8 collections: `ulp_blogs`, `ulp_youtube`, `pohribnyi_pronunciation`, `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs` | `query_cefr_level` → PULS A1-B1 → top-5000 → ULP S1-S6 | (same) |
| **b2** | (inherit b1) | (inherit b1) | (inherit b1) | (inherit b1, extend to PULS A1-B2) | (same) — content modes EXPAND (see §1.3) |
| **c1** | (inherit b1) | (inherit b1) | (inherit b1) + when ingested: peer-reviewed UA scholarship | (inherit b1, extend to PULS A1-C1) | (same) — posture shifts (see §1.4) |
| **c2** | (inherit c1) | (inherit c1) | (inherit c1) | (same as c1) | (same as c1) |
| **seminar (hist/oes/ruth/istorio)** | full | full + ingested OES manuscripts + Ruthenian Baroque corpus | full + ingested academic UA scholarship | (n/a — seminar is not vocab-driven) | strict-2-source citation rule (see §1.5) |
| **seminar (lit/bio + sub-tracks)** | full | full | full + ingested academic UA scholarship | (n/a) | hybrid posture (see §1.4) |

The bracketed `tag:` values in literary filtering (e.g. `tag:a1-curated`) refer to a follow-up filter layer (#F1 from the interview matrix) that is being built separately. **For this PR**, the writer should call `search_literary` with the level-appropriate intent in mind (children's lit at A1; widen at A2; full at B1+) and the gate will be enforced once the tag layer ships. Do NOT block on the tag layer; the directive language is the load-bearing contract.

### §1.1 Literary filter intent at A1/A2

A1/A2 literary scope means: short children's literary excerpts (`Глібов байки`, ditemai-poetry, simple folk songs, fairy-tale openings, iconic phrases like `Реве та стогне Дніпр широкий`). NOT chronicles, NOT dense modernist prose (Khvylovy, Pidmohylny, Zabuzhko), NOT Stus, NOT legal texts.

When you call `search_literary` at A1/A2 and a result returns an excerpt from outside this scope, DROP IT from your knowledge packet. Cite only level-appropriate excerpts. Register drift via "well-verified but wrong-register" literary quoting was the H1 prompt-bug failure mode (see `audit/2026-05-17-judge-calibration-h1/COMPARISON.md`).

### §1.2 Stacked vocab-level check

When introducing a new lemma BEYOND what `plan_references` mandates:

1. **First**: `query_cefr_level(lemma)`. If the result is your `{LEVEL}` or below (A1 ≤ A1; A2 ≤ A2; B1 ≤ B1; etc.), the lemma is in-scope.
2. **Else, fallback**: check `ubertext-freq` rank. If `rank ≤ 1000` at A1, `≤ 2000` at A2, `≤ 5000` at B1+, in-scope.
3. **Else, fallback**: check ULP cumulative coverage. If the lemma appears in `ulp_blogs` or `ulp_youtube` content for Season ≤ the level's season cap (A1: S1-S2, A2: S1-S4, B1+: S1-S6), in-scope.
4. **If none pass**: omit the lemma. Use plan-mandated vocabulary instead. Do NOT introduce a lemma that fails all three checks.

Record this gate in `<plan_reasoning>` under `<vocab_level_check>` for any non-plan lemma you intend to introduce.

### §1.3 Content modes at B2+

At B2 the writer's content surfaces EXPAND beyond A1-B1's "dialogue + rule explanation + prose":
- **Literary commentary** — 1-3 paragraph analysis of a Stefanyk / Franko / Lesya passage
- **Cultural-analysis prose** — e.g. "the кобзар tradition in 19th-c. Ukraine"
- **Historical narrative** — multi-paragraph chronological account
- Same evidence rule applies (every example traces to corpus); same VESUM + verify_quote + verify_source_attribution discipline.

### §1.4 Posture shifts at C1+ / seminars

- **C1**: HYBRID posture. Factual claims (dates, attributions, definitions, citations) MUST be tool-backed pre-emission. Prose flow connecting cited claims may be generated freely without per-sentence RAG. Still no fabrication paths: facts cited; transitions crafted.
- **C2**: same as C1; maxed sophistication.
- **Seminar history tracks (hist/oes/ruth/istorio)**: STRICT 2-source rule for every historical claim. Date + figure + event + attribution → ≥2 sources cited inline. `verify_quote` for primary-source quotes. Decolonization claims require evidence-pair (myth + truth from named sources).
- **Seminar lit/bio + sub-tracks**: HYBRID (same as C1).

### §1.5 Strict-2-source for seminar history claims

For HIST / OES / RUTH / ISTORIO modules, every historical CLAIM (a date, a figure's action, an event, an attribution) MUST cite ≥2 sources inline. Format: `«claim text» [Hrushevsky, Історія України-Руси, т. 3, p. 84; Plokhy, The Gates of Europe, p. 142]`. Where claim and counter-claim diverge (decolonization framing), name BOTH the imperial source (`Karamzin's История Государства Российского`) and the UA-grounded counter (Hrushevsky, Plokhy, etc.).

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

**Engagement floor (REQUIRED — `engagement_floor` gate counts these).** Every module MUST emit at least 2 content-anchored callouts. Use Starlight directive blocks (`:::tip` / `:::note` / `:::caution` / `:::warning`) or GitHub-style admonitions (`> [!myth-buster]` / `> [!history-bite]`). Each callout block must carry concrete pedagogy — a mnemonic, a myth-bust, a cultural note, or a common-mistake reminder. Empty or filler callouts that just restate the next paragraph do not count toward the floor.

Forbidden in prose (zero-tolerance — the `engagement_floor` gate fails the build on the first hit): "Let us begin", "Let us explore/look/learn/see/consider/now", "In this section/module/lesson/chapter/unit", "Welcome to A1/A2/...", "Congratulations on completing", "You have unlocked", "You now possess", "Your journey begins/starts/continues". These are persona breaks. Address the learner directly with content-anchored claims; do not narrate the lesson container.

**Russianism floor (HARD BAN — `russianisms_strict` gate fails on any critical-severity finding).** A two-detector layer scans every artifact: (1) the project's curated calque + lexical Russicism patterns (`приймати участь`, `самий кращий`, `получати`, `відноситися`, `слідуючий`, `давайте попрактикуємо`, dozens more) per `scripts/audit/checks/russicism_detection.py`; (2) the UA-GEC corpus (8,937 human-annotated Ukrainian error→correction pairs from the Grammarly UA team, filtered to russianism-relevant tags: F/Calque, F/Collocation, G/Case, G/Gender). Any `critical` finding from either detector halts the build. Lower-severity findings surface to the LLM review dim as advisory signal.

Use `mcp__sources__check_russian_shadow`, `mcp__sources__search_style_guide` (Антоненко-Давидович), `mcp__sources__search_ua_gec_errors`, and `mcp__sources__search_heritage` during drafting to verify any phrase that could plausibly be a Russianism. The authority hierarchy when uncertain: VESUM (does the form exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (historical usage). Heritage-defense check first when a word may be an authentic Ukrainian archaism / regionalism rather than a Russianism (`кобета`/`кобіта` pattern — see `mcp__sources__search_heritage`).

Quote ban: never paste raw Russian forms (e.g. `хорошо`, `спасибо`, `сейчас`, `пожалуйста`) into prose or dialogue, even inside a quoted learner mistake — use a `<!-- VERIFY -->` placeholder if you need to reference one. The russianism detectors will flag these as critical; the build will fail before MDX assembly.

**Dialogue format (REQUIRED for gate counting).** All Ukrainian dialogue lines MUST be emitted as one of:

- `<DialogueBox uk="..." en="...">` JSX component (preferred for V7 rendering), or
- `> `-prefixed Markdown blockquote (Markdown fallback)

The `l2_exposure_floor` gate counts only these two forms. **Em-dash dialogue lines (e.g. `— Привіт, Насте!`) under a `## Діалоги` heading WITHOUT `<DialogueBox>` or `> ` wrapping are an anti-pattern** — the gate cannot count them and the module will fail the dialogue-line floor even when the dialogue is pedagogically present.

Default to `<DialogueBox>` for new modules; `> ` blockquote acceptable when a multi-line dialogue is more naturally rendered as quoted prose.

**Inline gloss for dialogue lines (REQUIRED to clear `long_uk_ceiling`).** Each Ukrainian dialogue line MUST have an inline English gloss within 8 tokens of proximity. Two valid shapes:

- Italic gloss directly after the UK line: `— Привіт, Насте! *(Hi, Nastia!)*`
- Inside the same DialogueBox prop: `<DialogueBox uk="..." en="...">`

**UK example-sentence density (REQUIRED for `l2_exposure_floor`).** The
gate counts two pedagogical surfaces as "UK example sentences" — every
A1-m15-24 module needs **≥ 14 of these combined** to clear the floor:

1. **Bullet-list lines** (`- ...` or `* ...`) whose body contains any
   Ukrainian word. Use for routine-verb examples, paradigm rows in
   list form, phonetic-rule examples, trap-pair contrasts. Glossable
   inline (one bullet, one `*(en gloss)*` or `(en gloss)` clause).
2. **Markdown table data rows** (`| ... |`) whose cells contain any
   Ukrainian word. Header rows and `---` separators don't count.
   Contrast tables (Wrong / Right), conjugation paradigms, IPA
   reference, vocabulary preview — all valid.

**Anti-pattern: prose-only UK content.** A grammar section that
introduces a paradigm as paragraph prose without ANY bullet or table
row will count zero toward `l2_exposure_floor`, even if it shows 20
Ukrainian verb forms in narrative sentences. The 2026-05-21 a1/my-
morning gemini-tools build #1 produced 6 example sentences against the
14-minimum and rejected at this gate — the writer used flowing prose
where bullets/tables would have rendered the same paradigm in a
gate-countable shape.

**Practical guidance for module shape:**
- Under each grammar section (`Дієслова на -ся`, `Мій ранок`), emit at
  least **6 bullet lines** carrying conjugation forms or example
  sentences. A 6-row paradigm table also satisfies this.
- Under `Підсумок` / contrast or trap sections, add a 4+ row
  "Wrong / Right" or "Calque / Native" table.
- Vocabulary preview can be a short table too — its UK cells count.

The dialogue-line and example-sentence floors are independent — 14
dialogue lines alone won't clear the example-sentence floor, and
vice versa.

**Anti-pattern: block-bottom gloss.** Do NOT emit all UK dialogue lines first and then a separate "translation:" / "English:" block at the bottom. This causes `long_uk_ceiling` to flag the entire UK run as one unsupported segment, even when every line has a corresponding English translation farther down.

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

### Pre-emit activity-split audit (MANDATORY — new gate, parallel to `<implementation_map_audit>` and `<bad_form_audit>`)

Before emitting the four artifact fences, you MUST self-audit your activity split.

1. Count activities in `activities.yaml` that have a matching `<!-- INJECT_ACTIVITY: act-X -->` marker in `module.md` → call this `INLINE_N`.
2. Count activities in `activities.yaml` that do NOT have a matching `<!-- INJECT_ACTIVITY: act-X -->` marker → call this `WORKBOOK_N`.
3. Verify both counts fall within the level's allowed ranges (see "Split targets" above). For A1: `INLINE_N ∈ [4, 6]` and `WORKBOOK_N ∈ [6, 9]`. If EITHER count is outside its range, STOP. Either move activities between sets (add/remove INJECT markers) or write additional workbook activities. Do not proceed until both ranges are satisfied.

Emit a single visible `<activity_split_audit>` audit line BEFORE the artifact fences (after `<implementation_map_audit>` and `<bad_form_audit>` lines):

`<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`

If `split_valid=false`, the rebuild is wasted. The deterministic post-build gate will reject; do not try to ship past this audit.

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

{KNOWLEDGE_PACKET}

## Pre-emit verification (run BEFORE you write any artifact)

Confirm you have made AT LEAST one of each of the following MCP tool calls.
If any line below is FALSE for your current session, make the call now BEFORE
emitting any artifact:

1. **Textbook grounding** — `mcp__sources__search_text` for each `plan_references` textbook entry (one call per entry; verify the citation page exists in the search hit).
   Level-gate per §1: A1 uses Grades 1-4; A2 uses 1-5; B1+ uses full.
2. **Multimedia obligation** — AT LEAST ONE of `mcp__sources__query_wikipedia`, `mcp__sources__search_external` (with level-appropriate collections per §1: A1/A2 = `ulp_blogs`+`ulp_youtube`+`pohribnyi_pronunciation`; B1+ = all 8), OR `mcp__sources__search_images`.
   Non-negotiable: the `resources_search_attempted` gate REJECTS modules with `multimedia_calls_total == 0`.
3. **VESUM verification** — `mcp__sources__verify_words` on EVERY Ukrainian form you intend to write that isn't trivially known (top-100 frequency).
   One batched call per dozen lemmas is fine.
4. **Russianism check** — `mcp__sources__search_style_guide` on at least one Russianism-candidate form when teaching contrast pairs.
5. **Literary grounding (when applicable)** — `mcp__sources__search_literary` for any literary quote or cultural attribution.
   Level-gate per §1.1: A1/A2 use the curated subset; B1+ use full.
6. **CEFR level check (when introducing non-plan lemmas)** — `mcp__sources__query_cefr_level` per §1.2's stacked check.
7. **Style guide / Antonenko grounding (when emitting bad-form contrast)** — `mcp__sources__search_style_guide` (structured) AND `mcp__sources__search_text source=antonenko-davydovych-yak-my-hovorymo` (full-book prose).
   Both are required; the H1 prompt bug failed when only structured was queried.

If any line above is FALSE and is in-scope for your `{LEVEL}` per §1 (Corpus
Access), make the call now. Do not emit artifacts until the checklist is fully
green for your level.

Failure to satisfy ANY checklist line will cause the build to fail at the
`resources_search_attempted` / `vesum_verified` / `textbook_grounding` /
`style_guide_evidence` gate AFTER you've spent compute generating prose. The
checklist calls above cost you latency up front and unblock the entire build.
Make them.

## HARD STOP RULE

After emitting all required `<plan_reasoning>` blocks, the 4 artifact fences
(`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), and the
`<end_gate>` block, STOP. Do not write a summary, status report, completion
confirmation, or any meta-commentary about what you did. The 4 fences are the
deliverable. Anything after the `<end_gate>` block will be discarded by the
parser. If you feel the urge to write "Module drafted under..." or "All forms
verified...", DON'T. The verification is in the `<end_gate>` block, not in prose.
