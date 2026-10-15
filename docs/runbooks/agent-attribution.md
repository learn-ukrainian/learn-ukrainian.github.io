# Agent attribution on main (#10736)

Every commit that lands on `main` carries the `X-Agent` attribution of its
author(s). `scripts/ci/check_agent_attribution.py` fails a merge-group commit (and a
pull request) that does not. Parent program: #9737 (A1).

## Contract: a line, not a trailer

Attribution is a **line** in the landed message that matches

```text
^X-Agent: <agent>/<task-id>$
```

Do not promise `git interpret-trailers` or `%(trailers:key=X-Agent)` parsing. GitHub
ends every squash message with its own `---------` block of `Co-authored-by` lines, so
an `X-Agent` line is never in the final paragraph and Git's trailer parser returns
nothing for it. The check matches lines with a regular expression instead.

- `<agent>` is lowercase letters, digits and single hyphens, starting with a letter.
  The closed agent roster stays with the pre-push lint
  (`scripts/audit/lint_agent_trailer.py`); this check proves presence, shape and
  completeness.
- `<task-id>` is letters, digits, `.`, `_` and `-`.
- Exactly one space after the colon, no trailing whitespace. A line that starts with
  `X-Agent:` and does not match is **malformed**, even when another line is valid.

Source commits keep writing the trailer as today (`X-Agent: <agent>/<task-id>`).
The repository setting below is what carries those lines into the landed message.

## The repository setting

| Setting | Required value | Why |
| --- | --- | --- |
| `squash_merge_commit_title` | `PR_TITLE` | Subject ends in `(#N)`, which the merge-group check parses. |
| `squash_merge_commit_message` | `COMMIT_MESSAGES` | Copies every source commit's message, so each author's `X-Agent` line reaches `main` by construction. |

With `BLANK` the body is only GitHub's `Co-authored-by` block and every attribution is
lost; this is the state that began on 2026-10-08. The merge queue ignores any message
supplied at enqueue time (`scripts/publish/github.py`,
`scripts/orchestration/merge_queue_keeper.py`), so the setting is the only transport.
A PR-body footer was rejected: it is a second source of truth that goes stale after
review-fix pushes and puts review prose on `main`.

The setting lives outside the repository. The operator applies it and records the
readback; agent tokens do not change it.

## How the check works

### `--merge-group BASE HEAD` (primary gate)

`BASE` and `HEAD` are `merge_group.base_sha` and `merge_group.head_sha`.

1. `HEAD` must descend from `BASE`; an unreadable ref or a non-ancestor fails.
2. `git rev-list --first-parent BASE..HEAD` is the chain. Each commit must have exactly
   one parent: it is one PR's squash commit. An empty chain fails.
3. For **each** commit, independently (one PR's attribution never masks another's):
   - the terminal `(#N)` of the subject names the PR; earlier `(#issue)` references are
     ignored; none fails;
   - the landed message has at least one well-formed line and no malformed one;
   - `git fetch origin refs/pull/N/head` freezes the PR's source head; the non-merge
     commits in `<squash parent>..<source head>` are the PR's own commits;
   - every distinct `X-Agent` value found on those commits appears in the landed message;
   - a source commit with no line fails unless it is a verified app bot's (below).

A requeue or a new head produces a new chain and is checked afresh; a squash commit
built from an older head fails when the PR head has since gained another agent's value.

### `--pr BASE HEAD` (early feedback)

Every non-merge commit in `BASE..HEAD` carries a well-formed line or is a verified app
bot's. This catches the problem at review time, but it cannot see the setting; only the
merge-group check proves what actually lands.

### Bot exemption

A commit with no line is exempt only when GitHub's REST commit object for that exact
SHA (`GET repos/{repo}/commits/{sha}`) passes
`scripts.review.app_bot_authorship.verified_app_bot_login`: allowlisted account, `Bot`
type, matching Git author, created and signed by `web-flow`. A Git author name or a
`[bot]` suffix proves nothing, and an API failure is "not proven". In a merge group a
landed commit with no line is exempt only when every commit of its PR is verified; a PR
that mixes bot and agent commits keeps the agent attribution requirement.

### Violation codes

Output is `::error title=agent-attribution::<CODE> pr=#N commit=<12 hex> <detail>`.
A malformed value is never echoed.

| Code | Meaning |
| --- | --- |
| `GIT_ERROR` | A ref, ancestry or object read failed. |
| `EMPTY_CHAIN` | No commit between base and head. |
| `UNEXPECTED_SHAPE` | A queue commit is not a single-parent squash commit. |
| `MISSING_PR_REFERENCE` | Subject does not end in `(#N)`. |
| `FETCH_FAILED` | `refs/pull/N/head` could not be fetched or read. |
| `EMPTY_SOURCE` | The PR head adds no non-merge commit to the squash parent. |
| `MALFORMED_ATTRIBUTION` | An `X-Agent:` line does not match the grammar. |
| `MISSING_ATTRIBUTION` | No line and no verified app-bot authorship. |
| `SOURCE_UNATTRIBUTED` | A PR commit has no line and no verified app-bot authorship. |
| `INCOMPLETE_ATTRIBUTION` | The landed message omits a value present on the PR's commits. |

### Report-only switch

