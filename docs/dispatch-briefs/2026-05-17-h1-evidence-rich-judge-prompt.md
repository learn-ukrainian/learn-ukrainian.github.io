# Dispatch brief: Experiment H1 — evidence-rich judge prompt

**Agent:** Claude headless (claude-opus-4-7)
**Mode:** `--mode danger` (worktree-isolated)
**Base branch:** `main`
**Task ID:** `h1-evidence-rich-judge-2026-05-17`

## Why this work — root-cause from prior calibration

The original judge prompt (`scripts/audit/_judge_eval_lib.py:build_judge_prompt`) has THREE design flaws confirmed by the 2026-05-17 calibration matrix:

1. **Bias-push:** opens with *"Identify EVERY Russianism..."* — primes models to over-flag. Clean-verdict option is a buried afterthought.
2. **Silent retrieval failure:** when `retrieve_antonenko()` returns 0 entries, the prompt fills the gap with *"Apply general knowledge of Ukrainian register and Russianism patterns."* — explicitly delegates to pre-training intuition. For Opus, that intuition is biased by Russian surface-pattern similarity (Opus consistently false-flags `cal_clean_greeting` = canonical "Доброго дня! Як ваші справи?" at all 6 effort/MCP combos tested).
3. **No heritage check:** `mcp__sources__search_heritage` exists, returns "X is canonical Ukrainian; do NOT flag" for attested phrases — never wired into retrieval.

Result: Opus over-flags, GPT under-flags (P=1.000 / R=0.5), same prompt, opposite priors.

**Hypothesis (H1):** evidence-rich retrieval + inverted default + self-critique will:
- Eliminate Opus's `cal_clean_greeting` false flag → opus case_acc 0.917 → 1.000
- Raise Opus F1 from 0.839 → ~0.85+ (loses FP, no new misses)
- Raise GPT-5.5 recall (now has flag-supporting evidence) → F1 from 0.720 → ~0.78+
- Grok 4.3 already at case_acc=1.0 — predicted ~no change or slight gain
- Haiku will benefit most from explicit evidence (cheap models lean on retrieval hardest)

## Deterministic claims this work will produce (#M-4)

| Claim | Required evidence |
|---|---|
| "_judge_eval_lib.py modified, tests pass" | raw `pytest tests/audit/` summary line + raw `ruff check` final line |
| "6 H1 cells ran successfully" | `ls audit/2026-05-17-judge-calibration-h1/*/*/native_cli/*.json audit/2026-05-17-judge-calibration-h1/*/*/hermes/*.json \| wc -l` returns 6 |
| "0 errors" | grep `"errors": []` matches 6 OR list errors per cell |
| "cal_clean_greeting result for opus xhigh/with_mcp" | `jq -r '.judgments[] \| select(.case_id=="cal_clean_greeting") \| .case_acc' audit/2026-05-17-judge-calibration-h1/anthropic/claude-opus-4-7/native_cli/xhigh-with_mcp.json` → either `true` (hypothesis confirmed) or `false` (hypothesis falsified) |
| "Before/after comparison written" | `cat audit/2026-05-17-judge-calibration-h1/COMPARISON.md` shows 6 rows with prior F1/P/R/case_acc vs new |
| "PR opened, not merged" | raw `gh pr view --json url,state` line showing OPEN |

## Numbered execution steps

### 1. Worktree
Dispatch system creates `.worktrees/dispatch/claude/h1-evidence-rich-judge-2026-05-17/` from main.

### 2. Data symlinks (sparse worktree)

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/vesum.db ]   || { rm -f data/vesum.db;   ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db   data/vesum.db; }
```

### 3. Fetch calibration cases

```
git rev-parse origin/pr-2006 >/dev/null 2>&1 || git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
```

### 4. Modify `scripts/audit/_judge_eval_lib.py`

#### 4a. Add evidence-expansion function

Read the current file first. Then ADD a new function `retrieve_evidence(text)` (next to `retrieve_antonenko`) that returns a structured dict:

```python
def retrieve_evidence(text: str) -> dict[str, Any]:
    """Return all evidence signals for a judge prompt: Antonenko entries,
    heritage attestation, Russian-shadow morphology, VESUM verification."""
    return {
        "antonenko": retrieve_antonenko(text),
        "heritage_attested": _heritage_check(text),    # list of phrases with documented Ukrainian usage
        "russian_shadow_signal": _russian_shadow_check(text),  # boolean + evidence
        "vesum_unknown_tokens": _vesum_unknown(text),  # tokens NOT in VESUM (real Russianism candidates)
    }
