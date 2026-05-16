# H2c Typed Russianism Calibration Set

40 cases (32 dirty + 8 clean lures) spanning 4 russianism types:
morphological / lexical / phraseological / register.

Authored 2026-05-17 in response to H1 falsification finding
(audit/2026-05-17-judge-calibration-h1/COMPARISON.md): the existing
12-case set (origin/pr-2006:eval/russianism/calibration-cases.jsonl) is
dominated by lexical/phraseological cases that the morphology + style-guide
evidence channels structurally can't anchor.

H2c balances the type buckets to reveal per-channel coverage gaps:
which evidence channel each russianism type actually needs.

## Schema

```json
{
  "prompt_id": "cal_<bucket>_<short_id>",
  "model": "GOLD",
  "status": "ok",
  "output_text": "<2-4 sentences of realistic Ukrainian prose>",
  "gold": {
    "expected_clean": true|false,
    "expected_flags": [
      {
        "phrase": "<exact substring of output_text>",
        "correct": "<canonical Ukrainian alternative>",
        "severity": 1|2|3,
        "type": "<one of the 4 types>"
      }
    ],
    "rationale": "<1-2 sentences explaining the call>",
    "source": "<Antonenko / Pravopys §N / Karavansky chapter X / ESUM vol Y / UA-GEC / Textbook>"
  }
}
```

## Type Definitions

- **morphological**: Surface form errors (case, gender, preposition government, verb aspect).
- **lexical**: Single-word Russian loans that are morphologically valid Ukrainian but lexically incorrect.
- **phraseological**: Multi-word fixed expressions that are literal Russian calques.
- **register/stylistic**: Grammatically correct and lexically valid, but Russian-flavored collocations or preferences.

## Per-type test plan

After this lands, run baseline + H1 prompts against this set:

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --out-dir audit/2026-05-17-judge-calibration-h2c-baseline \
  --families anthropic,openai,google,xai \
  --models claude-opus-4-7,gpt-5.5,gemini-3.1-pro-preview,grok-4.3 \
  --harnesses native_cli \
  --efforts high \
  --mcp-states with_mcp \
  --cases-file eval/russianism/calibration-cases-h2c.jsonl
```

(Note: The `--cases-file` flag support must be verified/added to `judge_calibration_matrix.py` in a follow-up task.)
