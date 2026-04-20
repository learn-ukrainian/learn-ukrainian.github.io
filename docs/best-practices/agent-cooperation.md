# Agent Cooperation Best Practices

> **Scope:** How Claude, Gemini, and Codex work together without degrading each other's output quality.
> Full protocol: `docs/CLAUDE-GEMINI-COOPERATION.md`
> Review evidence contract: [`docs/review-protocol.md`](../review-protocol.md)
>
> **Runtime layer:** All agent CLI invocations route through `scripts/agent_runtime/`.
> If you're touching an agent subprocess, read [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md) first.

---

## Team Structure

| Team | Agent | Role |
|------|-------|------|
| 💙 **Синя команда** (Blue) | Claude | Architect, reviewer, quality gate |
| 💛 **Жовта команда** (Gold) | Gemini | Content builder, implementer |
| 🟢 **Зелена команда** (Green) | Codex | Adversarial reviewer, bug finder, code improver |

**Both teams are adversarial by design.** The purpose is quality through finding mistakes, not agreement. An approved module means both teams couldn't find serious problems — not that both teams were polite.

---

## The Non-Negotiable Rule

**An LLM must NEVER review its own work.**

Self-review produces inflated scores. Observed in production: Gemini reviewing its own content gave 9.9/10 scores with language like "ensuring a high score" and "reflecting the fixes made." This was not bias in the model — it was a structural failure: the same agent that wrote the content reviewed it.

### Valid review paths
- ✅ Claude reviews Gemini's content
- ✅ Gemini reviews Claude's architecture proposals
- ✅ Codex reviews Claude or Gemini implementation work
- ✅ Automated audit gates (no LLM bias)
- ❌ Gemini reviews its own content
- ❌ Claude reviews its own code without external validation
- ❌ Codex reviews its own code without external validation

---

## Communication Channels

### GitHub-first (primary)
All substantive discussion happens on GitHub where it is persistent and searchable.

| Channel | Use For | Max Length |
|---------|---------|------------|
| **GitHub issues** | Task specs, proposals, architecture plans | Unlimited |
| **GitHub comments** | Reviews, feedback, progress, disagreements | Unlimited |
| **Broker messages** | Short notifications pointing to GitHub | <200 chars |

**Never put full reviews or code in broker messages.** Post on GitHub, then ping with "review posted on #559."

### Runtime layer — single source of truth for agent CLI calls

As of #1184 (April 2026), all three agents (Claude, Gemini, Codex) are
invoked through `scripts/agent_runtime/runner.invoke()`. This applies to:

- `scripts/ai_agent_bridge/` — bridge messaging (`ask-gemini`, `ask-codex`, `process-claude`, etc.)
- `scripts/build/dispatch.py` — pipeline phase dispatch (`skeleton`, `write`, `review`, etc.)
- `scripts/delegate.py` (future) — ad-hoc coding task delegation
- `scripts/consult.py` (future) — multi-agent consultation

**If you find yourself writing `subprocess.Popen([... "claude", ...])` or similar — stop.** Use `runner.invoke()`. The runtime owns stall detection, usage logging, rate-limit headroom checks, mode validation, and resume-policy enforcement uniformly across all agents.

Full guide: [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md).

### Direct dispatch (ask-gemini / ask-codex)
For requests needing immediate response:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review posted on #559. Please read and respond." \
  --task-id issue-559

.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Bug report posted on #560. Please read and respond." \
  --task-id issue-560
```

### Multi-turn conversations (converse)
For iterative co-design, planning, or prompt optimization:
```bash
# Start a conversation
.venv/bin/python scripts/ai_agent_bridge/__main__.py converse \
  "Let's plan the A1/1 build. Here's the plan: ..." \
  --task-id "a1-1-planning"

# Continue (Gemini sees full history)
.venv/bin/python scripts/ai_agent_bridge/__main__.py converse \
  "Good points. What about the dialogue examples?" \
  --task-id "a1-1-planning"
```
Each turn includes full conversation history. Oldest messages truncated first if history exceeds 30K chars. Use `--model gemini-3.1-pro-preview` for design conversations.

### How the bridge works (architecture)
The bridge is **not** an MCP tool. MCP is one-directional (client→server). The bridge uses a different architecture:

1. **SQLite broker DB** (`data/broker.db`) — shared message queue
2. **CLI wrapper** spawns the target agent CLI (`gemini`, `claude`, or `codex`) as a subprocess with the message as prompt
3. The target agent runs, output is captured and stored back in the broker DB
4. Reviews auto-posted to GitHub issues (when task_id matches `issue-NNN`)

This means the broker can route among Claude, Gemini, and Codex. In practice, GitHub remains the source of truth and broker messages should stay short.

### Automatic Review Persistence

Reviews dispatched via `ask-gemini` are automatically posted to GitHub:

| task_id pattern | Behavior |
|-----------------|----------|
| `issue-NNN` / `gh-NNN` | Posted as comment on issue #NNN |
| Any other value | New issue created with `review-result` label |
| None | New issue created titled `Review: {timestamp}` |

Reviews >65K chars are split into multiple comments. To skip: `--no-github`.

Only applies to **standard mode** (not `--stdout-only` or `--output-path`).

### Passive notification (MCP send_message)
For non-blocking FYI messages Gemini sees at next session start:
```python
mcp__message-broker__send_message(
    to="gemini", content="FYI: bio Phase A complete. See #560.",
    from_llm="claude", message_type="context"
)
```

---

## Session Start Checklist

**Canonical path (GH #1309):** call the Monitor API. Do not open
rule files, session-state handoffs, or CLAUDE.md directly — they
are what the API serves.

```bash
# 1. Tiny index of per-component hashes. ~1 KB.
curl -s http://localhost:8765/api/state/manifest

