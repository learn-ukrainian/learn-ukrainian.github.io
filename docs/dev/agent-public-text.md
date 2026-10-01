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
| `pr-merge` | Subject and body, defaults included; squash is fixed |
| `pr-update-branch`, `pr-ready`, `pr-close`, `issue-reopen`, `run-rerun` | No text; rerun always selects failed jobs |
| `workflow-run` | Only `ci.yml` and `deploy-pages.yml`, explicit validated ref; both have no inputs |
| `pr-disarm`, `pr-dequeue`, `issue-link` | No text; identifiers have closed validation. `issue-link --replace-parent` moves an issue from its current parent through GitHub's typed `replaceParent` variable |
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
extra operands and raw GraphQL are refused. REST `gh api` is admitted only with
an implicit GET or GET in every method flag, no field/input flags, and a path
in the closed read-endpoint allowlist. Pagination and read formatting flags
are supported. `gh auth status -t` and `--show-token` are always refused.
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
| `search` | prs |

Specific API reads also have a shell interface,
`python -m scripts.publish read <name> --repo <owner/repo> ...`.
`gh pr checkout <N>` is permitted only inside a real dispatch worktree.
Named `read()` operations include: identity, issue, comments,
labels, timeline, reviews, commits, comment, checks, jobs, issues, runs,
deployments and deployment-statuses. GraphQL helpers build their own read-only
documents for issue-parent, membership, subissues, subissues-next,
subissue-batch, membership-head, queue-snapshot, queue-status, budget,
issue-scope, issue-states, merge-facts, pr-bases and default-head. Caller values are variables or JSON-escaped
selectors, never documents or endpoints.

A raw write is admitted only under a known write grammar to an allowlisted
private repository. The private REST exception requires a complete repository
endpoint under a known resource, rejects encoded or traversing paths, and uses
the last explicit hostname. GraphQL remains unavailable through the raw shim. The last explicit repository selector wins over `GH_REPO`
and the local origin; a resource URL selects its actual repository. Other
hosts and unresolved destinations receive no private exemption. Gists have no
repository exemption. Forwarded private writes explicitly pin `--repo` to the proven destination.
Public refusal messages name the typed publisher verb.

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
| `scripts/agent_runtime/shims/git` push, via `scripts/opsec/git_push.py` | New commit messages and the tag names and messages embedded in their mergetag headers (history already on the public default branch excluded), branch and tag names, annotated tag names and messages |
| `scripts/ci/data_tier.py`, `scripts/ci/flake_ledger.py`, `scripts/ci/comment_issue_task_quality.py` | Separate bot/CI workflows, outside the cooperative-agent inventory |
| Printed templates and `scripts/wt.sh` | No outbound publication; executed public writes require publisher verbs |

This boundary protects cooperative agents. Absolute executables, raw HTTP,
PATH resets and processes launched outside the project environment remain
outside shell interception. A credential-isolated publishing service would
require a separate operator decision.

`pr-merge` checks the current draft status and every non-advisory check before
sending a write, for public and private repositories alike. Unknown, red or
pending check states refuse the merge. `AGENT_NO_MERGE=1` refuses it before
any transport. A ready merge pins the observed head with `--match-head-commit`.
The hook recognises the publisher command and uses the same readiness parser.

After readiness, `pr-merge` reads GitHub's default squash subject and body
for the pinned head (`viewerMergeHeadlineText` and `viewerMergeBodyText`).
An omitted subject or body is filled with that default and sent explicitly,
so the scanned text is the sent text. A merge queue ignores explicit text and
composes the default itself, so for queued repositories the defaults are
scanned as `default_subject` and `default_body` as well. A changed head or an
unreadable default refuses the merge.

Known race: the head pin freezes commits, not metadata. A PR title or body
edited after the default squash text is read, but before GitHub composes a
queued merge, is published unscanned. Explicit (non-queued) merges send the
scanned text and are not affected.

## git push

The git shim sends every `push` (after global options such as `-C` and `-c`)
to `scripts/opsec/git_push.py` before the real git runs. A dry run
(`--dry-run --porcelain --no-verify --verbose`) reports which refs the push
names and the push URL git resolved (after `insteadOf` and `pushInsteadOf`),
printed without userinfo. For each destination that `is_private` does not
exempt, these are scanned through `check_texts`:

- every named branch, tag or other ref name, except deletions;
- the name inside every annotated tag object on the way from a pushed ref to
  its target, nested tags included (it can differ from the ref it is pushed
  to), and each such tag's message;
