# Public source Entire pilot

This receipt onboards `learn-ukrainian/learn-ukrainian.github.io` as a source
repository for Entire 0.8.42 capture.

Checkpoint bodies are stored only in the private
`learn-ukrainian/entire-checkpoints-private` repository. The public product
origin must retain zero `entire/*` refs and zero session bodies. Entire remains
optional and non-authoritative; GitHub, Fleet Comms, Monitor, rollover, leases,
and formal review remain authoritative.

The committed `.entire/settings.json` is the body-free project binding Entire.io
uses to locate the separate checkpoint repository. The canonical generated
agent configuration installs native `codex` and `claude-code` hooks, while the
tracked OpenCode plugin installs native `opencode` lifecycle capture.

Entire integrates with the host harness, not a model label:

- Codex CLI and Codex Desktop use the same `codex` project hooks.
- Kimi or GLM hosted inside Claude Code use `claude-code` hooks.
- Kimi or GLM hosted inside OpenCode use the OpenCode plugin, which records the
  actual `modelID` reported by OpenCode.

Do not run `entire agent add codex`, `entire agent add claude-code`, or
`entire agent add opencode` over the deployed project configuration. The 0.8.42
JSON installers drop project timeout/status metadata, while its stock OpenCode
plugin requires the tracked `entire-exit.ts` termination companion for
OpenCode 1.17.13. Change the canonical sources
under `agents_extensions/`, run the project deployment workflow under the
required rail receipt, and keep the onboarding contract tests green. A separate
`entire-agent-<harness>` adapter is justified only by a failed source-blind
native-host canary.

The public issue receipt in #6165 records the checkpoint identifier, source
commit, private destination ref, leakage verdict, retry result, and authenticated
Entire activity result without reproducing a prompt, response, transcript, or
generated summary.

Before rollout, run
`.venv/bin/python scripts/entire/validate_checkpoint_routing.py` to prove that
the product setting and egress allowlist still name one identical destination.

The deployed source commit must carry `Entire-Checkpoint` as a real Git trailer.
Escaped newline text is not a trailer and will not enter Entire's activity index.
