# Remote branch cleanup

The public repository runs `stale-branch-cleanup.yml` daily at 04:43 UTC and
through **Run workflow**. Both events run the same standard-library helper.
HTTP reads use `scripts.common.github_client` with fresh, uncached responses
and the helper's redirect refusal policy. The sparse checkout includes that
shared client, and the workflow invokes the helper as a Python module.
Select the default branch for manual runs. Branch and tag selections elsewhere
are refused. There is no local apply mode, host timer or local worktree purge.
The separate private-repository unit remains owned by codex-infra.

The job grants only `contents: write` and `pull-requests: read`. Checkout pins
the event SHA and does not persist credentials. The helper verifies the public
repository identity, canonical GitHub origin URL and current default-branch
HEAD before deleting anything. A queued run whose source is no longer the
current default head fails closed. The keep file is read through the API at the
verified default commit and its Git blob digest is checked. Keep entries are
exact names, one per line; empty lines and lines starting with `#` are ignored.
An inaccessible or malformed file stops deletion.

A branch qualifies only when its verified HEAD commit's **committer date** is
at least 48 hours old against the run's explicit UTC clock. The helper retains
`main`, the default branch, protected branches, keep entries and all open PR
heads belonging to this repository, including draft and reopened PRs. Fork
heads are repository-qualified, so an unrelated fork/name collision does not
exclude a local branch. Unknown PR repository identity fails closed.
Future or malformed timestamps never qualify. Listings follow complete
pagination and reject malformed or incomplete pagination evidence.

Immediately before each deletion the helper rereads open PR heads, the trusted
keep file, default/protection state and the candidate's head commit. Any
observed change retains the candidate; unknown evidence stops the run. Git
receives an argument array with an explicit expected-SHA condition:

```bash
git push --force-with-lease=refs/heads/<branch>:<sha> origin :refs/heads/<branch>
```

The implementation also requests porcelain receipts and disables follow-tags
and remote mirror behavior. Git atomically refuses a moved ref. It does not
transactionally bind GitHub metadata to that ref update. A PR, keep entry or
protection change arriving after the final eligibility check and before the
conditional delete is an accepted residual race, with the restore path below.
Do not describe this race as prevented. Include this statement neutrally in the
PR description.

The JSON log and Actions step summary name each actually deleted branch and its
exact SHA. A successful Git deletion receipt is required. A refusal, timeout,
API failure or later absence never counts as a deletion; failures make the job
fail. Summaries include the source SHA, UTC clock and actual Git version.

## Restore a branch

Use the exact name and SHA from the successful deletion summary. In a checkout
that still has the commit object, restore with the existing Git operation:

```bash
git push origin <sha>:refs/heads/<branch>
```

Confirm that the branch has not been recreated before restoring. Do not force
an update over another writer's branch. For an eligible closed PR, open the PR
and use **Restore branch** when GitHub offers it. Confirm the restored head.
A missing action or unavailable commit object means recovery is unverified;
escalate to codex-infra. Git SHA recoverability is temporary: unreachable objects
may be garbage-collected, and a SHA alone is not a permanent backup. This unit
adds no retention system or recovery guarantee.

## Validate and land

Author tests use deterministic API fixtures and owned disposable local Git
remotes, including real matching-SHA deletion and moved-SHA refusal. The local
Git version is recorded as the oracle. No destructive live test is authorized.
Independent critical review freezes an unseen case against the exact source SHA
before execution. Prompt critique, author tests and Git mechanism proof do not
replace that held-out case or exact-head cross-family approval.

The driver obtains separate workflow code-owner/delegated approval, same-head
branch and merge-group CI, confirms merge and performs common cleanup. After
merge, record a scheduled and a manual run's ID, event and source SHA, confirm
that the real helper executed, and inspect safe actual behavior. A skipped job
or zero deletions alone proves neither trigger nor helper behavior. Pair this
proof with the local positive deletion/refusal oracle before closing #10945.

References: [Git push lease semantics](https://git-scm.com/docs/git-push),
[branch API](https://docs.github.com/en/rest/branches/branches),
[open PR API](https://docs.github.com/en/rest/pulls/pulls),
[workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[Restore branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/deleting-and-restoring-branches-in-a-pull-request).
