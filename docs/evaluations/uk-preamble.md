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
must equal `text[start:end]` and start and end on scoring-token boundaries
(below); a non-empty span must hold a token. A set is refused when seeded errors
overlap each other or a protected span, or when an accepted form tokenises to
its error's own tokens (for example an apostrophe variant). `run`
refuses a plan below Protocol v2 (60 errors, 40 protected spans, writing at A2,
B1, B2 and C1, three repeats, both task kinds) unless `--smoke` is given; a
smoke plan is reported as incomplete and never authorises adoption.

## Converting the v2 set

The frozen set was built as JSON Lines (one item per line). `convert-set`
re-labels it as the harness set object; nothing is normalised or repaired.

```bash
.venv/bin/python -m scripts.eval.uk_preamble convert-set --input PRIVATE/set-v2.jsonl \
    --output PRIVATE/set-v1.json --set-id uk-preamble-v1
```

- Errors become `<item id>-e<n>` (source order) with `error_type` from the fixed
  mapping (`lexical_calque` maps to `other`), `accepted` from `corrections` and
  `origin` kept; `correct_spans` become protected spans `<item id>-p<n>` with
  `kind` set to the source `stratum`. `start`, `end`, `span` and `text` are
  copied verbatim. Source `level`, `subtype`, `stratum` on errors, `evidence` and
  `why_tricky` have no harness field and are dropped.
- The harness writing task has no topic, genre or register field, so those are
  appended to the task in one short sentence (`Тема: …; жанр: …; регістр: ….`);
  they are part of each task in the frozen set and every variant sees the same
  instruction. A metadata field that is absent or blank is skipped. `length_words`
  gives `min_words`/`max_words`.
- An unknown error type, a missing field, a malformed line, an empty `task`, a
  topic, genre or register that is present but not text, or a protection
  `stratum` that is not a short label (letters, digits, `_`, `.`, `-`) is refused
  with its line number, item id and rule (never text); nothing is written.
- The output must resolve outside every Git work tree (the `--results` check)
  and differ from the input. It is written owner-only (`0600`).
- The written file then goes through `load_set`, `review_geometry` and the
  Protocol v2 minimums. The JSON report on stdout holds counts per error type
  and protection kind, each validation problem as item id plus rule, Protocol v2
  shortfalls, and the SHA-256 of the input and the output.
- Exit codes: 0 valid; 1 written but invalid (`"valid": false`); 2 usage error or
  refused input.

## Execution

- The harness renders the complete prompt the worker receives: the rules core
  block delegate would prepend, then the preamble when present, then the task's
  fixed instructions, schema and input. Variants of one task kind differ only
  in the preamble.
- Every task goes through `scripts/delegate.py dispatch --mode read-only
  --language-lane --rules-seat core --cwd <worker cwd>`, without `--worktree`,
  `--lifecycle-file` or `--research-*` flags. Research pointers are
  deliberately not requested: they are resolved per dispatch from a changing
  registry and would add context outside the hashed prompt.
- Delegate still wraps the prompt. When the worker cwd lies in a registered
  Git worktree (the default cwd is this checkout, which is one when the
  harness runs from a dispatch worktree), delegate adds its worktree block
  (paths, interpreter, sparse-checkout note, test scope) and then the rules
  core again in front of it, and applies its sparse checkout to that
  worktree. The sparse-checkout note depends on paths the prompt names. The
  harness computes this composition with delegate's own functions, without
  spawning anything: the effective prompt, its prompt blocks, the recorded
  cwd and the worktree path for every prompt.
- `run` freezes the frame delegate puts around the prompts (cwd, worktree
  path, prompt blocks and the hashes of the text before and after the
  prompt) in `manifest.json`. A plan whose prompts would be framed
  differently is refused before anything is dispatched, for example a
  preamble naming `curriculum/`, because its arm would then differ in more
  than the preamble. A task whose frame has changed since the freeze is not
  dispatched, and a resumed run whose frame changed is refused.
- An answer is accepted only when the task record shows the planned agent and
  model, no substitution, the rendered prompt as source prompt, delegate's
  expected composition of it (effective prompt hash, prompt blocks, cwd and
  worktree path), no research context, read-only mode and the
  `dispatch_args_sha256` of the arguments the harness built; and when the
  worker checkout's fingerprint (commit, tracked changes, instruction and
  tool-configuration files) is the same at dispatch and at collection.
- Paired arms (same seat, repeat, kind and chunk) must also share every
  recorded condition (CLI version, effort, harness, resolved model, cwd,
  worktree, prompt blocks, worker checkout), the frozen frame, and prompts
  that differ only by the frozen preamble; `score` records every pair and why
  it is invalid.
- Resume: accepted tasks are never re-run; a dispatched task with a pending
  marker is waited on, not re-dispatched; a task found without its marker is
  collected but not accepted (its dispatch-time checkout is unknown); failed or
  unaccepted tasks are re-dispatched only with `--retry-failed`. The complete
  plan (set, variants, templates, rules core, seats, repeats, kinds, item ids,
  chunking, run tag, worker cwd, delegate's frame, protocol shortfalls, scoring
  version) is frozen in
  `manifest.json`; a resumed run with any different term is refused, and
  `score` and `report` read the plan from the manifest.

## Scoring

### Review scoring contract (`uk-preamble-scoring/2`)

Frozen by the designated decision of 2026-10-03 on #9623 (an alternative by
`gpt-6.1-sol`, approved with amendments by `claude-opus-5-5`). Implemented in
`scripts/eval/uk_preamble/scoring.py`; the set checks are in `dataset.py`.

