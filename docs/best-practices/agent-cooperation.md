# Agent Cooperation Best Practices

> **Scope:** How Claude, Codex, Cursor, DeepSeek, and track orchestrators work
> together without degrading each other's output quality.
> Historical protocol archive: `docs/archive/CLAUDE-GEMINI-COOPERATION.md`
> Review evidence contract: [`docs/review-protocol.md`](../review-protocol.md)
>
> **Runtime layer:** All agent CLI invocations route through `scripts/agent_runtime/`.
> If you're touching an agent subprocess, read [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md) first.

---

## Team Structure

| Team | Agent | Role |
|------|-------|------|
| 💙 **Синя команда** (Blue) | Claude | Architect, reviewer, quality gate |
| 💛 **Жовта команда** (Gold) | Cursor / track writers | Content builder, implementer |
| 🟢 **Зелена команда** (Green) | Codex | Main orchestrator, adversarial reviewer, bug finder, code improver |
| ⚙️ **Review lane** | DeepSeek | Cheap code/content review and deterministic triage |

Gemini is currently paused for review/merge confidence until the user re-enables
that lane. Historical Gemini instructions in this document describe old bridge
behavior; prefer Claude, Codex, Cursor, and DeepSeek for new orchestration work.

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

### Track orchestrator promotion

A **track orchestrator** is an agent promoted to own one curriculum track or
epic end-to-end, such as BIO. Once promoted, that orchestrator owns the track's
content queue, dispatches, handoff, and PR preparation. The main orchestrator
does not micromanage that track.

