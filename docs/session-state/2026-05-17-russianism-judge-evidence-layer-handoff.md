# Session handoff — Russianism judge evidence layer (2026-05-17)

**For:** Codex, Gemini, headless Claude, or whoever picks up this thread.
**Author:** Claude orchestrator session, 2026-05-16 ~21:00 UTC.
**Status:** Evidence layer ~80% built; calibration conclusions ON HOLD until full evidence layer lands.

---

## TL;DR (60 seconds)

We expanded the Russianism judge calibration matrix to include Claude models, ran two failed prompt experiments (H1, H2), discovered our evidence catalog has more gaps than we thought, and started ingesting UA-GEC (~9K russianism annotations) into MCP. **The headline finding is NEGATIVE: when retrieval is sparse, 5 of 6 models converge on identical numbers — meaning the bottleneck is the EVIDENCE LAYER, not the model.** Until UA-GEC + Karavansky + Holovashchuk + Paronyms are all loaded and served via MCP uniformly, **DO NOT DRAW CONCLUSIONS** about which model is best at Russianism judging.

---

## What landed today (chronological)

| PR | Title | What it does | Status |
|---|---|---|---|
| #2044 | Claude calibration matrix expansion (12 cells) | Adds opus-4-7, sonnet-4-6, haiku-4-5 × medium/high × MCP on/off to `audit/2026-05-17-judge-calibration-matrix/`. Also adds `CLAUDE_MATRIX_USE_BARE` env toggle so the anthropic native_cli lane works via OAuth (no API key needed) | ✅ MERGED |
| #2045 | opus-4-7 xhigh cells | Adds 2 cells closing the effort-tier gap | ✅ MERGED |
| #2000 | UA-GEC F/Calque mined patterns (audit pipeline) | Adds `data/russianism-patterns-ua-gec.csv` (218 high-frequency F/Calque pairs) + `check_ua_gec_calques()` info-tier detector to the audit pipeline. Cascade bug in `_antonenko_gate` fixed in this PR's merge commit (info-severity violations no longer feed the blocking gate) | ✅ MERGED |
| #2056 | Pre-push Dagger hook | New pre-commit-framework hook `dagger-pytest` at stage=pre-push. Runs `dagger call pytest --source=.` (full GHA replay) when push touches `scripts/`, `tests/`, `.dagger/`, or `.py`. Graceful fallback (WARN + allow) when Dagger missing, .dagger/ missing, OR Docker daemon down. Bypass: `git push --no-verify` | ✅ MERGED |

## Open PRs you'll inherit

| PR | What | Why it's open |
|---|---|---|
| **#2055** | **UA-GEC MCP ingest** — adds `ua_gec_errors` table (8,937 rows: F/Calque 2397 + G/Case 5024 + G/Gender 1057 + F/Collocation 459) + FTS5 + `mcp__sources__search_ua_gec_errors` tool | **Blocked on a pre-existing pre-commit env quirk** (rapidfuzz ModuleNotFoundError inside hook context, passes when pytest run directly). Fix commit is ready but blocked by the local hook. See "Open blocker" below. |
| **#2046** | H1 evidence-rich judge prompt (diagnostic) | The H1 prompt FAILED — recall collapsed because cite-or-forbid was too strict. Keep open as DIAGNOSTIC reference, do NOT merge to production code path |
| **#2049** | H2 — Antonenko full-text + UA-GEC calque retrieval (3-way A/B/C diagnostic) | Same — H2 was PARTIAL recovery (F1 0.135 → 0.478) but didn't reach baseline (0.753). Diagnostic artifact, NOT a production-ready prompt |
| #2051 | H2C typed calibration set (user/another agent dispatched in parallel) | Status unknown to this session; review independently |

## Issues filed today (gap surface)

