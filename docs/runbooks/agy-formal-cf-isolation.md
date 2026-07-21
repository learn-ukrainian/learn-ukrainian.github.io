# AGY sealed formal CF isolation (#5555)

## Status (2026-07-21)

| Capability | AGY / Antigravity CLI | Formal CF sealed path |
| --- | --- | --- |
| Project instructions suppress | **Unproven** — isolation raises `agy_isolated_review_unsupported` | Fail-closed |
| Ambient MCP suppress | **Unproven** | Fail-closed |
| Hooks / nested reviewers | **Unproven** | Fail-closed |
| Sealed snapshot cwd | Not a proven AGY transport | Fail-closed |
| `ask-agy --review` | Refuses before worktree provision (#5553) with substitute `review-pr` | Correct |
| Registry `formal_review_eligible` | `false` in `fleet_communications.yaml` | Correct until proof |

## Live lane (non-formal)

- Advisory bridge asks (`ask-agy` without `--review`)
- Content/language panel work with `sources` MCP outside sealed formal CF
- Substitute formal CF: `review-pr --reviewer claude|glm|codex`

## Flip criteria (do not skip)

1. Documented AGY flags (or sandbox profile) that suppress project instructions, MCP, hooks, nested agents.
2. `prepare_isolated_review_launch` positive path + ambient-instruction negative test.
3. Real smoke formal CF via AGY transport or registered sealed path.
4. Then flip `formal_review_eligible: true`.

Parent: #5555 · stream #4707 · product #5512.
