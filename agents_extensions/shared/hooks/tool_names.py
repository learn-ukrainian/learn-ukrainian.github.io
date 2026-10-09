"""Exact shell tool names shared by Claude-compatible and Cursor hooks."""


def is_shell_tool(tool_name: object) -> bool:
    """Recognize Bash and Cursor Shell without accepting unknown aliases."""
    return tool_name in ("Bash", "Shell")
