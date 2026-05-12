# Claude-headless `/goal` brief — bakeoff: claude-tools vs codex-tools writer on a1/my-morning

> **Issue:** #1807 (writer-prompt tool-theatre) + ratification of `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`
> **Mode:** danger (V7 builds + audit writes + commit; no auto-merge)
> **Worktree:** `.worktrees/dispatch/claude/bakeoff-2026-05-12-night/`
> **Base:** `origin/main`
> **Hard timeout:** 7200s (2 hr — generous; two V7 builds + analysis + writeup)
> **Silence timeout:** 1800s (30 min — V7 builds can think for a long time)
> **Effort:** xhigh (analytic verdict required, not just script-running)
> **Driver:** Claude headless via `claude -p "/goal ..."` per `claude_extensions/rules/goal-driven-runs.md`
> **Build invocation authorized:** USER OVERRIDE 2026-05-12 night ("you are allowed to run build when in auto mode")

---

## ⚠️ CRITICAL — fresh-shell behavior

**Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks.** Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && ...` and use the MAIN `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Why this matters (one paragraph context)

The V7 writer-selection decision (`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`) was ratified ACCEPTED for Codex (gpt-5.5 / codex-tools) on 2026-05-06. The 2026-05-08 follow-up bakeoff revealed that codex-tools and gemini-tools both produced **`tool_calls_total=0` while emitting prose `<verification_trace>` blocks** — i.e. they wrote tool-call signatures as theatre, never actually invoking the tools. Claude-tools was the only writer that called tools as designed.

Commit `28417cc3cb` (2026-05-11 evening) rewrote the writer + reviewer prompts to call new single-call primitives instead of compose-pattern, specifically addressing the theatre issue. **This bakeoff is the empirical test of whether the prompt rewrite fixed the theatre problem.** If codex-tools now produces `tool_calls_total > 0` and clean python_qg gates, ratification of the existing decision holds. If it still produces theatre, we flip to claude-tools.

Acceptance criteria are in `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` § "Concrete rollback criteria."

---

## The single predicate this `/goal` run satisfies

> **`GOAL_DONE reason="bakeoff complete: REPORT.md written, winner declared per acceptance criteria, both builds' artifacts preserved in audit/bakeoff-2026-05-12-night/"`**

Halt early with `GOAL_ABORT` if:
- 3 consecutive blocked rounds (e.g. v7_build subprocess stuck).
- Either build fails to produce a `python_qg.json` (treat as build infrastructure failure, not bakeoff signal).
- Telemetry parser raises uncaught exception twice in a row.

---

## Per-turn status line contract (MANDATORY, per `claude_extensions/rules/goal-driven-runs.md`)

Every turn ends with:

```
GOAL_STATUS turn=N/30 blocked=N/3 no_progress=N/3 queue_head=<token>
```

Terminal: `GOAL_DONE reason="..."` with deterministic predicate result.
Abort: `GOAL_ABORT reason="..." last_cmd="..." last_cwd="..." last_output="..." next_action="..." queue_head=<token>` — all six fields required.

**Counter source:** maintain `/tmp/bakeoff-2026-05-12-turn.txt` with `echo "$((n+1))" > /tmp/bakeoff-2026-05-12-turn.txt` after each turn-step block. Read with `cat`.

---

## Numbered steps

### Phase 0 — verify base + setup

1. **Verify worktree base.**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && git log --oneline -3
   ```
   Top commit must be `019d055f1c` or descendant. Branch `claude/bakeoff-2026-05-12-night`. Quote raw output.

2. **Create audit dir.**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && mkdir -p audit/bakeoff-2026-05-12-night/{claude,codex}
   ```

3. **Verify the prompts you'll be bakeoff'ing.** Read first 30 lines of `scripts/build/phases/linear-write.md` and `scripts/build/phases/linear-review-dim.md`. Confirm via `git log -1 --oneline scripts/build/phases/linear-write.md` that the most recent commit on those prompts is `28417cc3cb` (the 2026-05-11 rewrite) or a descendant of it. **If not, abort** — the bakeoff is meaningless without the new prompts. Quote the `git log` output.

4. **Initialize turn counter.** `echo 0 > /tmp/bakeoff-2026-05-12-turn.txt`.

### Phase 1 — build with claude-tools writer

