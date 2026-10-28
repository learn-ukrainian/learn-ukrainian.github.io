# Blind lesson-section A/B comparison of two writers

Scores two writers' Ukrainian lesson sections against each other, offline, from
outputs that were already generated. It answers "which writer's text is better
on these tasks, and how sure are we", not "is this text publishable". It reuses
the preamble harness (`scripts/eval/uk_preamble`, see
[uk-preamble.md](uk-preamble.md)) for writing metrics, judge dispatch and the
bootstrap, `scripts/verification/check_text.py` and `verify_stress` for stress,
and `scripts/eval/human_eval_tracker.py` for native-expert ratings.

Every result is labelled **exploratory: n tasks**. A handful of tasks can show a
direction; a broad model claim needs fresh held-out plans and native-expert
calibration.

## Command

```bash
# Mechanical checks only (no model calls); blind report.
.venv/bin/python -m scripts.eval.lesson_ab --manifest PRIVATE/manifest.json --results PRIVATE/results
# Render the judge prompts and preflight every dispatch without spawning anything.
.venv/bin/python -m scripts.eval.lesson_ab --manifest PRIVATE/manifest.json --results PRIVATE/results \
    --judge gemini-3.8-flash-high --judge claude-opus-5-5 --worker-cwd WORKTREE --dry-run
# Judge: every judge x every task x both orders. Re-running resumes; accepted judgements are never re-run.
.venv/bin/python -m scripts.eval.lesson_ab ...same flags without --dry-run...
# Unblind (and import native-expert ratings), scoring stored judgements without dispatching.
.venv/bin/python -m scripts.eval.lesson_ab --manifest PRIVATE/manifest.json --results PRIVATE/results \
    --judge gemini-3.8-flash-high --judge claude-opus-5-5 --no-dispatch \
    --key PRIVATE/key.json --human-ratings PRIVATE/human
```

`--help` lists every flag. `--results` must resolve outside every Git work tree.
It holds `frozen.json`, the judge `prompts/` and `raw/` records, `scores.json`,
and `report-blind.{md,json}` or `report-unblinded.{md,json}`. Exit 0 means
complete. Exit 1 means a judgement or mechanical check failed or was not run;
it is still in the report. Exit 2 means invalid input, inputs that changed
after the first run, or a judge in a writer's family.

## Inputs

The manifest is JSON. Relative paths resolve against the manifest's directory.

```json
{
  "evaluation_id": "terra-uk-1028",
  "writer_families": ["openai"],
  "key_sha256": "optional: SHA-256 of the key file, committed before judging",
  "provenance": "where the outputs came from",
  "tasks": [
    {"task_id": "a1-at-the-cafe", "plan_path": "plans/at-the-cafe.yaml",
     "prompt_path": "prompts/a1-at-the-cafe.md", "prompt_sha256": "…",
     "output_a": "blind/a1-at-the-cafe-A.md", "output_b": "blind/a1-at-the-cafe-B.md",
     "level": "optional CEFR override"}
  ]
}
```

- `prompt_sha256` must match the file at `prompt_path`, which is the exact
  prompt both writers received. The level comes from the plan's `level`,
  else its `cefr_min` (a seminar plan such as `level: BIO`), unless the
  manifest overrides it.
- `writer_families` names the writers' model families without saying which
  writer is A. Judges in those families are refused.
- The key is a separate file, read only at the final unblinding step:
  `{"writers": {"terra": "openai", "sol": "openai"}, "tasks": {"a1-at-the-cafe": {"A": "sol", "B": "terra"}, …}}`.
  When the manifest carries `key_sha256`, any other key file is refused. The
  report also flags key families that the manifest did not declare.
- **Provenance.** The outputs are imported. The harness did not run the
  writers, so it records each output's SHA-256 and the manifest's provenance
  note, and every text is marked `execution_attested: false`. Only judge runs
  carry dispatch attestation: the planned seat, the exact prompt bytes and the
  worker checkout.
