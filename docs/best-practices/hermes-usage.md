# Hermes Agent — usage guide for learn-ukrainian

> **Status:** baseline survey 2026-05-16. Hermes Agent v0.13.0 (2026.5.7).
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

## Auth pool (per `hermes auth list`)

| Provider | Type | Source | Status |
|---|---|---|---|
| anthropic | oauth | claude_code | ⚠️ logged-in flag set but silent-drop (#2036) |
| copilot | api_key | gh CLI token | ✅ |
| openai-codex | oauth | device_code | ✅ |
| xai-oauth | oauth | loopback_pkce (Grok) | ✅ |

**The `auth status PROVIDER` is unreliable for anthropic** — it reports "logged in" but `hermes -z -m claude-opus-4-7` returns empty stdout (issue #2036). Don't trust the status flag; probe with an actual call.

**API-key surface** (env vars Hermes recognizes, per `hermes status`): `OPENAI_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `ANTHROPIC_API_KEY`, plus `GH_TOKEN`, `OPENROUTER_API_KEY`, and ~15 others including providers we don't use (DeepSeek, Z.AI/GLM, Kimi, StepFun, MiniMax). All currently UNSET — auth flows exclusively through OAuth pool.

## MCP servers (per `hermes mcp list`)

```
sources    http://127.0.0.1:8766/mcp    all tools    ✓ enabled
```

Only our project's `sources` server is registered. It exposes 30+ Ukrainian-source tools (`verify_word`, `verify_words`, `verify_lemma`, `check_modern_form`, `search_text`, `check_russian_shadow`, `query_pravopys`, `search_grinchenko_1907`, `search_style_guide`, `search_synonyms`, `query_cefr_level`, `search_heritage`, etc.). Tools auto-flow into the model's tool list on every `-z` call (no per-invocation flag needed).

## Built-in toolsets enabled by default (`hermes tools list`)

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

**Implication:** when we route a model through Hermes (e.g. `-m grok-4.3`), it gains all 11 enabled tools on top of whatever MCP tools we've registered. If we want a "raw model, no tools" probe, we'd need to disable toolsets per-invocation (flag TBD).

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
  hard_stop_enabled: false           # ❗ DOES NOT STOP — only warns
  warn_after:
    exact_failure: 2                 # warn after 2 identical failed calls
    same_tool_failure: 3
    idempotent_no_progress: 2
  hard_stop_after:
    exact_failure: 5                 # would stop after 5 if enabled
```

**Recommendation:** enable `hard_stop_enabled: true` to prevent runaway tool loops on a misbehaving model. Cheap insurance.

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
| `ab ask-grok` (not yet implemented) | Q&A via hermes | SOUL.md slot #1 ✅ when added |
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

## References

- `~/.hermes/hermes-agent/website/docs/user-guide/features/personality.md` — SOUL.md mechanics
- `~/.hermes/hermes-agent/AGENTS.md` — Hermes-agent dev guide
- `~/.hermes/hermes-agent/run_agent.py:5938` — SOUL.md loading site
- `~/.hermes/hermes-agent/cli.py:4477` — `skip_context_files` plumbing
- `~/.hermes/hermes-agent/hermes_cli/commands.py:1495` — `/personality` slash command handler
- `audit/2026-05-17-judge-calibration-matrix/REPORT.md` — empirical Hermes vs native_cli data
- Project SOUL.md: `~/.hermes/SOUL.md` (live)
- Project Hermes config: `~/.hermes/config.yaml` (live, 514 lines)
