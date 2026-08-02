# Entire external agent for Kimi Code

This preview adapter adds Entire protocol-v1 capture for the standalone
`kimi` CLI. It is intentionally not used for Kimi or GLM models hosted by
Claude Code, for GLM hosted by OpenCode, or for Codex Desktop/CLI; those use
Entire's native `claude-code`, `opencode`, and `codex` integrations.

The adapter reads Kimi Code's native `session_index.jsonl` and
`agents/main/wire.jsonl`, preserves the actual model alias (for example
`kimi-code/k3`), extracts native prompt/file/token evidence, and installs a
single managed block in the user-level Kimi `config.toml`. Hook commands are
fail-open so an absent or unavailable Entire CLI cannot block Kimi.

## Build and verify

```bash
go test -race ./...
go build -trimpath -o entire-agent-kimi ./cmd/entire-agent-kimi
AGENT_BINARY="$PWD/entire-agent-kimi" external-agents-tests ./...
```

From the repository root, the project installer builds and atomically places
the binary on `PATH`:

```bash
scripts/entire/install_kimi_external_agent.sh
```

Then install the lifecycle hooks once:

```bash
entire-agent-kimi install-hooks
entire-agent-kimi are-hooks-installed
```

`uninstall-hooks` removes only the managed block and restores every surrounding
configuration byte. A drifted managed block requires explicit `--force` repair.

## Security boundary

- Session references must remain under Kimi's session root or the current
  repository root used by the protocol compliance harness.
- Session IDs reject separators and traversal.
- Hook installation preserves credentials and unrelated Kimi settings.
- Entire checkpoints remain routed to
  `learn-ukrainian/entire-checkpoints-private`; no public Entire refs are
  created.
- Subagent attribution is not declared because current Kimi hook payloads do
  not expose a stable child-run identifier.
