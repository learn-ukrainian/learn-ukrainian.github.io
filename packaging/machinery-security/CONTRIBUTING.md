<!--
DRAFT for the public learn-ukrainian/machinery repository. Install it there as
the root CONTRIBUTING.md.
-->
# Contributing

Report a security vulnerability privately, as [SECURITY.md](SECURITY.md)
describes, never in a public issue.

## Gates every change passes

1. **CI Gate.** It is the one required check. It passes only when every CI job
   succeeds.
2. **Independent review.** A reviewer from a different model family than the
   change's authors reviews the exact head commit, and the verdict is recorded
   on the PR. A new commit needs a new review.
3. **Merge queue.** Changes merge only through the merge queue. No auto-merge
   and no admin bypass.
4. **Workflow owner.** A change to `.github/workflows/` or `.github/CODEOWNERS`
   also needs approval from the code owner in [CODEOWNERS](.github/CODEOWNERS).

## What you must do

- Open a PR against `main`, using the PR template.
- End every agent commit message with an `X-Agent: <agent>/<task-id>` trailer.
- Never commit a secret, not even in a test value. Push protection checks
  every push, CI's secret scan reads every commit in the PR, and history was
  scanned on every ref before the first push. Removing a secret in a later
  commit does not remove it from history.
