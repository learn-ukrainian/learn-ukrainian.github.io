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

### Claude Code version gotchas (affects `delegate.py dispatch --agent claude`)

- **CC 2.1.119+: `--print` mode honors subagent `tools:` / `disallowedTools:` frontmatter.** Previously print mode ignored those restrictions — they only applied in interactive subagent invocations. Our dispatched-Claude pattern (`delegate.py dispatch --agent claude` → `claude -p ...`) now enforces them. Current subagents (`claude_extensions/agents/curriculum-maintainer.md`) declare `tools: "*"` so dispatches are unaffected today. **But** any new subagent that restricts tools will apply those restrictions in dispatch mode. Don't declare `tools: [Read, Grep]` on a subagent you plan to dispatch unless that limit is intentional for dispatched runs too.
- **CC 2.1.119+: `--agent <name>` honors agent definition's `permissionMode` for built-in agents.** We pass `--mode danger` explicitly on every dispatch, so this is a no-op for us. Don't remove the explicit `--mode danger` and expect the agent definition to carry it — not every dispatch target is a built-in agent.
- **CC 2.1.119+: `Agent` tool with `isolation: "worktree"` no longer reuses stale worktrees from prior sessions.** Until this fix we avoided the built-in Agent-tool isolation and hand-rolled `git worktree add` (see `.claude/rules/delegate-must-use-worktree.md`). The hand-rolled pattern is still correct — it survives across sessions, shows up in `git worktree list`, and matches our dispatch conventions — but the Agent-tool built-in is now a safe alternative for short-lived, same-session isolation.

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

## Multi-Agent Deliberation (`ab discuss`)

**This section was added 2026-05-02 after recognizing systematic underutilization** of `ab discuss` for design/framing/architecture decisions. We were defaulting to single-shot Gemini reviews and Claude-alone-reasoning where distributed deliberation would have caught more.

### What `ab discuss` is — and isn't

`ab discuss` runs bounded rounds (default 2, max 4) of parallel agent responses on a topic, short-circuiting when all agents end with `[AGREE]`. Transcript lands in the named channel with `parent_id` threading.

**It is NOT a quorum mechanism.** Three agents don't form an independent jury — Claude/Gemini/Codex all trained on overlapping internet corpora and have **correlated blind spots** (e.g., Russian-imperial framings show up in all three model families' priors). Math-voting on agent agreement isn't trustworthy.

**What it actually delivers:**
- **More angles per decision** — Gemini catches content/citation gaps, Codex catches code edge cases, Claude catches architecture
- **Adversarial pressure** — agents are prompted to challenge each other, which surfaces hidden assumptions one agent alone wouldn't pressure-test
- **Documented deliberation** — channel transcript = referenceable context for future sessions, not "trust me, I thought about it"

### When to use which tool

| Use `ab discuss` | Use `ask-gemini` (single-shot) | Don't use either |
|---|---|---|
| Architectural trade-offs (e.g., module_type categories, retrieval strategy) | Mechanical PR review with green CI | Trivial fixes (delete leftover file) |
| Pedagogy/framing decisions (POC scope, anchor choice, decolonization audits) | Adversarial review of a single PR | Implementation tasks (Codex codes alone) |
| Brief pre-flight before dispatch (catch ambiguities before Codex burns 8 min) | Quick disambiguation question | When the answer is obvious |
| Cross-agent deadlock (Gemini APPROVE, Codex REVISE on same artifact) | Spot-check an output against a rule | Time-sensitive merge decisions (3-min discussion latency stacks) |
| Quality review of foundational content (M1-M3 modules, ADRs) | One-off domain question | |

### Budget angle

- `ab discuss --with gemini,codex` (Claude excluded) is FREE for orchestrator — Gemini subscription unmetered, Codex on OpenAI subscription. Use aggressively when Anthropic budget is tight.
- `ab discuss --with claude,gemini,codex` burns Anthropic per round per Claude turn. Reserve for foundational decisions where Claude's voice as architect/reviewer matters (architecture, pedagogy framing, decision arbitration).

### Concrete example — what we missed today (2026-05-02)

When proposing the POC anchor module, Claude reasoned alone and offered A1/M10 colors as a "neutral steady-state baseline." User had to catch the Russian-imperial-propaganda angle on colors that invalidated "neutral." If we had run:

```bash
ab discuss content "POC anchor module choice — M10 colors vs M20 my-morning, considering decolonization sensitivity in A1" --with claude,gemini,codex --max-rounds 2
```

…Gemini or Codex might have surfaced the colors angle independently. The deliberation transcript would also exist as a referenceable record on the `content` channel, not buried in a Claude session that compaction would eventually destroy. **Pattern: when picking among options that touch decolonization, framing, or pedagogy — discuss, don't decide alone.**

### Decision Card pattern (when `ab discuss` surfaces a CHOICE)

Most `ab discuss` runs converge with `[AGREE]` — orchestrator just executes the consensus. But when discussion surfaces **disagreement OR multi-option output**, the orchestrator MUST emit a structured Decision Card so the user can override or approve. Don't bury decisions in transcript noise.

