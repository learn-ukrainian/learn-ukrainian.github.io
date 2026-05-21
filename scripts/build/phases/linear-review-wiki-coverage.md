{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 5 Linear Wiki-Coverage Goodhart Sentinel Prompt

Review only wiki-obligation coverage. This pass is parallel to the five
standard QG dimensions; it is not a `QG_DIMS` dimension.

The deterministic gate has already checked objective presence. Your job is to
verify semantic adequacy after that gate passes: each obligation must be woven
into substantive prose, dialogue, or activity work, not keyword-stuffed into the
claimed artifact location merely to satisfy deterministic coverage.

## Required Method

For every obligation in the Wiki Obligations Manifest:

1. Read the manifest obligation id, obligation type, required treatment, and
   source-line metadata.
2. Read the writer's implementation_map claim for that same obligation id.
3. Inspect the cited artifact and location in Generated Content.
4. Emit one verdict:
   - PASS: the cited evidence implements the obligation as substantive
     pedagogy — the manifest claim is woven into prose/dialogue/activity with
     explanation, example use, or integrated context.
   - KEYWORD_STUFFING: the cited evidence contains the required string verbatim
     but the surrounding prose does not actually teach, contrast, or apply it.
     Example failure: a contrast_pair where the "incorrect" and "correct" forms
     appear in a list with no learner activity around them; a phonetic_rule
     where the written→spoken mapping is named in a one-sentence aside with no
     example pair; a sequence_step where the section heading exists but the body
     skips to the next step. THIS VERDICT FAILS THE BUILD.
   - PARTIAL: evidence exists and shows some pedagogy, but is thin enough that
     the obligation is taught at a shallower level than the manifest target.
     Soft signal.
   - FAIL: missing, contradicted, or not in the claimed location.

Treatment-specific checks:

- `contrast_pair`:
  * PASS: both forms appear in an activity body AND the learner must distinguish
    them (multiple-choice, fill-in, correction exercise).
  * KEYWORD_STUFFING: both forms appear in a static list without an activity
    that requires distinguishing them; or both forms appear in a single example
    sentence with no learner-facing task.
- `prose_explanation`:
  * PASS: module.md prose names the manifest's `incorrect` and `correct`
    strings AND explains why one is preferred, with at least one substantive
    sentence of explanation beyond the bare contrast.
  * KEYWORD_STUFFING: the strings appear in a list/table/footnote without
    explanation prose; or the explanation is a generic "this is correct"
    without engaging the manifest's `why` field.
- `explicit_explanation` (phonetic):
  * PASS: learner-facing pronunciation guidance with at least one
    written→spoken example pair AND a brief contextual note (when does this rule
    apply, common confusable, etc.).
  * KEYWORD_STUFFING: a one-line "smooth speech" or "soft pronunciation"
    reminder without the actual rule mapping; or the rule is stated but no
    example pair is provided.
- `sequence_step`:
  * PASS: the module prose teaches the step's canonical pedagogical claim in
    the appropriate order, with the heading or marker AND body text that
    advances the learner toward the step's goal.
  * KEYWORD_STUFFING: the heading exists but the body skips ahead without
    teaching the step; or the step is named in a metadiscourse sentence ("we
    will now learn X") without actually teaching X.
- `decolonization_ban`:
  * PASS: the generated content avoids the banned framing AND, if the contrast
    is naturally adjacent (e.g. "Kyiv not Kiev"), offers a Ukrainian-centered
    framing.
  * KEYWORD_STUFFING: the banned framing is technically absent but a
    near-paraphrase remains; or a meta-disclaimer about avoiding the ban
    replaces the substance of the lesson.

Evidence MUST be a verbatim quote from the cited artifact location
(quote-marked). Paraphrase or summary evidence is invalid and forces
KEYWORD_STUFFING. Quotes must be at least 8 words long unless the obligation is
a single short word/phrase the manifest specifies — in which case quote the
full surrounding sentence containing it.

The new verdict enum: `PASS | KEYWORD_STUFFING | PARTIAL | FAIL`.
`overall_verdict` must be `FAIL` if any obligation verdict is `FAIL` OR
`KEYWORD_STUFFING`. `PARTIAL` is a soft signal — system aggregates, build
continues, but logs the pattern.

## Response Format — STRICT

Return ONLY a single JSON object. No preamble. No epilogue. No "I have
verified" narration. No markdown bold. No prose confirmation. The parser
calls `json.loads` on your response (with a fenced-block fallback) — any
prose outside the JSON shape will cause the build to fail at this phase
even when every obligation passes.

The JSON object MUST contain:

- `verdicts`: a list with one entry per obligation in the manifest. Each
  entry MUST have `obligation_id`, `verdict`, `evidence` (verbatim quote
  ≥8 chars containing `"…"` / `«…»` / `“…”`), and `rationale`.
- `overall_verdict`: `"PASS"`, `"PARTIAL"`, or `"FAIL"`. MUST be `"FAIL"`
  if any per-obligation verdict is `FAIL` or `KEYWORD_STUFFING`.
- `summary`: a single-sentence string (still inside the JSON object).

If every obligation passes, emit the all-PASS shape — STILL JSON, STILL no
narration:

```json
{
  "verdicts": [
    {
      "obligation_id": "err-1",
      "verdict": "PASS",
      "evidence": "\"Choose between я вибачаюся and я вибачаю себе, then explain which one fits the dialogue.\"",
      "rationale": "Activity body requires learners to distinguish both forms."
    }
  ],
  "overall_verdict": "PASS",
  "summary": "All 1 obligation woven into substantive pedagogy."
}
```

Mixed-verdict shape:

```json
{
  "verdicts": [
    {
      "obligation_id": "err-1",
      "verdict": "PASS",
      "evidence": "\"Choose between я вибачаюся and я вибачаю себе, then explain which one fits the dialogue.\"",
      "rationale": "The activity requires learners to distinguish both forms in context."
    },
    {
      "obligation_id": "phon-1",
      "verdict": "KEYWORD_STUFFING",
      "evidence": "\"Remember smooth speech for this phrase.\"",
      "rationale": "The quote names smooth speech but gives no written→spoken mapping or example pair."
    }
  ],
  "overall_verdict": "FAIL",
  "summary": "One obligation is keyword-stuffed rather than substantively taught."
}
```

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}

## Wiki Obligations Manifest

{WIKI_MANIFEST}

## Deterministic Wiki Coverage Gate

{WIKI_COVERAGE_GATE}

## Plan

```yaml
{PLAN_CONTENT}
```

## Generated Content

{GENERATED_CONTENT}
