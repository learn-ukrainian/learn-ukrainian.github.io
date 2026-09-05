"""GitHub integration: posting reviews to issues."""

import subprocess

from secret_redactor import redact_text

from ._config import GH_CHAR_LIMIT


def _format_review_chunk(chunk: str, model: str, part_num: int, total_parts: int) -> str:
    """Format a review chunk with part header for GitHub posting."""
    chunk = redact_text(chunk) or ""
    if total_parts > 1:
        return f"**[Part {part_num}/{total_parts}]** Review ({model})\n\n{chunk}"
    return f"**Review** ({model})\n\n{chunk}"


def _split_content(content: str, limit: int = GH_CHAR_LIMIT) -> list[str]:
    """Split content into chunks at newline boundaries, each under limit chars."""
    chunks = []
    pos = 0
    length = len(content)
    while pos < length:
        end = min(pos + limit, length)
        if end >= length:
            chunks.append(content[pos:])
            break
        # Find last newline before limit
        split_at = content.rfind('\n', pos, end)
        if split_at <= pos:
            split_at = end  # No newline found, hard split
        chunks.append(content[pos:split_at])
        # Skip past the newline
        pos = split_at + 1 if content[split_at] == '\n' else split_at
    return chunks


def _gh_comment(issue_num: int, body: str) -> bool:
    """Post a comment on a GitHub issue. Returns True on success."""
    body = redact_text(body) or ""
    result = subprocess.run(
        ["gh", "issue", "comment", str(issue_num), "-F", "-"],
        input=body, text=True, capture_output=True, timeout=15
    )
    if result.returncode != 0:
        stderr = redact_text(result.stderr or "") or ""
        print(f"⚠️  GitHub comment failed: {stderr[:200]}")
        return False
    return True


def _post_review_to_github(task_id: str, content: str, model: str) -> int | None:
    """Post review content to a GitHub issue. Returns issue number on success."""
    if not content:
        return None
    content = redact_text(content) or ""

    try:
        from ._messaging import _extract_issue_number
        issue_num = _extract_issue_number(task_id)
        chunks = _split_content(content)
        total_parts = len(chunks)

        if issue_num:
            return _post_to_existing_issue(issue_num, chunks, model, total_parts)
        else:
            # Don't auto-create GH issues for reviews without a target issue.
            # Review artifacts live in orchestration/ folders. GH issues are for
            # work items only. See #970.
            safe_task_id = redact_text(task_id) or ""
            print(f"   ℹ️  No issue number in task_id '{safe_task_id}' — skipping GH posting (review saved to orchestration/)")
            return None

    except FileNotFoundError:
        print("⚠️  gh CLI not found — skipping GitHub posting")
        return None
    except subprocess.TimeoutExpired:
        print("⚠️  GitHub posting timed out — skipping")
        return None
    except Exception as e:
        safe_error = redact_text(str(e)) or ""
        print(f"⚠️  GitHub posting failed: {safe_error}")
        return None


def _post_to_existing_issue(issue_num: int, chunks: list[str], model: str, total_parts: int) -> int | None:
    """Post review as comment(s) on an existing GitHub issue."""
    for i, chunk in enumerate(chunks, start=1):
        body = _format_review_chunk(chunk, model, i, total_parts)
        if not _gh_comment(issue_num, body):
            return None
    print(f"   📎 Review posted to #{issue_num} ({total_parts} part{'s' if total_parts > 1 else ''})")
    return issue_num
