# Claude session handoff — 2026-06-14 (cursor + grok-build reviewer fixes · 5-way reviewer bakeoff · #3087 deepseek routing · agy-noise research)

> **ROLE:** main orchestrator = infra / tooling / tech-debt / general features / integration / merge. Track issues (folk/bio/lit/seminar) are track-orchestrator-owned.

## TL;DR
Long session triggered by the user noticing on `runtime.html` that **cursor calls were 0/44 (all failing)** and demanding it be fixed + proven, plus the proper #3087 reviewer comparison "now that all of them work." Root-caused and fixed TWO distinct reviewer breakages, ran the real 5-way bakeoff, shipped the reviewer routing decision, and researched agy noise. **Nothing in flight at handoff.**

## Shipped (all merged to main)
- **#3155** (`4c3a63a67f`) — `fix(agent-runtime): wire cursor sources-MCP + correct grok-build model id`. Contains 4 proven fixes:
  1. **cursor** — adapter never wired the `sources` MCP server (only toggled `--approve-mcps`). Dispatch (codex) added the MCP wiring. **Proven: cursor PASS/8, was 0/44.**
  2. **grok-build model id** — registry/adapter/bridge defaulted to `grok-4.20` (a *Hermes* model id); native grok CLI only knows `grok-build`/`grok-composer-2.5-fast`. Fixed → `grok-build`. Closed **#3151**.
  3. **grok-build permission mode (my inline fix)** — review runs `read-only` → adapter mapped to grok `--permission-mode plan`, which is **analysis-only and BLOCKS tool execution** → grok planned the MCP call but never ran it → empty/`stopReason=Cancelled`. Override `plan`→`bypassPermissions` only when read-only MCP servers requested. **Proven: grok-build PASS/10.**
  4. **grok-build security hardening (my inline fix, from a HIGH security-review finding)** — `bypassPermissions` over-permissioned a review of *arbitrary article content* (prompt-injection → file-write/shell). Added `--deny Write/Edit/MultiEdit/NotebookEdit/search_replace/Bash` (**deny wins over bypass** per grok's model), `--disable-web-search`, and a read-only-server allowlist (`{sources}`). **Proven still PASS/10.**
- **#3160** (`10ba702fb5`) — `feat(wiki): route CORE factual_accuracy+register off Gemini → deepseek (#3087)`. Added `core_reviewer_overrides()` (mirrors `seminar_reviewer_overrides`), merged into compile path `{**core, **seminar}`; `DEFAULT_PRIMARY` untouched. Diff reviewed inline = APPROVE. Closed **#3087**.

## The 5-way reviewer bakeoff (the #3087 decision data)
Same dense B1 article (`grammar/b1/short-form-adjectives.md` + an A1 article), 3 repeats, single-pass, no-fallback. Decisive metric = score σ (reliability):

| reviewer | factual σ | register σ | err | ~latency | verdict |
|---|---|---|---|---|---|
| **deepseek** | **0.47** | **0.0** | 0 | 387s | ✅ winner |
| claude | 0.0 | 0.82 | 1 | 346s | reliable but quota + 1 flake |
| agy (status quo) | 0.94 | 0.0 | 0 | 143s | documented factual noise |
| cursor | 0.94 | 0.0 | 1 | 156s | no better than agy |
| grok-build | **2.83** (10,10,4) | 0.47 | 0 | 202s | worst reviewer (good code agent) |

→ **deepseek** chosen for CORE. cursor/grok-build work now but are NOT good reviewers — their value is that they stopped silently burning money.

## #3159 — agy-noise research (filed)
**Structural, not tunable.** agy = Gemini 3.5 Flash via Antigravity CLI; `agy --help` exposes **no temperature/top-p/seed** (only `--model`) → reviews run at default temp → non-deterministic by construction. Fix = route critical dims off agy (= #3087/#3057). Where agy must stay: constrained rubric / Pro model / deterministic recompute (none free). Full detail in #3159.

## MONEY/COST GAP found (important, user cares — "it's my money")
Usage records (`batch_state/api_usage/*.jsonl`, 217 files) capture **call counts + char counts but ZERO cost/tokens** — every agent shows `$0.000`. **You currently cannot see dollar spend.** Per-agent call/ok data IS valid (codex 424/459, gemini 261/273, claude 213/224, deepseek 90/101, cursor 0/44→fixed, agy 42/43, grok 21/21, grok-build 3/9→fixed).

## Queued — NOT started
- **#3153** (auto-telemetry) — PR1 brief WRITTEN at `docs/dispatch-briefs/2026-06-14-telemetry-auto-capture-pr1.md` (central JSONL emitter + correlation IDs + dispatch event; emitter at `scripts/telemetry/emit.py` NOT the existing `agent_runtime/telemetry.py` which is a metadata resolver). **Expand PR1 to capture cost/tokens first-class** — directly serves the money-visibility concern. Ready to fire. User was asked fire-now vs stop; answered "session handoff" instead.
- **#3150** (Atlas auto-freshness) — manifest + vocab→Atlas MDX drift gate; design done, fingerprint-gate + local regen (CI can't regen: needs 967MB vesum.db). Tied to #3097 (slovnyk mirror, design-gated).
- Earlier infra queue still open: #3098 §6 calque layer, #3116 §7 qualifiers, deps #2732/#2261.

## State at handoff
- main == origin/main (`b9b1a78078`), tree clean except 3 untracked dispatch briefs in `docs/dispatch-briefs/` (records of this session's dispatches — keep or commit).
- 0 dispatches in flight, 0 stray procs, all session worktrees reaped.
- Bakeoff data preserved: `batch_state/bakeoff/stage1.jsonl` (agy/deepseek/claude) + `stage2.jsonl` (cursor/grok-build), driver `batch_state/bakeoff/reviewer_bakeoff.py`.

## Key learnings / watch-items
- **Verify, don't trust dispatch self-reports** — the cursor-grok dispatch claimed both worked (`DIM_RESULT REVISE 6`); independent runs showed grok-build genuinely Cancelled. The user explicitly distrusted self-reports (rightly).
- **Timeout methodology**: MCP-grounded reviews take ~2–6.5 min; a 300s test cap produces FALSE failures (burned one cursor "fail"). Use ≥720s for review proofs.
- grok lanes: **`grok-build` agent = native grok CLI** (models `grok-build`/`grok-composer-2.5-fast`); **`grok` agent = Hermes** (`grok-4.3`/`grok-4.20`). Never put a Hermes model id on the native-CLI agent.
- grok permission model: `--permission-mode dontAsk/acceptEdits` are accepted but NOT enforced via CLI; only `bypassPermissions`/`default` take effect. `--allow`/`--deny` rules work regardless of mode and `deny` > bypass.
