**Phase**: Phase 0: Research (Core)
**Step**: Full research
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Switched to `run_shell_command` with `grep` directly to bypass the broken `grep_search` tool wrapper.
**Proposed Tooling Fix**: Fix the `grep_search` tool definition to correctly handle the `--threads` argument or remove the redundant injection.
