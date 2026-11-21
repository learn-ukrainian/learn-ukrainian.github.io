# GitHub Workflows

CI, security, and deploy automation for the learn-ukrainian curriculum.

## Active Workflows

| Workflow | Purpose | Trigger | Notes |
|----------|---------|---------|-------|
| `ci.yml` | Secret scan, Checks, Fleet security, pytest, Frontend, affected tests and guards, large-file guard and attribution. PRs run affected tests and repository invariants. Merge groups, nightly runs and manual runs use the full supported suite. | PR (opened/synchronize/reopened) / merge_group / nightly schedule / manual | `CI Gate` requires Fleet security and the other checks for its event. Landing requires green CI on the queue candidate. Queue metadata is always secret-scanned. Cancelled, missing and unexpectedly skipped jobs fail closed. See `docs/runbooks/ci-gate.md`. |
| `pr-body-guard.yml` | Negated-closing-reference PR-body lint (#8505), direct-push publication scan | PR (opened/edited/synchronize/reopened) / push | Advisory (not required). Moved out of `ci.yml` so body edits re-check only the body instead of restarting full CI. |
| `pr-publication-scan.yml` | Edit-time PR publication-field scan (title, body, branch, commit messages) | PR (opened/edited/synchronize/reopened) / merge_group | `Scan PR publication fields` carries the title/body edit scan; `ci.yml` has no `edited` trigger, so an edit re-checks only the PR text instead of restarting full CI. No push trigger, so no skipped duplicate of the check lands on a head. |
| `ci-gate-queue-recovery.yml` | Re-run cancelled CI Gate once when upstream jobs succeeded (runner-queue starvation) | Every 15 min / manual | Stopgap for #4811; scans recent CI runs via `gh api` (no `workflow_run` — zizmor); never re-runs genuine failures; default-branch logic only. |
| `cache-hygiene.yml` | Deletes dead Actions cache entries: CodeQL TRAP entries on main except the newest per language and version and those at an open PR's base commit, TRAP entries on other refs, superseded setup-uv entries on main after 24 h unread; deletes nothing unless the cache and open-PR listings are complete (#9101) | Every 2 h / manual / pull_request (this workflow and its sparse inputs) | Rules and dry run: `LU_PRODUCT_ROOT="$PWD" .venv/bin/python -m lu_machinery.ci.cache_hygiene --repo <owner/name>` (add `--apply` to delete). Everything else is left alone. A pull request only imports the script, in its own concurrency group; scheduled and manual prune stay on `cache-hygiene`. |
| `security-audit.yml` | Dependency advisories from `pip-audit` and `npm audit`, advisory issue updates, and stack currency report | Daily / weekly / manual / npm audit policy PRs | PRs that change the npm audit policy or this workflow validate the scheduled npm audit. |
| `actionlint.yml` | Runner-slot budget and workflow interpolation checks | PR / main push / manual | Main pushes and manual runs also run the local actionlint script. |
| `zizmor.yml` | Static security analysis of workflow YAML | Main push / weekly / manual | Offline scan reports to the Security tab. |
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

## Fleet security

`ci.yml` calls the shared machinery workflow at a full commit SHA. Its
`Fleet security gate` summary shows the scanner results and per-target
`fleet-security-receipt.v1` evidence. Every PR and merge candidate runs:

- Trivy filesystem scans of `package-lock.json`, `site/package-lock.json`,
  and `uv.lock` for high and critical vulnerabilities and licence findings.
- Separate Trivy scans of `pocketbase/Dockerfile` and the built PocketBase image.
- ShellCheck for tracked shell scripts, actionlint for workflows, and offline
  zizmor for workflows and composite actions.

The product's secret scan checks the selected commit range and public
identifiers. The publication workflow also checks edits to PR metadata.
The merge queue scans its generated commit metadata separately. CI also
keeps the Python advisory check that blocks unsuppressed findings at every
severity. Dependabot opens updates for Actions, npm, and uv.

## Gemini CI automation — retired (2026-06-04)

The previous `gemini-*.yml` workflows + `.github/commands/gemini-*.toml`
configs (gemini-cli PR/issue automation) were disabled in #2683 and removed
here. Gemini review/triage proved unreliable for merge confidence; agent
coordination now runs through the bridge (`scripts/ai_agent_bridge`) and
`scripts/dispatch.py`, not GitHub Actions. See
`docs/best-practices/agent-cooperation.md`.

Gemini Code Assist for GitHub PR reviews is disabled by `.gemini/config.yaml`.
Use local machine-agent review via `scripts/dispatch.py` instead.

## References

- **Agent cooperation:** `docs/best-practices/agent-cooperation.md`
- **Stanza CI autopsy:** `docs/bug-autopsies/stanza-model-md5-flake.md`

### Issue task quality

`issue-task-quality.yml` runs only on issue opened/edited events. DevOps owns
its single marker comment and non-overrideable structure/ancestry failures plus
new-orphan feedback. It refetches the current issue and observes native ancestry
once, at most eight parent reads. It never audits the full tree or retries body
evidence. Dispatch owns full orphan and body-evidence classification. It is not
a required code-PR check.
Parent-link-only changes do not trigger Actions; dispatch rechecks live ancestry.
A workflow in another repository can invoke the pinned public checkout's
`LU_PRODUCT_ROOT=<checkout> .venv/bin/python -m lu_machinery.ci.check_issue_task_quality --repo OWNER/REPO --issue NUMBER
--strict --json`; the caller must install that checkout's pinned dependencies.