# 2. Only fetch components whose hash changed since last session.
curl -s http://localhost:8765/api/rules?format=markdown
curl -s http://localhost:8765/api/session/current

# 3. Always-fresh: git state, pipeline, runtime, wiki, health, hints.
curl -s http://localhost:8765/api/orient

# 4. Do I have unread channel deliveries?
curl -s "http://localhost:8765/api/comms/inbox?agent=claude"
# (agent=gemini / agent=codex for the other workers)
```

Agents running Python should use the SDK instead — one call, caching
built in:

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap()
rules_md = boot["rules"].body
session_md = boot["session"].body
# boot[...].source tells you why ("cache" / "not-modified" / "network").
```

Both `/api/rules` and `/api/session/current` support
`If-None-Match: "<hash>"` and return `304 Not Modified` when the hash
matches. The on-disk cache under `.agent/cache/monitor/` persists
across sessions so repeat cold-starts pay near-zero bytes for the
rule + session payloads.

### Scoped queries during work

Once bootstrapped, prefer these deterministic endpoints over
filesystem spelunking:

| Question | Endpoint |
|---|---|
| What's module `{slug}` doing right now? | `GET /api/state/module/{track}/slug/{slug}` |
| Per-module dashboard for N..M on {track} | `GET /api/state/range/{track}?start=N&end=M` |
| Which files would `--force` delete? | `GET /api/artifacts/{track}/{slug}/force-preview` |
| Classified file manifest (source/generated/published/stale) | `GET /api/artifacts/{track}/{slug}/files` |
| Main + style review + empty-findings flag | `GET /api/artifacts/{track}/{slug}/review-snapshot` |
| state.json vs reality cross-check | `GET /api/artifacts/{track}/{slug}/drift` |
| Ship-ready snapshot for one module | `GET /api/artifacts/{track}/{slug}` |
| Aggregate ship-ready list | `GET /api/artifacts/ship-ready[?track=...]` |
| Public site reachability + freshness | `GET /api/site/health` |
| Recent GH Pages deployments | `GET /api/site/deployments` |
| Active worktrees | `GET /api/worktrees` |
| Open issues grouped + supersede metadata | `GET /api/issues/map` |
| Per-agent auth mode | `GET /api/runtime/auth` |

Full endpoint reference: [`docs/MONITOR-API.md`](../MONITOR-API.md).

Legacy steps that remain useful if the API is unreachable:

1. **Load memory** — what was in progress last session:
   ```python
   mcp__memory__search_nodes(query="in progress current session")
   mcp__memory__search_nodes(query="next session todo")
   ```

2. **Check inbox** — notifications from other agents:
   ```python
   mcp__message-broker__check_inbox(for_llm="claude")
   ```

3. **Read unread messages** — respond on GitHub if substantive

At session end: save progress summary to memory.

---

## Issue Claiming Protocol

**Agents never self-assign.** Only the user or orchestrator assigns work.

When starting an issue:
```bash
gh issue edit {N} --add-label "working:{agent}"
gh issue comment {N} --body "Starting work on X"
```

When done:
```bash
gh issue edit {N} --remove-label "working:{agent}"
gh issue edit {N} --add-label "review:{reviewer}"  # or review:human
# or: gh issue close {N}
```

---

## Cross-Review Requirements

When reviewing Gemini's content or Gemini's review of Claude's work:

**Required elements:**
- Point out specific problems (not "looks good overall")
- Quote the problematic content
- Suggest a concrete fix
- Score honestly — never rubber-stamp

**Red flags in a review to reject:**
- All dimensions 9-10/10 with no substantive issues
- Empty "issues" section
- Language like "ensuring a high score", "reflecting the fixes"
- Praise without specifics

If you see these: the review is invalid. Request a new review from a different perspective.

---

## Skill-Based Dispatch

Use Gemini's skill files instead of verbose prompts. Each skill encodes the full protocol.

```bash
# Seminar track rebuild
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "/full-rebuild-bio 5" \
  --task-id rebuild-bio-5

# Core track rebuild
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "/full-rebuild-core-a a1 3" \
  --task-id rebuild-a1-3
```

**Always use skills for content work.** Ad-hoc prompts miss critical protocol steps.

---

## Builder Notes (Gemini→Claude structured handoff)

After every content or activity build, Gemini outputs a `===BUILDER_NOTES_START===` block with:
- **status**: SUCCESS / PARTIAL / BLOCKED
- **deviations**: where and why Gemini deviated from the plan
- **frictions**: template/schema issues encountered
- **unverified_terms**: Ukrainian words Gemini couldn't verify via sources tools / VESUM (compile-layer retrieval architecture: ADR-006)
- **review_focus**: specific items that need reviewer attention

The pipeline extracts this to `orchestration/{slug}/builder-notes.yaml`. The review prompt injects it via `{BUILDER_NOTES_BLOCK}` so Claude knows where to focus the review.

---

## Gemini Output Handling

Gemini outputs verbose thinking tokens (10-100K chars). All structured output uses `===TAG_START===` / `===TAG_END===` delimiters. Content outside delimiters is noise.

```python
# Extraction utility
from pipeline_lib import _extract_delimiter
research = _extract_delimiter(output, "===RESEARCH_START===", "===RESEARCH_END===")
```

Never parse Gemini's prose output for structured data.

---

## Escalation

If Gemini is stuck (not completing a phase, silently failing):
```bash
.venv/bin/python scripts/build_module_v5.py {track} {num} --force-phase {research|content|activities|validate|review}
```

Or use the process-escalations skill:
```
/process-escalations
```

Post on the relevant GH issue explaining what was stuck and why.
