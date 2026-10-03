# Ukrainian preamble comparison harness (#9623)

Measures whether a Ukrainian-language system preamble improves the Ukrainian
reviewed and written by each seat (`gemini-3.8-flash-high` via AGY,
`gpt-6.1-sol`, `claude-opus-5-5`). The binding protocol is the "Protocol v2"
comment on #9623; this page documents how the harness implements it.

The harness is public. The evaluation set, the preamble texts and every result
file are private inputs and outputs passed by path. Never commit them, and never
paste set items or preamble text into issues or PRs.

## Commands

```bash
# 1. Validate every dispatch without spawning workers (writes prompts only).
.venv/bin/python -m scripts.eval.uk_preamble run --set PRIVATE/set.json --results PRIVATE/results \
    --variant none --variant original=PRIVATE/original.md --variant adapted-v2=PRIVATE/adapted-v2.md --dry-run
# 2. The 27 cells: 3 seats x 3 variants x 3 repeats. Re-running resumes.
.venv/bin/python -m scripts.eval.uk_preamble run ...same flags without --dry-run...
# 3. Deterministic scoring plus the blind cross-family judges.
.venv/bin/python -m scripts.eval.uk_preamble score --results PRIVATE/results --judge
# 4. Paired differences, bootstrap CIs, adoption rule.
.venv/bin/python -m scripts.eval.uk_preamble report --results PRIVATE/results
```

`--help` on each subcommand lists every flag.

## Set format

One JSON object (see the `dataset.py` docstring): `review` paragraphs with
seeded `errors` (offsets, exact `span`, `error_type` from the fixed label list,
`accepted` corrections) and `protected` correct-but-tricky spans; `writing`
tasks with a CEFR `level`, an `instruction` and an optional word range. Spans
must equal `text[start:end]`; errors and protected spans may not overlap. `run`
refuses a set below the Protocol v2 minimums (60 errors, 40 protected spans,
writing at A2, B1, B2 and C1) unless `--allow-undersized-set` is given for a
smoke run.

## Execution

- Every task goes through `scripts/delegate.py dispatch --mode read-only
  --language-lane` with the Ukrainian review or authoring task family, so the
  task record attests the launched agent, model, any substitution, and the
  digest of the exact prompt. An answer is accepted only when the record shows
  the planned seat, no substitution, and the planned prompt digest.
- Variants of one task kind share byte-identical instructions, output schema
  and input block; the preamble, when present, is placed first. Tool access is
  whatever the delegate gives the seat, identical across variants.
- Resume: accepted tasks are never re-run; a dispatched task without a stored
  outcome is waited on, not re-dispatched; failed or unattributable tasks are
  kept as failures and re-dispatched only with `--retry-failed`. Set, preamble,
  template and chunking hashes are frozen in `manifest.json`, and a resumed run
  with different terms is refused.

## Scoring

Review, per seeded error and per correction:

- A correction is anchored by its offsets when they match its span, otherwise
  by relocating the span; an unanchorable correction is an unsupported
  accusation (a false alarm). Only the changed part of a correction counts as
  its edit, so quoting extra context is harmless.
- A hit needs an edit that reaches the error span and a result equal to the
  original with one of the error's accepted corrections, normalised for
  whitespace and apostrophe variants. Several errors fixed by one edit are all
  hits; a wrong fix on an error span is a miss, counted as a wrong correction.
- A false alarm is an edit on correct text, any edit that changes a protected
  span (including inside paragraphs with errors), or an unanchored correction.
  The rule's false-alarm rate is all false alarms per 100 protected spans.
- Style suggestions are tallied separately (total, on protected spans, on
  error spans) and never count as hits or false alarms.
- Also reported: edits in `corrected_text` that no listed correction explains,
  and VESUM-invalid forms that the corrected text introduces.
- A failed item (no answer, malformed JSON, schema violation, overlapping
  corrections, unattributable task, task not run) stays in the denominator
  with all its errors missed.

Writing, per text, through the local `sources` tool implementations:
calque density (verdict-tier `check_text` Russian-shadow and multi-token UA-GEC
calque occurrences per 100 tokens; `check_text` suspicions are reported
separately and not ruled on), VESUM-invalid forms, CEFR level adherence (share
of PULS-known words at or below the task level), English intrusion (Latin-script
words), and the word range. The Антоненко-Давидович evidence enters through the
curated calque list behind `check_text`; the style-guide index itself is
essay-form and is not matched directly.

Judging: each pair of variants of one candidate seat is judged blind by the two
seats of the other families, with A/B order randomised per judge and
comparison, a fixed four-criterion rubric, and an explicit instruction not to
reward length. Judge outputs are stored like any other task.

## Report and adoption rule

The pairing unit is the set item. Each item's value is its mean over repeats;
the bootstrap resamples items (10,000 draws, percentile 95% interval). Per seat,
`adapted-v2` (else `original`) is adopted only when:

1. the seeded-error recall difference has a 95% CI with lower bound above zero;
2. the false-alarm rate rises by at most 2 per 100 protected spans (point
   estimate);
3. writing calque density does not rise (point estimate at most zero), and no
   writing answer of either variant failed.

Anything else, including an inconclusive result, is "no change" for that seat.