- the message of every commit reachable from the named tips, and the tag name
  and message of each tag object embedded in its `mergetag` headers (a merge
  of a signed tag, one header per merged tag), except commits already on the
  public default branch (below).

Messages are read from the raw objects (`git cat-file`), everything after
the first blank line, so a NUL byte cannot hide the rest of a message the way
`%B` would. Each message is decoded as UTF-8 and, when its `encoding` header
names a codec that reads it differently, that reading is scanned too. A
`mergetag` value is unfolded (each continuation line loses its one leading
space; unfolding is linear in the header size) and read with the same
tag-object parser; its fields are reported as
`commit[<id>].mergetag[<n>].tagname` and `.message`. A commit or tag object,
including an embedded one, that has no blank line after its headers, or whose
headers open with a continuation line, refuses the push naming only the
object: git would deliver text that no reader shows as a message. Lines after
the first blank line are message text even when they look like headers.

Nothing the destination reports counts as evidence of what it already has:
no `ls-remote`, no tracking refs, and no old tips or up-to-date or rejected
verdicts from the preview. A forged or stale advertisement therefore cannot
shrink the scan.

**History already on the public default branch.** Nothing from an earlier
push is trusted: there is no cache, and every push decides afresh. Commits
already public are excluded from the scan, not excused after it. Per push that
sends commits, one typed `default-head` read asks the catalogue's canonical
public repository (the `public-monorepo` row of
`scripts/config/fleet_repos.yaml`) for `nameWithOwner` and the name and head
commit of its default branch, through the publisher's authenticated read path,
never the push URL, a tracking ref, `insteadOf` or other local configuration.
The reply counts only when it is bound to the question: `nameWithOwner` is the
catalogue repository, the branch is `main`, the head is 40 lowercase hex
characters, and the reply has no GraphQL `errors`. A failure, timeout (10
seconds), 404, 403 or rate limit, a truncated or malformed body, or any
mismatch excludes nothing, and the scan covers all reachable history.

When the head commit is present locally, the scan set is
`git rev-list <pushed tips> ^<public head>`. Object ids are content addressed
and a commit id covers its parents' ids, so every commit reachable from the
authoritative public head is public; no local ref, URL rewrite or object can
put a commit inside that history without a hash collision. Ancestry is read
from the commit objects themselves: replacement objects, grafts and
commit-graph files (a local cache of parents that git does not rehash) are
off, a grafted repository is refused, a shallow one is refused only when a
boundary commit is inside the scan set (below), and objects are never fetched
lazily. A merge commit in the public history is excluded with the tag text
embedded in its `mergetag` headers, because publishing the merge published
that text. Ref names, tag names (embedded `tag` headers included) and annotated
tag messages are always scanned, even when the commit they name is public.

When the head commit is not present locally (a clone that has not fetched the
current public default branch), nothing can be excluded: every reachable
commit is scanned. If that refuses a hit in history older than the pushed
tips, the refusal adds that fetching the public default branch lets the scan
skip history that is already public. Refusals are unchanged otherwise: rule,
class, field and line of each hit, never the matched text, with the same
single-use logged override. Every push that sends commits prints one line with
the number of commits scanned, whether the public head was present, absent or
unavailable, and the number of public-repository calls (one).