- **Evidence.** Only the answer's `corrected_text` is scored. Its `corrections`
  are claims: they never create, split or merge a counted unit, so every
  schema-valid claim list (empty, combined, partitioned, irrelevant, unapplied
  or unanchorable) gives the same primary counts.
- **Tokens.** NFC; apostrophe variants folded to `'`, U+2010 and U+2011 to `-`,
  `…` to `...`; U+00AD, U+200B–U+200D, U+2060 and U+FEFF deleted. A word is a
  run of letters, digits and combining marks (U+0300–U+036F, so a stress mark
  stays part of its word) joined internally by `'` or `-`; two or more full
  stops are one token; every other non-space character is its own token.
  Whitespace is never a token, so whitespace-only edits are invisible.
  Comparison is case-sensitive. Dashes (U+2013, U+2014) and quote marks are not
  folded: hyphen and dash are distinct in the norm (Правопис 2019, § 35, item 6.3,
  note: `три-чотири` but `3 — 4 дні`).
  Joining or splitting words is a real change (`не має` → `немає` counts two).
- **Alignment.** One alignment of the original's tokens to the corrected
  text's tokens, computed without seeds, protected spans or claims. Cost is
  lexicographic: first token edits (delete, insert, substitute one each), then
  character edits (Levenshtein distance for a substitution, the token's length
  for a deletion or insertion). Among minimum-cost alignments, forward
  reconstruction takes the first admissible operation in the order equal,
  delete, insert, substitute. `difflib` is not used.
- **Hits.** Seeds with no correct token between them form a cluster; its window
  runs between the nearest correct tokens aligned as unchanged on either side.
  When the corrected window equals the original window with every seed in it
  given an accepted form or left as it was, the seeds that take an accepted form
  in every such assignment are hits, and nothing else in that window counts.
  Otherwise a seed is a hit when its slice (target tokens aligned to it plus
  insertions strictly inside it; for an empty seed, the insertions at its point)
  equals an accepted form, trying no edge insertion, then the left one, the
  right one, then both. Seeds try their edges in source order, so an insertion
  one seed's match uses is not available to the next seed.
  A seed changed but not hit is a wrong correction. A wrong correction is a
  miss, never a false alarm, for a seed's own tokens and the insertions
  strictly inside it. An insertion at a seed's edge, including between two
  seeds, is collateral unless an accepted form needs it.
  No alignment or assignment is chosen to maximise hits.
- **False alarms (primary units).** Each protected span affected once (a token
  changed or an insertion strictly inside it); each changed correct token
  outside protected spans once; each other insertion site once. An insertion at
  a protected span's edge is an ordinary insertion site. The rule's false-alarm
  rate is all false alarms per 100 protected spans.
- **Logging diagnostics, outside adoption.** Changed units some claim covers;
  claims applied (the corrected text realises the claimed replacement over the
  claimed tokens, so overlap alone never counts), unapplied, no-op and
  unanchorable; protected spans an unapplied claim accuses that stay unchanged;
  tokens inserted at false-alarm sites (a site counts once however long the
  insertion). None of these enters the adoption rule.
- **Documented residual.** When equal-cost alignments attribute a repeated
  token differently, the tie order decides. For `p A x A q` → `p B A q` with the
  seed on the first `A`, the seed counts as a miss and `x` as a changed token,
  although the writer may have meant the opposite. Oracle case C8b pins this.
- **Known edge cases** (designated decision 2026-10-03 (2) on #9623).
  - An unused inserted word that would complete a correct fix next to a wrong
    one counts as one false alarm. For `p badfirst badsecond q`, where the
    second seed's accepted form is `до goodsecond`, the output
    `p worsefirst до worsesecond q` scores the `до` as collateral, as the
    single-seed edge rule does for `x worse extra y`.
  - Text fused into a seed's own token (`goodoneextra`) counts as a wrong
    correction, not a false alarm: it lies in the seed's own span and costs the
    hit.
- Style suggestions are tallied separately (total, on protected spans, on
  error spans) and never count as hits or false alarms. VESUM-invalid forms the
  corrected text introduces are reported.
- A failed item (no answer, malformed JSON, schema violation, task not run or
  not accepted) stays in the denominator with all its errors missed.

The worked oracle cases (R1–R3, C5–C10 of the decision, and the adjacent-seed
cases of decision (2)) are tests with literal
expected counts in `tests/eval/test_uk_preamble_scoring_contract.py`, with a
seeded exhaustive check that every schema-valid claim list scores identically.

**Version rule.** The scoring version is frozen in `manifest.json`. `run`
(resume), `score` and `report` refuse a results directory frozen under another
scoring version, including manifests written before scoring was versioned
(`uk-preamble-scoring/1`, the per-correction diffing): results are never
compared across scoring versions. The contract changed before any evaluation
was paid for: no adoption-run result exists under version 1, so the change
cannot have been tuned to a viewed result. No adoption-run result exists under
version 2 either, including the rule for insertions between adjacent seeds
(designated decision 2026-10-03 (2)); if one is viewed before a further
contract change, that change must bump the version.

### Writing and judging

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
frozen in the manifest by the first `score --judge`, before any pair is judged
or excluded, even when every pair is excluded; a later call with different
terms is refused. Judge tasks are attested against delegate's composition of
their own prompts. Judge outputs are stored like any other task.

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
