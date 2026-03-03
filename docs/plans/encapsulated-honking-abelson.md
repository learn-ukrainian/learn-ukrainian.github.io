# Plan: Persist Bridge Reviews to GitHub Issues (#721)

## Context

When Claude's context window compresses during long sessions, Gemini's adversarial review responses are lost. The review lives in stdout (ephemeral) and broker SQLite (not discoverable). Neither survives context compression usefully. This feature auto-posts reviews to GitHub issues so they're always retrievable via `gh issue view`.

## Files to Modify

| File | Change |
|------|--------|
| `scripts/ai_agent_bridge.py` | Add `_extract_issue_number()`, `_post_review_to_github()`, hook into `process_and_respond()` |
| `docs/best-practices/agent-cooperation.md` | Document auto-posting behavior |
| `docs/SCRIPTS.md` | Document new `--no-github` flag in ask-gemini flags table |

## Implementation

### 1. New helper: `_extract_issue_number(task_id) -> int | None`

```python
import re

def _extract_issue_number(task_id: str) -> int | None:
    """Extract GH issue number from task_id. Returns None if no issue pattern."""
    if not task_id:
        return None
    match = re.match(r'^(?:issue|gh)-(\d+)$', task_id)
    return int(match.group(1)) if match else None
```

Strict regex per Gemini's review — prevents injection via malformed task_ids.

### 2. New helper: `_post_review_to_github(task_id, content, model) -> int | None`

Logic:
1. Try `_extract_issue_number(task_id)` — if matched, post as comment(s) on that issue
2. If no issue pattern, **create a new issue** titled `Review: {task_id}` with label `review-result`, and post the review as the body (or body + follow-up comments if >65K)
3. If no `task_id` at all, create issue titled `Review: {ISO timestamp}` with label `review-result`

**65K splitting**: GitHub limit is 65,536 chars per comment/body. Split at nearest newline before 64,000 chars. Post sequentially as `[Part 1/N]` header prefix. First chunk goes into body (new issue) or first comment (existing issue), rest as follow-up comments.

**Safety**:
- Use `subprocess.run(["gh", ...], input=content, text=True, timeout=15)` — pipe via stdin (`-F -`), never `--body` (avoids ARG_MAX + escaping)
- `timeout=15` per comment to prevent hanging the bridge
- Wrap entire function in try/except — failure prints warning but never breaks the bridge
- Return the issue number on success (for logging)

### 3. Hook into `process_and_respond()` response routing

In the **standard mode** `else` branch (line ~1184), after the existing `send_message()` + `acknowledge()` calls, add:

```python
# Persist review to GitHub
_post_review_to_github(msg['task_id'], response, model)
```

**Only standard mode** — not `stdout_only` (orchestrated builds) and not `output_path` (file output mode). Those are batch pipeline paths where the calling script manages persistence.

### 4. New flag: `--no-github`

Add `--no-github` flag to `ask-gemini` subcommand to skip GH posting. Useful for quick ad-hoc queries that don't need persistence. Pass through to `process_and_respond()` as `skip_github=False` kwarg.

### 5. Documentation updates

**`docs/best-practices/agent-cooperation.md`** — Add a section under "Communication Channels":

```markdown
### Automatic Review Persistence

Reviews dispatched via `ask-gemini` are automatically posted to GitHub:

| task_id pattern | Behavior |
|-----------------|----------|
| `issue-NNN` / `gh-NNN` | Posted as comment on issue #NNN |
| Any other value | New issue created with `review-result` label |
| None | New issue created titled `Review: {timestamp}` |

Reviews >65K chars are split into multiple comments. To skip: `--no-github`.
```

**`docs/SCRIPTS.md`** — Add `--no-github` to the flags table:

```markdown
| `--no-github` | Skip auto-posting review to GitHub issue |
```

## Verification

1. **With existing issue**: `ask-gemini "test" --task-id issue-721 --model gemini-3-flash-preview` — verify comment appears on #721
2. **Without issue pattern**: `ask-gemini "test" --task-id test-review --model gemini-3-flash-preview` — verify new issue created with `review-result` label
3. **Large review**: Manually test with >65K content to verify splitting works
4. **No gh CLI**: Temporarily rename `gh` binary, verify bridge still completes with warning
5. **`--no-github` flag**: Verify it suppresses GH posting
