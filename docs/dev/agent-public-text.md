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
deployments, deployment-statuses and compare (two full commit ids). GraphQL helpers build their own read-only
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
| `scripts/agent_runtime/shims/git` push, via `scripts/opsec/git_push.py` | New commit messages and the tag names and messages embedded in their mergetag headers (hits already on the public default branch excused), branch and tag names, annotated tag names and messages |
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
  of a signed tag, one header per merged tag), except commits this machine
  already scanned clean or already found public (below).

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

**Clean-commit cache.** `<git-common-dir>/lu-push-scan-clean` lists the
commits whose messages a push scan on this machine found clean. Its first line
binds it to a SHA-256 fingerprint of the matcher, rules and blocking policy and
to a SHA-256 digest of the scanning code's source (`scripts/opsec/git_push.py`
and `scripts/opsec/prepublish.py`, read once when the scanner loads); each further line is
one commit id. An entry is the verdict of the code that wrote it, so a commit
an older, weaker scanner found clean (for example one that did not read
mergetag text) must be scanned again by the current one. Hashing the source
does that on every code change without a version constant someone has to
remember to bump; the cost is one first-push-sized scan (cost below) after
each change to those files. If either file cannot be read, both caches are
unused for that push: every commit is scanned and nothing is written.
The digest is taken at import, before any scan, so it names the code the
process runs rather than whatever is on disk later; a checkout updated while a
push runs (a pull of the primary checkout, say) cannot lend the new code's
fingerprint to the old code's verdicts. Before writing to either cache the
process reads the source again; if it changed or cannot be read, nothing is
written, a one-line note says so, and the push result is unchanged. What
remains is the milliseconds between the interpreter reading the files to
compile them and the digest read.
Commit ids are content-addressed, so an id always names the same message. An id is written only after `check_texts`
accepts the push, and only for commits none of whose scanned texts (message
and mergetag fields) had a blocking finding. A hit that an override let through is never cached and is scanned
again on the next push. An unreadable, malformed or partly written file, or
one written under another fingerprint (for example after a rules update
or a change to the scanning code),
holds nothing: every reachable commit is scanned, a one-line note says so,
and a scan that skipped nothing replaces the file. Writers take an exclusive
`flock` on `lu-push-scan-clean.lock` and readers a shared one, so concurrent
pushes neither interleave lines nor read half of one. Every push prints how
many commit messages it scanned and how many it skipped as cached. The cache is
as trusted as the git directory itself; a hand-edited entry skips that
commit, as an edited hook could.

**Hits that are already public.** A commit message or mergetag field with a
blocking finding is excused only when the catalogue's canonical public repository (the
`public-monorepo` row of `scripts/config/fleet_repos.yaml`) already holds that
commit on its default branch. The question goes to that repository through
the typed publisher reads, never to the push URL, a tracking ref or local git
configuration. One `default-head` read returns the commit the default branch
names now. If that commit is present locally, local ancestry decides every hit
at once: commit ids name their parents, and replacement objects and grafts are
off. Otherwise each hit, newest first, is checked with GitHub's "Compare two
commits" (`compare` read, `{public head}...{hit}`): a yes counts only when
the reply is about the question asked and consistent with itself:
`base_commit.sha` is the public head that was queried, `merge_base_commit.sha`
is the hit, `ahead_by` is 0, and either status `behind` with `behind_by` of at
least 1, or status `identical` with `behind_by` 0 and the hit equal to the
head. That hit's ancestors are excused with it. A 404, `ahead` or `diverged`
is a no for that hit. Any other reply, including a yes-shaped one that fails
those checks, a failure, rate limit, timeout (10 seconds per call), or a
truncated or malformed body, stops the questions, and every unanswered hit is
refused and nothing is cached. One push asks at most 20 compare questions.
Ref names, tag names and tag messages are never excused. Refusals are unchanged: rule, class, field and line of each
unexcused hit, with the same single-use logged override. Excused messages are
never printed. With nothing cached, this repository's 385 published hits took
one call when the public head was present locally and two when it was not.

**Public-commit cache.** `<git-common-dir>/lu-push-scan-public` records the
excused commit ids. It uses the clean cache's format, fingerprint header
(matcher and scanning code), lock and fail-closed reading: an unusable file
holds nothing, a one-line note says so, and every hit is asked again. Only yes answers are
recorded. A refused, unanswered or overridden hit is never recorded, and an
excused commit is never recorded as clean. Commits in this cache are skipped
without scanning, as their text is already public, so a later push asks
nothing. The summary line counts the scanned, cached-clean and excused
commits and the public-repository calls.

**What the scan reads.** Every enumeration runs with replacement objects
(`--no-replace-objects`, `GIT_NO_REPLACE_OBJECTS=1`,
`-c core.useReplaceRefs=false`) and grafts (`GIT_GRAFT_FILE` set to the null
device) disabled, so reachability follows the parents recorded in the commits
the destination receives. A push is refused while a non-empty grafts file
exists (`info/grafts`, or the caller's `GIT_GRAFT_FILE`) or the repository is
shallow. Refusal is simpler than proving that a grafted pack and the scanned
history agree, and grafts are deprecated in favour of `git replace`.

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

Cost on this repository (9,485 commits reachable from a branch tip, 385 of
them published hits): the first push in a clone scans every message and asks
the public repository once or twice, in 12 to 17 seconds; a later push with
warm caches takes about 0.2 to 0.3 seconds and no calls, plus the time to scan
new commits.

Known gaps: git aliases that expand to push, absolute git paths, `git-push`
called from the exec path, submodule pushes from `--recurse-submodules`,
and note blobs under `refs/notes/` are not scanned.
An ssh host alias that does not name the hosted domain is scanned as public.
A local ref moved by another process between the scan and the push is not
rescanned. For matching refspecs (`:` or `push.default=matching`) the set of
refs comes from the preview's negotiation with the destination, so a
destination that gains a matching branch between the preview and the push can
receive that branch unscanned; explicit refspecs, `--all`, `--tags` and
`--mirror` name their refs locally. A hit can be excused only while GitHub is
reachable or after it was cached. The answer is as trustworthy as the `gh`
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

A compare reply is accepted on its SHA binding (the queried public head as
`base_commit`, the hit as `merge_base_commit`) without checking that the
reply's URLs name the canonical repository. The request itself is made only
to the catalogue repository through the typed publisher read, and no bypass of
that authenticated ancestry has been shown; matching the reply's URLs would
need host, case and rename normalisation, so it stays a recorded residual.

Two further residuals are recorded. The cache fingerprint does not include the
catalogue's canonical public repository, so public-cache entries survive a
change of that repository in `scripts/config/fleet_repos.yaml` until the
matcher, rules, policy or scanning code next changes. The scaling test for
mergetag header unfolding compares wall-clock timings, so it can fail or pass
on machine load rather than on the algorithm alone. The matcher fingerprint is
read before the private matcher loads and is not rechecked at write time, so a
private-tooling rollback during a push could still record a newer matcher's
verdicts under the older fingerprint.

Historical dispatch briefs, session records and autopsies retain their original
commands as evidence. For current execution, replace their raw writes with the
typed verbs above and their GraphQL reads with named read operations.

Payload transport follows the [GitHub CLI merge manual](https://cli.github.com/manual/gh_pr_merge),
[comment manual](https://cli.github.com/manual/gh_issue_comment) and
[release upload manual](https://cli.github.com/manual/gh_release_upload).
