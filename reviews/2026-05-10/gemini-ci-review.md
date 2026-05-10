Here is the diagnostic report of the GitHub Actions CI setup, focusing on noise reduction, slow paths, and redundancies.

## Drop
- **CodeQL settings (implied `codeql-analysis.yml`)**: Running 3 lanes wastes CI compute since `actions` and `javascript-typescript` offer low security value for a heavily Python-centric backend. *(Note: CodeQL configuration file was not explicitly found in `.github/workflows/*.yml`, assuming standard implementation based on prompt description).*
  - **Change**: Remove the `actions` and `javascript-typescript` languages from the CodeQL `strategy.matrix.language` array, keeping only `python`.
- **`.github/workflows/gemini-dispatch.yml:25`**: The standalone `debugger` job almost always evaluates to skipped (unless `vars.GEMINI_DEBUG` is explicitly true), adding a permanent, noisy "skipped" line item to every PR and issue comment event.
  - **Change**: Delete the isolated `debugger` job and merge its debug printing steps directly into the start of the `dispatch` job behind the same condition.

## Fix
- **`.github/workflows/gemini-dispatch.yml:38`**: The `dispatch` job evaluates on every single issue and PR comment, but skips entirely if the comment doesn't start with `@gemini-cli`. Because the downstream jobs (`review`, `triage`, `invoke`, `plan-execute`, `fallthrough`) use `needs: dispatch`, this causes a massive UI cascade where 6 jobs report as "skipped" on every normal comment.
  - **Change**: Since `on:` cannot filter comment bodies natively, move the comment body prefix check to an initial, lightweight router job that outputs a boolean. Conditionally invoke the heavyweight callable workflows only if true, collapsing the skipped noise into a single job.

## Parallelize
- **`.github/workflows/ci.yml:247`**: The `Test (pytest)` job relies solely on node-local thread concurrency (`-n auto`). At ~5 minutes, it is a bottleneck.
  - **Change**: Implement a matrix strategy (e.g., `strategy: matrix: suite: [tests/core, tests/wiki, tests/orchestration]`) to distribute the test payload across multiple concurrent GitHub-hosted runners.

## Cache
- **`.github/workflows/rules-deployment-check.yml:24`**: Python dependencies (`pytest`, `pyyaml`) are installed cleanly on every execution without leveraging pip caching.
  - **Change**: Add `cache: 'pip'` to the `actions/setup-python` step to utilize cross-run layer caching.
- **`.github/workflows/ci.yml:204`**: The manual `actions/cache` block uses a rigid composite hash of three files; if any single byte changes, the entire pip cache invalidates.
  - **Change**: Remove the manual `actions/cache` block and replace it with `cache: 'pip'` inside the `setup-python` action, which manages granular dependency invalidation automatically.

## Triggers
- **`.github/workflows/validate-yaml.yml:6-14`**, **`.github/workflows/rules-deployment-check.yml:6-20`**, **`.github/workflows/ci.yml:6-26`**: These workflows declare identical path filters for both `push` and `pull_request` events without branch restrictions.
  - **Rationale**: Pushing a new commit to an open PR branch fires both events simultaneously, causing the exact same CI suite to run twice per commit (once for branch context, once for PR context).
  - **Change**: Restrict the `push` trigger specifically to `branches: [main]` so that feature-branch commits only trigger the `pull_request` runs.

## Keep
- **`.github/workflows/ci.yml:190`**: The `if: '!cancelled()'` condition on the `Test (pytest)` job is an essential structural workaround.
  - **Rationale**: It ensures the required status check always reports back to GitHub (even if inner steps skip because linting failed), preventing the PR from being permanently deadlocked by a pending requirement.
  - **Change**: Do not modify this condition or its accompanying inner `needs.lint.result` step guards.

============================================================
📎 Attached Data:
{"from_model": "gemini-3.1-pro-preview"}