**Template:**

```markdown
## DECISION REQUIRED — {one-line question}

**Agents:** claude, gemini, codex (R rounds, channel: {name}, thread: {id})

**Options surfaced:**
- **Option A:** {description}  *(proposed by: gemini)*
- **Option B:** {description}  *(proposed by: codex)*
- **Option C:** {description}  *(proposed by: claude)*

**Votes (with 1-line rationale):**
- claude → A: {rationale}
- gemini → B: {rationale}
- codex → A: {rationale}

**Real disagreement (not surface-level):** {what they actually differ on — the underlying assumption gap, not just which letter they picked}

**Scope:** {what this pending decision blocks and what remains safe}
  - Tracks/levels blocked: {e.g., a1 zero-onset modules; a2 unaffected}
  - Issues blocked: {e.g., #1622 round-4 bakeoff downstream}
  - Paths/dirs blocked: {e.g., scripts/build/v7_build.py changes}
  - Safe to proceed: {e.g., dependabot triage, wiki cleanup, A2/B1/B2 module fixes, infrastructure}

**Orchestrator recommendation:** A — {1-3 line rationale weighing the votes against project priors}

**Awaiting:** user override (`go with B because…`) or `go` to proceed with the recommendation
```

### High-risk-track override (false-consensus failsafe)

When all participating agents share the same underlying bias on a topic (e.g., Russian-imperial framing on Ukrainian topics, Western centrism on decolonization), an `[AGREE]` consensus is NOT a green light. It is exactly when the Decision Card mechanism is most needed and most likely to be bypassed.

For high-risk tracks — **HIST, BIO, ISTORIO, LIT, OES, RUTH** (all decolonization-sensitive seminar tracks where Russian/Soviet-imperial framings are most ingrained in training data) — the orchestrator MUST apply at least one of the following failsafe mechanisms:

- **Mechanism A (Force-emit Decision Card on `[AGREE]`):** If `ab discuss` runs on a topic touching any high-risk track and converges with `[AGREE]`, the orchestrator emits a Decision Card anyway. The question is framed as "agents converged on X — but consensus on this track is suspect; user should sanity-check." The user can quickly approve or override.
- **Mechanism B (Inject domain-specific bias checklist):** For high-risk tracks, the `ab discuss` prompt is augmented with a short bias checklist explicitly provoking adversarial review on known bias vectors.
  - *Example for HIST:* "Did you check the proposed framing against canonical decolonized sources? Bulgakov-as-Ukrainian, Gogol-as-Ukrainian, Akhmatova-as-Ukrainian, etc., are the 'Kyiv-born equals Ukrainian writer' trap — flag if you see it. Did you check whether the historical actor is being framed in Russian-imperial categories versus Ukrainian native categories?"

**Recommendation:** Prefer **Mechanism B** (proactive — catches bias during discussion) for any new `ab discuss` on high-risk tracks. Fall back to **Mechanism A** (reactive — emit card on consensus) when no domain-specific checklist exists yet for that track.

**Pattern:** Consensus on high-risk tracks is a SIGNAL TO CHECK, not a signal to proceed.

### Where Decision Cards land

Three locations depending on user availability:

| Situation | Location | Why |
|---|---|---|
| User online, mid-session | Inline in chat reply | Immediate visibility, user can `go` in next message |
| User AFK, no live session | `docs/decisions/pending/{YYYY-MM-DD}-{slug}.md` | Durable, scannable on return; cold-start protocol checks this dir |
| Multi-week architectural call | New GH issue with `decision-pending` label + Decision Card as body | Long-lived discussion needs an issue thread, not a markdown file |

Note: High-risk-track Decision Cards (the ones force-emitted by Mechanism A) should ALWAYS be routed inline-or-pending, never silently auto-resolved, even when the user appears online.

Every Decision Card MUST include a `Scope` field. The scope declares exactly which tracks, issues, and paths are blocked by the pending decision and which work can continue independently. If a Decision Card omits scope, agents must use the conservative interpretation that it blocks everything — precisely the failure mode this field is meant to avoid.

When the user decides:
- `pending/` file → moves to `docs/decisions/{date}-{slug}.md` with the chosen option recorded + closed
- GH issue → updated with chosen option, label flipped from `decision-pending` to `decided`
- Inline chat → orchestrator simply executes the choice, no further file movement needed

### Cold-start integration

The session-start checklist below now includes `docs/decisions/pending/` as a required scan. If pending decisions exist, the cold-start surface them before the user asks. This closes the "decisions buried in transcripts" gap — pending decisions are first-class state, not deliberation noise.

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

# 5. Are there pending decisions awaiting user input?
ls docs/decisions/pending/ 2>/dev/null
# If non-empty: read each, surface to user before any other work.
# Pending decisions block only their declared scope; check Scope before assuming work is blocked.
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
<!-- TODO(#1394): classify --force usage -->
```bash
.venv/bin/python scripts/build_module_v5.py {track} {num} --force-phase {research|content|activities|validate|review}
```

Or use the process-escalations skill:
```
/process-escalations
```

Post on the relevant GH issue explaining what was stuck and why.
