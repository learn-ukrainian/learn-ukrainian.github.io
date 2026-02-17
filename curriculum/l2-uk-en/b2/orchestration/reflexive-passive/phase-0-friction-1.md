**Phase**: Phase 0: Research (Core)
**Step**: Full research
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: `grep_search` failed with `--threads` argument error.
**Self-Correction**: Switched to `run_shell_command` with `rg` as per core mandates.
**Proposed Tooling Fix**: The `grep_search` tool wrapper needs to be fixed to not inject duplicate `--threads` flags.