| # | Title | Severity | What needs to happen |
|---|---|---|---|
| **#2050** | _judge_eval_lib russian_shadow channel silently dead — ModuleNotFoundError swallowed | Medium | One-line `sys.path` shim or fallback import. **BOTH H1 AND H2 measured the evidence layer with this channel disabled** — confounds conclusions |
| **#2052** | Karavansky data acquisition missing — #1664 closed without scraper landing | Medium-high | Build r2u.org.ua HTML scraper (~1-2 days), run existing post-scrape ingester, register MCP tool. Source IS live (HTTP 200) — no JSON dump exists |
| **#2053** | Holovashchuk data acquisition missing — kpdi.edu.ua PDF 404 | Medium | Locate alt source (Internet Archive ISBN search / chtyvo.org.ua / diasporiana.org.ua / slovnyk.me linguistic_norm mirror), OCR, ingest |
| **#2054** | Paronyms data acquisition missing — NBU 1986 PDF OCR pending | Medium | Locate NBU 1986 PDF on Internet Archive/diasporiana, Cyrillic OCR, parse to paronym-pair TSV, ingest |

**Systemic pattern:** PR #1755's boilerplate close comment ("Implemented in PR #1755") was applied to #1664/#1665/#1666 even though PR #1755 only landed the post-source ingester, not the data acquisition. Three "completed" issues had zero data loaded. Don't trust "Implemented in #1755" claims without verifying actual table rows in `data/sources.db`.

---

## Open blocker requiring user/operator decision

**PR #2055 commit blocked by `.git/hooks/pre-commit` env divergence.**

- The fix (2-line edit to 2 test files) verified locally — all 4 affected tests pass via direct pytest
- The project's `.git/hooks/pre-commit` script runs the same pytest command but gets `ModuleNotFoundError: rapidfuzz` on a pre-existing, unrelated test
- rapidfuzz IS installed in the venv (verified)
- Same command, same Python, same files, same args → different result
- Suspect: env-var difference between pre-commit hook subshell and the parent shell

Decision needed: `--no-verify` for THIS commit (the actual change is safe, GHA + pre-push Dagger hook are the real gates) OR debug the env divergence (potentially long).

**My recommendation:** `--no-verify` this one commit, file a separate issue for the env divergence in `.git/hooks/pre-commit`. The fix is verifiable independently. Don't let a hook bug block a real fix.

---

## Why "no conclusions until evidence layer is complete" — the diagnostic story

H1 + H2 ran the same 6 calibration cells (opus-xhigh+mcp, opus-high−mcp, haiku-high−mcp, gpt-5.5-medium+mcp, gemini-default+mcp, grok-xhigh-hermes+mcp) against three different judge prompts:

| Prompt | Mean F1 | Greeting FP fix? | Note |
|---|---|---|---|
| Baseline ("Identify EVERY") | **0.753** | NO — opus FPs 3/3 cells | Production prompt today |
| H1 (cite-or-forbid, evidence-strict) | 0.135 ❌ | YES — 0/6 FPs | F1 collapse: evidence-floor became the bottleneck |
| H2 (H1 + Antonenko full-text + UA-GEC inline) | 0.478 ↗ | YES — 0/6 FPs | Partial recovery, but Gemini was the ONLY cell beating baseline (0.857) |