5. **Fire claude-tools build.** From inside the worktree:

   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer claude-tools --telemetry-out audit/bakeoff-2026-05-12-night/claude.write.jsonl --out audit/bakeoff-2026-05-12-night/claude/ 2>&1 | tee audit/bakeoff-2026-05-12-night/claude.stdout.log
   ```

   This will run for 5-15 minutes. Wait for it. Do NOT use ScheduleWakeup. Use synchronous tee-to-file so you have a full log on disk regardless of exit code.

6. **Capture build exit status.** Quote the last 20 lines of `audit/bakeoff-2026-05-12-night/claude.stdout.log`. If exit was non-zero, document why and continue to Phase 2 anyway — we still want the codex-tools data for comparison.

7. **Probe telemetry.** Quote the count of `writer_tool_call` events and any `writer_tool_theatre` events:

   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && grep -c '"event": *"writer_tool_call"' audit/bakeoff-2026-05-12-night/claude.write.jsonl && grep -c '"event": *"writer_tool_theatre"' audit/bakeoff-2026-05-12-night/claude.write.jsonl && grep '"event": *"phase_writer_summary"' audit/bakeoff-2026-05-12-night/claude.write.jsonl | python3 -m json.tool
   ```

   If the file is empty or the grep returns no matches, document that explicitly.

### Phase 2 — build with codex-tools writer

8. **Fire codex-tools build.**

   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer codex-tools --telemetry-out audit/bakeoff-2026-05-12-night/codex.write.jsonl --out audit/bakeoff-2026-05-12-night/codex/ 2>&1 | tee audit/bakeoff-2026-05-12-night/codex.stdout.log
   ```

9. **Capture exit + probe telemetry** (same pattern as steps 6 + 7, on the codex artifacts).

### Phase 3 — score both outputs against acceptance criteria

10. **Read the acceptance criteria FROM the decision card.** Quote the relevant lines of `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` § "Concrete rollback criteria" and § "What the bakeoff showed" verbatim. These define the gates.

11. **Inspect python_qg for both.**

    ```bash
    cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && cat audit/bakeoff-2026-05-12-night/claude/python_qg.json 2>/dev/null | python3 -m json.tool | head -100
    echo ---
    cat audit/bakeoff-2026-05-12-night/codex/python_qg.json 2>/dev/null | python3 -m json.tool | head -100
    ```

12. **Per-writer, compute the verdict.** For each writer (claude, codex), record in REPORT.md:

    | Field | claude-tools | codex-tools |
    |---|---|---|
    | Module file produced? (size > 1000 bytes) | yes/no | yes/no |
    | `tool_calls_total` | N | N |
    | `writer_tool_theatre` violations | N | N |
    | python_qg gates passed | M of K | M of K |
    | Hard-gate fails | list | list |
    | word_count vs target | N vs T | N vs T |
    | Invented `-ся` forms (per decision card rollback criterion) | yes/no — list any | yes/no — list any |
    | wiki-path miscites in references[] | count | count |
    | immersion percentage | N% vs ≤35% | N% vs ≤35% |
    | Writer phase duration | seconds | seconds |

13. **Declare winner per ranking rule:**

    Winner = writer that has BOTH: (a) `tool_calls_total > 0` AND (b) fewest hard-gate fails. Tiebreak by writer-phase duration (faster wins).

    If neither writer has `tool_calls_total > 0` → BAKEOFF FAIL — escalate to next-stage prompt iteration per the 2026-05-08 handoff Stage 2 (verify→write phase split).

    If both have `tool_calls_total > 0` and equal hard-gate fails, default to **codex-tools** per the existing ACCEPTED decision card (incumbent wins ties).

### Phase 4 — write REPORT.md + commit

14. **Write `audit/bakeoff-2026-05-12-night/REPORT.md`** following the template at the end of this brief. The report MUST include:

    - The full comparison table from step 12.
    - Winner declaration with one-sentence rationale.
    - Either: "Existing decision card RATIFIED" or "Decision card needs revision — codex-tools no longer passes positive evidence gates."
    - Pointers to all artifact files (`claude/`, `codex/`, `*.jsonl`, `*.stdout.log`).
    - Three verbatim quotes: one each from claude `module.md`, codex `module.md`, and the predecessor 2026-05-06 module.md, of the same target sentence (e.g. the first sentence of the "Діалоги" section). 5-15 words each. For qualitative reader judgment by orchestrator on wake.

15. **Update the existing decision card if winner != codex-tools.** Append a `## 2026-05-12 night bakeoff — REVISED` section quoting the new signal + linking REPORT.md. Do NOT move the file or change ACCEPTED status — the orchestrator decides whether to flip on wake.

16. **Commit.**

    ```bash
    cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night && git add audit/bakeoff-2026-05-12-night/ docs/decisions/2026-05-06-writer-selection-codex-gpt55.md && git commit -m "$(cat <<'EOF'
    test(bakeoff): claude-tools vs codex-tools on a1/my-morning (2026-05-12 night)

    Empirical test of writer-prompt rewrite (28417cc3cb) against the theatre
    diagnosis from 2026-05-08. See audit/bakeoff-2026-05-12-night/REPORT.md
    for verdict + per-writer telemetry.

    Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
    EOF
    )"
    ```

