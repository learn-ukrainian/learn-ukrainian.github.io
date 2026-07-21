# Grok sealed formal CF isolation (#5557)

## Status (2026-07-21)

| Capability | Native Grok CLI | Formal CF sealed path |
| --- | --- | --- |
| OAuth / tool credentials | Required for Read/Grep/Glob; isolation cannot hide OAuth store from those tools | **Fail-closed** (`grok_isolated_review_unsupported`) |
| Project instructions suppress | N/A relative to OAuth residual | Fail-closed |
| Sealed snapshot cwd | Not a proven formal transport while OAuth is tool-visible | Fail-closed |
| Registry `formal_review_eligible` | `false` | Correct |

## Decision (provisional)

**Keep permanent fail-closed for sealed formal CF** until xAI tooling supports a review-only credential profile that cannot reach primary checkout / ambient project state while still allowing sealed Read/Grep/Glob on a snapshot.

Option A (preferred if vendor supports later): review-only OAuth profile scoped to snapshot roots.  
Option B (current): document residual; formal CF via `review-pr --reviewer claude|glm|codex` only.  
Option C: Grok as advisory/implement lane only for CF-adjacent work (already true for formal gate).

## Live lane (non-formal)

- Implement + advisory: `start-grok.sh`, `delegate --agent grok`, bridge asks
- Formal CF substitute seats: Claude / Codex / GLM

## Flip criteria

1. Secure design that hides OAuth from tools **or** a proxy that only serves sealed snapshot bytes.
2. Isolation tests: credentials not visible to tools; ambient instruction negative.
3. Smoke formal CF via Grok transport.
4. Then flip `formal_review_eligible: true`.

Parent: #5557 · stream #4707 · product #5512.
