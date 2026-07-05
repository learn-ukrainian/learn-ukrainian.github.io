# Hermes Agent — usage guide for learn-ukrainian

> **Status:** baseline survey 2026-05-16 (v0.13.0) · **refreshed 2026-07-05 against live
> v0.18.0 (2026.7.1)** — auth pool re-probed, § Automation adoption plan added.
> Replaces "Hermes is a thin LLM wrapper" mental model. It is a full agent
> platform with 40+ subcommands, a SQLite session store, native delegation,
> kanban, cron, skills, plugins, and messaging gateways.

## TL;DR for orchestrators

- **Hermes is NOT a thin wrapper.** Every `hermes -z` we fire spawns a real agent loop (up to `max_turns=90`), with auto-discovered tools, MCP routing, session persistence, and prompt assembly across 8 slots.
- **`SOUL.md`** at `~/.hermes/SOUL.md` is the persona / identity slot for `-z` calls. **This IS our knob.** Edited 2026-05-16 with project-aware content (technical, tool-disciplined, Ukrainian-curriculum aware).
- **`/personality` is interactive-only.** It does not apply to `-z` mode. The `personalities:` dict in config.yaml is a registry for the slash command.
- **Hermes already has** delegation, kanban, cron, openai-compat proxy, memory, session store, ACP IDE mode, and 20+ messaging-platform adapters. We've duplicated several of these in-house (`delegate.py`, ai_agent_bridge, our `:8767` proxy, Monitor API). Migration question: open.

## The system-prompt stack (`-z` one-shot mode)

When you run `hermes -z PROMPT -m model`, the system prompt is built from 8 slots (per `run_agent.py:_build_system_prompt_parts` + `website/docs/user-guide/features/personality.md`):

| # | Slot | Source | Applies to `-z`? |
|---|---|---|---|
| 1 | **Agent identity** | `$HERMES_HOME/SOUL.md` (or built-in fallback if empty) | ✅ YES |
| 2 | Tool-aware behavior guidance | `model_tools.py` constants per model family | ✅ YES |
| 3 | Memory / user context | Built-in memory store + (optional) external memory plugin | ✅ YES unless `--ignore-rules` |
| 4 | Skills guidance | `agent/prompt_builder.build_skills_system_prompt()` | ✅ YES |
| 5 | Context files | `AGENTS.md`, `.cursorrules` from CWD | ✅ YES unless `--ignore-rules` |
| 6 | Timestamp | injected at message time | ✅ YES |
| 7 | Platform-specific hints | per-provider operational guidance | ✅ YES |
| 8 | `/personality` overlay | interactive `/personality NAME` command | ❌ NO (interactive-only) |

**The skip flag** `skip_context_files=True` (set when `--ignore-rules` is passed, in curator runs, and in batch_runner contexts) bypasses slots 1+3+5. Default for our calls is `False` → all slots active.

**Also injected:**
- `agent.system_prompt` (config field) or `HERMES_SYSTEM_PROMPT` env var → `ephemeral_system_prompt` — applied at execution time, **NOT saved to trajectories**. Use for per-invocation overrides that shouldn't pollute the session log.

## SOUL.md — the durable persona knob

`~/.hermes/SOUL.md` is loaded **fresh on every message** (no restart). It occupies slot #1 — the agent identity position — and replaces the hardcoded default ("You are Hermes Agent, an intelligent AI assistant created by Nous Research...") with whatever you write.

**Current content (2026-05-16):** project-aware persona at `~/.hermes/SOUL.md` setting tone (direct, no sycophancy, no fictional characters), tool discipline (deterministic over hallucination — verify before guessing), Ukrainian linguistic principles (VESUM → Правопис → Горох → Антоненко-Давидович → Грінченко authority hierarchy; рос**і**янізм not русизм), and operational posture (root-cause, not symptom-patch; word counts are minimums).

**To edit:** just rewrite the file. Hermes re-reads on every message.

**To verify it's loaded:** check `~/.hermes/sessions/session_*.json` for the most recent session — search for `"system_prompt"` and confirm SOUL.md content appears in slot #1.