17. **Push the branch.** `git push -u origin claude/bakeoff-2026-05-12-night`.

18. **DO NOT open a PR. DO NOT auto-merge.** This is research, not code. The orchestrator will decide on wake whether to copy the winning module to `curriculum/l2-uk-en/a1/my-morning/` and whether to update the decision card status.

### Phase 5 — emit GOAL_DONE

19. Final turn: emit `GOAL_DONE reason="bakeoff complete: REPORT.md written, winner=<claude-tools|codex-tools|FAIL>, both builds preserved in audit/bakeoff-2026-05-12-night/, branch claude/bakeoff-2026-05-12-night pushed"`.

---

## Anti-fabrication preamble (per #M-4)

For each writer, every cell in the comparison table must be backed by `<command + cwd + raw-output>` evidence either inline in the REPORT.md or in this `/goal` transcript. Examples:

| Claim | Required evidence |
|---|---|
| "tool_calls_total=N" | `grep -c '"event":"writer_tool_call"' audit/.../X.write.jsonl` + raw count |
| "Module file produced" | `wc -c audit/.../X/module.md` + raw size |
| "Word count = N" | python_qg.json `word_count` field with raw extracted line |
| "Invented -ся forms" | python_qg.json `vesum_verified` failure list raw |
| "Immersion N%" | python_qg.json `immersion` raw |
| "Build duration Xs" | jsonl event `phase_writer_summary.duration_seconds` raw |

"I observed X" without a quoted line is hallucination. Full rule: `docs/best-practices/deterministic-over-hallucination.md`.

---

## REPORT.md template (use exactly this skeleton)

```markdown
# Bakeoff Report — claude-tools vs codex-tools on a1/my-morning (2026-05-12 night)

> **Run timestamp:** <ISO 8601 from filesystem mtime of REPORT.md>
> **Writers compared:** claude-tools, codex-tools
> **Slug:** a1/my-morning
> **Plan:** curriculum/l2-uk-en/plans/a1/my-morning.yaml
> **Prompt commit at run time:** <output of `git log -1 --oneline scripts/build/phases/linear-write.md`>
> **Acceptance criteria source:** docs/decisions/2026-05-06-writer-selection-codex-gpt55.md

## Verdict

**Winner:** <claude-tools | codex-tools | FAIL>

**One-sentence rationale:** <text — quote a metric>

**Decision card delta:** <RATIFIED | REVISED — flip recommended | FAIL — escalate to next-stage prompt iteration>

## Comparison table

[from step 12]

## Telemetry — claude-tools

- `tool_calls_total`: N
- `writer_tool_theatre`: N
- `phase_writer_summary`:
  ```json
  <raw event JSON>
  ```

## Telemetry — codex-tools

[same shape]

## python_qg — claude-tools

```json
<full python_qg.json from claude/ — pretty-printed, gates section only>
```

## python_qg — codex-tools

```json
<same for codex/>
```

## Qualitative sample — same sentence, three eras

**Target sentence:** first sentence of Діалоги section

- 2026-05-02 module (prior incumbent codex run): `<verbatim quote, 5-15 words>`
- 2026-05-12 night, claude-tools: `<verbatim quote>`
- 2026-05-12 night, codex-tools: `<verbatim quote>`

## Artifacts

- claude/ — `audit/bakeoff-2026-05-12-night/claude/`
- codex/ — `audit/bakeoff-2026-05-12-night/codex/`
- claude telemetry — `audit/bakeoff-2026-05-12-night/claude.write.jsonl`
- codex telemetry — `audit/bakeoff-2026-05-12-night/codex.write.jsonl`
- claude stdout — `audit/bakeoff-2026-05-12-night/claude.stdout.log`
- codex stdout — `audit/bakeoff-2026-05-12-night/codex.stdout.log`

## Next action for orchestrator

[ONE concrete action — e.g. "if RATIFIED: copy audit/.../codex/* to curriculum/l2-uk-en/a1/my-morning/ and update the May-2 artifacts. If REVISED: flip writer-selection ADR to claude-tools and file follow-up issue for codex-tools prompt iteration."]
```

---

## Out of scope (do NOT do these)

- Modifying writer/reviewer prompts (`scripts/build/phases/linear-*.md`).
- Modifying `v7_build.py` pipeline code.
- Copying the winning module to `curriculum/l2-uk-en/a1/my-morning/` (orchestrator owns that decision on wake).
- Opening a PR (this is research; leave on a branch).
- Auto-merging anything.
- Running a third writer (`gemini-tools`) — separate question, separate bakeoff.