```

Implement each helper using MCP-equivalent local DB queries:
- `_heritage_check`: query `slovnyk_me_entries`, `grinchenko_entries`, `esum_entries` tables in `data/sources.db` for multi-word phrase attestation. If a 2-3 word substring of the text appears in any of these dictionaries, return it as "attested canonical."
- `_russian_shadow_check`: call existing `pymorphy3` heuristic in `scripts/sources/russian_shadow.py` (find it via grep).
- `_vesum_unknown`: tokenize text, look up each token in `data/vesum.db` `forms` table. Return tokens NOT found.

If a helper module doesn't exist yet, build a minimal version inline. Keep it ≤60 LOC total for the helpers.

#### 4b. Rewrite `build_judge_prompt` with H1 design

NEW prompt structure (paraphrased — produce the exact text):

```
You are a careful Ukrainian-language proofreader.

The DEFAULT verdict is CLEAN. Only raise an issue when you can cite SPECIFIC
evidence below. Surface similarity to Russian is NOT evidence. The canonical
greeting "Доброго дня! Як ваші справи?" is correct Ukrainian — never flag it.

## Text to evaluate
```
<text>
```

## Evidence available

### Antonenko-Davidovych entries directly keyed to words in this text
<antonenko entries if any, else: "(none — that means no direct condemnation exists)">

### Heritage attestation (these phrases have documented Ukrainian usage — DO NOT FLAG)
<list of attested phrases, else: "(no multi-word matches checked)">

### Russian-shadow morphology signal (pymorphy3 Russian-pattern detection)
<true/false + offending tokens if any>

### Tokens NOT found in VESUM (real Russianism candidates — investigate these first)
<list of tokens, else: "(all tokens are valid Ukrainian forms)">

## Your task

For each flag you wish to raise, you must cite EXACTLY ONE of:
- An Antonenko rule shown above (quote the headword)
- A VESUM-unknown token shown above
- A Russian-shadow morphology hit shown above

If you cannot cite one of these, the flag is forbidden — output CLEAN.

Output ONLY this JSON:

{"verdict": "clean", "issues": []}
OR
{"verdict": "issues_found", "issues": [{"phrase": "...", "evidence_type": "antonenko|vesum_unknown|russian_shadow", "evidence_key": "...", "correct": "...", "severity": 1-3}]}
```

#### 4c. Update `score_case` if needed

Check whether `score_case` needs to read the new `evidence_type` field. If existing code only reads `verdict` and `issues[].phrase`, no change. Don't touch what isn't needed.

#### 4d. Pass `retrieve_evidence` through to `judge_calibration_matrix.py`

In `run_cell`, change:
```python
prompt = build_judge_prompt(target, retrieve_antonenko(target))
```
to:
```python
prompt = build_judge_prompt(target, retrieve_evidence(target))
```

And update `build_judge_prompt` signature to accept the dict instead of a list. Keep BACKWARD COMPAT: if the value passed is a list (old-shape), wrap it into the new dict shape with empty other fields. This avoids breaking other callers.

### 5. Tests + lint

```
.venv/bin/python -m pytest tests/audit/ -q
.venv/bin/ruff check scripts/audit/_judge_eval_lib.py scripts/audit/judge_calibration_matrix.py
```

If existing tests break: read them, understand why, fix the test if the contract changed legitimately. DO NOT comment out or skip tests.

### 6. Render the new prompt for the false-positive case (eyeball check)

```
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts/audit')
from _judge_eval_lib import build_judge_prompt, retrieve_evidence
text = 'Доброго дня! Як ваші справи? Сподіваюся, у вас усе гаразд.'
ev = retrieve_evidence(text)
print('--- evidence ---')
print(ev)
print('--- prompt ---')
print(build_judge_prompt(text, ev))
"
```

Confirm the rendered prompt:
- States CLEAN as default
- Includes the canonical-greeting anti-flag rule
- Shows real heritage attestation evidence for the greeting (if any found)
- Does NOT say "use general knowledge"

If the heritage check returns no rows for the greeting, that means the local DB doesn't index that phrase. Acceptable — the inverted default + explicit anti-flag rule should still suppress the false positive.

### 7. Run the 6 H1 cells

**New out-dir:** `audit/2026-05-17-judge-calibration-h1/` (preserves the original matrix for diff).

```
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --out-dir audit/2026-05-17-judge-calibration-h1 \
  --families anthropic,openai,google,xai \
  --models claude-opus-4-7,claude-haiku-4-5-20251001,gpt-5.5,gemini-3.1-pro-preview,grok-4.3 \
  --harnesses native_cli,hermes \
  --efforts xhigh,high,medium,default \
  --mcp-states with_mcp,without_mcp \
  --max-parallel 2
