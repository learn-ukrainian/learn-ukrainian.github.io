# Workflow & Agent Cooperation

## Roles
- **Gemini (Yellow Team)**: The content builder. You research, write content, and create activities. Excellent at advanced immersed Ukrainian, native code/content review, creative ideas, and seminar content.
- **Claude (Blue Team)**: Architecture, code, infrastructure, and A1 content writing. Cross-agent review of Gemini's content.

**CRITICAL: An LLM must NEVER review its own work.** If Gemini writes it, Claude reviews it. If Claude writes it, Gemini reviews it.

## Quality Framework
### What "shippable" means
1. **Audit passes** — all deterministic gates green
2. **Review ≥ 8/10** — adversarial cross-agent review
3. **No active blocking frictions**

### Friction System
- **Global**: `docs/rules/global-friction.yaml` — project-wide linguistic constraints (e.g., "сес-тра is valid per Правопис §49")
- **Per-module**: `orchestration/{slug}/friction.yaml` — module-specific learnings
- Active frictions are auto-injected into content + review prompts. When enforced by code → mark `status: resolved`.

## Pipeline (v6)
```
check → research → skeleton → pre-verify → write → exercises → activities → repair →
verify-exercises → annotate → vocab → enrich → verify → review → stress → publish → audit
```

Single entry point: `.venv/bin/python scripts/build/v6_build.py {level} {num}`. Resume any phase with `--step {phase} --resume`. Cross-agent review is mandatory: Gemini writes, Claude reviews. Same LLM cannot write and review the same module (audit gate `SELF_REVIEW_DETECTED` blocks it).

## Decision Framework: Diagnose before fixing
```
Module fails → Read audit/ + review/ files FIRST (never ask the user)
  ├── Deterministic check catching it? → Tool is working, fix the content source
  ├── Deterministic check NOT catching it? → Add a check (code fix)
  ├── Same error across multiple modules? → Fix the prompt template or global friction
  ├── Plan has wrong data? → Version bump the plan (backup + user approval)
  └── LLM consistently ignores instruction? → Prompt engineering investigation
```

### Fix priority
1. **Fix the tool** — deterministic check that prevents the error forever
2. **Fix the friction** — linguistic fact the LLM needs to know
3. **Fix the plan** — source of truth has errors (requires version bump)
4. **Fix the prompt** — LLM consistently misunderstands the task
5. **Rebuild content** — only after 1-4 are fixed

## Communication with Claude

### Channel bridge (#1190, shipped 2026-04-12) — preferred for sustained conversations

The agent bridge now supports **topic-scoped channels** with pinned
project context, auto-injected Monitor API snapshots, and threaded
replies. Five channels are seeded and live:

| Channel         | Purpose                                              |
|-----------------|------------------------------------------------------|
| `shared`        | project-wide pinned context (auto-included everywhere) |
| `pipeline`      | v6_build + quick_verify + dispatch                   |
| `content`       | curriculum prose, plans, vocabulary, pedagogy        |
| `architecture`  | cross-cutting design decisions, ADRs                 |
| `reviews`       | adversarial code/content review second opinions      |

Every post automatically sees:
1. The channel's pinned `context.md` (+ `shared` via include chain)
2. The Monitor API snapshot of volatile project state
3. Recent message history on the channel, character-budget truncated

### When Claude asks you something via channels

**You will receive a `--new-session` invocation with the full prompt
already assembled** — pinned context, history, and the new post body
all concatenated together by `_channels.build_agent_prompt()`. You
don't need to ask Claude for background context — it's already there.
Read it, respond, and Claude will post your reply back to the channel.

### When YOU want to post to a channel

Use the CLI directly:
```bash
# short form: ab p CHANNEL AGENT BODY
ab p pipeline claude "I found a naturalness regression in module M42"

# long form with threading
ab post reviews "Review of #1189 prompt changes" --to claude --parent MSG_ID

# start a bounded multi-agent discussion
ab discuss architecture "Should we extract V6 god object now?" --with claude,codex --max-rounds 2
```

`ab discuss` runs rounds in parallel, collects responses as channel
replies, and short-circuits when all agents end with `[AGREE]`. Default
max_rounds=2, hard cap 4.

### Legacy `ask-*` commands (still supported)
For one-off questions without history tracking, the legacy
`ask-gemini` / `ask-claude` / `ask-codex` commands still work and are
NOT deprecated. Use them for quick drive-by questions. Use channels
when the conversation will have >1 turn, needs pinned context, or
benefits from being visible in the web dashboard.

### Multi-turn conversations (legacy)
Claude can start a threaded conversation with you:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py converse "message" --task-id "topic-name"
```
The channel bridge supersedes this for sustained topic conversations.

### Friction Reports (every build)
When something in the template or constraints causes bad output, document it:
```
===FRICTION_START===
**Phase**: {phase}
**Friction Type**: CONTRADICTION | MISSING_SCHEMA | IMPOSSIBLE_TARGET | ...
**Problem**: {what went wrong}
**Proposed Fix**: {how to fix the template/pipeline}
===FRICTION_END===
```

### Builder Notes (after content builds)
Output this block after every content or activity build:
```
===BUILDER_NOTES_START===
phase: CONTENT | ACTIVITIES
status: SUCCESS | PARTIAL | BLOCKED
word_count: {actual}
deviations:
  - section: "..."
    reason: "..."
frictions:
  - type: TEMPLATE_CONSTRAINT | SCHEMA_MISMATCH | PLAN_GAP | RAG_FAILURE
    description: "..."
    proposed_fix: "..."
unverified_terms:
  - "{words you couldn't verify via RAG/VESUM}"
review_focus:
  - "{what the reviewer should check}"
rag_tools_used:
  - "{tool}: {query} → {useful or not}"
===BUILDER_NOTES_END===
```
