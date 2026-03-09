# Agent Cooperation Best Practices

> **Scope:** How Claude and Gemini work together without degrading each other's output quality.
> Full protocol: `docs/CLAUDE-GEMINI-COOPERATION.md`

---

## Team Structure

| Team | Agent | Role |
|------|-------|------|
| 💙 **Синя команда** (Blue) | Claude | Architect, reviewer, quality gate |
| 💛 **Жовта команда** (Gold) | Gemini | Content builder, implementer |

**Both teams are adversarial by design.** The purpose is quality through finding mistakes, not agreement. An approved module means both teams couldn't find serious problems — not that both teams were polite.

---

## The Non-Negotiable Rule

**An LLM must NEVER review its own work.**

Self-review produces inflated scores. Observed in production: Gemini reviewing its own content gave 9.9/10 scores with language like "ensuring a high score" and "reflecting the fixes made." This was not bias in the model — it was a structural failure: the same agent that wrote the content reviewed it.

### Valid review paths
- ✅ Claude reviews Gemini's content
- ✅ Gemini reviews Claude's architecture proposals
- ✅ Automated audit gates (no LLM bias)
- ❌ Gemini reviews its own content
- ❌ Claude reviews its own code without external validation

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

### Direct dispatch (ask-gemini)
For requests needing immediate response:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Review posted on #559. Please read and respond." \
  --task-id issue-559
```

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

At the start of every session:

1. **Load memory** — what was in progress last session:
   ```python
   mcp__memory__search_nodes(query="in progress current session")
   mcp__memory__search_nodes(query="next session todo")
   ```

2. **Check inbox** — notifications from Gemini:
   ```python
   mcp__message-broker__check_inbox(for_llm="claude")
   ```

3. **Read unread messages** — respond on GitHub if substantive

4. **Check monitoring API** — what's building right now:
   ```bash
   curl -s http://localhost:8765/api/batch/active
   ```

At session end: save progress summary to memory.

---

## Issue Claiming Protocol

**Agents never self-assign.** Only the user or orchestrator assigns work.

When starting an issue:
```bash
gh issue edit {N} --add-label "working:claude"
gh issue comment {N} --body "Starting work on X"
```

When done:
```bash
gh issue edit {N} --remove-label "working:claude"
gh issue edit {N} --add-label "review:gemini"  # or review:human
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
