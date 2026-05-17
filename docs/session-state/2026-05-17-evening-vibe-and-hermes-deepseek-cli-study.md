---
date: 2026-05-17
session: "Evening — user at Ukrainian lesson. Orchestrator studied `vibe` (Mistral) + `hermes` (DeepSeek v4) CLIs inline per afternoon handoff. CLI surfaces mapped, 4 PONG + 4 domain-capability probes run. One CRITICAL finding: devstral-small fails Ukrainian Russianism judgment (Russian-pretraining contamination)."
status: green  # study complete, awaiting user sign-off on routing implications
main_sha: ed953e65b2
main_green: true
open_prs: [1873]  # dependabot only
active_dispatches: 0
worktrees_open: 1  # main + clawpatch-trial (eval artifact)
predecessor: docs/session-state/2026-05-17-afternoon-path3-decision-card-handoff.md

p0_for_user_return:
  - "REVIEW this handoff. Confirm routing recommendations (esp. devstral-small CARVE-OUT)."
  - "Confirm bakeoff target: HIGH-severity clawpatch bug #2099 vs MEDIUM #2100/2101/2102."
  - "On sign-off: orchestrator re-arranges queue + fires Path 3 PR1."

unchanged_decisions:
  - "All 4 afternoon decisions stand (Path 3, m20 bridge=A, evidence-layer, clawpatch ACTIVE)."
  - "Per-area routing table from afternoon handoff: VALID for mistral-medium-3.5. INVALID for devstral-small on any UK-content surface — see finding #1."
---

# Findings — `vibe` (Mistral) + `opencode` (DeepSeek v4 max) + `hermes` (Grok) CLI study

## CORRECTION (user direction, post-initial-handoff)

User clarified: **DeepSeek lane goes through `opencode` (max effort)**, NOT through
hermes. Hermes stays as the **Grok** lane (which is what `hermes_grok.py` already does).
Re-probed; key updates:

