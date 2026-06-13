# GitHub Workflows

CI, security, and deploy automation for the learn-ukrainian curriculum.

## Active Workflows

| Workflow | Purpose | Trigger | Notes |
|----------|---------|---------|-------|
| `ci.yml` | Lint (ruff), Quality Gates (radon), Lint Prompts, root-script guard, MDX source parity, lesson-schema drift, **Test (pytest)**, Frontend (build + vitest), Secret Scanning (trufflehog) | PR / push to main | `Test (pytest)` is the only **required** status check. Required path is hermetic — no network model downloads (Stanza/HF tests are `slow` and excluded; see `docs/bug-autopsies/stanza-model-md5-flake.md`). pytest gates on **Python** paths only; `site/**` gates the frontend job, so content/MDX PRs skip pytest. |
| `content-ci.yml` | Advisory content gates (bio dossier Section-7 xref, dossier word-count) | PR | Non-blocking; unfiltered `pull_request` so it never wedges as "expected". |
| `security-audit.yml` | Advisory dependency-vuln report (`pip-audit` + `npm audit`) | PR / weekly | Report-only; visibility layer over the dependabot backlog. Does not block. |
| `zizmor.yml` | Static security analysis of all workflow YAML | PR / push / weekly | SARIF → Security tab. Runs `--offline`. |
| `validate-yaml.yml` | YAML syntax / schema validation | PR / push | |
| `rules-deployment-check.yml` | Agent-rule deploy idempotency check | PR / push | |
| `deploy-pages.yml` | Build Site + deploy to GitHub Pages | **Manual** (`workflow_dispatch`) | Auto-deploy on push is intentionally disabled. |

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
