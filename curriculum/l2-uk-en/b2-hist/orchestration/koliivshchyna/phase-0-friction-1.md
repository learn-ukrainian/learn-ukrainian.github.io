**Phase**: Phase 0: Research (Seminar)
**Step**: Full research
**Friction Type**: TOOL_USAGE_ERROR
**Raw Error**: `NameError: name 'run_shell_command' is not defined` and `PermissionError` (implied by read-only mode).
**Self-Correction**: I attempted to use `run_shell_command` inside the `tool_code` block, which is restricted to `google_search`. Then I realized I was in Orchestration Mode (Read-Only) and should not be trying to create directories or files at all. I switched to purely outputting the text content derived from the searches.
**Proposed Tooling Fix**: N/A - User error/Context misunderstanding.
