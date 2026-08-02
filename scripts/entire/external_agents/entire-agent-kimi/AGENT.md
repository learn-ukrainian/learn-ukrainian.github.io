# Kimi Code protocol notes

Authoritative upstream contracts:

- Entire external-agent protocol v1:
  <https://github.com/entireio/cli/blob/main/docs/architecture/external-agent-protocol.md>
- Entire external-agent reference implementations and test workflow:
  <https://github.com/entireio/external-agents>
- Kimi Code hooks:
  <https://moonshotai.github.io/kimi-code/en/customization/hooks>
- Kimi Code sessions:
  <https://moonshotai.github.io/kimi-code/en/guides/sessions.html>

Do not create model-specific variants. The registry name is the standalone
harness, `kimi`; model identity comes from the native wire records.

Keep protocol behavior stateless. Do not add network calls, public checkpoint
routing, transcript summaries, or a second session store. Kimi's native
`wire.jsonl` remains the session source. The managed hook block is the only
allowed mutation outside the repository and must stay byte-preserving,
idempotent, atomic, contention-safe, and fail-open.
