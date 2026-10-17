# Stack currency

## 1. One pin file (desired state)

`scripts/config/stack_pins.yaml`: one row per component that Dependabot does not cover: agent CLIs (Claude Code, Codex, Grok, cursor-agent, AGY), Entire, gh, uv, Python and Node versions, SQLite/PostgreSQL, Prometheus/Grafana/Alertmanager/exporters, MCP servers, model ids we pin, CI literals (runner images, action-less tool versions), browser and test runtimes (Playwright browsers, pytest plugins outside pip), deployment tooling (deploy scripts' CLIs, Pages build), and backup/restore tooling with its restore-compatibility note. Fields: component, owner lane (exactly one), pinned version, where it is pinned (repo-relative path), upstream source, class, last review date. Each row also carries `review_by`. No schema engine, no dashboard.

## 2. Watching (reuse what runs today)

- Dependabot stays the only updater for github-actions, pip and site npm: weekly, grouped non-major, 7-day cooldown for version updates, none for security updates. Add the root npm manifest.
- One report-only step added to the existing weekly `security-audit.yml` run: pinned (from §1) vs latest stable upstream. Output: versions and repo-relative paths only, into the existing advisory issue. It never opens PRs, enqueues, arms merge or satisfies the workflows CODEOWNERS gate.
- One small local drift check on the host (installed vs pinned vs running process), folded into an existing host check (DevOps picks which); private output, no new timer.
- Collection is separate from publication: the collectors only write a local private report. Only the CI step publishes, with read-only repository permission plus write to the one advisory issue, and only versions and repo-relative paths.
- Why not Renovate: it is a second app with regex parsing, and it cannot run the canaries that matter (Entire privacy, fail-open). A green Renovate PR would invite exactly the landing ADR-018 forbids. The report-only diff gives the same signal with no new machinery.

## 3. Security

- Daily security detection stays the existing 04:23 UTC advisory refresh. Deadlines by severity: actively exploited (CISA KEV or vendor-confirmed) = triage the same day; critical 48 h; high 7 days; others at the next monthly review.
- Ubuntu security updates come from unattended-upgrades; a distro backport is not a version gap. Track pending reboots (the 2026-10-08 kernel is still pending) and services still running old libraries after an upgrade (needrestart), and apply them in the maintenance window.
- Model and API retirements count as security/availability events (catalog freshness already runs Mondays).

## 4. Cadence and expiry

- Agent CLIs and Entire: reviewed every 2 weeks. Libraries, Python, Node, OS, monitoring: monthly. Each review either moves the pin through §5 or re-confirms it with a new review date and one-line reason.
- Alternatives: one stack layer per quarter, in rotation (origin hosting, store, recall layer, CI, monitoring), plus event triggers (vendor price or terms change, end of support, repeated incidents). Each review writes a short comparison record: incumbent, one credible alternative, maintenance, privacy, migration cost, decision (adopt/trial/assess/hold). A switch needs a new decision record after a trial. No research cron.
- Expiry means the review is overdue; it never invalidates an accepted pin or blocks use. `check_decisions.py` (reads docs/decisions/decisions.yaml) gains one input: the `review_by` column of stack_pins.yaml, reported as overdue reviews beside expired decisions. Before relying on it: dec-008, dec-009 and dec-010 are past expiry and still active; their owners re-confirm or retire them first. ADR-018 joins the journal.

## 5. Upgrade path (the side-by-side canary is only for what can change data destination, transcripts or fail-open behaviour; every upgrade, patches included, keeps provenance, review and rollback)

1. Read the changelog as untrusted data; list breaking and security items that touch our surfaces.
2. Verify provenance of the candidate binary (checksum or signature from the vendor) before running it.
3. Canary side by side (separate binary path, throwaway clone; never the live install first) with explicit checks.
4. Move the pin in one PR with rollback steps; independent cross-family review; critical/security components get Opus or Sol sign-off.

ADR-018 consequence sentence (replaces "does not authorize moving beyond 0.8.42"):

"The last accepted Entire CLI version is recorded in stack_pins.yaml; it is an acceptance record, not an expiry. A newer CLI is allowed only after a compatibility review re-proves the version-sensitive canaries (fail-closed version preflight, private-destination allowlist, zero public entire/* refs, body-leakage scan, fail-open outage behaviour, locator digest checks), with independent cross-family review and a reviewed rollback procedure. Until that review is recorded, automated calls prove the accepted version. A version probe is not that review. After approval, the native-recall preflight and the runtime version guard move to the new version in the same change."

## 6. Owners

DevOps: pin file, CI report step, host drift check, host packages, monitoring, CI. Infra: agent runtime, hooks, Entire, agent CLIs. Monitor: API and dashboards. Each lane: its own libraries. The CTO reads the weekly report and assigns.

## Non-goals

No Renovate, no new scheduler or bot, no second scanner, no Monitor panel, no automatic changelog extraction, no auto-upgrade of agent CLIs or host packages, no daily non-advisory noise, no mandatory canary for plain patches.