- **opencode + deepseek-v4-pro `--variant max`:** PONG **13.1s** (cold-start tax),
  Russianism **11.3s CORRECT** — with grammar-detail bonus ("instrumental case used
  as a preposition"). Faster than hermes on the substantive probe (11.3s vs 37.5s)
  despite slower PONG.
- **opencode `--format json` event stream is RICHER than hermes:** emits
  `step_start` / `text` / `step_finish` events with `tokens: {total, input, output,
  reasoning, cache.read, cache.write}` + `cost` per call. Hermes `-z` gives us
  none of this — `hermes_grok.py` flagged `tool_calls_total=None` because of it.
- **Adapter target changes** from `hermes_deepseek.py` to `opencode_deepseek.py`.
  Better shape: real telemetry parity with claude/codex/gemini adapters.
- **Hermes-DeepSeek probe data** below is preserved for forensic value but
  superseded by opencode for routing.
- Sample telemetry envelope from a real opencode JSON call:
  ```
  step_finish: {tokens: {total: 13177, input: 6758, output: 3, reasoning: 16,
                          cache: {write: 0, read: 6400}}, cost: 0.01275304}
  ```
  Cost surfaced per-call — directly wires into `/api/state/routing-budget`.

Everything else in this handoff stands; routing table updated below in
"Routing implications" section to use opencode-deepseek-v4-pro.

## TL;DR (3 lines)

1. **Both CLIs alive, auth configured.** `vibe -p` and `hermes -z` are clean one-shot
   surfaces ready for `delegate.py` + `ab` integration. PONG round-trips: vibe 3-4s,
   hermes 3-5s.
2. **Critical capability gap:** `devstral-small` FAILED the canonical Russianism test
   (`на протязі` → "correct UK") — Russian-pretraining contamination. The other 3
   (`mistral-medium-3.5`, `deepseek-v4-pro`, `deepseek-v4-flash`) ALL CORRECT.
3. **Routing recommendation:** Pin **`mistral-medium-3.5`** for any UK-content surface;
   carve **`devstral-small`** out to non-Ukrainian work (infrastructure code-review,
   starlight TS, build scripts only). Recommended bakeoff target on user return:
   **clawpatch HIGH #2099** (`audit_level.py` CI-trust killer) — code-only, no UK
   content, lets devstral-small + flash compete on the lane they're actually fit for.

## Capability matrix (probes I just ran)

| Probe | `mistral-medium-3.5` (vibe) | `devstral-small` (vibe) | `deepseek-v4-pro` (hermes) | `deepseek-v4-flash` (hermes) |
|---|---|---|---|---|
| **PONG** | ✅ 4.0s | ✅ 3.2s | ✅ 4.8s | ✅ 3.6s |
| **Russianism: `на протязі`** | ✅ correct: "YES (Russianism). Use 'протягом'" — 7.7s | ❌ **WRONG**: "NO (correct UK)… standard Ukrainian for 'during'" — 3.2s | ✅ correct: "YES… Russian calque (← *на протяжении*); standard Ukrainian = протягом + gen" — 37.5s | ✅ correct + best output: "YES… syntactic calque; **на протязі** is only correct for literal 'in a draft of air', not temporal" — 26.8s |

**Reasoning observations:**
- DeepSeek pro and flash both ENGAGE substantial reasoning tokens on the substantive
  probe (5-8× the PONG latency). Flash actually beat pro on output quality (polysemy
  disambiguation) despite being the "lighter" variant — for our use cases the
  routing assumption "pro = default, flash = lighter" may be wrong.
- Mistral medium-3.5 was fastest on the substantive probe (7.7s) with terse-correct
  output — no reasoning trace.
- Devstral-small was nearly as fast on substantive (3.2s) as on PONG (3.2s), which
  tells us it did NOT reason about the question. It pattern-matched. Bad signal for
  any UK-content task.

## CLI surface — `vibe` (Mistral)

```
vibe [-p PROMPT] [--output text|json|streaming] [--max-turns N] [--max-price $]
     [--enabled-tools TOOL] [--agent NAME] [--workdir DIR] [--trust]
     [-c | --resume [SESSION_ID]]
```

- **One-shot:** `vibe -p "PROMPT" --output text --trust` — auto-approves all tools,
  prints response, exits. This is the `delegate.py` / `ab discuss` integration shape.
- **Model override:** `VIBE_ACTIVE_MODEL=mistral-medium-3.5 vibe -p ...` (env var) OR
  edit `~/.vibe/config.toml` `active_model`. **No `-m` flag.**
- **Tool gating:** `--enabled-tools` accepts exact names, globs, regex. In `-p` mode
  enabling specific tools disables all others — explicit allowlist, MCP-server-name
  friendly.
- **MCP support:** native via `mcp_servers = [...]` in `~/.vibe/config.toml`. Empty
  by default; needs the same `sources` server registration that Claude/Codex/Gemini
  use.
- **Worktree:** `--workdir DIR` + `--trust` skip the trust prompt for non-interactive
  automation. No built-in `git worktree add` — adapter must create the worktree itself.
- **Warm-cache resume:** `-c`/`--continue` or `--resume [SESSION_ID]` — matches our
  existing claude/gemini/codex pattern.
- **Budget cap:** `--max-price DOLLARS` and `--max-turns N` — native cost gate.
- **Agents:** builtin (`default`, `plan`, `accept-edits`, `auto-approve`) or a custom
  toml at `$VIBE_HOME/agents/<NAME>.toml` (per `vibe --help`; `VIBE_HOME` defaults to
  the user's `.vibe` directory). We can ship a `curriculum-writer` agent toml the
  same way we ship `claude_extensions/agents/curriculum-orchestrator.md`.

## CLI surface — `hermes` (DeepSeek v4 — and Grok)

```
hermes [-z PROMPT] [-m MODEL] [--provider PROVIDER] [-t TOOLSETS]
       [--resume SESSION | --continue [SESSION_NAME]] [--worktree]
       [--accept-hooks] [--skills SKILLS] [--yolo] [--pass-session-id]
       [--tui] [--dev]
```

- **One-shot:** `hermes -z "PROMPT" -m deepseek-v4-pro` — clean stdout only, no
  banner/spinner/tool-preview. Auto-bypasses approvals.
- **Model override:** `-m deepseek-v4-pro` or `-m deepseek-v4-flash` or
  `-m grok-4.3`. Applies to `-z` and `--tui`. Also `HERMES_INFERENCE_MODEL` env var.
- **MCP support:** `hermes mcp add/configure/list` — registry-based, native. Existing
  `hermes_grok.py` adapter already validates `sources` server registration via
  `_sources_mcp_registered()`. DeepSeek adapter can reuse the same check.
- **Worktree:** **built-in `--worktree`/`-w`** flag — Hermes creates an isolated git
  worktree on its own, unlike vibe. Major ergonomic advantage.
- **Warm-cache:** `--resume SESSION` (by ID) or `--continue [SESSION_NAME]` (by name
  or most recent). Same shape as Claude/Codex/Gemini.
- **`--tui`** flag launches the modern TypeScript TUI (with `--dev` running source via
  tsx). **Not relevant to dispatch lane** — interactive only. Useful for the user when
  they want to chat with DeepSeek v4 directly.
- **`hermes proxy`** subcommand exists but **ONLY supports Nous Portal upstream**
  (`hermes proxy providers` → `nous — Nous Portal`). **Does NOT replace our `:8767`
  proxy from PR #2025** — that question is settled.

## Integration shapes for delegate.py / ab / openai_proxy

### `delegate.py dispatch --agent mistral` (NEW lane)

Pattern: model on adapters/codex.py (Mistral CLI shape closer to Codex than Hermes):

```python
# scripts/agent_runtime/adapters/vibe_mistral.py
class VibeMistralAdapter:
    cli = "vibe"
    one_shot_args = ["-p", "--output", "text", "--trust"]
    model_via = "env"  # VIBE_ACTIVE_MODEL=...
    worktree_via = "manual"  # create with `git worktree add`, then --workdir
    warm_cache = "-c"  # or --resume SESSION_ID
```

Key gotchas:
1. **No `-m` flag** — model selection is via `VIBE_ACTIVE_MODEL` env var. Adapter
   must set it per call. Race-safe because env is per-invocation.
2. **No native worktree** — adapter creates `git worktree add` first, then passes
   `--workdir DIR`. Mirrors how we wrap codex/claude/gemini.
3. **No streaming tool-call telemetry in `-p` text mode** — to get tool calls,
   switch to `--output streaming` (newline-delimited JSON per message) or
   `--output json` (all messages at end). For V7 writer telemetry parity, need
   the streaming envelope.

### `delegate.py dispatch --agent deepseek` (NEW lane via opencode — CORRECTED)

Pattern: new adapter `scripts/agent_runtime/adapters/opencode_deepseek.py`. Modeled
on claude/codex adapters (rich JSON event stream), NOT on `hermes_grok.py`.

```
opencode run \
  --model deepseek/deepseek-v4-pro \
  --variant max \
  --dangerously-skip-permissions \
  --format json \
  --dir <worktree_path> \
  "PROMPT"
```

```python
# scripts/agent_runtime/adapters/opencode_deepseek.py
class OpencodeDeepseekAdapter:
    cli = "opencode"
    subcommand = "run"
    model = "deepseek/deepseek-v4-pro"
    variant = "max"  # provider-specific reasoning effort
    permissions = "--dangerously-skip-permissions"  # auto-approve
    output = "--format json"  # emit JSONL events
    worktree_via = "--dir"  # manual git worktree add + pass --dir
    warm_cache = "-c/--continue or -s SESSION_ID"
    # Telemetry parity with claude/codex:
    #   - step_start / text / tool_use / step_finish events
    #   - step_finish.tokens = {total, input, output, reasoning, cache.{read,write}}
    #   - step_finish.cost = per-call USD
```

Key wins vs the originally-proposed hermes path:
- **Real telemetry**: `tool_calls_total` is computable from `tool_use` events; no
  need for the `None` sentinel that `hermes_grok.py` had to carry.
- **Per-call cost** surfaced directly — routing-budget endpoint gets cleaner data.
- **`--variant max`** is opencode's reasoning-effort flag (`high`, `max`, `minimal`
  per `opencode run --help`). User's directive "max effort" maps cleanly.
- **Cache read/write** counters mean we can verify prompt-cache hit rate the same
  way Claude/Codex give us.

### Hermes adapter scope (clarification)

Hermes stays as the **Grok** lane via the existing `hermes_grok.py`. The DeepSeek
probes I ran via hermes earlier in this handoff are forensic data only — they are
NOT the production path. No `hermes_deepseek.py` adapter to write.

### `ab ask-mistral` / `ab ask-deepseek` (Q&A bridge)

Trivial — wire both as new flat-string identities in `ai_agent_bridge` like Codex
Desktop / Claude Desktop were wired (`cli_available=True` since the binaries are
real CLIs, unlike the Desktop wrappers).

### Existing `:8767` OpenAI-compat proxy

PR #2025 covers `codex` / `gemini` / `claude` / `grok-via-hermes` upstreams.
Adding `deepseek-v4-pro` / `deepseek-v4-flash` upstreams is a small extension to
`scripts/ai_agent_bridge/openai_proxy.py` (DeepSeek is OpenAI-compatible at the
API layer; the proxy just needs the `/v1/chat/completions` routing). Mistral is
also OpenAI-compatible (`https://api.mistral.ai/v1` per `~/.vibe/config.toml`).
**Neither requires a new proxy backend** — both are bog-standard OpenAI-compat.

## Routing implications for afternoon-handoff per-area table

The afternoon handoff proposed:

| Area | Today (4 agents) | When DeepSeek + Mistral online |
|---|---|---|
| scripts/build/ | Claude headless | Claude ↔ Mistral |
| scripts/wiki/ + curriculum/ | Gemini | Gemini ↔ Mistral |
| Frontend starlight/ | Claude | Claude ↔ Mistral |

**Action required:** disambiguate **Mistral** in those rows to `mistral-medium-3.5`
explicitly. `devstral-small` is now a separate, narrower routing target.

Proposed refined table (corrected: opencode is the DeepSeek harness; hermes is the Grok harness):

| Area | Today | + DeepSeek + Mistral |
|---|---|---|
| scripts/audit/ | Codex | Codex ↔ opencode-deepseek-v4-pro-max |
| scripts/build/ | Claude headless | Claude ↔ mistral-medium-3.5 |
| scripts/wiki/ + curriculum/ | Gemini | Gemini ↔ mistral-medium-3.5 |
| tests/ | Codex | Codex ↔ opencode-deepseek-v4-pro-max |
| .mcp/servers/ | Codex | Codex ↔ opencode-deepseek-v4-pro-max |
| Frontend starlight/ | Claude | Claude ↔ mistral-medium-3.5 OR devstral-small (TS-only, no UK content) |
| scripts/ infrastructure | Claude | Claude ↔ hermes-grok-4.3 or devstral-small (code-only, no UK) |
| **UK content surfaces (anywhere)** | — | **NEVER devstral-small** |

`devstral-small` carve-out applies anywhere a model might see Ukrainian text
verbatim (writer prompts, reviewer prompts, curriculum/, wiki/, audit/ when the
audit reads module content). Code-only surfaces are fine.

## Recommended next-action: bakeoff target

**Recommend: clawpatch HIGH #2099** (`audit_level.py` full-level audits exit 0
with no modules audited). Rationale:

