# Phase 4 Round 3.5 Exemplar Report

## Scope

This pass exercised the post-#1603 round-3.5 writer prompt against the live
writer harness for A1/20 `my-morning`, using `gemini-tools` as the writer.

The result is diagnostic, not publishable: the strict JSON redispatch
succeeded, but deterministic Python QG failed on content gates. Per the Phase 4
round-3.5 brief, LLM QG, stress annotation, MDX assembly, and Starlight smoke
were skipped after the Python QG failure.

## Writer Run

- Writer: `gemini-tools`
- Total wallclock: 837.26 seconds
- Corrective redispatch: fired once
- Attempt 1 wallclock: 510.12 seconds
- Attempt 1 parser result: FAIL
- Attempt 1 parser error:
  `activities.yaml schema validation failed: item 3 has unexpected fields ['groups']; allowed: ['answer', 'correctAnswer', 'correct_order', 'correction', 'error', 'hints', 'id', 'instruction', 'isCorrect', 'items', 'note', 'options', 'pairs', 'passage', 'prompt', 'question', 'questions', 'sentence', 'sentences', 'source', 'statement', 'tags', 'target', 'title', 'translation', 'type']`
- Attempt 2 wallclock: 327.10 seconds
- Attempt 2 parser result: PASS

## Python QG

Overall deterministic verdict: FAIL.

| Gate | Verdict | Evidence |
|---|---:|---|
| `word_count` | FAIL | 1020 words; target 1200 |
| `plan_sections` | FAIL | no missing headings; `Діалоги` 263 words below 270 min; `Підсумок` 159 words below 270 min |
| `vesum_verified` | FAIL | 110 checked, 5 whitelisted, missing `вмиваєця`, `одягаєся`, `ться`, `шся` |
| `citations_resolve` | PASS | no unknown resources |
| `immersion` | FAIL | 15.11% Ukrainian, within 15-35% band, but long Ukrainian table blocks were flagged |
| `inject_activity_ids` | PASS | all 10 injected ids resolve |
| `activity_types` | PASS | A1 types accepted: `match-up`, `quiz`, `fill-in`, `order`, `true-false`, `unjumble`, `odd-one-out`, `fill-in`, `error-correction`, `translate` |
| `ai_slop_clean` | PASS | no banlist hits |
| `component_props` | PASS | no missing required props |
| `russianisms_clean` | PASS | no hits |
| `surzhyk_clean` | PASS | no hits |
| `calques_clean` | PASS | no hits |
| `paronym_clean` | PASS | no hits |
| `mdx_render` | SKIPPED | publish stage was not reached |

The `vesum_verified` failure was not the environment-regression message
`VESUM database not found`; the real VESUM gate ran and found content errors.

## LLM QG

Per-dimension Codex LLM QG was not run. The brief requires fail-fast on a RED
Python content gate, and this build had RED deterministic gates before the LLM
review stage.

Aggregate LLM verdict: not computed.

## Anti-Meta-Narration Assessment

The exact forbidden phrase scan found no literal hits for the listed strings
such as "Welcome to the start of our journey", "In this section we will learn",
"Before we move on", "Note that", "Observe how", "Pay attention to", "Remember
that", "It is important to", "Let's", "We will", or "You should now".

However, Gemini still produced visible English meta-narration and instructional
framing that violates the broader round-3.5 directive:

- "Notice how reflexive verbs like **прокидатися** (to wake up) are used
  alongside non-reflexive verbs like **гуляти** (to walk/hang out) to build a
  complete picture of the day."
- "Understanding this gap between spelling and sound is essential for listening
  comprehension and for speaking clearly during your daily interactions."
- "As a final self-check, try to narrate your morning routine out loud."

The prompt reduced exact forbidden-phrase reuse, but it did not eliminate the
teacher-facing English framing style.

## Pipeline Issues Surfaced

- The delegated worktree did not contain `.venv/`; a local ignored symlink to
  the main checkout venv was created so commands could use `.venv/bin/python`
  with Python 3.12.8.
- Local Qdrant on `127.0.0.1:6334` was not running. The knowledge-packet builder
  degraded by logging RAG connection failures and producing a packet with plan
  references but no retrieved textbook excerpts.
- The first Gemini response satisfied fenced-block structure but not the
  activity JSON schema, requiring the one allowed corrective redispatch.