| Scope | Main orchestrator owns | Track orchestrator owns |
|---|---|---|
| Branch policy | `main`, merge sequencing, release safety | Dispatch worktrees and PR branches only |
| State | `docs/session-state/codex-orchestrator-handoff.md` and router | Track handoff (gitignored local), e.g. `.claude/bio-epic/CLAUDE-DRIVER-HANDOFF.md` — not in git/PRs |
| Work selection | Repo-wide priorities, A1 spine, tooling, infra, tech debt, issues | Track backlog, batches, reviews, content quality |
| Agent dispatch | Cross-track/tooling agents | Track-local writers/reviewers, including headless Codex |
| Merge authority | Final reconcile on cross-track/contested merges; sweep backstop for out-of-lane PRs sitting green >1h (#4703) | Open PRs, route track feedback; self-merge own-track PRs after cross-family review + green CI (#M-12 grant, user 2026-06-16); arm `gh pr merge --auto --squash --delete-branch` at review-gate-pass |

**Boundary rule:** if a track orchestrator exists, the main orchestrator treats
that track's PRs and delegates as awareness-only unless the track orchestrator
asks for help. This keeps one owner per workstream and prevents duplicate
triage. The only exception is the merge-sweep backstop (user directive
2026-07-07, #4703): an out-of-lane PR that has sat GREEN (CI passing + review
gate passed) idle for more than 1 hour may be picked up by any orchestrator
sweep. Fresh out-of-lane PRs are hands-off — do not shepherd, review-route, or
arm auto-merge on them before that threshold.

### Track ↔ main communication protocol

Track orchestrators and the main orchestrator communicate through durable,
low-noise surfaces:

1. **Track handoff is the track source of truth.** The track orchestrator keeps
   a track handoff current as **gitignored LOCAL state** under `.claude/<track>-epic/`
   (user policy 2026-06-23 — driver handoffs are out of git/PRs). It does NOT ride
   in the batch PR; cross-agent state reaches the main orchestrator via the TRACK-UPDATE
   pings + PR descriptions below.
2. **GitHub PRs carry deliverables.** Track orchestrators open PRs with clear
   scope, validation, active dispatch ids, and blockers. The main orchestrator
   reads the PR instead of scraping private chat context.
3. **Bridge messages are pings, not payloads.** Use `.venv/bin/python scripts/ai_agent_bridge/__main__.py p` / channel posts only
   to point to the PR, issue, or handoff section that changed.
4. **Main only interrupts for repo-wide risk.** Examples: generated artifacts in
   diff, `.python-version`/linter config changes, merge conflicts, failing
   required CI, cross-track architectural conflicts, or user direction changes.
5. **Track asks for help explicitly.** If the track needs Codex, it dispatches
   or requests a bounded Codex task with a file scope, expected output, and
   ownership boundary.
6. **Decisions use Decision Cards.** Cross-track or user-visible choices go to a
   Decision Card with scope; local track implementation choices stay in the
   track handoff/PR.

Recommended ping format:

```text
TRACK-UPDATE track=<track> pr=<number|none> state=<blocked|ready|in-flight>
owner=<agent> needs=<main-review|merge|codex-help|decision|none>
summary=<one sentence, link to handoff/PR for details>
```

Recommended main response format:

```text
MAIN-ACK track=<track> action=<merge-queued|needs-fix|codex-dispatched|noted>
scope=<what main will do> boundary=<what remains track-owned>
```

### Thread handoff ownership

`docs/session-state/current.md` is a compatibility router, not a shared scratch
handoff. It keeps `Latest-Brief:` plus an `Agent-Handoff:` mapping.

Durable role handoffs and thread rollover packets are separate:

| Agent | Durable role handoff |
|---|---|
| orchestrator | `docs/session-state/codex-orchestrator-handoff.md` |
| codex | `docs/session-state/current.orchestrator.md` → `docs/session-state/codex-orchestrator-handoff.md` |
| claude | `docs/session-state/current.claude.md` |
| gemini | `docs/session-state/current.gemini.md` |

Thread rollover packets are generated locally under
`.agent/<agent>-thread-handoff.md` by
`scripts/orchestration/thread_handoff.py prepare`. They are for moving a
saturated thread to a fresh thread; do not use them as the durable orchestrator
state file.

For compatibility, `docs/session-state/current.orchestrator.md` remains a thin
pointer to `docs/session-state/codex-orchestrator-handoff.md` while older
routers and cold-start hooks still reference it.

Codex UI cold-starts should read the orchestrator pointer above instead of a
missing Codex-specific handoff file.

Use `/api/session/current?agent=<name>` or read the matching
durable role handoff directly. Only the orchestrator updates the router by
default; other agents update it only when the task explicitly asks for a router
change.

### Runtime layer — single source of truth for agent CLI calls

As of #1184 (April 2026), all three agents (Claude, Gemini, Codex) are
invoked through `scripts/agent_runtime/runner.invoke()`. This applies to:

- `scripts/ai_agent_bridge/` — bridge messaging (`ask-agy`, `ask-codex`, `process-claude`, etc.)
- `scripts/build/dispatch.py` — pipeline phase dispatch (`skeleton`, `write`, `review`, etc.)
- `scripts/delegate.py` (future) — ad-hoc coding task delegation
- `scripts/consult.py` (future) — multi-agent consultation

**If you find yourself writing `subprocess.Popen([... "claude", ...])` or similar — stop.** Use `runner.invoke()`. The runtime owns stall detection, usage logging, rate-limit headroom checks, mode validation, and resume-policy enforcement uniformly across all agents.

Full guide: [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md).

### Claude Code version gotchas (affects `delegate.py dispatch --agent claude`)

- **CC 2.1.119+: `--print` mode honors subagent `tools:` / `disallowedTools:` frontmatter.** Previously print mode ignored those restrictions — they only applied in interactive subagent invocations. Our dispatched-Claude pattern (`delegate.py dispatch --agent claude` → `claude -p ...`) now enforces them. The curriculum orchestrator declares `tools: "*"`, while restricted writer agents must be treated as intentionally tool-limited in dispatch mode. Don't declare `tools: [Read, Grep]` on a subagent you plan to dispatch unless that limit is intentional for dispatched runs too.
- **CC 2.1.119+: `--agent <name>` honors agent definition's `permissionMode` for built-in agents.** We pass `--mode danger` explicitly on every dispatch, so this is a no-op for us. Don't remove the explicit `--mode danger` and expect the agent definition to carry it — not every dispatch target is a built-in agent.
- **CC 2.1.119+: `Agent` tool with `isolation: "worktree"` no longer reuses stale worktrees from prior sessions.** Until this fix we avoided the built-in Agent-tool isolation and hand-rolled `git worktree add` (see `.claude/rules/delegate-must-use-worktree.md`). The hand-rolled pattern is still correct — it survives across sessions, shows up in `git worktree list`, and matches our dispatch conventions — but the Agent-tool built-in is now a safe alternative for short-lived, same-session isolation.

### Direct dispatch (ask-agy / ask-codex)
For requests needing immediate response:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy \
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
Each turn includes full conversation history. Oldest messages truncated first if history exceeds 30K chars. Use AGY via `ask-agy` for current Gemini-family design questions.

### How the bridge works (architecture)
The bridge is **not** an MCP tool. MCP is one-directional (client→server). The bridge uses a different architecture:

1. **SQLite broker DB** (`data/broker.db`) — shared message queue
2. **CLI wrapper** spawns the target agent CLI (`agy`, `claude`, or `codex`) as a subprocess with the message as prompt
3. The target agent runs, output is captured and stored back in the broker DB
4. Reviews auto-posted to GitHub issues (when task_id matches `issue-NNN`)

This means the broker can route among Claude, AGY, and Codex. In practice, GitHub remains the source of truth and broker messages should stay short.

### Review Persistence

Gemini CLI review auto-posting is legacy behavior and is not a current route.
For current Gemini-family review, use AGY via the bridge and record the review
result in the PR body or GitHub issue explicitly.

### Passive notification (MCP send_message)
For non-blocking FYI messages AGY sees at next session start:
```python
mcp__message-broker__send_message(
    to="agy", content="FYI: bio Phase A complete. See #560.",
    from_llm="claude", message_type="context"
)
```

---

## Multi-Agent Deliberation (`.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss`)

**This section was added 2026-05-02 after recognizing systematic underutilization** of `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` for design/framing/architecture decisions. We were defaulting to single-shot AGY reviews and Claude-alone-reasoning where distributed deliberation would have caught more.

### What `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` is — and isn't

`.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` runs bounded rounds (default 2, max 4) of parallel agent responses on a topic, short-circuiting when all agents end with `[AGREE]`. Transcript lands in the named channel with `parent_id` threading.

**It is NOT a quorum mechanism.** Three agents don't form an independent jury — Claude/Gemini/Codex all trained on overlapping internet corpora and have **correlated blind spots** (e.g., Russian-imperial framings show up in all three model families' priors). Math-voting on agent agreement isn't trustworthy.