1. **Code-only** — no Ukrainian content. Lets `devstral-small` + `deepseek-v4-flash`
   compete on the lane they're actually fit for, vs CompetingAgainst Codex.
2. **HIGH severity** — fixing it is real value, not just bakeoff theater.
3. **Bounded** — Python script audit, well-defined predicate (CI-trust passes when
   audit_level on an empty set exits non-zero).
4. **Symmetric** — each candidate gets the same brief + same evidence; we measure
   (a) PR shipped Y/N, (b) tests included Y/N, (c) latency, (d) diff quality.

Alternative: **#2100** (`audit_external_resources.py` path bug, one-line fix) —
faster but lower signal because the work is too small for capability differentiation.

I have NOT fired this bakeoff. Awaiting your sign-off on (a) target choice,
(b) bakeoff design (4-way vs 2-way vs sequential), and (c) `devstral-small`
carve-out before re-arranging the queue.

## What I did NOT do (and why)

- **Did not fire Path 3 PR1.** Explicitly per afternoon handoff: "Re-arrange queue
  based on what study reveals (user explicit 'we might need to rearrange')." Queue
  rearrangement waits for your sign-off on the findings above.
- **Did not write `vibe_mistral.py` or `hermes_deepseek.py` adapters.** Implementation
  ships as a follow-up PR after routing decisions land. Adapter shapes documented
  above are scoping notes, not code.
