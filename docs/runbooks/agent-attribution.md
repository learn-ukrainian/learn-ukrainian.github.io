# Agent attribution on main (#10736)

Every commit that lands on `main` carries the `X-Agent` attribution of its
author(s). `scripts/ci/check_agent_attribution.py` fails a merge-group commit (and a
pull request) that does not. Parent program: #9737 (A1).

## Contract: a declaration paragraph, not a trailer block

Attribution is an exact line

```text
X-Agent: <agent>/<task-id>
```

inside a **declaration paragraph** of the message. Do not promise
`git interpret-trailers` or `%(trailers:key=X-Agent)` parsing: GitHub ends every squash
message with its own `---------` block of `Co-authored-by` lines and copies each source
body verbatim, so an `X-Agent` line is rarely in the final paragraph and Git's trailer
parser (a backward walk from the end) returns nothing for it. The check does not use
that walk.

- `<agent>` is lowercase letters, digits and single hyphens, starting with a letter.
  The closed agent roster stays with the pre-push lint
  (`scripts/audit/lint_agent_trailer.py`); this check proves presence, shape and
  completeness.
- `<task-id>` is letters, digits, `.`, `_` and `-`.
- Exactly one space after the colon, no trailing whitespace, ASCII only.

The check applies this grammar (the module docstring of
`scripts/ci/check_agent_attribution.py` is the normative copy):

1. **Whole-message refusal**, before any exemption (bot commits included), with the
   reason in `REFUSED_MESSAGE`:
   - `MESSAGE_TOO_LARGE`: more than 64 KiB of UTF-8. The parser is quadratic on some
     inputs; the largest landed message seen is under 48 KiB.
   - `FORBIDDEN_CHARACTER`: NUL, VT, FF, U+001C–U+001E, NEL, U+2028 or U+2029. Other
     tools treat these as line breaks (or rewrite them) while the parser does not, so
     they could shift a line into or out of a code block.
   - `BARE_CR`: a CR that is not part of CRLF. CRLF is normalised to LF; the message is
     read from the commit object as bytes, so nothing else rewrites it first.
   - `COMMENT_MARKER`: the literal `<!--` or `-->` anywhere, even a harmless comment
     or prose such as `"-->" in a name`. Write *HTML comment marker* in prose instead.
   - `HTML_BLOCK`: any raw HTML block (`<div>`, `<pre>`, `<details>`, a tag alone on a
     line, …).
2. **Parse** the LF-normalised message with markdown-it-py's CommonMark preset (pinned
   `markdown-it-py==4.2.0`, `mdurl==0.1.2`). A **declaration paragraph** is a top-level
   paragraph (not inside a list, quote, heading, code block or link reference) whose every
   source line is `Key: value` (`[A-Za-z][A-Za-z0-9-]*`, colon, one space, no leading or
   trailing whitespace). Lines come from the parser's line map over `text.split("\n")`,
   never from rendered text, and must equal the parser's own paragraph text.
3. Each exact `X-Agent` line of a declaration paragraph is one value, unless an inline
   construct (code span, link, emphasis, image or multi-line inline HTML) spans into that
   line. Declaration paragraphs may appear anywhere in the message; a value repeated on
   several lines counts once. Other keys share the paragraph freely:
   `Co-Authored-By: … <…>`, `X-Agent-Model: …`, `Refs: #N`. Inline HTML elsewhere (for
   example a `<pid>` placeholder in prose) is allowed.
4. **Malformed**: any line, anywhere in the message (code blocks included), whose key
   (the text before its first `:`) lowercases to `x-agent` and that is not an exact line.
   `X-Agent-Model` is a different key.

So a fenced, indented, quoted, listed, heading or link-reference line is an example,
never a declaration: it satisfies nothing and is not required of the landed message.
A paragraph that mixes prose and attribution does not declare:

```text
Refs #10549              <- not "Key: value": the X-Agent line below does not count
X-Agent: codex/task-1
```

Write `Refs: #10549`, or put a blank line between the two.

