reviews:

Uncertainty: `gh pr checks 1849` failed locally with `error connecting to api.github.com`, so I used the local workflow YAML plus your sample check names. I found 10 workflow YAML files, not 11; no repo-local CodeQL workflow is present, so CodeQL appears to be GitHub default setup or repo settings, not YAML-managed here.

## Drop

- `.github/workflows/gemini-dispatch.yml:26` — `debugger` is a dedicated job that is skipped unless debug vars are set, so it creates a persistent skipped check with no PR signal; replace it with a conditional debug step inside `dispatch` or delete it.
- `.github/workflows/gemini-dispatch.yml:142`, `.github/workflows/gemini-dispatch.yml:156`, `.github/workflows/gemini-dispatch.yml:170`, `.github/workflows/gemini-dispatch.yml:184` — `triage`, `invoke`, `plan-execute`, and `fallthrough` are expected to skip on normal PR-open review runs; remove them from required checks and consider moving command handling out of the PR-open workflow later.
- `.github/workflows/gemini-dispatch.yml:4` and `.github/workflows/gemini-dispatch.yml:7` — normal PR review comments/reviews fire the dispatcher but usually fail the `@gemini-cli` predicate, producing all-skipped runs; drop `pull_request_review_comment` and `pull_request_review` triggers unless review-thread commands are actively used.
- CodeQL `Analyze (actions)` — no local CodeQL YAML exists, and the Actions surface is tiny compared with Python/TS; disable the `actions` language in GitHub CodeQL default setup if it is only advisory.

## Fix

- `.github/workflows/ci.yml:308` — pytest spends time recreating a venv and installing heavy ML wheels before every run; first proposed change is to remove the unconditional torch/torchvision reinstall or gate it behind tests that actually import torch.
- `.github/workflows/ci.yml:315` — `--force-reinstall` guarantees churn even with pip download cache; drop `--force-reinstall` unless a prior CI bug proves it is needed.
- `.github/workflows/validate-yaml.yml:20`, `.github/workflows/validate-yaml.yml:112`, `.github/workflows/validate-yaml.yml:217` — all three jobs run whenever the workflow path filter matches, even if only one YAML class changed; add a lightweight `changes` job or per-job `if` guards so unrelated YAML categories do not emit no-op checks.
- `.github/workflows/ci.yml:242` — `Lesson Schema Drift` installs both Python and Node and runs in the broad CI workflow, which is why it duplicates visibly with push+PR; keep the check but stop duplicate triggers first before optimizing the job.

## Parallelize

- `.github/workflows/ci.yml:322` — pytest already uses `-n auto`, so intra-job parallelism is already enabled; avoid splitting by directory unless timing data shows collection or a subset dominates.
- `.github/workflows/ci.yml:395` and `.github/workflows/ci.yml:275` — frontend and pytest already run as separate jobs after `changes`; keep that parallelism.
- `.github/workflows/ci.yml:82` — `Quality Gates (radon)` unnecessarily waits on `lint`; change `needs: [changes, lint]` to `needs: changes` if you want a small wall-clock win with no coverage loss.
- `.github/workflows/ci.yml:242` — `Lesson Schema Drift` only needs `changes`, so it is already parallel with pytest; no split recommended until duplicate-trigger noise is removed.

## Cache

- `.github/workflows/ci.yml:300` — pip cache exists, but only downloads are cached while the venv is rebuilt; keep the cache, but make the install cheaper by removing unconditional heavyweight reinstalls.
- `.github/workflows/ci.yml:304` — cache key includes `requirements.txt`, which this repo says does not exist; remove that filename from `hashFiles(...)` to reduce confusion, keeping `requirements-lock.txt` and `pyproject.toml`.
- `.github/workflows/ci.yml:406` and `.github/workflows/deploy-pages.yml:33` — Node caches are configured for frontend/deploy; keep them.
- `.github/workflows/ci.yml:257` — schema drift runs `npm ci` from repo root with `cache-dependency-path: package-lock.json`; verify whether the root lockfile is intentional, because frontend uses `starlight/package-lock.json`.

## Triggers

- `.github/workflows/ci.yml:7` and `.github/workflows/ci.yml:34` — duplicate `Lint (ruff)`, `Lesson Schema Drift`, and `Test (pytest)` checks are expected when an internal PR branch push triggers both `push` and `pull_request`; restrict `push` to `branches: [main]`.
- `.github/workflows/validate-yaml.yml:7` and `.github/workflows/validate-yaml.yml:12` — same push+PR duplication pattern for YAML checks; restrict `push` to `branches: [main]`.
- `.github/workflows/rules-deployment-check.yml:7` and `.github/workflows/rules-deployment-check.yml:17` — same duplication pattern for deploy drift checks; restrict `push` to `branches: [main]`.
- `.github/workflows/gemini-dispatch.yml:10` — PR-open auto-review is not CI coverage; if skipped-check noise matters more than automatic Gemini review, remove this trigger and invoke review explicitly via comments.

## Keep

- `.github/workflows/ci.yml:275` — keep `Test (pytest)` as the required PR check; comments at `.github/workflows/ci.yml:282` explain why the job must still report even when inner pytest steps skip.
- `.github/workflows/ci.yml:64`, `.github/workflows/ci.yml:166`, `.github/workflows/ci.yml:181`, `.github/workflows/ci.yml:420` — keep ruff, prompt lint, root-script guard, and secret scan as real CI signal.
- `.github/workflows/rules-deployment-check.yml:30` — keep deploy idempotency because current session setup reports deploy drift, so this check is catching a real failure mode.
- `.github/workflows/deploy-pages.yml:9` — keep deploy manual-only; it is not contributing PR check noise.
- CodeQL `Analyze (python)` and `Analyze (javascript-typescript)` — keep both unless repo settings show one language has zero indexed files; they cover the actual Python and Starlight/TS surfaces.
