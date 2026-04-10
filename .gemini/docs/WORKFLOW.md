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

### Multi-turn conversations
Claude can start a threaded conversation with you:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py converse "message" --task-id "topic-name"
```

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