**What it actually delivers:**
- **More angles per decision** — Gemini catches content/citation gaps, Codex catches code edge cases, Claude catches architecture
- **Adversarial pressure** — agents are prompted to challenge each other, which surfaces hidden assumptions one agent alone wouldn't pressure-test
- **Documented deliberation** — channel transcript = referenceable context for future sessions, not "trust me, I thought about it"

### When to use which tool

| Use `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` | Use bridge `ask-agy` (single-shot) | Don't use either |
|---|---|---|
| Architectural trade-offs (e.g., module_type categories, retrieval strategy) | Mechanical PR review with green CI | Trivial fixes (delete leftover file) |
| Pedagogy/framing decisions (POC scope, anchor choice, decolonization audits) | Adversarial review of a single PR | Implementation tasks (Codex codes alone) |
| Brief pre-flight before dispatch (catch ambiguities before Codex burns 8 min) | Quick disambiguation question | When the answer is obvious |
| Cross-agent deadlock (Gemini APPROVE, Codex REVISE on same artifact) | Spot-check an output against a rule | Time-sensitive merge decisions (3-min discussion latency stacks) |
| Quality review of foundational content (M1-M3 modules, ADRs) | One-off domain question | |

### Budget angle

- `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss ... --with agy,codex` (Claude excluded) avoids Anthropic spend; AGY itself is metered. Use when AGY/Codex perspectives are enough.
- `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss ... --with claude,agy,codex` burns Anthropic per round per Claude turn. Reserve for foundational decisions where Claude's voice as architect/reviewer matters (architecture, pedagogy framing, decision arbitration).

