# Russianism Eval

End-to-end evaluation pipeline for measuring Russianism prevalence in LLM
Ukrainian output, grounded in Антоненко-Давидович «Як ми говоримо».

## Contents

| File | Purpose |
|---|---|
| `prompts-v1.yaml` | 5 starter prompts engineered to elicit Russianisms (translation × 2, business email, medical message, social-media post). |
| `calibration-cases.jsonl` | 12 hand-labeled gold cases for scoring judge precision/recall. 5 clean, 6 dirty with known TP calques, 1 debatable, 1 lure (clean text using canonical alternatives to known calques — tests whether the judge invents Russianisms). |

## Pipeline

```
prompts-v1.yaml ─┐
                 ▼
   scripts/audit/russianism_eval.py  →  outputs.jsonl  (1 cell per (prompt, model))
                                          │
                                          ▼
   scripts/audit/russianism_judge.py  →  judgments-{tag}.jsonl  (one issue list per cell)
                                          │
                                          ▼
   scripts/audit/score_judge_calibration.py  →  per-judge P/R/F1 vs calibration gold
```

## Judge selection — recommendations from 2026-05-15 calibration study

Calibration across three judges on the 12-case gold set (sev1-tolerant
phrase F1):

| Judge | F1 | Precision | Recall | Case acc | Profile |
|---|---:|---:|---:|---:|---|
| `claude-opus-4-7` | **86%** | 79% | **94%** | **100%** | Thorough; defensible sev1 style FPs |
| `gemini-3.1-pro-preview` | 84% | 81% | 87% | 92% | High recall but **over-flags `Доброго дня!` + other clean greetings** |
| `gpt-5.5` | 78% | **90%** | 69% | 83% | Conservative; never false-flags clean text; misses some sev2-3 calques |

**Recommended for the curriculum Russianism review position:**

- **Primary reviewer: `claude-opus-4-7`** — best F1, 100% case-level accuracy
- **Second-opinion validator: `gpt-5.5`** — highest precision, near-zero clean-case FPs
- **Block rule:** sev≥2 flag from BOTH judges = block / require correction
- **Avoid `gemini-3.1-pro-preview` as primary** — greeting-FP pattern will produce noise on every dialogue/email module
- **`gemini-3-pro-preview` is unsuitable at any scale** — single judge calls regularly exceed 4-minute budget

Run the calibration set as a regression check whenever the judge model or
prompt changes:

```bash
# Generate judgments
.venv/bin/python scripts/audit/russianism_judge.py \
    --judge-family claude --judge-model claude-opus-4-7 \
    --inputs eval/russianism/calibration-cases.jsonl \
    --out /tmp/cal-judgments.jsonl

# Score against gold
.venv/bin/python scripts/audit/score_judge_calibration.py \
    --judgments-dir /tmp \
    --judges cal-judgments.jsonl
```

If F1 falls below 80% on the same calibration with the same judge,
investigate before adopting the change.

## Model-naming note

Default model names follow the dispatch brief, with one local bridge-name
substitution: `gemini-3.0-pro` is represented as `gemini-3-pro-preview`.
The bridge passes Gemini model IDs through to `gemini -m`; the repository
has current local references for `gemini-3-pro-preview` but none for
`gemini-3.0-pro`.

## Calibration gold methodology limits

- **n=12 and single-rater** — the gold reflects one orchestrator's
  Antonenko-grounded reading. Higher-quality gold requires a 2-3
  native-speaker linguist panel. Treat the calibration ranking as a
  **directional signal**, not a publishable claim, until peer-reviewed.
- **`sev1`-tolerant scoring by default** — debatable register calls
  (sev=1) do not penalize judge recall. Use `--strict-sev1` if you want
  to score them strictly.
- **Phrase-match is normalized-string overlap**, not semantic. A judge
  that flags "залишити коментарі" vs gold "залишимо коментарі" matches;
  semantically-different paraphrases do not.
