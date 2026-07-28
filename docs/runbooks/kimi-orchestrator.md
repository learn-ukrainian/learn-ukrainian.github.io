# Kimi interactive launcher

Kimi has no certified public driver entrypoint. `start-kimi.sh` is therefore
interactive-only: it never claims a stream lease and rejects `--epic`.

```bash
./start-kimi.sh --model k3 "review the open PR"
./start-kimi.sh --harness claude-code --model k2.7
LAUNCHER_DRY_RUN=1 ./start-kimi.sh --harness claude-code --endpoint coding
```

The native `kimi-code` harness is the default. The Claude-Code harness accepts
only explicit Kimi credentials (`KIMICC_AUTH_TOKEN`, `MOONSHOT_API_KEY`, or
`KIMI_API_KEY`) or Kimi OAuth; it never consumes an ambient
`ANTHROPIC_AUTH_TOKEN`.

Use a certified Claude, Codex, Gemini, or Grok driver for lease-bound
orchestration. If Kimi gains a T4-certified driver in the future, add its public
entrypoint and lifecycle contract before documenting lane selection here.
