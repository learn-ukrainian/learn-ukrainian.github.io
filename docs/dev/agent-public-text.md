# Agent GitHub publishing

Use `python -m scripts.publish <verb>` for public GitHub writes. Project code
uses `scripts.publish.github.publish()` or a `Request` with `request_run()`.
Both interfaces validate the same closed field schemas. PR creation requires
explicit base and head names so implicit branch names cannot escape scanning. Arbitrary flags,
endpoints, GraphQL documents and payload passthrough are unavailable.

```sh
python -m scripts.publish issue-comment --repo unit/public --number 1 --body-file reply.md
python -m scripts.publish pr-review --repo unit/public --number 1 --verdict approve
python -m scripts.publish release-upload --repo unit/public --tag unit --assets unit.json.gz
```

Run Python with the task's prescribed project interpreter. Every subcommand's
`--help` lists its fields. `--body-file -` reads stdin. Absolute body-file and
artifact source paths work: only their contents and public artifact names are
scanned. Transport paths are never published or scanned as public text.

## Typed verbs

| Verbs | Public fields scanned |
| --- | --- |
| `issue-create`, `issue-edit` | Title, body, labels, milestone name |
| `issue-comment`, `issue-comment-json` | Body (JSON variant returns the API response) |
| `issue-close` | Optional comment; reason is a closed enum |
| `pr-create`, `pr-edit`, `pr-comment` | Title, body, labels, milestone, head/base names when present |
| `pr-review` | Optional body; verdict is approve, comment or request-changes |
| `pr-merge` | Optional subject and body; squash is fixed |
| `pr-disarm`, `pr-dequeue`, `issue-link` | No text; identifiers have closed validation |
| `release-create`, `release-edit` | Tag, title, notes, target, artifact names and UTF-8 content |
| `release-upload` | Tag, artifact names and UTF-8 content |
| `gist-create` | Description, filenames, UTF-8 file content; never repository-exempt |
| `label-create`, `label-edit` | Name, new name, description |
| `milestone-create`, `milestone-edit` | Title and description |
| `commit-status` | Context and description; state is a closed enum |

Body and notes inputs are read once, decoded as UTF-8 without newline
normalization, scanned, then sent from a temporary file written by the publisher.
Artifacts require an explicit `Asset(source, public_name)`; their bytes are read
once into a separate snapshot. UTF-8-decodable artifacts are scanned as text,
including ones named as binary files. Undecodable release assets pass as binary;
gists require UTF-8. Retries use the same frozen files. Temporary snapshots are
removed on exit. The existing merge/approval guard and rate-limit retry helper
remain on the production transport.

Missing rules, incompatible matcher results and checker errors refuse text
writes before transport. Text shape never grants an exemption. Operations
without text fields do not load private tooling. The private matcher contract
is `Matcher(rules).scan(text)` with `rule_id`, `class_id`, and half-open `span`.
Diagnostics contain only rule/class identifiers, field and line.

`LU_OPSEC_OVERRIDE=reason` permits a false-positive match only after a durable
local log write. It cannot bypass missing or incompatible tooling. The log
contains timestamp, repository identity, rule identifiers and reason, never
payload text. The child receives no override; a parent-scoped reason can be
consumed once. Claim-file reclamation remains maintenance work.

## Raw gh reads and private writes

The launcher shim remains first on PATH. The Claude hook only installs that
routing; it does not classify payloads or scan shell literals.

Raw reads require the entire argv to match `READ_GRAMMARS` in
`scripts/opsec/gh_snapshot.py`: exact group/verb, known flags with fixed arity,
and bounded positional operands. Unknown flags, aliases, extensions, commands,
extra operands and public generic `gh api` (including GraphQL) are refused.
Exact `gh version` and `gh --version` are also allowed; neither accepts extra operands.

| Group | Allowed read verbs |
| --- | --- |
| `pr` | view, list, status, checks, diff |
| `issue` | view, list, status |
| `run` | view, list, watch, download |
| `workflow` | view, list |
| `repo` | view, list |
| `release` | view, list, download |
| `auth` | status |
| `gist` | view, list |
| `label` | list |

Specific API reads use named `read()` operations: identity, issue, comments,
labels, timeline, reviews, commits, comment, checks, jobs, issues, runs,
deployments and deployment-statuses. GraphQL helpers build their own read-only
documents for issue-parent, membership, subissues, subissues-next,
subissue-batch, membership-head and queue-snapshot. Caller values are variables or JSON-escaped
selectors, never documents or endpoints.

A raw write is admitted only under a known write grammar to an allowlisted
private repository. The private REST exception requires a complete repository
endpoint under a known resource, rejects encoded or traversing paths, and uses
the last explicit hostname. GraphQL remains unavailable through the raw shim. The last explicit repository selector wins over `GH_REPO`
and the local origin; a resource URL selects its actual repository. Other
hosts and unresolved destinations receive no private exemption. Gists have no
repository exemption. Public refusal messages name the typed publisher verb.

## Posting inventory

This is the implementation review denominator. Compare it against CLI and HTTP
posting searches at the exact head.

| Consumer | Typed publication |
| --- | --- |
| `scripts/ai_agent_bridge/_github.py` | Issue comments |
| `scripts/delegate.py`, `scripts/orchestration/dispatch_settle.py` | Explicit PR creation |
| `scripts/audit/check_decisions.py` | Label and issue creation |
| `scripts/audit/check_review_issues.py`, `scripts/verify_review.py` | Issue comments and close |
| `scripts/review/record_cf_verdict.py` | Verdict comments with JSON response |
| `scripts/fleet_comms/review_publisher.py` | PR comments and exact-head commit status |
| `scripts/orchestration/task_closeout.py` | Issue body edits, close, squash merge |
| `scripts/orchestration/merge_queue_keeper.py` | Comments, issue creation, merge/disarm/dequeue |
| `scripts/orchestration/issue_stream_audit.py` | Fixed native membership mutation |
| `scripts/practice_deck/publish.py`, `scripts/open_dataset/publish.py` | Release creation and artifact upload |
| `scripts/lexicon/publish_manifest.py`, `scripts/lexicon/admit_fmu_boosters.py` | Artifact upload |
| `agents_extensions/shared/hooks/guard-public-github-text.py` | Routing only |
| `scripts/agent_runtime/shims/gh` | Closed raw admission; public writes refused |
| `scripts/ci/data_tier.py`, `scripts/ci/flake_ledger.py`, `scripts/ci/comment_issue_task_quality.py` | Separate bot/CI workflows, outside the cooperative-agent inventory |
| Printed templates and `scripts/wt.sh` | No outbound publication; executed public writes require publisher verbs |

This boundary protects cooperative agents. Absolute executables, raw HTTP,
PATH resets and processes launched outside the project environment remain
outside shell interception. A credential-isolated publishing service would
require a separate operator decision.

Payload transport follows the [GitHub CLI merge manual](https://cli.github.com/manual/gh_pr_merge),
[comment manual](https://cli.github.com/manual/gh_issue_comment) and
[release upload manual](https://cli.github.com/manual/gh_release_upload).
