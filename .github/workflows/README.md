# GitHub Workflows

CI, security, and deploy automation for the learn-ukrainian curriculum.

## Active Workflows

| Workflow | Purpose | Trigger | Notes |
|----------|---------|---------|-------|
| `ci.yml` | Required path: pytest shards, contracts (schema/MDX/atlas/BIO + secret scan + PR-body guard), frontend, coverage floor, **CI Gate**; advisory E2E after gate | PR / push to main / merge_group | `CI Gate` is the only **required** status check. Always-on parallel fan-out is capped (#4811). |
| `ci-gate-queue-recovery.yml` | Re-run cancelled CI Gate once when upstream jobs succeeded (runner-queue starvation) | Every 15 min / manual | Stopgap for #4811; scans recent CI runs via `gh api` (no `workflow_run` — zizmor); never re-runs genuine failures; default-branch logic only. |
| `content-ci.yml` | Advisory content gates (bio dossier Section-7 xref, dossier word-count) | PR | Non-blocking; unfiltered `pull_request` so it never wedges as "expected". |
| `hygiene.yml` | Advisory radon / prompt lint / postmortem / agent-config / scripts-root checks | PR | Composite `hygiene-checks` job (#4811 slot cut); not in CI Gate. |
| `integration-sweep.yml` | Arms auto-merge for abandoned reviewed PRs | Every 15 min / manual | Fail-closed membership, current-head approval, required-CI, and idle-owner checks; manual runs default to dry-run. |
| `security-audit.yml` | Advisory dependency-vuln report (`pip-audit` + `npm audit`) | PR / weekly | Report-only; visibility layer over the dependabot backlog. Does not block. |
| `zizmor.yml` | Static security analysis of all workflow YAML | PR / push / weekly | SARIF → Security tab. Runs `--offline`. |
| `validate-yaml.yml` | YAML syntax / schema validation | PR / push | |
| `rules-deployment-check.yml` | Agent-rule deploy idempotency check | PR / push | |
| `deploy-pages.yml` | Build Site + deploy to GitHub Pages | Manual, plus safe `main` pushes | Pushes deploy only when every changed path since the last successful Pages deployment is approved site code; curriculum, generated site content/data, and unknown paths stay manual. |

## Supply-chain hardening

- **All actions are SHA-pinned** (not tag-pinned). Dependabot's `github-actions`
  ecosystem keeps the pins fresh (7-day cooldown). See `.github/dependabot.yml`.
- **`persist-credentials: false`** on checkouts that don't push.
- **Least privilege**: top-level `permissions: contents: read`; per-job
  escalation only where needed.
- **Secret scanning** via trufflehog (`--results=verified,unknown`).
- **CodeQL** runs via GitHub default setup (Python / JS / TS / Actions).

## Security gates (layered, non-wedging)

1. **Auto-remediate** — Dependabot covers every ecosystem (github-actions, npm,
   **pip**) with automated security fixes enabled. Security PRs land continuously.
2. **Block-new** — CodeQL + (recommended) required-check promotion of
   `Secret Scanning` / `CodeQL`. Promoting a check to *required* is a
   branch-protection change and is done deliberately, not in-queue.
3. **Visibility** — `security-audit.yml` reports the live vuln count per PR.

## Gemini CI automation — retired (2026-06-04)

The previous `gemini-*.yml` workflows + `.github/commands/gemini-*.toml`
configs (gemini-cli PR/issue automation) were disabled in #2683 and removed
here. Gemini review/triage proved unreliable for merge confidence; agent
coordination now runs through the bridge (`scripts/ai_agent_bridge`) and
`scripts/delegate.py`, not GitHub Actions. See
`docs/best-practices/agent-cooperation.md`.

Gemini Code Assist for GitHub PR reviews is disabled by `.gemini/config.yaml`.
Use local machine-agent review via `scripts/delegate.py` instead.

## References

- **Agent cooperation:** `docs/best-practices/agent-cooperation.md`
- **Workflow audit:** `docs/dev/GITHUB_WORKFLOWS_AUDIT.md`
- **Stanza CI autopsy:** `docs/bug-autopsies/stanza-model-md5-flake.md`
