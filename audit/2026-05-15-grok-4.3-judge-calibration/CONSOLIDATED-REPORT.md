# Grok 4.3 — Russianism judge onboarding report (2026-05-15)

Standalone test harness at `scripts/audit/grok_judge_calibration.py`. Pulls the
12-case Antonenko-grounded gold from PR #2006 (`origin/pr-2006:eval/russianism/
calibration-cases.jsonl`) without depending on the PR landing first.

## Final leaderboard — all 4 judges, 12-case gold

| Judge | F1 | Precision | Recall | Case acc | Avg dur | Cost / M tok (in / out) |
|---|---:|---:|---:|---:|---:|---:|
| claude-opus-4-7 | **86%** | 79% | **94%** | **100%** | ~30s | $15 / $75 |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% | ~60–240s | $1.25 / $5 |
| gpt-5.5 | 78% | **90%** | 69% | 83% | ~25s | $1.25 / $10 |
| **grok-4.3 (medium, +MCP)** | **76%** | **85%** | 69% | **92%** | ~19s | **$0.20 / $0.50** |

(3 baseline rows from the 2026-05-15 calibration study on `origin/pr-2006`.
Grok row is round 2 — the production-recommended configuration.)

## Three-round Grok calibration

| Round | reasoning_effort | MCP | F1 | Case acc | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| 1 | medium | ✗ | 77.4% | 75.0% | 80.0% | 75.0% |
| 2 | medium | ✓ | 75.9% | **91.7%** | **84.6%** | 68.8% |
| 3 | **high** | ✓ | 61.5% | 66.7% | 80.0% | **50.0%** |

**Key findings:**

1. **MCP grounding moved case accuracy 75% → 92%** (round 1 → round 2). Same model,
   same prompt, the only delta was `hermes mcp add sources --url ...`. Three cases
   flipped ✗→✓: `cal_clean_short_prose` (FP fixed), `cal_dirty_medical` (FN fixed),
   `cal_debatable_next_steps` (FN fixed). One case regressed ✓→✗:
   `cal_clean_greeting` ("Доброго дня!") — same canonical-greeting over-flag pattern
   that bit gemini-3.1-pro in the original study. This is a Grok prior about genitive
   constructions; MCP grounding didn't fix it.

2. **`reasoning_effort=high` measurably HURT this task.** Recall fell from 68.8% to
   50.0%; case accuracy fell from 91.7% to 66.7%. Two cases that Grok correctly
   classified at `medium` regressed at `high`:
   - `cal_debatable_next_steps` flipped ✓→✗ (FN — said clean on debatable Russianism)
   - `cal_clean_with_lure` flipped ✓→✗ (FP — fell for the deliberate lure case)

   Hypothesis: deeper reasoning produces more confident binary calls on borderline
   cases, but the extra confidence trips on adversarial / debatable inputs more often
   than `medium`'s default-to-safer-answer pattern.

3. **Grok is the fastest judge in the field — and the cheapest by an order of magnitude.**
   Average ~19s/call (vs claude-opus ~30s, gemini ~60-240s, gpt-5.5 ~25s). Pricing
   $0.20 in / $0.50 out per million tokens — claude-opus is 75× costlier on input,
   150× costlier on output.

## Role recommendations

| Role | Verdict | Rationale |
|---|---|---|
| **Primary judge** | Not yet | claude-opus-4-7 still wins on F1 (86% vs 76%) and case accuracy (100% vs 92%). Margin small enough that prompt tuning specifically for genitive greetings could close it. |
| **Cleanliness classifier** (binary clean / dirty) | **Strong** | Case accuracy 91.7% is second only to claude-opus-4-7. At 19s + $0.20/M tokens, viable for high-volume batch screening. |
| **Second-opinion validator** (sev≥2 precision) | **Strong** | Precision 85% is best-in-class except gpt-5.5. Fastest in the field. |
| **Code reviewer** | **Strong candidate** | Independent PR review test (PR #2019 at `reasoning_effort=high`) identified the exact writer-compliance gap I'd filed as issue #2018 — without seeing #2018. Plus three real regex edge cases I'd missed. Review depth comparable to claude-opus-4-7. |
| **V7 module writer** | Untested | Stage 3 onboarding pending. Tool-use discipline confirmed (probe showed `verify_words` invoked correctly via Hermes MCP). |
| **Honesty / hallucination resistance** | **Strong** | Stage 5 probe: Grok caught a fake citation ("Антоненко-Давидович p.999 says сонце is a Russianism"), used MCP tools to verify, identified the impossible page number, and refused to validate. |

## Hermes harness — what we learned

Onboarding Grok required adding MCP server registration in Hermes:

```bash
printf 'n\nY\n' | hermes mcp add sources --url http://127.0.0.1:8766/mcp
```

After this, `hermes -z PROMPT -m grok-4.3` exposes all 33 sources tools without
extra flags. Tool calls don't require manual approval in non-interactive mode
(`approvals.mode: manual` only gates MCP reloads and destructive slash commands).

`reasoning_effort` adjustment for headless mode requires editing
`~/.hermes/config.yaml` line 52 (`agent.reasoning_effort`). The interactive TUI
exposes the same control via `/reasoning [none|minimal|low|medium|high|xhigh]`
slash command per session.

## Open questions / follow-ups

1. **Prompt tuning for Grok specifically.** Adding "Note: genitive greetings
   `Доброго дня!`, `Доброго ранку!` are canonical and not Russianisms" to the
   judge prompt would likely close the case accuracy gap with claude-opus-4-7.
   We didn't run this round because the original calibration didn't tune for
   each model — apples-to-apples.
2. **Stage 3 (V7 writer trial).** Most expensive remaining test. Requires
   adding `grok-tools` writer in `linear_pipeline.py` and a single A1 module
   build. Decision should come after stage 2 (single-shot code edit at a
   smaller scope) lands a green signal.
3. **Stage 4 (reviewer-as-fixer).** Requires Grok to emit `<fixes>` find/replace
   blocks compatible with the per-dim QG pipeline. PR review test showed
   Grok produces structured analysis, but the strict `<fixes>` shape requires
   a different prompt template.
4. **`xhigh` calibration.** Skipped because `high` already regressed; `xhigh`
   would likely regress further. Re-test only if we find a task where `high`
   helps.
5. **Routing layer integration (#15).** Add `grok` family to
   `scripts/audit/russianism_judge.py`, `scripts/delegate.py`, and
   `scripts/ai_agent_bridge/__main__.py` so the broader pipeline can dispatch
   to Grok uniformly.

## Artifacts

- `audit/2026-05-15-grok-4.3-judge-calibration/` — round 1 (no MCP)
- `audit/2026-05-15-grok-4.3-judge-calibration-with-mcp/` — round 2 (production-recommended config)
- `audit/2026-05-15-grok-4.3-judge-calibration-effort-high/` — round 3 (high effort, archived for the negative result)
- `scripts/audit/grok_judge_calibration.py` — reusable harness; supports `--out-dir` for round comparison

## Refs

- #1975 — m20 build RED (originator of judge work)
- PR #2006 — russianism_judge harness + 12-case calibration gold (DIRTY; pending rebase)
- PR #2019 — m20 gate + writer-prompt patches (where Grok's PR review found #2018-class bugs)
- #2018 — writer-compliance bottleneck (Grok independently identified during PR review)
