# Kimi Code external-agent decision and evidence

## Decision

Use one external Entire agent only for the standalone Kimi Code CLI. Do not
create `kimi-in-claude`, `glm-in-claude`, `glm-opencode`, or `codex-gui`
agents. Entire integration follows the host harness that owns the lifecycle
and transcript:

| Execution surface | Entire agent |
| --- | --- |
| Kimi or GLM model inside Claude Code | `claude-code` |
| GLM model inside OpenCode | `opencode` |
| Codex Desktop or Codex CLI | `codex` |
| Standalone `kimi` CLI | `kimi` external agent |

This is the smallest root-cause bridge because a source-blind standalone Kimi
K3 canary completed successfully but produced no Entire session, while the
native Claude Code, OpenCode, and Codex paths already exist.

## Black-box evidence

The installed Kimi Code version is `0.31.1`. Read-only inspection of native
session metadata established:

- user-level config: `${KIMI_CODE_HOME:-~/.kimi-code}/config.toml`;
- session index: `session_index.jsonl` with `sessionId`, `sessionDir`, and
  `workDir`;
- transcript: `<sessionDir>/agents/main/wire.jsonl`;
- model identity: `config.update.modelAlias`, `llm.request.modelAlias`, and
  `usage.record.model` (observed `kimi-code/k3`);
- prompt records: `turn.prompt.input[]` text parts;
- modified-file records: `context.append_loop_event` → `tool.call` → native
  `Write`/`Edit` `args.path`;
- usage records: `inputOther`, `inputCacheRead`, `inputCacheCreation`, and
  `output`.

No prompt or transcript body was copied into this public document. The
adapter reads the native source only when Entire invokes its protocol.

## Lifecycle mapping

| Kimi hook | Entire protocol event |
| --- | --- |
| `SessionStart` | `SessionStart` (1) |
| `UserPromptSubmit` | `TurnStart` (2) |
| `Stop` | `TurnEnd` (3) |
| `PreCompact` | `Compaction` (4) |
| `SessionEnd` | `SessionEnd` (5) |

`PostCompact` is intentionally not installed because `PreCompact` already
creates the protocol compaction boundary. Subagent events remain undeclared:
the current public hook payload names an agent but lacks a stable child-run ID
needed for honest attribution.

## Safety and rollout contract

- Entire CLI remains pinned to `0.8.42`.
- External-agent discovery is explicitly enabled in `.entire/settings.json`.
- The binary name is `entire-agent-kimi`, protocol version 1.
- Hooks are fail-open when Entire is absent or returns an error.
- Installation is atomic and contention-safe, preserves all bytes outside one
  marked block, and requires `--force` for managed-block drift.
- Session IDs and references are traversal checked.
- Public source-repository checkpoints continue to route only to
  `learn-ukrainian/entire-checkpoints-private`; public shadow refs are
  forbidden.
- Entire remains a non-load-bearing journal/provenance layer. GitHub, Fleet
  Comms, Monitor, rollover, and formal review remain authoritative.

## Verification gates

The merge gate requires:

1. Go unit and race tests, including concurrent hook installation and exact
   config restoration.
2. The upstream `entireio/external-agents-tests` protocol-v1 suite.
3. A source-blind real Kimi K3 lifecycle canary with actual model attribution.
4. Retry, outage/fail-open, multiple-worktree, checkpoint, explain/blame, and
   private-routing canaries.
5. Independent cross-family review and green repository CI.

Sources: [Entire agent overview](https://docs.entire.io/agents/overview),
[external plugins](https://docs.entire.io/agents/external-agent-plugins/overview),
[protocol architecture](https://docs.entire.io/agents/external-agent-plugins/architecture),
[lifecycle](https://docs.entire.io/agents/external-agent-plugins/lifecycle),
[commands](https://docs.entire.io/agents/external-agent-plugins/commands),
[data model](https://docs.entire.io/agents/external-agent-plugins/data-model),
[reference implementations](https://github.com/entireio/external-agents), and
[Kimi hooks](https://moonshotai.github.io/kimi-code/en/customization/hooks).
