# Agent GitHub text publishing

The publishing gate prevents accidental disclosure by cooperative agents. It
is defense in depth, not universal enforcement. Absolute executable paths,
aliases, extensions and raw HTTP clients can bypass shell interception. A
controlled publisher with credentials unavailable to agents is a separate
operator decision.

All launchers and delegate worker environments put the existing GitHub CLI shim
first on PATH. The Claude Bash hook installs that same PATH in the tool command;
literal warnings are advisory. The shim snapshots arguments, destination, file
contents and consumed stdin, then calls `scripts.opsec.prepublish.check_texts`.
Retries retain the same scanned files and stdin. Project publishing functions
use `checked_run`, which applies the same checker and preserves the established
merge guard and retry helper without scanning twice.

Repository identity comes from explicit repository options, resource URLs, REST
paths, GitHub environment selectors or an unambiguous local remote. Opaque
GraphQL targets and unresolved REST node paths are treated as public. Only
positively identified allowlisted private destinations are exempt. GraphQL
queries remain reads even when sent with POST. Unsupported interactive and
unresolved generated text forms are refused with instructions to provide
explicit text or a body file.

The matcher and rules remain in the configured private sibling repository. The
supported adapter contract is `scan_text(text, rules)`, returning finding maps
with `rule_id` and numeric `class`. Unknown results or unavailable private
inputs refuse publication. The public policy contains identifiers only; matching
expressions remain private. The live contract test must run against that private
implementation before certifying compatibility.

For a false positive, set `LU_OPSEC_OVERRIDE='reason'` on one command. A successful
local log write is mandatory before sending. Only timestamp, destination,
identifiers and reason are logged in ignored local state; text is omitted. The
reason is removed before spawning GitHub and from worker environments. A parent
shell cannot reuse the same inherited reason for another write; provide a fresh
command-scoped reason when another override is warranted.

## Posting consumers

This inventory is the review denominator. The reviewer must compare it with
GitHub CLI and HTTP posting searches and inspect the exact branch head.

| Consumer | Text or operation | Disposition |
| --- | --- | --- |
| `agents_extensions/shared/hooks/guard-public-github-text.py` | Claude Bash commands | Installs shim; advisory literals |
| `scripts/agent_runtime/shims/gh` | Issue/PR create, edit, comment, review, close comment; merge subject/body | Snapshot and shared checker |
| Same shim | REST payloads, nested review comments, field files and stdin; GraphQL documents/variables | Snapshot and shared checker; queries pass |
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
| `scripts/orchestration/task_closeout.py` | Issue bodies, close and merge operations | Direct shared checker; unresolved merge text refuses |
| `scripts/orchestration/merge_queue_keeper.py` | Comments, merge operations and GraphQL mutations | Direct shared checker; unresolved merge text refuses |
| `scripts/orchestration/issue_stream_audit.py` | GraphQL membership mutation | Direct shared checker |
| `scripts/practice_deck/publish.py` | Release title and notes | Direct shared checker |
| `scripts/open_dataset/publish.py` | Release title and notes | Direct shared checker |
| `scripts/lexicon/publish_manifest.py`; release asset uploads in the two publishers above | Binary asset upload, download and inspection | No authored GitHub text; outside text gate |
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