### Concrete example — what we missed today (2026-05-02)

When proposing the POC anchor module, Claude reasoned alone and offered A1/M10 colors as a "neutral steady-state baseline." User had to catch the Russian-imperial-propaganda angle on colors that invalidated "neutral." If we had run:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss content "POC anchor module choice — M10 colors vs M20 my-morning, considering decolonization sensitivity in A1" --with claude,agy,codex --max-rounds 2
```

…Gemini or Codex might have surfaced the colors angle independently. The deliberation transcript would also exist as a referenceable record on the `content` channel, not buried in a Claude session that compaction would eventually destroy. **Pattern: when picking among options that touch decolonization, framing, or pedagogy — discuss, don't decide alone.**

### Decision Card pattern (when `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` surfaces a CHOICE)

Most `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` runs converge with `[AGREE]` — orchestrator just executes the consensus. But when discussion surfaces **disagreement OR multi-option output**, the orchestrator MUST emit a structured Decision Card so the user can override or approve. Don't bury decisions in transcript noise.

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

For high-risk tracks — **FOLK, HIST, BIO, ISTORIO, LIT, OES, RUTH** (all decolonization-sensitive seminar tracks where Russian/Soviet-imperial framings are most ingrained in training data) — the orchestrator MUST apply at least one of the following failsafe mechanisms:

- **Mechanism A (Force-emit Decision Card on `[AGREE]`):** If `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` runs on a topic touching any high-risk track and converges with `[AGREE]`, the orchestrator emits a Decision Card anyway. The question is framed as "agents converged on X — but consensus on this track is suspect; user should sanity-check." The user can quickly approve or override.
- **Mechanism B (Inject domain-specific bias checklist):** For high-risk tracks, the `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` prompt is augmented with a short bias checklist explicitly provoking adversarial review on known bias vectors.
  - *Example for HIST:* "Did you check the proposed framing against canonical decolonized sources? Bulgakov-as-Ukrainian, Gogol-as-Ukrainian, Akhmatova-as-Ukrainian, etc., are the 'Kyiv-born equals Ukrainian writer' trap — flag if you see it. Did you check whether the historical actor is being framed in Russian-imperial categories versus Ukrainian native categories?"

**Recommendation:** Prefer **Mechanism B** (proactive — catches bias during discussion) for any new `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` on high-risk tracks. Fall back to **Mechanism A** (reactive — emit card on consensus) when no domain-specific checklist exists yet for that track.

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

### Citation provenance check (#1683, shipped 2026-05-05)

The bridge runs a citation-provenance check on every channel post and reply before commit. Verbatim attributions to authoritative sources (Антоненко-Давидович, Грінченко 1907, Правопис 2019, СУМ-11, ЕСУМ) are verified against `data/sources.db`. Unverified citations get an inline `<!-- CITATION-UNVERIFIED ... -->` marker; verified citations and citations to sources without an automated verifier (VESUM, Шевельов, Вихованець, Пономарів) pass through silently.

**Annotate-mode, not block-mode.** The check never refuses a post — it surfaces the doubt. This keeps the cost of a false-positive low (the channel still flows; reviewers see the marker and can dismiss it) and the cost of a true-positive a clear breadcrumb for downstream consumers (reviewer prompts, content modules, students never inherit a forged citation).

**Why this exists.** On 2026-05-05, two `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` runs hours apart on собака gender produced the same fabricated Антоненко-Давидович citation ("Антоненко-Давидович categorizes feminine собака as a calque/Russianism") in Gemini's reply. АД has no entry on собака per `mcp__sources__search_style_guide`; the model's prior was the bug, not the source. The deliberation-protocol fix (commit `872d8376b0`) blocked round-1 short-circuit so a single round of cross-agent comparison happens — but if a fabrication had survived two rounds of `[AGREE]`, it would have shipped to curriculum. This check closes that gap.

**Detection scope (v1):** verbatim source-name match (with permissive inflection across Cyrillic case endings) + headword extraction from the local window (italicized, code-fenced, quoted, or "іменник X" / "слово X" patterns). Multi-pattern same-source mentions within ~200 chars are de-duplicated to one citation. Out of scope (deferred): fuzzy-match of quoted text against source body content; LLM-based attribution detection; block-mode rejection. The v1 catches outright fabrication where the headword does not exist anywhere in the source corpus.

**Implementation:** `scripts/ai_agent_bridge/_citation_check.py` (detection + verification + annotation). Hook lives in `_channels.py:post()` — controlled by `verify_citations: bool = True` keyword. System/audit kinds (anything other than `post`/`reply`) skip verification automatically.

**Graceful degradation:** the verifier soft-skips if `data/sources.db` is missing (worktree without the data dir, fresh checkout, CI minimal env). Soft-skips never produce flags — they're recorded internally as "verifier unavailable" so a deployment problem cannot manufacture false positives.

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
curl -s 'http://localhost:8765/api/session/current?agent=claude'

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
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "/full-rebuild-bio 5" \
  --task-id rebuild-bio-5

# Core track rebuild
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "/full-rebuild-core-a a1 3" \
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

### AGY Model Names

Gemini CLI and Gemini Code Assist are unsupported for current project work.
For Gemini-family review or support, use AGY through
`.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy ...` or
`scripts/delegate.py dispatch --agent agy ...`.

Direct `agy --model` calls use display labels from `agy models`, such as
`Gemini 3.1 Pro (High)` and `Gemini 3.5 Flash (High)`. The bridge and runtime
may accept slugs such as `gemini-3.1-pro-high` and map them to AGY display
labels before invoking AGY.

---

## MCP Writer Observability

Codex `*-tools` writer dispatch must fail before model invocation when MCP intent
cannot be wired. The dispatch path emits:

- `mcp_config_resolved`: emitted after resolving `.mcp.json` into runtime
  `tool_config`. Check `requested_servers`, `resolved_servers`,
  `resolution_status`, `missing_server_names`, and `config_path`.
- `mcp_runtime_init`: emitted by the runner when Codex output shows MCP runtime
  status. `status=ready` comes from `mcp: <server>/<tool> started` or
  `(completed)`. `status=failed` comes from Codex `rmcp::transport::worker`
  transport errors. `status=timeout` means no runtime init line appeared within
  the init-observation window.

If a writer label ends in `-tools`, requests MCP servers, and resolves none, the
pipeline raises `LinearPipelineError` and refuses to dispatch tool-less. Codex
legacy SSE endpoints (`type: sse` or URLs ending `/sse`) are treated as
unresolved for this path; use the streamable HTTP `/mcp` endpoint.

To debug "writer produced 0 tool calls", start with the writer JSONL:

1. Find `mcp_config_resolved`. If `resolved_servers` is empty, fix `.mcp.json`
   or the requested server name before rerunning the bakeoff.
2. Find `mcp_runtime_init`. `failed` usually includes the Codex transport error
   line; `timeout` means Codex never showed a server/tool init line.
3. Only inspect prompt/tool-theatre telemetry after both config resolution and
   runtime init show the expected `sources` server.

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
