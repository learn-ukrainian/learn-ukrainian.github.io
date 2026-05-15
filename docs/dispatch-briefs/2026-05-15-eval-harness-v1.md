# Codex Dispatch — Eval harness v1: Russianism eval across model variants

**Dispatched:** 2026-05-15 by orchestrator (Claude)
**Agent:** Codex (gpt-5.5, high effort)
**Worktree:** `.worktrees/dispatch/codex/eval-harness-v1-2026-05-15/`
**Branch:** `codex/eval-harness-v1-2026-05-15`
**Estimated:** ~3 hours runtime, ~400 LOC code + tests

---

## Goal (one sentence)

Build an internal LLM Russianism eval harness that runs N prompts × M model variants → scored outputs → leaderboard markdown report, reusing existing bakeoff infrastructure (`scripts/audit/bakeoff_run.py`) and the deterministic Russianism detector (`scripts/audit/checks/russicism_detection.py`).

## Why this exists

We want measurable, reproducible answers to:
- Does Russianism rate scale with Claude family size? (Opus vs Sonnet vs Haiku)
- Same for OpenAI (GPT-5.5 vs GPT-5.4-mini — note: there is NO 5.5-mini; mini variant is one minor version back) and Google (Gemini 3.1 Pro vs 3.0 Pro vs 3.0 Flash, plus Gemini 2.5 Flash for free-tier comparison)?
- Should we revise our V7 writer-selection decision based on current numbers?
- Empirical evidence to add to the Anthropic bug report (filed at anthropics/claude-code#59146).

The detector is the scorer (already exists). Bakeoff is the dispatch primitive (already exists). What's missing is the harness that wires prompts × models × scorer together and emits a comparison report.

## Acceptance criteria (measurable)

1. **New file:** `scripts/audit/russianism_eval.py` — single-file harness:
   - CLI: `russianism_eval.py --prompts <yaml> --models <comma-list> [--out-dir <path>] [--max-parallel N]`
   - Loads prompt YAML
   - For each (prompt, model) pair:
     - Dispatches to model via agent bridge (`scripts/ai_agent_bridge/__main__.py ask-claude / ask-codex / ask-gemini`)
     - Captures raw model output text
   - Runs `check_russicisms` + (if `check_ua_gec_calques` exists post-PR-2) on each output
   - Aggregates per-model: total Russianisms, rate per 100 words, per-prompt breakdown
   - Writes `audit/russianism-eval-{timestamp}/`:
     - `REPORT.md` — human-readable leaderboard table + per-prompt breakdown + sample bad outputs
     - `outputs.jsonl` — one line per (prompt, model) with raw output
     - `scores.csv` — per-prompt per-model detailed scores
     - `summary.json` — machine-readable summary for dashboard / API consumption

2. **Prompt suite:** ship `eval/russianism/prompts-v1.yaml` with 5 starter prompts:
   - 2 EN→UK translations engineered to elicit calques (the orchestrator will provide content for these — see "Prompts" section below; you author the YAML schema and 3 additional prompts in calque-prone domains: a medical scenario, a business email, a social-media post)
   - Each prompt entry: `id`, `category`, `prompt_text`, `expected_calque_categories`, `notes`

3. **Tests:** `tests/test_russianism_eval.py`:
   - Mock the agent bridge calls (return canned bad outputs with known Russianisms)
   - Verify scorer runs, aggregation correct, REPORT.md generated, schema of summary.json
   - At least 6 tests

4. **Dry-run mode:** `--dry-run` flag prints what would be dispatched but doesn't actually call agents. Used for verifying YAML schema and model list without spending tokens.

5. **Cost report:** at end of run, print estimated tokens consumed per model. Doesn't have to be exact — back-of-envelope based on input + output char counts at standard ratios. Helps user decide whether to keep running daily.

6. **Verifiable claims preamble (per #M-4):** Brief explicitly enumerates these required tool-backed evidence lines in your turn body:
   - `pytest tests/test_russianism_eval.py` final summary line raw
   - `ruff check scripts/audit/russianism_eval.py tests/test_russianism_eval.py` final line raw
   - Output of `--dry-run` against the shipped prompts × default model list (proves CLI works)
   - `git log -1 --oneline` raw
   - `gh pr view N --json url` raw URL

## Hard guardrails

- **DO NOT actually run the eval against real models.** This PR adds the harness and mocks. The orchestrator will run the live eval after PR merge. (Saves you Codex tokens, saves user money, isolates infrastructure work from data-gathering work.)
- **DO NOT use `git commit --no-verify`.**
- **DO NOT use `gh pr merge --admin`.**
- **DO NOT touch starlight/** — known build-hook issue. Revert any worktree-side changes before commit.
- Reuse existing dispatch primitives — DO NOT reimplement what bakeoff_run.py or `ai_agent_bridge` already provide. Read them first; extend rather than parallel.
- Mock the bridge in tests using monkeypatch on `subprocess.run` or by substituting an injected `Caller` class — your call, but tests must not actually call out.

## Prompts to ship in v1

Use these two as-is for the EN→UK translation prompts:

**Prompt 1 — translation:**
```
You are writing for a Ukrainian-language email at A2 level. Translate the
following English text into idiomatic standard Ukrainian. Avoid Russianisms.

"Hello! I am writing to let you know that I will be taking part in the
meeting next week. I want to receive the documents in advance so I can
prepare. Generally, I think the following points are the most important:
budget, timeline, and the next steps. Please send everything by any moment
that works for you. Thanks!"

Output ONLY the Ukrainian translation — no commentary.
```

**Prompt 2 — translation (longer):**
```
Translate to standard literary Ukrainian. Avoid Russianisms, calques, and
Surzhyk. Output only the translation.

"In the first place, the following points concern us. The doctor said that
in general the situation is improving. Pretty much everyone takes part in
the discussion. As soon as we receive the documents, we will send them to
you. From one side it looks fine, from another it does not. We made a
couple of decisions and decided to act accordingly."
```

For the other 3 prompts (medical / business / social-media), AUTHOR them yourself
matching the spirit: prompt asks for Ukrainian generation, gives the model
opportunity to use calque-prone vocabulary, explicitly forbids Russianisms.

## Default model list for v1

```
claude-opus-4-7,claude-sonnet-4-6,claude-sonnet-4-5,claude-haiku-4-5,gpt-5.5,gpt-5.4-mini,gemini-3.1-pro-preview,gemini-3.0-pro,gemini-3.0-flash-preview,gemini-2.5-flash
```

Verify each model name against current bridge support — if any name has changed,
use the bridge's actual current name and note the substitution in the README.

## Step-by-step

1. `git worktree add -b codex/eval-harness-v1-2026-05-15 .worktrees/dispatch/codex/eval-harness-v1-2026-05-15 origin/main`
2. `cd .worktrees/dispatch/codex/eval-harness-v1-2026-05-15 && ln -s ../../../../.venv .venv`
3. Read `scripts/audit/bakeoff_run.py` and `scripts/ai_agent_bridge/__main__.py` to understand existing dispatch shape — DO NOT duplicate this code.
4. Implement `scripts/audit/russianism_eval.py`. Keep it under 400 LOC; if it bloats, split into `russianism_eval/{cli.py,runner.py,reporter.py}` instead.
5. Author `eval/russianism/prompts-v1.yaml` with 5 prompts.
6. Write tests in `tests/test_russianism_eval.py` with mocked bridge.
7. Run pytest, ruff. Run `--dry-run` to confirm CLI works.
8. Commit:
   ```
   feat(audit): Russianism eval harness v1 — prompts × models × scorer → leaderboard
   ```
9. `git push -u origin codex/eval-harness-v1-2026-05-15`
10. `gh pr create` with body covering: what it does, why now (links Anthropic bug + writer-selection decision card), test coverage, NO auto-merge, NO live runs in this PR (orchestrator runs eval post-merge).

## What success looks like

You return with:
- PR URL (raw `gh pr view --json url` output)
- Pytest pass count (raw final-summary line)
- Ruff result (raw final line)
- `--dry-run` output proving CLI works (raw stdout)
- Commit SHA (raw `git log -1 --oneline`)

If `--dry-run` reveals model names that don't exist in the bridge, document the substitutions in PR body. If you need the orchestrator to verify bridge behavior, leave a `## QUESTIONS` section in the PR body — but only if a real blocker.