```

The cells we actually want (the harness will skip unsupported combos):
- anthropic/claude-opus-4-7/native_cli/xhigh/with_mcp
- anthropic/claude-opus-4-7/native_cli/high/without_mcp
- anthropic/claude-haiku-4-5-20251001/native_cli/high/without_mcp
- openai/gpt-5.5/native_cli/medium/with_mcp
- google/gemini-3.1-pro-preview/native_cli/default/with_mcp
- xai/grok-4.3/hermes/xhigh/with_mcp

If the model/effort/mcp filters above run too many cells, narrow with `--models` per dispatch. **6 cells total is the target.**

NOTE: anthropic native_cli inherits OAuth from this worker session (no API key needed — the CLAUDE_MATRIX_USE_BARE toggle defaults to OAuth). Hermes anthropic is STILL broken (#2036) — don't try.

### 8. Build the comparison report

After all cells complete, generate `audit/2026-05-17-judge-calibration-h1/COMPARISON.md`:

```markdown
# H1 Before/After Comparison

For each of the 6 cells, table:

| Cell | Prior F1 | H1 F1 | ΔF1 | Prior P | H1 P | ΔP | Prior R | H1 R | ΔR | Prior case_acc | H1 case_acc | Δacc |

Then 1-paragraph summary:
- Did Opus's cal_clean_greeting false flag disappear? (boolean answer + jq evidence quoted)
- Did GPT-5.5 recall rise as predicted? (numbers)
- Surprises?
```

Read prior cells from `audit/2026-05-17-judge-calibration-matrix/.../` and H1 cells from `audit/2026-05-17-judge-calibration-h1/.../`. Use `jq` for both — quote raw output in the report.

### 9. Commit

```
git add scripts/audit/_judge_eval_lib.py audit/2026-05-17-judge-calibration-h1/
[ -f scripts/audit/judge_calibration_matrix.py ] && git diff --quiet scripts/audit/judge_calibration_matrix.py || git add scripts/audit/judge_calibration_matrix.py
git commit -m "$(cat <<'EOF'
feat(audit): H1 evidence-rich judge prompt + 6-cell A/B

Hypothesis: the original judge prompt's "Identify EVERY ... apply general
knowledge" framing exploits Opus's Russian-surface-pattern bias and
suppresses GPT-5.5's flag rate. H1 inverts the prompt to CLEAN-by-default,
adds heritage/Russian-shadow/VESUM signals to retrieval, and requires
each flag to cite specific evidence.

Concrete predicted deltas:
- opus-4-7 xhigh/with_mcp: case_acc 0.917 → 1.000 (greeting FP eliminated)
- gpt-5.5 medium/with_mcp: F1 0.720 → ~0.78 (recall rises via evidence)
- grok-4.3 xhigh/with_mcp: case_acc stays 1.000 (already perfect)

Actual deltas: see audit/2026-05-17-judge-calibration-h1/COMPARISON.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 10. Push + PR (no auto-merge)

```
git push -u origin <branch>
gh pr create --title "feat(audit): H1 evidence-rich judge prompt (6-cell A/B)" --body "$(cat <<'EOF'
## Summary
- New `retrieve_evidence(text)` aggregates Antonenko + heritage attestation + Russian-shadow signal + VESUM-unknown tokens
- New `build_judge_prompt` flips to CLEAN-by-default + requires each flag to cite specific evidence
- A/B: 6-cell re-run in new out-dir `audit/2026-05-17-judge-calibration-h1/`

## Results (see COMPARISON.md for full table)
<paste the 1-paragraph summary from COMPARISON.md>

## Test plan
- [ ] pytest tests/audit/ — pass
- [ ] ruff check scripts/audit/_judge_eval_lib.py — pass
- [ ] manual: open audit/2026-05-17-judge-calibration-h1/REPORT.html
- [ ] manual: read COMPARISON.md — confirm Opus greeting FP is gone (or document why hypothesis was wrong)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" --base main
```

**Do NOT auto-merge.**

## Hard rules

- Do NOT modify the prior calibration cells in `audit/2026-05-17-judge-calibration-matrix/` — they are the BEFORE baseline.
- Do NOT try the hermes/anthropic lane (#2036 still live).
- If `pytest tests/audit/` fails with NEW errors caused by your changes, FIX the cause, do not skip the test.
- If H1 makes the numbers WORSE on any cell, report it honestly in COMPARISON.md. Negative result is still a result — do not retry until the numbers look good.
- Stay under 75 min wall-time. If you're at 60 min with cells still queued, STOP, commit what completed, document what's missing in COMPARISON.md.

## What you do NOT do

- Do NOT change the calibration cases themselves (eval/russianism/calibration-cases.jsonl) — A/B requires SAME inputs.
- Do NOT auto-merge.
- Do NOT touch `.bash_secrets` or env files.
- Do NOT add a "max" effort tier "for completeness" — user explicitly approved 6 cells listed above, nothing more.
