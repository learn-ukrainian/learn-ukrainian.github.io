# Current Session Router

Latest-Brief: docs/session-state/current.orchestrator.md

Agent-Handoff:
- orchestrator: docs/session-state/current.orchestrator.md
- codex: docs/session-state/current.codex.md
- claude: docs/session-state/current.claude.md
- gemini: docs/session-state/current.gemini.md

Default-Agent: orchestrator
Generated-At: 2026-06-01T00:25:00Z

This file is a small compatibility router. Detailed thread state lives in
`docs/session-state/current.<agent>.md`; this router was refreshed after the
A1 M6 slice so the next cold-start sees the current agent handoff timestamps.
