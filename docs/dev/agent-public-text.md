# Agent GitHub text publishing

The publishing gate prevents accidental disclosure by cooperative agents. It
is defense in depth, not universal enforcement. Absolute executable paths,
aliases, extensions and raw HTTP clients can bypass shell interception. A
controlled publisher with credentials unavailable to agents is a separate
operator decision.

All launchers and delegate worker environments put the existing GitHub CLI shim
first on PATH. The Claude Bash hook installs that same PATH in commands invoking
`gh`, including newline-separated commands, conditional commands, `time`,
`timeout`, `xargs`, and shell `-c` wrappers. It leaves commands untouched when
that shim is already first on PATH; literal warnings are advisory. A nested shell
that resets PATH, absolute executables and manually started sessions without the
launcher PATH or Claude hook remain outside shell interception. The shim
snapshots arguments, destination, file
contents and consumed stdin, then calls `scripts.opsec.prepublish.check_texts`.
Retries retain the same scanned files and stdin. Project publishing functions
use `checked_run`, which applies the same checker and preserves the established
merge guard and retry helper without scanning twice.

Repository identity comes from explicit repository options, resource URLs, REST
paths, GitHub environment selectors or an unambiguous local remote. Opaque
GraphQL targets and unresolved REST node paths are treated as public. Only
positively identified allowlisted private destinations are exempt. Every explicit
repository selector, environment selector and destination URL must agree on the
same private repository. Conflicts or ambiguous URL arguments are treated as
public, even if the final repository option would select a private repository.
GraphQL
queries remain reads even when sent with POST. Unsupported interactive and
unresolved generated text forms are refused with instructions to provide
explicit text or a body file.

The matcher and rules remain in the configured private sibling repository. The
supported adapter contract is `Matcher(rules).scan(text)`, returning hit objects
with `rule_id`, `class_id` and a half-open `span`. Public policy IDs are validated
against the loaded class-6 identities before any field is scanned. Unknown results or unavailable private
inputs refuse publication. The public policy contains identifiers only; matching
expressions remain private. The live contract test must run against that private
implementation before certifying compatibility.

For a false positive, set `LU_OPSEC_OVERRIDE='reason'` on one command. A successful
local log write is mandatory before sending. Only timestamp, destination,
identifiers and reason are logged in ignored local state; text is omitted. The
reason is removed before spawning GitHub and from worker environments. A parent
shell cannot reuse the same inherited reason for another write; provide a fresh
command-scoped reason when another override is warranted. Consumption claims currently
remain in ignored local state; safe reclamation is follow-up maintenance.

## Classification and scan set

The command group and verb are the first two non-flag tokens after skipping
global repository and hostname option values. `READ_VERBS` in
`scripts/opsec/gh_snapshot.py` is the explicit read allowlist; all other commands,
including unknown verbs, are writes. An API call is read-only when it has a read
method and no field/input payload; parsed GraphQL queries remain reads even with
POST. API payloads are inspected even with an explicit GET method.

For a write, scan every original argument token, consumed stdin, generated text,
and the contents of every existing regular file named by an argument. File
references include bare paths, `@file`, assignments, nested field assignments,
and attached short options. Files are copied once; consumed file inputs replay
from those copies, while inline text remains literal. Non-UTF-8 files are refused. Option interpretation is limited to
materializing payloads and resolving generated text; it never decides which
arguments to scan. Diagnostics contain a field or argument index and line,
without source text or file paths.

A write has no text only when, after removing the command group and verb,
every token is a standalone flag, a pure decimal number, a 7–40 digit hex SHA,
or a bare `OWNER/REPO`, and there is no file/stdin/generated payload. Repository
selectors with an attached bare `OWNER/REPO` also satisfy this condition. Other
attached values and assignments are text. Labels, milestone names, topics and
unknown option values are scanned. Empty scan sets pass without loading the
private matcher, so plain merges and numeric edits work without private tooling.

