# Pass-2-only contract test — 2026-05-13

## Verdict

**YELLOW — anchors preserved BUT immersion outside band.**

The Pass 2 module preserved all Pass 1 anchor content byte-identical, so the
anchor contract is enforceable by deterministic hashing. It did not hit the
18-22% immersion target and exceeded the 24% hard cap. The run also exposed a
separate V7 schema failure in `activities.yaml`, so a full two-pass
`a1/my-morning` bakeoff is not justified until the Pass 2 prompt is tuned.

## Pass 1 stripped artifact

Command:

```bash
.venv/bin/python scripts/strip_for_pass1.py --module audit/bakeoff-2026-05-13-midday/claude/module.md --vocabulary audit/bakeoff-2026-05-13-midday/claude/vocabulary.yaml --output audit/twopass-pass2-only-2026-05-13/pass1_stripped.md --anchors-json audit/twopass-pass2-only-2026-05-13/pass1_anchors.json
```

Output:

```text
anchor_count=74
pass1=audit/twopass-pass2-only-2026-05-13/pass1_stripped.md
anchors_json=audit/twopass-pass2-only-2026-05-13/pass1_anchors.json
```

Stats:

```text
531 audit/twopass-pass2-only-2026-05-13/pass1_stripped.md
```

Hash:

```text
d5fb52760d8dca4c9f7f21453ace0f628a118da95217ac29cf2b76f3c68e1c8e  audit/twopass-pass2-only-2026-05-13/pass1_stripped.md
```

## Pass 2 LLM call

One Claude adapter invocation was made via
`audit/twopass-pass2-only-2026-05-13/run_pass2.py`. The call completed and
captured raw output in `pass2_output/writer_output.raw.md`.

Metadata:

```json
{
  "duration_s": 77.706,
  "tokens": null,
  "input_chars": 20318,
  "output_chars": 14253,
  "model": "claude-opus-4-7",
  "cli_version": "2.1.139"
}
```

Token counts and cost were not exposed by the CLI for this call
(`"tokens": null`), so exact dollar cost is unavailable from deterministic
metadata.

Strict V7 parse result:

```text
activities.yaml schema validation failed: item 1 has unexpected fields ['questions']; allowed: ['id', 'instruction', 'items', 'notes', 'title', 'type']
```

The raw fenced artifacts were extracted unchanged for inspection and for the
module-only anchor/immersion gates.

## Anchor preservation

Command:

```bash
.venv/bin/python audit/twopass-pass2-only-2026-05-13/check_anchors.py --anchors-json audit/twopass-pass2-only-2026-05-13/pass1_anchors.json --module audit/twopass-pass2-only-2026-05-13/pass2_output/module.md --json-out audit/twopass-pass2-only-2026-05-13/anchor_check.json
```

Output:

```json
{
  "passed": true,
  "expected_count": 74,
  "actual_count": 74,
  "missing": [],
  "extra": [],
  "mismatches": []
}
```

The literal brief-suggested `grep -A 200` diff was also run and saved to
`anchor_grep_diff.txt`. It is non-empty because the command compares all
English scaffolding after the first anchor, while the contract allows English
around anchors. The deterministic hash gate above compares each marker plus
its immediately following content line and is the isolation gate for anchor
preservation.

Saved diff size:

```text
346 audit/twopass-pass2-only-2026-05-13/anchor_grep_diff.txt
```

## Immersion

Command:

```bash
.venv/bin/python audit/twopass-pass2-only-2026-05-13/check_immersion.py --module audit/twopass-pass2-only-2026-05-13/pass2_output/module.md --json-out audit/twopass-pass2-only-2026-05-13/immersion_check.json
```

Output:

```json
{
  "passed": false,
  "pct": 32.03,
  "min_pct": 15,
  "max_pct": 35,
  "policy": "a1-m15-24",
  "long_ukrainian_sentences": [
    "Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними: навчатися, закохатися",
    "Сучасний дієслівний суфікс -ся(-сь) — це давня коротка форма зворотного займенника себе в Зн",
    "Уживається -ся(-сь) після інфінітивного суфікса -ти(-ть) або закінчення в особових формах дієслова: вмивати — вмиватися, взувати — взуватися"
  ],
  "experiment_target_min_pct": 18,
  "experiment_target_max_pct": 22,
  "experiment_cap_pct": 24,
  "experiment_passed": false,
  "experiment_cap_passed": false
}
```

Pass 2 module word count:

```text
1079 audit/twopass-pass2-only-2026-05-13/pass2_output/module.md
```

## Tests

Command:

```bash
.venv/bin/python -m pytest tests/test_twopass_check_anchors.py -q
```

Output:

```text
tests/test_twopass_check_anchors.py ..                                   [100%]
============================== 2 passed in 0.04s ===============================
```

## Conclusion

The experiment should not advance to a full two-pass `a1/my-morning` bakeoff
yet. The anchor-preservation mechanism works, but the Pass 2 prompt needs
tuning to reduce Ukrainian token share below the cap and to keep JSON artifact
schemas compatible with the V7 parser.

Follow-up issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1914