**Per-cell read from H2:**
- 5 of 6 models converged on near-identical numbers (opus high=xhigh=0.545, gpt=0.476, haiku=grok=0.222). **Model intelligence stopped mattering when retrieval was the bottleneck.**
- Of 33 sev≥2 flags raised across all 6 H2 cells, only 9 cited `ua_gec_calque` and 6 cited `vesum_unknown`. **18 fell back to `general_principle` (judge intuition)** — the exact failure mode H1/H2 were trying to eliminate.
- `antonenko_prose` channel: 0 citations — prefix-match retrieval too broad
- `russian_shadow` channel: silently dead (bug #2050)

**Why this matters:** before H2, the early signal looked like "Gemini thrives, Grok collapses — different model temperaments." That framing was wrong; the user correctly pushed back that we couldn't conclude anything until the evidence layer is complete and consistent. The actual finding is that the evidence catalog is the lever, not model selection.

---

## What "complete evidence layer" means concretely

Required before H3 (next calibration iteration):

1. **UA-GEC MCP** — blocked on PR #2055 → unblock + merge
2. **russian_shadow channel** — fix #2050 (import shim)
3. **Karavansky** — #2052 (build scraper + ingest; ~1-2 days work)
4. **Antonenko prose retrieval** — narrow the n-gram match (in H2 helper, NOT yet in MCP; per #2049 recommendations) OR ship `mcp__sources__search_antonenko_full` wrapper
5. **Holovashchuk** (#2053) and **Paronyms** (#2054) — lower priority; smaller payloads

When ALL these are live, refactor `scripts/audit/_judge_eval_lib.py` to call MCP tools instead of inline DB queries (consistency: same evidence layer the entire project uses), then re-run H3 calibration.

---

## What I would do as the next agent

Priority order:
1. **Get #2055 across the line.** Either help the user decide on `--no-verify` or actually debug the pre-commit env divergence. Without UA-GEC in MCP, every other consumer (writers, reviewers, bridge) is also missing this evidence layer.
2. **Fix #2050.** ~30 LOC change to `_judge_eval_lib.py`. Without it, future calibration runs continue to measure with one retrieval channel silently dark.
3. **Locate Karavansky source** (#2052). The hardest of the four data gaps. Could dispatch to a Gemini research session to confirm whether r2u.org.ua's structure has changed since the 2026-05-05 verification.
4. **Refactor inline helpers to MCP calls.** Once UA-GEC is in MCP, the H2 inline `_ua_gec_calque_search` helper in `_judge_eval_lib.py` becomes redundant. Replace with a thin wrapper over `mcp__sources__search_ua_gec_errors`.
5. **Fire H3.** Same 6 cells, but now against the complete + consistent evidence layer. Add max-effort cells for opus-4-7 if you want absolute ceiling.

**Do NOT:**
- Merge H1 (PR #2046) or H2 (PR #2049) prompt changes to production — they're diagnostics, the prompts themselves underperform baseline
- Skip the russian_shadow fix and claim H3 is conclusive — same confound
- Use the H2 "Gemini thrives" framing — it was retrieval-floor effect, not model temperament

---

## Worktree state (post-session)

Active dispatch worktrees still alive:
- `.worktrees/dispatch/claude/h1-evidence-rich-judge-2026-05-17` (PR #2046 OPEN)
- `.worktrees/dispatch/claude/h2-antonenko-fulltext-uagec-2026-05-17` (PR #2049 OPEN)
- `.worktrees/dispatch/gemini/h2c-typed-calibration-authoring-2026-05-17{,-v2,-v3}` (PR #2051 OPEN on v3; v1 and v2 are superseded — safe to clean up)
- `.worktrees/dispatch/gemini/ua-gec-mcp-ingest-2026-05-17` (PR #2055 OPEN — has the unmerged fix commit in flight)

Cleaned up this session: `.worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15` (post #2000 merge), `.worktrees/dispatch/claude/dagger-pre-push-hook-2026-05-17` (post #2056 merge).

---

## References

- Original calibration matrix harness: `scripts/audit/judge_calibration_matrix.py`
- Judge prompt + retrieval: `scripts/audit/_judge_eval_lib.py`
- MCP server: `.mcp/servers/sources/server.py`
- Pre-push hook script: `scripts/pre_push/dagger_pytest.sh`
- Pre-commit config: `.pre-commit-config.yaml`
- Calibration baseline report (HTML): http://localhost:8765/artifacts/audit/2026-05-17-judge-calibration-matrix/REPORT.html
- H1 diagnostic: `audit/2026-05-17-judge-calibration-h1/COMPARISON.md` (or PR #2046)
- H2 diagnostic: `audit/2026-05-17-judge-calibration-h2/COMPARISON.md` (or PR #2049)
- MEMORY.md #M-7 (pytest locally before push) — codifies the discipline; pre-push hook now enforces it
