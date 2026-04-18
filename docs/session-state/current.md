# Session Handoff — 2026-04-18 close

You're starting cold. Boot via the API, not the filesystem:

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap()      # manifest + cached rules + this file
```

Then `curl /api/orient` for live state and `curl /api/comms/inbox?agent=claude` for unread messages. **Do not** read `CLAUDE.md` or `claude_extensions/rules/*.md` directly. See `docs/MONITOR-API.md` for endpoints.

## 🟢 Dimensional review system — Phase 1 SHIPPED

User's idea: replace the single-call 9-dim module review with parallel dimensional review (specialist personas per dim, per-dim min-score gates, no weighted averaging). User sequencing: **wiki first, then modules.**

**Full design:** `docs/design/dimensional-review.md` (~500 LOC, absorbs Codex adversarial review — App D has the finding log).

### Phase 1 commits (this session — 4 commits ahead of origin)

| Commit | What |
|---|---|
| `a21ffbfc7` | `fix(runtime): CodexAdapter honors tool_config for MCP failover (#1325)` — Codex can now serve MCP-requiring dims as fallback. Real `codex exec` smoke test passed. |
| `c55bc3997` | `feat(wiki): code gates for Джерела section + citation-registry (#1326)` — quality_gate.py now emits `SOURCES_SECTION_PRESENT`, `ORPHAN_INLINE_REF`, `UNUSED_SOURCE`, `MISSING_SOURCES_YAML`, `MALFORMED_SOURCES_YAML`. |
| `cf48b25d4` | `feat(wiki): dimensional review design + source-grounding prompt + compile fix` — design doc, first dim reviewer prompt (`scripts/wiki/prompts/review_source_grounding.md`), compile_article.md no longer emits `## Джерела`. |
| `492d62d4d` | `docs(archive): preserve two historical memory files as archive records` — memory audit, 30→23 files. |

### Phase 2 — start here when you resume

1. **3 more wiki dim reviewer prompts** (factual_accuracy, ukrainian_perspective, register) — pattern: `scripts/wiki/prompts/review_source_grounding.md`. Each ~150-200 LOC.
2. **Orchestrator** at `scripts/wiki/review.py` — parallel dimensional calls via `scripts/agent_runtime/` (unified runtime, design §6a), prewarm-then-fan-out for Claude (§6b), deterministic fix-merger — NOT single LLM patcher (§6c), per-dim gates (§6d), primary+fallback failover (§9 Q4).
3. **Seeded benchmark** per design §7b — 5 wiki × 3 versions × 3 agents × 4 dims × 3 reruns ≈ 540 calls. Freezes agent assignments + per-dim thresholds.
4. **Canary rollout** per §8 — rebuild small wiki batch with review in shadow mode, calibrate, promote to hard gate.

Phase 3+ (module refactor) waits for Phase 2.

## Load-bearing decisions this session (don't re-litigate)

- **Reviewer policy**: Codex primary for contract/structural dims. Claude primary for decolonization + engagement + dialogue. Gemini primary for linguistic/factual/pedagogical/register. All dims have fallback agent (primary+fallback matrix, design doc §3/§4). Self-review is OFF. Cross-agent mandatory.
- **Ukrainian for artifact, English for reviewer instructions** until Phase 2 benchmark proves parity (design §2 principle 11). Decolonization principle preserved — learner-facing content stays Ukrainian.
- **No LLM patcher.** Reviewer-as-fixer per dim + deterministic fix-merger in code. ADR-001 already rejected centralized rewrites (9.6→8.4 degradation).
- **Engagement rubric is decomposed**, not a "Zhadan gate." A Zhadan-as-gate test would punish correct A2 plainness. Sub-checks with per-level weights (design §5.5).
- **Humor is structural, not decorative.** Humor-under-siege (Zhadan), NOT cheerful-imperial-erasure. Chipper register while Kharkiv is bombed = failure mode.
- **Outward clarity** is a decolonization signal — Ukrainian voices that see other societies with artistic authority (Zhadan-on-Orbán). Curriculum is not parochial.
- **Calibration limit**: reviewer catches structural failures; cannot judge Zhadan-register tonal authenticity. Native ear (Tetiana / user) is final arbiter.

## Fact corrections for persona / content writing

- **Yulia Svyrydenko** — current PM (2025-07-17), safe to reference positively.
- **Yulia Tymoshenko** — DO NOT reference; user framing "Russian sellout."
- **President = highest Ukrainian leader**, not PM.
- **Do NOT invent historical figures.** 2026-04-18 lesson: fabricated "Hetman Tymoshenko." Verify via `mcp__sources__query_wikipedia` before naming anyone.
- **Bulgakov is NOT Ukrainian canon.** Russian-imperial, wrote Ukrainian revolution forces as bandits, removed from Ukrainian institutions since 2022. Same for Gogol (as "Ukrainian"), Akhmatova, Pasternak.
- **Safe Ukrainian literary touchstones**: Shevchenko (lineage anchor), Zhadan (contemporary north-star), Zabuzhko, Andrukhovych, Pidmohylny, Stus, Khvylovy, Lesya Ukrainka, Franko.
- **Humor touchstones**: Zhadan band (*300 китайців*, *Холодна Гора*), Телебачення Торонто, Наші без раші (user-recommended, unverified by me).
- **BIO seminar track = BIOGRAPHIES, not biology.**
- **Wiki is strictly Ukrainian across all levels** (decolonization principle). No production wiki exists yet — rebuild is pending, will produce clean output with today's compile prompt fix + new code gates.

## Behavior changes callers may trip on (preserved from prior handoff)

- `scripts/wiki/state.py:is_compiled` AND-checks on-disk file + self-purges stale rows.
- `ai_agent_bridge --stdout-only` now actually writes Gemini response to stdout. Wiki parser depends on this. `bash scripts/ops/smoketest_bridge_stdout_only.sh` after any bridge change.
- `services.sh restart` serialized via mkdir-lock at `.pids/.restart.lock.d/`.
- **NEW 2026-04-18**: `CodexAdapter` (`scripts/agent_runtime/adapters/codex.py`) now honors non-None `tool_config` and emits `-c mcp_servers.<name>.<key>=<value>` CLI flags. Callers passing `tool_config=None` behave identically to before (backward compat).
- **NEW 2026-04-18**: `scripts/wiki/quality_gate.py` emits 5 new check types. Downstream consumers that filter check outputs should handle these.
- **NEW 2026-04-18**: `scripts/wiki/prompts/compile_article.md` no longer emits `## Джерела` block. Articles generated with this prompt do not need the section stripped post-compile.

## Decisions still pending (from prior session, not touched today)

| # | Decision | Resolve by |
|---|---|---|
| 1 | **Phase B kickoff** — different pipeline from Phase A; proceed or re-verify | Say "go Phase B" or "rerun Phase A" |
| 2 | **Merge #1323 + #1324 round-2 patches** as-is or re-verify | Spot-check regression tests |
| 3 | **`rclone config`** for Phase C backup activation (OAuth needs browser) | `rclone config` + install cron |
| 4 | **Restore agent-watcher LaunchAgent?** Unloaded, backup at `.disabled-2026-04-18` | Leave unloaded unless auto-broker needed |
| 5 | **Cold-start-handoff pattern deltas** — `scripts/cold-start.sh` wrapper, bridge-smoketest pre-commit hook, audit other `session-state/*.md` for bloat | Pick one or all when resuming |

## Open design questions still needing user input (not blocking Phase 2 Step 1)

- Engagement per-level weights (design §5.5 table) — user/Tetiana calibration before freezing
- Orchestrator availability-detection signal — resolve during Phase 2 Step 2 when building orchestrator
- §9 question 2 — Ukrainian-vs-English instruction benchmark — part of Phase 2 seeded benchmark

## Archived

Earlier running-log handoff (pre-dimensional-review work): `docs/session-state/2026-04-18-am-autonomous-handoff.md`.
