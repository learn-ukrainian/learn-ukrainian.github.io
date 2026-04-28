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