`ATTRIBUTION_ENFORCE=1` makes violations fail the run (exit 1). Any other value,
including unset, prints the same findings as `::warning` and exits 0, with the log line
`report-only (ATTRIBUTION_ENFORCE!=1)`. Bad usage always exits 2. Until the operator's
setting change is read back, the workflow keeps `ATTRIBUTION_ENFORCE: '0'`, because
the landing is gated on that readback.

## CI Gate step

Add to the existing `ci-gate` job in `.github/workflows/ci.yml`, after the
`Check large files guard` step. It reuses that job's checkout (`fetch-depth: 0`, queue
head ref) and Python setup, and runs on every `pull_request` and `merge_group`, outside
the reuse path. The job also needs the permission block shown.

```yaml
  ci-gate:
    permissions:
      contents: read
      pull-requests: read
    # ...
    steps:
      # ... checkout, setup-python (id: setup-python-gate), Check large files guard ...
      - name: Check agent attribution
        if: github.event_name == 'pull_request' || github.event_name == 'merge_group'
        env:
          # Report-only until the squash_merge_commit_message readback is recorded
          # (docs/runbooks/agent-attribution.md). Set to '1' to enforce.
          ATTRIBUTION_ENFORCE: '0'
          EVENT_NAME: ${{ github.event_name }}
          BASE_SHA: ${{ github.event_name == 'merge_group' && github.event.merge_group.base_sha || github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event_name == 'merge_group' && github.event.merge_group.head_sha || github.event.pull_request.head.sha }}
          GITHUB_TOKEN: ${{ github.token }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          PYTHON_BIN: ${{ steps.setup-python-gate.outputs.python-path }}
        run: |
          if [ -z "$BASE_SHA" ] || [ -z "$HEAD_SHA" ]; then
            echo "::error::Missing base or head SHA for agent attribution in $EVENT_NAME"
            [ "$ATTRIBUTION_ENFORCE" = 1 ] && exit 1
            exit 0
          fi
          if [ "$EVENT_NAME" = "merge_group" ]; then
            "$PYTHON_BIN" scripts/ci/check_agent_attribution.py --merge-group "$BASE_SHA" "$HEAD_SHA"
          else
            "$PYTHON_BIN" scripts/ci/check_agent_attribution.py --pr "$BASE_SHA" "$HEAD_SHA"
          fi
```

Notes:

- The script is standard-library only and needs no `pip install`.
- `persist-credentials: false` stays. The repository is public, so
  `refs/pull/N/head` fetches anonymously; when `GITHUB_TOKEN` is set the script also
  sends it to a `https://github.com/` remote through `GIT_CONFIG_*` environment
  variables (never argv, never written to config).
- Pin any new action the way the file does (full SHA with a version comment). This step
  uses none.
- Do not add the step to a job that can be skipped or reused. A skipped required check
  counts as passing.
- When the step lands, mention it in `docs/runbooks/ci-gate.md`.

## Controlled landing (S0)

Run only after exact-head cross-family approval of the check, with the step still
report-only.

1. **Precondition.** The operator confirms the 2026-10-08 change to `BLANK` was not
   deliberate. If it was, the operator decides and this procedure stops.
2. **Designated approval.** Opus 5.5 and Sol 6.1 agree on `PR_TITLE` /
   `COMMIT_MESSAGES` (the amended design is endorsed by both).
3. **Apply and read back.** The operator records the old values, sets
   `squash_merge_commit_title=PR_TITLE` and `squash_merge_commit_message=COMMIT_MESSAGES`,
   and records the readback.
4. **Land one harmless docs-only PR** with two commits carrying *different*
   `X-Agent` values, through review, CI Gate and the merge queue.
5. **Capture** the PR number, the merge-group run ID and its `base_sha`/`head_sha`.
6. **Prove** after `MERGED`: `git show -s --format=%B <mergeCommit.oid>` contains both
   values as whole lines, and the merge-group run's `Check agent attribution` log shows
   `violations=0`.
7. **Enforce.** A follow-up PR changes `ATTRIBUTION_ENFORCE` to `'1'`; it lands through
   the same gates.

Also inspect source messages and PR bodies for `Closes #N` text: with
`COMMIT_MESSAGES` it is carried onto `main`, where GitHub acts on it.

## Rollback

1. Set `ATTRIBUTION_ENFORCE` back to `'0'` (report-only) if the check blocks the queue.
2. If the setting misbehaves, the operator sets
   `squash_merge_commit_message=BLANK` again and records the readback. This is
   containment, not repair: attribution is lost again.
3. Keep the evidence and leave #10736 open. Never rewrite `main` and never bypass the
   gates.

## Residuals

- **Single-HEAD metadata scan (DevOps).** `queue-metadata-scan`
  (`.github/workflows/ci.yml`, `fetch-depth: 2`) scans only the queue HEAD commit's
  metadata. Earlier commits of a grouped chain are not metadata-scanned. Track as a
  separate issue; this check does not cover it.
- **Group-coverage proof not yet captured.** The two-commit controlled landing proves
  multi-author transport, not multi-PR group coverage. A real merge group with two or
  more PRs must be captured, including the `base_sha` GitHub delivers for it, before
  #10736 is called complete. The tests build the same shape (a first-parent chain of
  squash commits with `(#N)` subjects) in temporary repositories, not from a live
  queue.
- **Bot exemption on a live queue.** The exemption is exercised against REST payloads
  shaped like GitHub's, not a live Dependabot landing.
- **Declaration, not identity.** An `X-Agent` line records who claims authorship; it is
  not cryptographic proof.
