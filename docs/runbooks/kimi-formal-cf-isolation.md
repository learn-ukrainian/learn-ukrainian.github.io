# Kimi sealed formal CF isolation (#5556)

## Status (2026-07-21)

| Capability | Native Kimi Code CLI | Formal CF sealed path |
| --- | --- | --- |
| Project instructions suppress | **Unproven** — no documented equivalent of Codex `--sandbox` / Claude disable-project-instructions for repo `AGENTS.md` / Claude-style project prompts | Fail-closed |
| Ambient MCP suppress | **Unproven** for sealed review transport | Fail-closed |
| Hooks / nested reviewers | **Unproven** | Fail-closed |
| Sealed snapshot cwd only | Not wired through `prepare_isolated_review_launch` for engine `kimi` | Absent → refuse |
| `review-pr --reviewer kimi` | **Not implemented** (reviewers: auto\|codex\|glm\|claude only) | Use substitute seats |
| Registry `formal_review_eligible` | `false` in `scripts/config/fleet_communications.yaml` | Correct until proof |

## Live lane (non-formal)

- `delegate.py --agent kimi` (default `k2.7-coding`; K3 via model override)
- `ai_agent_bridge ask-kimi` / `process-kimi`
- `./start-kimi.sh --epic …` (supervisor + canary mint)
- `./start-kimicc.sh` (Claude UI → Kimi API route)

## Substitute formal CF

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer glm   # local
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> --reviewer claude
```

## Flip criteria (do not skip)

1. Isolation capability matrix with proven CLI flags or sandbox profile.
2. `prepare_isolated_review_launch` positive path + ambient-instruction negative test.
3. `review-pr --reviewer kimi` or sealed transport registration.
4. Real smoke formal CF on a PR.
5. Then flip `formal_review_eligible: true`.

Parent: #5556 · stream #4707 · product #5512.
