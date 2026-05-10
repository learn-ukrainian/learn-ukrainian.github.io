# Gemini-tools deep review

Canonical report: [`REPORT.html`](REPORT.html)

The audit is HTML-first per `MEMORY.md` rule `#M-2`. Summary: root cause found. Gemini-tools ran from the bakeoff artifact directory, where Gemini CLI had no `.gemini/settings.json`, so `--allowed-mcp-server-names sources` filtered an empty MCP catalog instead of loading the repo-root `sources` server.