**What the scan reads.** Every enumeration runs with replacement objects
(`--no-replace-objects`, `GIT_NO_REPLACE_OBJECTS=1`,
`-c core.useReplaceRefs=false`), grafts (`GIT_GRAFT_FILE` set to the null
device) and commit-graph files (`-c core.commitGraph=false`) disabled, so reachability follows the parents recorded in the commits
the destination receives. A push is refused while a non-empty grafts file
exists (`info/grafts`, or the caller's `GIT_GRAFT_FILE`). Refusal is simpler
than proving that a grafted pack and the scanned history agree, and grafts are
deprecated in favour of `git replace`.

**Shallow clones.** git walks every commit listed in the shallow file as
parentless, so history behind it is invisible to the scan. The scan reads that
file once per push, through `git rev-parse --git-path shallow` (a linked
worktree resolves to the shared file), and refuses the push only when a listed
boundary commit is in the scan set: reachable from the pushed tips and not
excluded by the public head. The refusal names the rule and the boundary's
position (`commit[<id>]`) and says to deepen (`git fetch --deepen=<n>`) or
unshallow (`git fetch --unshallow`) the clone. A boundary outside the scan set
(not reachable from the tips, or reachable only through the excluded public
history) hides nothing the push sends and does not refuse. A forged entry
cannot shrink the scan set: a boundary only removes parents, so the excluded
history it truncates is never larger than the true public history, and any
commit the push sends but the walk misses lies behind a boundary that is itself
in the scan set. An unreadable, non-regular or malformed shallow file (any line
that is not exactly one lowercase commit id of the repository's object format)
refuses the push, and so does git's `--shallow-file` option, which would swap
the file the push reads.

**What the scan writes.** The scan's own git calls drop `GIT_TRACE*` and
`GIT_CURL_VERBOSE`, set `GIT_TRACE2`, `GIT_TRACE2_EVENT` and `GIT_TRACE2_PERF`
to `0` (which outranks `trace2.*` targets in configuration) and set
`GIT_TERMINAL_PROMPT=0` and `GIT_NO_LAZY_FETCH=1` (no partial-clone object
fetches). The scan never passes a URL to git and never reads
one with userinfo. Caller tracing still applies to the real push the caller
asked for.

Classification uses the URL the preview prints. Scp-like, `ssh://`, `git://`
and `https://` forms name a hosted destination; local paths, file URLs, remote
helpers and unparseable text are scanned (never private by default). A hit, a
missing or incompatible matcher, or an unreadable or failed preview refuses
the push before anything is sent. Diagnostics name the rule, class, field and
line, or only the failing phase and exit code; git's own output from these
steps is never replayed. The same single-use, logged `LU_OPSEC_OVERRIDE`
applies; the real git does not receive it. File contents are not scanned.

Cost on this repository (9,502 commits reachable from the measured branch
tip; real `default-head` read, dry-run preview to the real remote, nothing
pushed): an agent branch with 10 new commits on the public base took 1.05 to
1.21 seconds end to end, of which git's own dry-run preview was 0.62 seconds,
the one API read 0.45 seconds, and enumeration, reading and matching 0.05
seconds. With the public head absent locally the push scanned all 9,502
commits in 12.4 to 12.6 seconds with one API call and was refused on hits in
already-public history, with the fetch hint. That case is bounded by matching
every message in the history; it grows with the history and is paid only by a
clone that lacks the public head.

Known gaps: git aliases that expand to push, absolute git paths, `git-push`
called from the exec path, submodule pushes from `--recurse-submodules`,
and note blobs under `refs/notes/` are not scanned.
An ssh host alias that does not name the hosted domain is scanned as public.
A local ref moved by another process between the scan and the push is not
rescanned. For matching refspecs (`:` or `push.default=matching`) the set of
refs comes from the preview's negotiation with the destination, so a
destination that gains a matching branch between the preview and the push can
receive that branch unscanned; explicit refspecs, `--all`, `--tags` and
`--mirror` name their refs locally. History is excluded only while GitHub
answers; otherwise the scan is full. The answer is as trustworthy as the `gh`
executable and its configuration, which every publisher already relies on. For the guarded non-push commands (`checkout` and `switch`
under `AGENT_NO_MERGE=1`) the shim fails closed when its guard interpreter
(`AGENT_GIT_SHIM_PYTHON`, else the main checkout's `.venv`, else the shim
checkout's) is missing or fails to run (#9448).

**Scope boundary: identities and signatures.** Author, committer and tagger
identity lines (including the tagger line of a mergetag), `gpgsig` headers and
other signature headers are not scanned. The scan's denominator is message and
name text; an identity line repeats the same name and address on every commit
a person makes, so a private matcher rule that matched it would refuse every
push over that identity, with no edit to the message able to clear it.
Signature armor that git appends to a tag message is the exception: its start
is a marker line the tag author writes, so it is scanned as part of the
message rather than trusted to end the message text.

Recorded residuals. A stale clone without the public head pays a full scan
(cost above) and is refused while already-public history holds hits, until it
fetches the public default branch. The canonical repository identity is read
from the catalogue, so a wrong `public-monorepo` row would exclude the wrong
repository's history; the catalogue is reviewed repository configuration. The
expected default branch name (`main`) is a constant in
`scripts/opsec/git_push.py`; renaming the public default branch makes every
reply mismatch and every scan full until the constant changes. The scaling
test for mergetag header unfolding compares wall-clock timings, so it can fail
or pass on machine load rather than on the algorithm alone.

Historical dispatch briefs, session records and autopsies retain their original
commands as evidence. For current execution, replace their raw writes with the
typed verbs above and their GraphQL reads with named read operations.

Payload transport follows the [GitHub CLI merge manual](https://cli.github.com/manual/gh_pr_merge),
[comment manual](https://cli.github.com/manual/gh_issue_comment) and
[release upload manual](https://cli.github.com/manual/gh_release_upload).