## Auth pool (per `hermes auth list` — re-probed 2026-07-05, v0.18.0)

| Provider | Type | Source | Status |
|---|---|---|---|
| deepseek | api_key | env `DEEPSEEK_API_KEY` | ✅ (dirt-cheap lane — the delegate deepseek adapter rides this) |
| openai-codex | oauth | device_code | ✅ (gpt-5.5 via subscription) |
| openrouter | api_key | env `OPENROUTER_API_KEY` | ✅ (long-tail catalog: qwen, gemma, …) |
| xai-oauth | oauth | loopback_pkce (Grok) | ✅ |
| zai | api_key | env `GLM_API_KEY` | ✅ (⚠️ GLM = China-hosted — same LOCAL-ONLY rule as opencode glm: never CI/automated pipelines) |

**Changed since the May baseline:** anthropic and copilot are gone from the pool; DeepSeek and
OpenRouter now flow through API keys (the May doc's "all API keys UNSET" no longer holds).
Historical lesson from the anthropic silent-drop era (#2036) stands: **never trust the
`auth status` flag; probe with an actual call.** Auth changes between refreshes —
`hermes auth list` is the source of truth, not this table.

## MCP servers (per `hermes mcp list`)

```
sources    http://127.0.0.1:8766/mcp    all tools    ✓ enabled
```

Only our project's `sources` server is registered. It exposes 30+ Ukrainian-source tools (`verify_word`, `verify_words`, `verify_lemma`, `check_modern_form`, `search_text`, `check_russian_shadow`, `query_pravopys`, `search_grinchenko_1907`, `search_style_guide`, `search_synonyms`, `query_cefr_level`, `search_heritage`, etc.). Tools auto-flow into the model's tool list on every `-z` call (no per-invocation flag needed).

## Built-in toolsets enabled by default (`hermes tools list`)

> **v0.18.0 re-probe (2026-07-05): 16 toolsets enabled** (was 11 in May). New since the
> baseline: `x_search`, `session_search`, `clarify`, `delegation`, `cronjob` as toolsets;
> still disabled: `video`, `video_gen`, `context_engine`. Table below is the May baseline —
> re-probe with `hermes tools list` before relying on a specific toolset.

| Toolset | Status | What it does |
|---|---|---|
| web | ✓ | Web search & scraping |
| browser | ✓ | Browser automation (Playwright) |
| terminal | ✓ | Terminal & process control |
| file | ✓ | File ops (read/write/edit) |
| code_execution | ✓ | Python/shell code execution |
| vision | ✓ | Image analysis |
| image_gen | ✓ | Image generation |
| tts | ✓ | Text-to-speech |
| skills | ✓ | Auto-discovered skills |
| todo | ✓ | Task planning |
| memory | ✓ | Built-in memory store |
| video | ✗ disabled | Video analysis |
| video_gen | ✗ disabled | Video generation |
| moa | ✗ disabled | Mixture of Agents |

**Implication:** when we route a model through Hermes (e.g. `-m grok-4.3`), it gains ALL enabled toolsets (16 as of v0.18.0) on top of whatever MCP tools we've registered. If we want a "raw model, no tools" probe, we'd need to disable toolsets per-invocation (flag TBD).

## Skills installed (`hermes skills list`)

87 skills installed. Categories include `apple`, `autonomous-ai-agents`, etc. The autonomous-ai-agents category is the interesting one for us:

- `claude-code` (builtin) — orchestrate Claude Code as a sub-agent
- `codex` (builtin) — orchestrate Codex as a sub-agent
- `opencode` (builtin) — orchestrate OpenCode as a sub-agent
- `hermes-agent` (builtin) — recursive Hermes orchestration

**This duplicates `scripts/delegate.py` functionality.** Open question: do we want to migrate dispatch traffic to Hermes-native sub-agent skills?

## Plugins available (none enabled)

- `disk-cleanup` (v2.0.0) — auto-track and clean ephemeral test/temp files via plugin hooks. Could replace some of our `tmp/` hygiene.
- `google_meet` (v0.2.0) — join Google Meet, transcribe captions, speak realtime. Not relevant for us.

## Memory layer

- **Built-in:** always active, lives in `~/.hermes/memories/` (SQLite-ish).
- **External plugins** available but not installed: byterover, hindsight, holographic, honcho, mem0, openviking, retaindb, supermemory.
- Built-in memory exposes the `memory` tool to the model in every session (write/recall facts across sessions).

Our `memory/MEMORY.md` (Claude Code's per-project auto-memory) is **separate** from Hermes's memory store. They're parallel.

## Session store

Every `-z` call creates a session. Stored as JSON at `~/.hermes/sessions/session_YYYYMMDD_HHMMSS_<id>.json` with full conversation transcript (system prompt, user messages, model responses, tool calls, tool results).

**Insights count:** 248 sessions, 1,379 messages, 519 tool calls, 21.46M total tokens in the last 30 days, mostly from our judge calibration matrix + V7 grok-tools builds.

**Search:** Hermes has FTS5 full-text search on the session store (`hermes_state.py SessionDB`). Use `hermes sessions list` and `hermes sessions show ID` to navigate.

## Native delegation (`delegation:` config block)

Hermes has built-in agent orchestration. Current settings (`~/.hermes/config.yaml:331-343`):

```yaml
delegation:
  model: ''
  provider: ''
  base_url: ''
  api_key: ''
  inherit_mcp_toolsets: true          # children inherit sources MCP
  max_iterations: 50                  # per-child cap
  child_timeout_seconds: 600          # 10 min per child
  reasoning_effort: ''
  max_concurrent_children: 3          # parallel cap
  max_spawn_depth: 1                  # children can't spawn grandchildren
  orchestrator_enabled: true
  subagent_auto_approve: false        # parent must approve sub-tool-use
```

**Overlap with our `delegate.py`:** both manage agent dispatch with concurrency/timeout/depth controls. Hermes's version is in-process (model spawns sub-agents during its tool loop). Ours is subprocess-based (dispatch.py spawns external CLI processes with worktree isolation).

## Kanban (`hermes kanban`)

SQLite-backed task board, multi-profile shared. Subcommands: `init`, `boards`, `create`, `assign`, `claim`, `block`, `comment`, `complete`, `link`, `dispatch`, `daemon`, `watch`, `stats`, `heartbeat`, `notify-subscribe`, etc.

**Current state:** board `default` exists but empty.

**Overlap:** our Monitor API + GitHub Issues + `delegate.py` task state machine cover similar ground. Hermes kanban could absorb some of it but the integration would be non-trivial (we'd need to keep GH issues for public-facing visibility).

## Cron (`hermes cron`)

Hermes has its own scheduler. **No jobs configured.** Subcommands: `create`, `list`, `delete`, etc. Use case: schedule recurring Hermes runs (e.g. daily curriculum quality sweeps).

**Overlap:** we use `ScheduleWakeup` (Claude Code) and could use system `cron`. Hermes's variant is Hermes-aware.

## Profiles (`hermes profile`)

Profiles bundle: model + gateway + alias + distribution + SOUL.md + .env. Currently one profile: `default` (model: `claude-opus-4-7` provider: anthropic, gateway: stopped, 87 skills, SOUL.md present, .env present).

**Distributions** are pre-packaged profile bundles installable from git URLs (`hermes profile install <url>`). We don't use any.

## Tool loop guardrails (`tool_loop_guardrails:`)

```yaml
tool_loop_guardrails:
  warnings_enabled: true             # warn when model loops on same tool
  hard_stop_enabled: true            # ✅ flipped 2026-07-05 (was false since May)
  warn_after:
    exact_failure: 2                 # warn after 2 identical failed calls
    same_tool_failure: 3
    idempotent_no_progress: 2
  hard_stop_after:
    exact_failure: 5                 # would stop after 5 if enabled
```

**Applied 2026-07-05** (verify: `grep hard_stop_enabled ~/.hermes/config.yaml` → `true`).
Watch-item: a hard stop after 5 identical failures can abort legitimate V7 writer/reviewer runs
when the `sources` MCP is transiently flaky (repeated `verify_words` timeouts). If V7
hermes-backed runs start aborting on transient tool errors, raise `hard_stop_after.exact_failure`
or scope-disable for the writer profile — record the change in § Automation adoption plan.

## OpenAI-compat proxy (`hermes proxy`)

Hermes ships its own OpenAI-compat proxy (`hermes proxy start [--provider NAME]`). Routes to Nous Portal + other backends. Currently **not running** (Nous Portal not logged in).

**Our `:8767` proxy** (PR #2025) is a separate `scripts/ai_agent_bridge/openai_proxy.py` that fronts codex/gemini-cli/claude/grok-via-hermes. Different scope. We may want to consolidate eventually.

## ACP mode (`hermes acp`)

Hermes can serve as an in-editor agent (VS Code, Zed, JetBrains) via Agent Communication Protocol. `hermes acp --setup` configures auth + browser deps. We use Claude Code interactively; Hermes ACP is an alternative we haven't tried.

## Gateway (`hermes gateway`)

Background service for messaging platforms: telegram, discord, slack, whatsapp, weixin, homeassistant, signal, matrix, mattermost, email, sms, dingtalk, wecom, feishu, qqbot, bluebubbles, yuanbao, webhook, api_server. Currently **stopped**. We don't use it.

## Insights (`hermes insights`)

Built-in analytics dashboard. Shows sessions, messages, tool calls, token counts. **Use this instead of grepping logs.** Run `hermes insights` for a snapshot of last-30-days activity.

## Curator (`hermes curator status`)

Background skill maintenance. Runs every 7d. Archives unused skills after 90d. Currently 0 agent-created skills. Curator runs as a `skip_context_files=True` agent (per `agent/curator.py:1705`).

## Config sections we haven't tuned (worth examining)

| Section | Lines | What it does |
|---|---|---|
| `providers:` | small | Per-provider routing config |
| `fallback_providers:` | empty | Auto-fail-over when primary fails |
| `credential_pool_strategies:` | empty | When pool has multiple creds, how to pick |
| `prompt_caching:` | TBD | Anthropic prompt-cache reuse |
| `compression:` | TBD | Context compression behavior |
| `checkpoints:` | TBD | Conversation rollback points (`hermes checkpoints`) |
| `context:` | TBD | Context-loading rules |
| `display:` | TBD | Terminal cosmetics (skins) |
| `browser:` | TBD | Browser automation config |
| `web:` | TBD | Web tool config |
| `terminal:` | TBD | Terminal backend (local/docker/ssh/modal/daytona/singularity) |
| `tool_output:` | TBD | Tool output formatting |
| `human_delay:` | TBD | Human-in-the-loop delay defaults |
| `bedrock:` | TBD | AWS Bedrock provider config |
| `openrouter:` | TBD | OpenRouter provider config |
| `tts:` / `stt:` / `voice:` | TBD | Audio I/O |
| `dashboard:` | TBD | Web dashboard config |
| `privacy:` | TBD | Telemetry / data sharing |

Total config: **514 lines, 31 top-level keys.** We've meaningfully configured ~3 of them (`agent.reasoning_effort`, `agent.personalities`, our SOUL.md isn't in config).

## Practical invocation patterns we use

| Pattern | What it does | Persona applied? |
|---|---|---|
| `hermes -z PROMPT -m grok-4.3` | One-shot judge / classifier call | SOUL.md slot #1 ✅ |
| `hermes -z "$(cat brief.md)" -m claude-opus-4-7` | One-shot with Claude (broken — #2036) | SOUL.md slot #1 ✅ |
| `--writer grok-tools` in V7 (our adapter calls `hermes -z`) | V7 module writer phase | SOUL.md slot #1 ✅ |
| `--reviewer grok-tools` in V7 | V7 reviewer phase | SOUL.md slot #1 ✅ |
| `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-grok` | Q&A via hermes | SOUL.md slot #1 ✅ when added |
| `hermes chat` (interactive) | Manual TUI session | SOUL.md slot #1 + `/personality` overlay |
| `--ignore-rules` flag | Skip SOUL.md + AGENTS.md + memory | ❌ NO persona |
| `hermes cron …` | Scheduled hermes runs | SOUL.md slot #1 ✅ |
| `hermes acp` mode | IDE-embedded agent | SOUL.md slot #1 ✅ |
| `hermes kanban dispatch …` | Kanban-driven sub-agent | depends on profile config |

## Diagnostic tools (when something goes wrong)

| Symptom | Tool to reach for |
|---|---|
| Model returns empty stdout | `hermes auth status PROVIDER` + actual probe call |
| Tool not available to model | `hermes mcp list`, `hermes tools list` |
| Model keeps looping on a tool | `tool_loop_guardrails.hard_stop_enabled: true` |
| Persona/voice off | inspect `~/.hermes/SOUL.md`, check session JSON slot #1 |
| Quota hit | provider-specific; `hermes auth list` shows pool, can `hermes auth add` more |
| Want to see what was actually sent | `~/.hermes/sessions/session_*.json` — full transcript |
| Want analytics | `hermes insights` |
| Want to diagnose installed setup | `hermes doctor` |
| Hermes home structure unclear | `~/.hermes/` — config.yaml, SOUL.md, AGENTS.md, sessions/, memories/, skills/, logs/, hooks/, cron/, auth.json |

## Open strategic questions

1. **Consolidate on Hermes-native vs keep our in-house tooling?** Hermes has built-in delegate, proxy, kanban, memory, session store, scheduler, plugins. We have parallel implementations of several. Migration would be invasive but reduce moving parts.
2. **Enable `tool_loop_guardrails.hard_stop_enabled`?** Cheap insurance against runaway tool loops.
3. **Define custom `personalities` for interactive use?** E.g. `module-writer`, `judge`, `adversarial-reviewer` — for when we manually `hermes chat` to debug.
4. **Set `fallback_providers`?** Would auto-route around provider outages.
5. **Migrate session/dispatch artifacts to Hermes session DB?** FTS5 search would be useful for finding past prompts/outputs.

## Empirical findings on Hermes routing (calibration matrix 2026-05-16)

Per `audit/2026-05-17-judge-calibration-matrix/REPORT.md`:

| Model | Harness | Effort | MCP | F1 | case_acc | Notes |
|---|---|---|---|---|---|---|
| gemini-3.1-pro-preview | native_cli | default | with | 80.0% | 91.7% | Strongest non-Hermes |
| grok-4.3 | hermes | xhigh | with | 78.6% | 100.0% | Best Grok cell |
| gpt-5.5 | hermes | medium | with | 76.9% | 91.7% | Best GPT via Hermes |
| grok-4.3 | hermes | high | with | 76.9% | 83.3% | |
| gpt-5.5 | native_cli | medium | with | 72.0% | 100.0% | |
| grok-4.3 | hermes | medium | with | 66.7% | 75.0% | Onboarding said best — matrix disagrees |

**Hermes-vs-native_cli for the same model:** mixed. gpt-5.5 medium with_mcp gets +4.9pp via Hermes; gpt-5.5 high without_mcp gets -66.7pp via Hermes (collapses to 0%). Hermes is not strictly better or worse — depends on model + effort + MCP.

**Without-MCP Hermes cells all errored** (harness bug: calls `hermes mcp` when no MCP attached). To be cleaned in the next harness iteration.

## Automation adoption plan (2026-07-05 — user order: "hermes is more than a harness; use its features for automation")

Prioritized, each item with its trigger condition and owner-lane. Status legend:
✅ applied · 🟡 approved-pending-implementation · ⬜ evaluate-then-decide.

| P | Feature | Action | Why / trigger | Status |
|---|---|---|---|---|
| P0 | `tool_loop_guardrails.hard_stop_enabled: true` | flip in `~/.hermes/config.yaml` | Cheap insurance against runaway tool loops on any hermes-routed model (recommended since May, never actioned). Warn thresholds already tuned; hard-stop at 5 identical failures. | ✅ applied 2026-07-05 |
| P1 | `fallback_providers` | set `openrouter` as fallback for the deepseek + xai lanes | Expectation #6 (limits happen — handle them): auto-fail-over at the harness level beats every agent hand-implementing retry-elsewhere. Keeps V7 grok-tools + deepseek reviews alive through provider hiccups. ⚠️ Guardrails: the ACTUAL substituted provider/model must be surfaced in the run artifact (review-independence, cost, and egress change with the substitution — silent failover violates the operator contract #6); zai/GLM must NEVER be a fallback target for automated runs (LOCAL-ONLY). | 🟡 implementation shipped (PR #4457), pending machine-local enable + live probe |
| P1 | `hermes cron` | nightly READ-ONLY deterministic sweep over the published levels (explicitly: a1 a2 b1 b2): `track_deterministic_audit --track <lvl>` + `hermes insights` snapshot → report written ONLY to a gitignored runtime path the Monitor API serves | Recurring drift detection without burning an orchestrator session on polling. "Read-only" must be MECHANICAL, not prose: hermes enables `file`/`terminal`/`code_execution` toolsets by default, so the cron job runs with `--ignore-rules` + toolsets disabled (or an isolated read-only cwd) and its prompt template forbids writes outside the report path. Never builds/commits (build policy unchanged: agent-run, `--worktree`). | 🟡 pilot 1 job with the toolset-disable recipe, review output for a week, then extend |
| P1 | Session store FTS5 | recipe: `hermes sessions list` / `hermes sessions show <id>`; grep 21M+ tokens of past writer/judge transcripts for prompt forensics | Every `-z` call is already recorded — free provenance for "what did the writer actually see" debugging (cf. #M-10 build-artifact forensics). | ✅ documented (recipe here; no config change needed) |
| P2 | `hermes insights` | use INSTEAD of log-grepping for lane utilization stats; feed the monthly quota review | Deterministic usage data per model/session — supports expectation #4 (keep lanes busy) with numbers, not vibes. | ✅ documented |
| P2 | Kanban / native delegation / gateway / ACP / proxy | **do not adopt now** | Overlap with load-bearing in-house tooling (delegate.py worktree isolation, Monitor API, GH issues as public SSOT, `:8767` proxy). Migration = high blast radius, low marginal value today. Re-evaluate if delegate.py grows a second concurrency bug. | ⬜ stance recorded |
| P2 | `hermes doctor` + `hermes auth list` probes | add to the services troubleshooting runbook as first-line hermes diagnostics | Faster than re-deriving from raw config every incident. | ✅ documented |

Ground rules for all hermes automation:
- Cron/automated hermes runs are **read-only analysis lanes** — no commits, no builds, no
  curriculum writes. Anything that mutates the repo keeps going through `delegate.py` dispatch
  with worktree isolation + PR + review.
- Every adopted feature gets a forced-failure verification before we rely on it (#M-4 —
  a fallback that was never seen failing over is an assumption, not a feature).
- Config flips in `~/.hermes/config.yaml` are machine-local: record them HERE (this section) so
  a machine rebuild can replay them; the file itself is not in the repo.

## References

- `~/.hermes/hermes-agent/website/docs/user-guide/features/personality.md` — SOUL.md mechanics
- `~/.hermes/hermes-agent/AGENTS.md` — Hermes-agent dev guide
- `~/.hermes/hermes-agent/run_agent.py:5938` — SOUL.md loading site
- `~/.hermes/hermes-agent/cli.py:4477` — `skip_context_files` plumbing
- `~/.hermes/hermes-agent/hermes_cli/commands.py:1495` — `/personality` slash command handler
- `audit/2026-05-17-judge-calibration-matrix/REPORT.md` — empirical Hermes vs native_cli data
- Project SOUL.md: `~/.hermes/SOUL.md` (live)
- Project Hermes config: `~/.hermes/config.yaml` (live, 514 lines)