## Posting consumers

This inventory is the review denominator. The reviewer must compare it with
GitHub CLI and HTTP posting searches and inspect the exact branch head.

| Consumer | Text or operation | Disposition |
| --- | --- | --- |
| `agents_extensions/shared/hooks/guard-public-github-text.py` | Claude Bash commands | Installs shim; advisory literals |
| `scripts/agent_runtime/shims/gh` | Every non-read command, including unknown groups/verbs; all argument text and regular files | Snapshot and shared checker; empty scan sets pass |
| Same shim | REST payloads, nested review comments, field files and stdin; GraphQL documents/variables | Snapshot and shared checker; queries pass |
| Same shim | Repository create/edit descriptions and topics; project create/edit/item text; gist create/edit descriptions and files | Snapshot and shared checker; unknown destinations treated as public |
| Same shim | Label and milestone names, workflow inputs, clustered API payload options | All argument text scanned; no safe-label exemption |
| Same shim | Commit-generated PR bodies and release titles/notes | Materialize, scan, forward snapshot; unresolved forms refuse |
| `scripts/lib/launcher_core.sh` | All launcher shell publishing | Shim first, real executable pinned |
| `scripts/delegate.py` | Worker environments; auto-finalize PR title/body | Shim first; direct shared checker |
| `scripts/agent_runtime/runner.py` | Agent child processes | Shim retained even with merge permission |
| `scripts/ai_agent_bridge/_github.py` | Review issue comments | Direct shared checker |
| `scripts/audit/check_decisions.py` | Stale-decision issues and label descriptions | Direct shared checker |
| `scripts/audit/check_review_issues.py` | Review-result comments and issue close | Direct shared checker |
| `scripts/verify_review.py` | Review verification summaries | Direct shared checker |
| `scripts/review/record_cf_verdict.py` | Exact-head verdict comments | Direct shared checker |
| `scripts/fleet_comms/review_publisher.py` | PR comments and status descriptions | Direct shared checker |
| `scripts/orchestration/dispatch_settle.py` | Opt-in PR creation | Direct shared checker |
| `scripts/orchestration/task_closeout.py` | Issue bodies, close and merge operations | Direct shared checker; merge text scanned when supplied |
| `scripts/orchestration/merge_queue_keeper.py` | Comments, merge operations and GraphQL mutations | Direct shared checker; merge text scanned when supplied |
| `scripts/orchestration/issue_stream_audit.py` | GraphQL membership mutation | Direct shared checker |
| `scripts/practice_deck/publish.py` | Release title and notes | Direct shared checker |
| `scripts/open_dataset/publish.py` | Release title and notes | Direct shared checker |
| `scripts/lexicon/publish_manifest.py`; release asset uploads in the two publishers above | Release assets, downloads and inspection | Reads pass; write arguments and existing files are scanned, non-UTF-8 files refuse |
| `scripts/ci/data_tier.py` | CI maintenance issue bodies/comments | CI workflow out of scope |
| `scripts/ci/flake_ledger.py` | Nightly issue comments | CI workflow out of scope |
| `scripts/ci/comment_issue_task_quality.py` | Bot HTTP issue comments | Bot/CI workflow out of scope |
| `scripts/wt.sh`; dispatch prompt templates | Printed command examples | No outbound write; execution goes through shim |
| Other GitHub CLI consumers | View, list, auth, fetch and API reads | No posting; reads pass without private matcher |

CLI payload semantics follow the [GitHub CLI API manual](https://cli.github.com/manual/gh_api)
and [PR creation manual](https://cli.github.com/manual/gh_pr_create).

Commit-generated PR text follows the CLI's
[title/body implementation](https://github.com/cli/cli/blob/trunk/pkg/cmd/pr/create/create.go):
oldest-commit selection for first-fill, chronological summaries, and verbose
body indentation. The scanned result is sent as explicit title/body arguments.