- `frozen.json` fixes the manifest, every input digest, the judge template and
  the rules-core block on first use. Any later change is refused, so a new
  comparison needs a new `--results`.

## Mechanical checks (per text)

Stress marks are removed before the text checks. They are verified separately.

- **Writing metrics** (`uk_preamble` `LocalSources.writing_metrics`):
  - `vesum_invalid`: forms VESUM attests in no case;
  - verdict-tier `calque_hits` and `calque_suspicion_hits`;
  - `cefr_above_level` and `level_adherence` against the task level;
  - `english_intrusion`, the Latin-script word share (expected at A1, where
    English scaffolding is by design);
  - `words`, the length.
- **`vesum_capitalised`**: capitals that `check_text` does not license, such as
  a quoted example `«Можна карткою?»` in mid-sentence, where VESUM attests the
  lowercase form. These are counted separately from `vesum_invalid`.
- **Stress.** Each distinct marked word is checked with `verify_stress`:
  - *attested*: the marks equal a reading's positions, or a single mark sits on
    one position of a variant-stress reading;
  - *wrong*: readings exist and none matches; the attested forms are listed;
  - *unverified*: there is no trusted reading, for example a proper name.

  `stress_ambiguous_unresolved` is `check_text`'s stress check with the
  writer's marks as asserted readings. It counts the forms that are still
  ambiguous. `stress_mark_coverage` is marked words divided by polysyllabic
  words.

These are screening signals, not verdicts. A grammar fragment such as `-уч-` is
not a VESUM form, and a stress-oracle reading can need adjudication. The judges
and native experts decide.

## Judging

Each judge gets the frozen prompt (`scripts/eval/lesson_ab/judge.py`, hashed
into `frozen.json`). The prompt contains the writing prompt, the full plan
YAML, and the two texts labelled Text 1 and Text 2. Every judge sees every task
in both orders: A first (`AB`) and B first (`BA`).

**Criteria.** Each is scored 1–5:

- the preamble harness's naturalness, correctness, task_fit and level_fit;
- pedagogy;
- plan_fidelity, which includes a fact check of every claim against the plan.

**Errors.** Each error carries a quote, a correction, a kind and a severity:

- P0 teaches something wrong;
- P1 is a clear defect;
- P2 is minor.

**Score.** Each text gets a SCORE from 1 to 10, anchored on the errors:

- 10: no errors;
- 7–9: P2 errors only;
- 4–6: at least one P1;
- 1–3: a P0 or off-task.

The verdict is `preferred`: `1`, `2`, `tie` or `abstain`. Judges verify forms
with the Sources tools when their harness provides them, and report whether
they did in `sources_checked`.

Verdicts are mapped back to A/B and, at unblinding, to writers. Failed, unrun,
unparseable and abstaining judgements are kept and counted.

## Report

- **Per task:** each judgement (judge × order) is one vote. The side with more
  votes wins, equal votes are a tie, and failures and abstentions are shown but
  do not vote. Totals give wins, ties and losses, with an exact two-sided sign
  test on decided tasks.
- **Metrics:** per-task paired values for the two sides. Judge scores and
  criteria are means over valid judgements. Each metric shows the mean
  difference with a percentile bootstrap 95% CI over tasks.
- **Judges:**
  - per judge: failures, abstentions, position consistency (the same preference
    in both orders) and the Text 1 preference rate;
  - per pair: percent agreement and Cohen's kappa on the verdicts combined over
    both orders (an order flip counts as a tie), and the Pearson correlation of
    per-text scores.
- Before unblinding, sides are the blind labels A and B, which only mean
  something within one task. With `--key`, every statistic is writer against
  writer.

## Native-expert calibration slot

`--human-ratings DIR` reads YAML in the `human_eval_tracker` format
(`docs/eval/human-eval-rubric.md`, 0–10 per dimension). Each file rates one
blind text: `module.slug` is `<task id>-A` or `<task id>-B`, so the raters stay
blind. The report adds `human_score` per text, the paired human difference, and
the Pearson correlation between human and mean judge scores.
