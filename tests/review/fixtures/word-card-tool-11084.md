# Read-only `word_card` Sources grant (#11084)

The Sources MCP server gains the read-only `word_card` tool. It takes the
server's default read-only annotation, so
`scripts/agent_runtime/sources_read_only.sources_tool_sets` lists it among the
read-only tools, and the Codex adapter's `_sources_read_only_flags`
(`scripts/agent_runtime/adapters/codex.py`) grants it to read-only workers.
The Claude adapters disallow only persisting Sources tools, so their argv is
unchanged.

Both configurations were captured with the documented `capture.py` command
against this checkout, using the test module's scoped `CAPTURE_RUNNER` cache,
and compared with every approved surface. Only the `adapters` surface differs,
identically in both configurations: rows 0 (`codex`) and 4 (`codex-desktop`),
read-only without review isolation, change argv tokens 19 and 23.

- `mcp_servers.sources.enabled_tools` appends `"word_card"`, which sorts last.
- `mcp_servers.sources.tools` appends `word_card={approval_mode="approve"}`.

`word-card-tool-11084.json` records these two exact-once literal replacements
and is applied after every other overlay (`approved_word_card_tool_baseline` in
`tests/review/test_model_catalog.py`). Its digest is pinned there. A scope test
checks, in both configurations, that no other row, token, field or surface
changes and that the granted list equals the server's current read-only tools.
Historical baselines, inputs, the occurrence ledger, `capture.py`, `SPEC.md` and
checksum manifests stay byte-identical. Any other difference blocks
regeneration.
