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
For each obligation_id in the Wiki Obligations Manifest, list:
  - obligation_id: <id>
  - artifact: <module.md | activities.yaml | vocabulary.yaml | resources.yaml>
  - location: <section name or activity id>
  - treatment: <how the obligation is addressed, for example "contrast_pair in activity act-3"
                or "prose explanation in section §Дієслова на -ся paragraph 2">
Do not defer. Every obligation must be implemented in THIS module, not a later one.
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

   **Verbatim textbook grounding (mandatory).** For each `plan_references` entry, you MUST call `mcp__sources__search_text` with a query targeting that textbook + topic, then quote at least one verbatim block (≥30 words) inline in the relevant section. The citation must include the textbook author + grade + page extracted from the search result, and the quote must be set off as a blockquote so reviewers can verify it. Inventing or paraphrasing in place of retrieving is a hard fail (`textbook_grounding`).

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

## Plan

```yaml
{PLAN_CONTENT}
```

## Full Wiki Context (source of truth for citations)

{KNOWLEDGE_PACKET}

## HARD STOP RULE

After emitting all required `<plan_reasoning>` blocks, the 4 artifact fences
(`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), and the
`<end_gate>` block, STOP. Do not write a summary, status report, completion
confirmation, or any meta-commentary about what you did. The 4 fences are the
deliverable. Anything after the `<end_gate>` block will be discarded by the
parser. If you feel the urge to write "Module drafted under..." or "All forms
verified...", DON'T. The verification is in the `<end_gate>` block, not in prose.