Source commits keep writing the trailer as today (`X-Agent: <agent>/<task-id>` in its own
paragraph or beside other `Key: value` trailers). The repository setting below is what
carries those lines into the landed message.

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
   - `git fetch origin refs/pull/N/head` freezes the PR's source head. It must be
     **verifiably the squash's own source**: `git merge-tree --write-tree <squash
     parent> <source head>` (a three-way merge from their merge base, as a squash does)
     must succeed without conflict and yield exactly the squash commit's tree. Unrelated
     histories, a conflict or any tree difference is `UNVERIFIABLE_SOURCE`; the PR
     number alone never certifies a history. The check writes the merged tree objects
     into the CI checkout's object database only;
   - the non-merge commits in `<squash parent>..<source head>` are the PR's own commits;
   - every distinct `X-Agent` value found on those commits appears in the landed message;
   - a source commit with no line fails unless it is a verified app bot's (below).

A requeue or a new head produces a new chain and is checked afresh; a squash commit
built from an older head fails (`UNVERIFIABLE_SOURCE`, its tree no longer matches the
moved head) once the PR head has gained another commit. The check is exact: if GitHub's
squash merge ever differs from `git merge-tree` for a legitimate PR (for example a
different rename heuristic), the finding is a false failure that stays a warning while
`ATTRIBUTION_ENFORCE` is not `1`; investigate before enforcing.

### `--pr BASE HEAD` (early feedback)

`BASE` and `HEAD` must share history (`git merge-base BASE HEAD` succeeds); otherwise
`BASE..HEAD` is not the pull request's own range and the run fails with
`UNVERIFIABLE_SOURCE`. A PR that diverged from a newer base still passes: the range is
the PR's own commits. Every non-merge commit in `BASE..HEAD` (an empty range fails;
merge commits are skipped, they carry no authored change) carries a well-formed line or
is a verified app bot's. This catches the problem at review time, but it cannot see the
setting; only the merge-group check proves what actually lands.

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
Details carry counts, PR numbers and short SHAs only. No message content is echoed: not
a malformed line, and not a task id (`omits 1 of 2 PR value(s)` names no value).

| Code | Meaning |
| --- | --- |
| `GIT_ERROR` | A ref, ancestry or object read failed. |
| `EMPTY_CHAIN` | No commit between base and head. |
| `UNEXPECTED_SHAPE` | A queue commit is not a single-parent squash commit. |
| `MISSING_PR_REFERENCE` | Subject does not end in `(#N)`. |
| `FETCH_FAILED` | `refs/pull/N/head` could not be fetched or read. |
| `EMPTY_SOURCE` | The PR head adds no non-merge commit to the squash parent. |
| `UNVERIFIABLE_SOURCE` | The fetched PR head is not verifiably the squash's source (merge-group), or `--pr` BASE and HEAD share no history. |
| `REFUSED_MESSAGE` | The whole message is refused; the detail names the reason (`MESSAGE_TOO_LARGE`, `FORBIDDEN_CHARACTER`, `BARE_CR`, `COMMENT_MARKER`, `HTML_BLOCK`). |
| `MALFORMED_ATTRIBUTION` | A line keyed `x-agent` (any case) is not an exact line. |
| `MISSING_ATTRIBUTION` | No line and no verified app-bot authorship. |
| `SOURCE_UNATTRIBUTED` | A PR commit has no line and no verified app-bot authorship. |
| `INCOMPLETE_ATTRIBUTION` | The landed message omits a value present on the PR's commits. |

### Report-only switch

`ATTRIBUTION_ENFORCE=1` makes violations fail the run (exit 1). Any other value,
including unset, prints the same findings as `::warning` and exits 0, with the log line
`report-only (ATTRIBUTION_ENFORCE!=1)`. Bad usage always exits 2.

The switch downgrades **violations only**, including the typed fail-closed ones
(`GIT_ERROR`, `FETCH_FAILED`, …). A crash of the checker itself (the parser missing, an
unexpected exception) exits 1 with a traceback in every mode, so the step fails even
while report-only. The step runs under `set -euo pipefail` and calls the checker last,
with no `|| true` and no `continue-on-error`.

In CI the value comes from the **repository variable** `ATTRIBUTION_ENFORCE`
(Settings → Secrets and variables → Actions → Variables), passed to the step as
`ATTRIBUTION_ENFORCE: ${{ vars.ATTRIBUTION_ENFORCE }}`. Unset means report-only. Do not
set it to `1` until the replay below has zero unexplained rejections and the operator's
setting readback is recorded.

## CI Gate step

`Check agent attribution` is a step of the `ci-gate` job in `.github/workflows/ci.yml`
(the job behind the one required context, `CI Gate`). It runs after
`Check large files guard` and `Require every job`, on every `pull_request` and
`merge_group` event, including merge-group runs that reuse an earlier run's tree: the
queue commit's message is new even when its tree is not. It reuses that job's checkout
(`fetch-depth: 0`; the queue head on `merge_group`, the PR merge ref on `pull_request`)
and Python setup.

| Event | Mode | `BASE_SHA` | `HEAD_SHA` |
| --- | --- | --- | --- |
| `merge_group` | `--merge-group` | `merge_group.base_sha` | `merge_group.head_sha` |
| `pull_request` | `--pr` | `pull_request.base.sha` | `pull_request.head.sha` |

A missing SHA fails the step in every mode. The job has no project environment, so the
step installs exactly the locked parser first:
`pip install --no-deps --only-binary=:all: markdown-it-py==4.2.0 mdurl==0.1.2` (keep in
step with `requirements-lock.txt`; a test pins the pair). The rest of the checker's import
closure is the standard library and `scripts/` itself.

- Permissions stay `contents: read`. History comes from the checkout (`fetch-depth: 0`),
  never from API calls. The repository is public, so `refs/pull/N/head` fetches
  anonymously; with `GITHUB_TOKEN` set the script also sends it to a
  `https://github.com/` remote through `GIT_CONFIG_*` environment variables (never argv,
  never written to config). The bot-exemption read goes through
  `scripts/common/github_client.py` (`gh api`, credential from `GITHUB_TOKEN`).
- On `pull_request` the PR head is reachable as the merge ref's second parent. If GitHub's
  merge ref lags a just-pushed head, the run reports `GIT_ERROR`; the next synchronize
  run checks the new head.
- Do not move the step to a job that can be skipped or reused. A skipped required check
  counts as passing.

## Replay before enforcing

Run the checker over real history and explain every rejection before setting
`ATTRIBUTION_ENFORCE=1`. Classes: **LANDED** (`git rev-list --first-parent origin/main`
since the window start), **SOURCE** (the non-merge commits of `refs/pull/N/head` for each
landed PR, which the merge-group completeness check reads), **QUEUE** (the current
merge-group head, if any). Unmerged branches, tags, `gh-readonly-queue/*` and
`ci-queue-metadata` refs are reported separately and never count against the bar.

Replay of 2026-10-16 (window from 2026-10-10, attributed commits only):

| Class | Commits | Attributed | Accepted | Rejected |
| --- | --- | --- | --- | --- |
| LANDED | 173 | 22 | 22 | 0 |
| SOURCE | 559 | 552 | 548 | 4 |
| QUEUE | 0 | 0 | 0 | 0 |
| Other refs (not counted) | 403 | 319 | 317 | 2 |

Every rejection is explained: two `X-Agent: sre-platform` values without a task id
(malformed before this grammar too), one `Refs #10549` line in the attribution paragraph
(prose and attribution mixed), and one literal `-->` in prose (comment-marker veto). The
two uncounted rejections are one of each of the first two classes. A merge-group replay
of the 173 landed squashes reports the same violations as the previous checker except
PR #10726, which now fails on its source's `-->` rather than on its landed message.

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
7. **Enforce.** After a fresh replay with zero unexplained rejections, the operator sets
   the repository variable `ATTRIBUTION_ENFORCE` to `1` and records the readback. No
   workflow change is needed.

Also inspect source messages and PR bodies for `Closes #N` text: with
`COMMIT_MESSAGES` it is carried onto `main`, where GitHub acts on it.

## Rollback

1. Delete the repository variable `ATTRIBUTION_ENFORCE` (or set it to anything but `1`)
   to return to report-only if the check blocks the queue. A checker crash still fails
   the step; fix or revert the checker instead.
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
  queue. The same capture must show the squash-tree check (`git merge-tree`) agreeing
  with GitHub's squash on a live queue commit; it is proven here only against Git's own
  squash merges.
- **Bot exemption on a live queue.** The exemption is exercised against REST payloads
  shaped like GitHub's, not a live Dependabot landing.
- **Declaration, not identity.** An `X-Agent` line records who claims authorship; it is
  not cryptographic proof.
- **Pre-push lint alignment (DevOps).** `scripts/audit/lint_agent_trailer.py` still
  accepts an `X-Agent` line anywhere in the message, so a commit can pass pre-push and
  then be refused here (for example `Refs #N` directly above the line). Aligning it with
  this grammar is a recorded follow-up.
- **Inline HTML around a declaration line.** Non-comment inline HTML on the other lines
  of a declaration paragraph (`Refs: <span hidden>` … `Note: </span>`) is not refused.
  Commit messages are shown as plain text on GitHub, and the check defines syntax, not
  browser visibility.
- **Live CI evidence.** Both event paths and the reused-tree path must be shown on real
  runs (run and job IDs) before #10736 closes; `docs/runbooks/ci-gate.md` should then
  list this step.