- The successful redispatch still missed core content gates: minimum word count,
  per-section budget, VESUM cleanliness, and immersion long-sentence shape.

## Decision

Round 3.5 = round-4 bakeoff trigger.

Diagnostic signal: round 3.5 can now recover from one strict-schema failure,
but a fresh live Gemini build still fails deterministic content QG and retains
English meta-narration adjacent to the newly forbidden phrase class. The output
is not canonical for Phase 5 fan-out.

## Cross-agent adversarial review (added by orchestrator)

Per #0H discipline, parallel adversarial review on PR #1621 by
Gemini-3.1-pro-preview and Codex-gpt-5.5. Both reviewers agreed on the
"round-4 bakeoff trigger" verdict. Three significant findings supplement
the dispatch report:

### Tool-noise findings (gate bugs, NOT writer failures)

1. **`vesum_verified` false positives.** Gemini-reviewer correctly
   identified that `вмиваєця`, `одягаєся` are intentional `errorWord`
   values inside the `error-correction` activity (`a1-020-act9`), not
   bad orthography. The Python QG should skip `errorWord`/`error`
   fields when running VESUM verification. **Filed as separate issue.**

2. **`groups` whitelist false positive.** The Attempt-1 parser
   rejection of `groups` was wrong: `groups` IS a legitimate field
   for the `group-sort` activity type per `docs/lesson-schema.yaml`
   and `scripts/yaml_activities.py`. The strict-extras gate's
   `optional_item_fields` whitelist is global, not per-activity-type,
   so it cannot accept `groups` only for `group-sort`. The corrective
   redispatch was forced by a whitelist bug, not a real schema
   violation. Codex-reviewer recommends per-type extra-field
   validation rather than simply whitelisting `groups` globally.
   **Filed as separate issue.**

### Writer-discipline findings (genuine round-4 bakeoff signal)

3. **Meta-narration is more pervasive than dispatch reported.** This
   exemplar report quotes 3 violations; cross-agent review surfaced
   6+ distinct violations:

   - "Notice how reflexive verbs like **прокидатися** (to wake up)
     are used alongside non-reflexive verbs..."  *(line 19)*
   - "On the weekend, the rhythm of the morning changes
     significantly. The second dialogue highlights the contrast
     between..."  *(line 19, broader narrative-essay register)*
   - "One of the most important aspects of these verbs is their
     pronunciation. Ukrainian phonetics dictates that certain letter
     combinations transform when spoken..."  *(line 52)*
   - "This is a crucial rule for achieving a natural-sounding
     accent."  *(line 52)*
   - "Understanding this gap between spelling and sound is essential
     for listening comprehension..."  *(line 59)*
   - "Without these connectors, a description would simply be a
     disjointed list of verbs. With them, you can share a coherent
     experience."  *(line 111)*
   - "As a final self-check, try to narrate your morning routine out
     loud... will make your Ukrainian sound much more advanced and
     fluid."  *(line 119)*

   The forbidden-phrase blacklist catches *literal* patterns; Gemini's
   meta-narration manifests as full paragraphs that none of the
   explicit phrases match. **Persona-erasure framing is the round-4
   recommendation** (per Gemini-reviewer): replace the negative list
   with a positive "Zero Meta-Narration" constraint such as "Prohibit
   addressing the reader or commenting on the lesson content."

4. **JSX prop-stuffing.** Gemini routed dialogues through
   `<DialogueBox>` JSX with `translation` props baked in (`module.md`
   lines 7–29), bypassing the immersion gate's expectation of
   markdown-blockquote dialogues. The Codex round-3 hand-draft used
   plain blockquotes; Gemini's structural shift may game prose/
   immersion checks via JSX nesting.

### Disposition

- Codex-reviewer flagged a HIGH-severity blocker on the original PR:
  *"Merging failed, nonpublishable curriculum artifacts would
  overwrite canonical module files."* Acted on:
  - `curriculum/l2-uk-en/a1/my-morning/{module.md, activities.yaml,
    vocabulary.yaml, resources.yaml}` restored to round-3 baseline
    (`c91ae3bbe1` from #1594) on this branch.
  - Failed Gemini outputs preserved at
    `experiments/phase-4/round-3.5/` for evidence with a README
    explaining the round-4 bakeoff context.
- Round-4 bakeoff brief, Qdrant infra fragility, VESUM gate
  error-correction skip, and per-type extra-field validation will
  each be filed as separate follow-up issues.
