# Ukrainian preamble comparison harness (#9623)

Measures whether a Ukrainian-language system preamble improves the Ukrainian
reviewed and written by each seat (`gemini-3.8-flash-high` via AGY,
`gpt-6.1-sol`, `claude-opus-5-5`). The binding protocol is the "Protocol v2"
comment on #9623; this page documents how the harness implements it.

The harness is public. The evaluation set, the preamble texts and every result
file are private inputs and outputs passed by path. Never commit them, and never
paste set items or preamble text into issues or PRs. `--results` must resolve,
symlinks followed, outside every Git work tree, and `--run-tag` is limited to
lowercase letters, digits and `-`; both are checked before anything is written,
and every output path is checked to stay inside the results directory.

## Commands

```bash
# 1. Validate every dispatch without spawning workers (writes prompts only).
.venv/bin/python -m scripts.eval.uk_preamble run --set PRIVATE/set.json --results PRIVATE/results \
    --variant none --variant original=PRIVATE/original.md --variant adapted-v2=PRIVATE/adapted-v2.md --dry-run
# 2. The 27 cells: 3 seats x 3 variants x 3 repeats. Re-running resumes.
#    Run from a pinned checkout: the rules core and the worker checkout are part of the frozen conditions.
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
refuses a plan below Protocol v2 (60 errors, 40 protected spans, writing at A2,
B1, B2 and C1, three repeats, both task kinds) unless `--smoke` is given; a
smoke plan is reported as incomplete and never authorises adoption.

## Execution

- The harness renders the complete prompt the worker receives: the rules core
  block delegate would prepend, then the preamble when present, then the task's
  fixed instructions, schema and input. Variants of one task kind differ only
  in the preamble.
- Every task goes through `scripts/delegate.py dispatch --mode read-only
  --language-lane --rules-seat core --cwd <worker cwd>`, without `--worktree`,
  `--lifecycle-file` or `--research-*` flags, so delegate appends nothing.
  Research pointers are deliberately not requested: they are resolved per
  dispatch from a changing registry and would add context outside the hashed
  prompt.
- An answer is accepted only when the task record shows the planned agent and
  model, no substitution, the rendered prompt as both source and effective
  prompt, no appended blocks, no research context, read-only mode, the frozen
  cwd, and the `dispatch_args_sha256` of the arguments the harness built; and
  when the worker checkout's fingerprint (commit, tracked changes, instruction
  and tool-configuration files) is the same at dispatch and at collection.
- Paired arms (same seat, repeat, kind and chunk) must also share every
  recorded condition (CLI version, effort, harness, resolved model, cwd, worker
  checkout) and prompts that differ only by the frozen preamble; `score`
  records every pair and why it is invalid.
- Resume: accepted tasks are never re-run; a dispatched task with a pending
  marker is waited on, not re-dispatched; a task found without its marker is
  collected but not accepted (its dispatch-time checkout is unknown); failed or
  unaccepted tasks are re-dispatched only with `--retry-failed`. The complete
  plan (set, variants, templates, rules core, seats, repeats, kinds, item ids,
  chunking, run tag, worker cwd, protocol shortfalls) is frozen in
  `manifest.json`; a resumed run with any different term is refused, and
  `score` and `report` read the plan from the manifest.

## Scoring

Review, from the answer's `corrected_text` (the evidence) and its
`corrections` (the claims):

- Changes are the token-level difference between the original and
  `corrected_text` (words, punctuation marks, whitespace; apostrophe variants
  and whitespace amounts compare equal; whitespace-only changes ignored). They
  depend only on the two texts, never on how corrections were grouped.
- A seeded error is a hit when `corrected_text` realises one of its accepted
  corrections. A logged correction that `corrected_text` does not apply is not
  a hit; an unlogged change counts like a logged one. A remaining difference on
  an error span is a wrong correction (a miss).
- False alarms are counted in packaging-independent units: each protected span
  changed or accused (including inside paragraphs with errors), and each other
  correct word or insertion point changed or accused, collateral changes
  included. An accusation is a logged correction's own token difference, so
  quoted unchanged context is never accused. Corrections that cannot be
  anchored are unsupported accusations, one each. The rule's false-alarm rate
  is all false alarms per 100 protected spans.
- Style suggestions are tallied separately (total, on protected spans, on
  error spans) and never count as hits or false alarms.
- Also reported: changed units no correction claims (unlogged), claimed units
  `corrected_text` does not change (unapplied), and VESUM-invalid forms that
  the corrected text introduces.
- A failed item (no answer, malformed JSON, schema violation, task not run or
  not accepted) stays in the denominator with all its errors missed.

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
comparison and a fixed four-criterion rubric. Length is controlled, not only
instructed: a pair is sent to the judges only when the shorter text has at
least `--judge-length-ratio` (default 0.8) of the longer text's words; pairs
outside the bound, or missing a text, are recorded with their word counts as
exclusions and reported. The word counts of every judged pair are stored with
its verdict. The seed, chunking, length bound and rules core of the judges are
frozen in the manifest at first use. Judge outputs are stored like any other
task.

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

The denominator is the frozen plan, never what happens to be in `scores.json`
(`report` refuses scores computed from another plan). A comparison is
incomplete, and cannot adopt, when the plan is a smoke plan, when any planned
answer of either variant is missing, duplicated or unplanned, when any planned
task was not run or not accepted, or when any paired cell is invalid.
