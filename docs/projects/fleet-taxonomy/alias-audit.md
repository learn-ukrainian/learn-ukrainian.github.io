# Fleet Taxonomy — Launcher Alias Audit

The launcher estate was consolidated in #5935. Public launchers use one
grammar from `scripts/lib/launcher_core.sh`; provider adapters do not accept
ad-hoc selector spellings.

| Entry point | Lane surface | Unknown / invalid behavior |
| --- | --- | --- |
| Interactive launchers | No lane flag | `--epic` exits 2 and directs users to a driver. |
| `start-claude-driver.sh` | `--epic SELECTOR` | Selector is allowlisted; uncertified model exits 4. |
| `start-codex-driver.sh` | `--epic SELECTOR` or `--governor SELECTOR\|AUTO` | Invalid selector exits 2; governor never claims a lease. |
| `start-gemini-driver.sh` | `--epic SELECTOR` | Selector is allowlisted; uncertified model exits 4. |
| `start-grok-driver.sh` | `--epic SELECTOR` | Selector is allowlisted; uncertified model exits 4. |

`scripts/lib/handoff_identity.sh` remains the selector source of truth:
`infra`, `devops`, `atlas`, `hramatka`, `folk`, `bio`, and `corpus`, including
their documented aliases. Driver lifecycle is deterministic: validate model and
selector, claim lease, run the provider canary, then bind `drive-epic`.

All public scripts accept `--help` and `LAUNCHER_DRY_RUN=1`; unknown launcher
flags exit 2. Provider CLI flags must follow `--` so their ownership is
unambiguous.
