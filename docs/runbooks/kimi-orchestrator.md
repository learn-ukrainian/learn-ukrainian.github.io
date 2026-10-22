# Kimi interactive launcher

Kimi models are retired (OO-58, #11327). `start-kimi.sh` and `start-kimicc.sh`
refuse every catalog id before a session starts. There is no interactive default
and no certified Kimi driver. Use a certified Claude, Codex, or Grok driver for
lease-bound orchestration.

Historically `start-kimi.sh` was interactive-only: it never claimed a stream
lease and rejected `--epic`. The Claude-Code harness accepted only explicit Kimi
credentials and never an ambient `ANTHROPIC_AUTH_TOKEN`. Those commands are not
a route.