- **Did not extend `openai_proxy.py` for Mistral/DeepSeek upstreams.** Same reason —
  wait on routing sign-off.
- **Did not run vibe + devstral-small concurrently** — per #M-9 LOCAL FANOUT ONE AT
  A TIME. All 8 probes (4 PONG + 4 Russianism) ran sequentially.

## Files I touched

- THIS document (new, MD per #M-2 ai→ai handoff).
- Probed `vibe`, `hermes`, `~/.vibe/config.toml` (read-only).
- No code changes. Working tree at `ed953e65b2` plus this new handoff doc.

## Open questions for user on return

1. **Bakeoff target:** clawpatch #2099 HIGH (recommended) OR something else?
2. **Bakeoff shape:** 4-way concurrent (codex + claude + mistral-medium-3.5 +
   deepseek-v4-pro), 2-way head-to-head, or sequential? Recommended: 2-way
   **deepseek-v4-pro vs codex** on the same #2099 brief, since codex is our
   incumbent for `scripts/audit/`.
3. **Devstral-small lane:** which non-UK surface gets it as primary? Recommended:
   `scripts/ infrastructure` (code-only paths) — leave Claude as the architecture
   reviewer there.
4. **DeepSeek flash vs pro:** based on my single probe, flash was actually MORE
   thorough than pro. Want me to expand the probe set, or proceed with pro as
   default + flash as cost-cap fallback per afternoon handoff?
5. **Adapter implementation timing:** dispatch the `hermes_deepseek.py` +
   `vibe_mistral.py` adapter PRs BEFORE Path 3 PR1, or AFTER? Recommended: AFTER
   — Path 3 doesn't depend on the new agents, and we need a real adapter test
   ride before trusting them on production work anyway.

## Sequence on user return (proposed)

1. User reviews this handoff, confirms or revises findings.
2. User signs off bakeoff target + shape + devstral-small carve-out.
3. Orchestrator re-arranges queue with confirmed routing.
4. Orchestrator fires Path 3 PR1 (skeleton seeder) to Codex.
5. **In parallel** (different Codex dispatch lane is full, so sequential):
   bakeoff dispatch fires after Path 3 PR1 confirmation.
6. PR2-PR4 sequential through Path 3 completion.
7. m20 rebuild under Path 3 architecture → ships as proof-of-pipeline.
8. Phase 2b A1 batch under Path 3.

## Predecessor chain

1. `docs/session-state/2026-05-17-afternoon-path3-decision-card-handoff.md`
2. THIS DOCUMENT (evening — vibe + hermes-DeepSeek CLI study)

## Format note

MD per #M-2 (ai→ai handoff). HTML companion deferred — this is study/scoping output,
not a build/audit result with rich human-read value.
