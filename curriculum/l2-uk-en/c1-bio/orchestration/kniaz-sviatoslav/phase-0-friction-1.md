**Phase**: Phase 0: Research (Seminar)
**Step**: Full research
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: NameError: name 'run_shell_command' is not defined (repeatedly when trying to create dir)
**Self-Correction**: Abandoned attempt to create local directory for notes; focused purely on generating the text output as per the "TEXT GENERATOR" role which prohibits file creation anyway. Also, search snippets didn't provide clean direct URLs for ESU, so I had to rely on known base URLs and constructed searches to verify facts, using `history.org.ua` search URL as a reference.
**Proposed Tooling Fix**: Ensure `run_shell_command` is available or clarify in instructions that the agent should NOT try to create the `research/` directory themselves if they are in "TEXT GENERATOR" mode (the prompt says "Output ONLY text", but the skill implies a file workflow).
