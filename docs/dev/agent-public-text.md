# Agent GitHub publishing

Use `python -m scripts.publish <verb>` for public GitHub writes. Project code
uses `scripts.publish.github.publish()` or a `Request` with `request_run()`.
Both interfaces validate the same closed field schemas. PR creation requires
explicit base and head names so implicit branch names cannot escape scanning. Arbitrary flags,
endpoints, GraphQL documents and payload passthrough are unavailable.

Destination resolution validates ASCII hostname labels before lowercasing;
malformed destinations remain `unknown`. Repository-bound operations refuse
`unknown`; both `GH_HOST` and API hostname flags use the resolved host.

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

The verdict recorder uses the scanner's validated absolute-path spans to make
checkout citations repository-relative. It rewrites only complete spans on
normalization-stable lines, for existing files, directories or symlinks lexically
inside the primary checkout or recorded worktree. Parent directories must resolve
inside the allowed root; the final component is checked without following its
symlink, so an interpreter symlink can be cited. A terminal `:line[:column]`
annotation must identify a regular file and have no competing suffixed filename.
Outside, nonexistent or ambiguous citations stay verbatim;
lines made normalization-unstable by editing are restored. The typed publisher
still scans the complete rendered comment before sending it. Missing path
rules or incompatible spans refuse recording without a fallback tokenizer.

`LU_OPSEC_OVERRIDE=reason` permits a false-positive match only after a durable
local log write. It cannot bypass missing or incompatible tooling. The log
contains timestamp, repository identity, rule identifiers and reason, never
payload text. Transports and internal lookups receive no override; a reason
can be consumed once per command. A clean, empty or private publish never uses
up the override: it is claimed and logged only when a scan blocks, so one
override covers exactly one flagged publish. Claim-file reclamation remains
maintenance work.

The claim belongs to the command, not to the process that publishes (#9681).
The first process of a command to read the override names its parent, the
shell that set it, in `LU_OPSEC_OVERRIDE_ANCHOR` (`<pid>:<reason>`): importing
`scripts.opsec.prepublish` does this, and so does the agent git shim for a
push. Child processes inherit that anchor, so an in-process publish and a
child push (`dispatch_settle`, delegate auto-finalize) or a recursive
submodule push share one use. An anchor names a process only for its own
reason, and only an ancestor of the claiming process can be claimed for; any
other anchor refuses the flagged publish. Setting the anchor to another of
one's own ancestors does yield a new claim, as setting a new reason always
has: the override is a cooperative agent's logged false-positive escape, and
the threat model excludes a malicious local writer.

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
issue-scope, issue-states, merge-facts, pr-bases, default-head and squash-text. Caller values are variables or JSON-escaped
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
| `scripts/agent_runtime/shims/git` push, Git's pre-push hook `scripts/opsec/git_push.py` | Branch, tag and other ref names; annotated tag names and messages; new commit messages with their embedded mergetag tag names and messages |
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

The enqueue mutation takes no commit text: the queue composes the squash from
the PR's title and body when it builds the merge group. Every agent edit of a
title or body goes through the publisher (`pr-edit`), which scans it. The merge
queue keeper (`scripts/orchestration/merge_queue_keeper.py`, every five
minutes) also re-reads each queued PR's default squash subject and body, and
the message of the queue entry's head commit once GitHub reports one, through
the `squash-text` read, and dequeues the PR on a blocking finding
(`revoked: squash-text-blocked`, no text quoted). A read or matcher failure is
reported as `squash text unverified` and does not dequeue. Residual, controlled
only by GitHub (owner: the operator): an edit made outside agent tooling after
the last scan reaches the merge group if the queue merges it before the next
keeper run. Server-created squash text never passes a client hook, so these
checks stay alongside the push scan below.

## git push

**Where the scan runs.** Git runs the `pre-push` hook after it has chosen the
ref updates and the destination and before it sends anything, and passes the
hook one line per update: local ref, local object id, remote ref, remote object
id. The scan runs there, so the ids it reads are the ids Git sends, and a branch
that moves during the scan changes nothing. Git also keeps its own semantics
for everything else (refspecs, leases, `--follow-tags`, tracking refs,
upstreams); the scanner does not predict or rebuild the push.

The agent git shim makes that hook run. For `git push` the shim adds
`-c core.hooksPath=<checkout>/scripts/opsec/push_hooks`
as the last option before the command. A command-line assignment outranks
configuration files, `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_<n>`/`GIT_CONFIG_VALUE_<n>`
and earlier `GIT_CONFIG_PARAMETERS`, and the last one wins over every earlier
`-c` or `--config-env`, so no configuration source redirects the hook. Git
passes command-line configuration to the pushes it starts in submodules, so
each recursive child push runs the same hook in its own repository, on its own
updates and destination. A child that is refused stops the whole push before
the parent is sent. Recursion by configuration (`push.recurseSubmodules`,
`submodule.recurse`) reaches nested submodules; Git's command-line
`--recurse-submodules` pushes only the first level, so deeper commits are not
sent at all.

**Aliases are refused.** Agents run Git commands directly. After the global
options, the shim forwards a command only when its first word passes two
checks, both answered by the Git it is about to run, with the caller's global
options and environment, on every call and with nothing cached:

1. The word is one of Git's own commands: a builtin or a `git-<name>` program
   in Git's exec path (`git --list-cmds=builtins,main`, so `--exec-path` and
   `GIT_EXEC_PATH` count). Anything else is refused: every alias of another
   name (`git -c alias.p=push p` included), a `git-<name>` program found only
   on `PATH`, and a mistyped name, which Git could otherwise autocorrect.
2. No alias of that name is defined. A listed name can still run as an alias:
   Git looks an alias up before a deprecated builtin (`alias.whatchanged`), and
   falls back to the alias when a `git-<name>` program fails to start. So the
   shim asks Git for its alias names (`git config --name-only --get-regexp`,
   compared without regard to case, as Git does) and refuses the command when
   one matches, over any builtin (`alias.status`, `alias.push`) or program.
   The lookup sees every source Git reads aliases from: system, global,
   repository and worktree files, include files, `-c`, `--config-env`,
   `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_<n>`/
   `GIT_CONFIG_VALUE_<n>`. It runs with `GIT_CONFIG` unset, because that
   variable narrows `git config` to one file while Git's alias lookup ignores
   it, under a ten-second limit. A probe key it adds itself must come back, so
   a lookup that fails, times out or reads no configuration refuses. Git 2.53
   does not read aliases from a worktree file; the shim refuses them anyway.

Refusals come before Git runs, with a message saying what to do instead. The
shim never reads alias values, so no difference between its reading and Git's
(quoting, separators such as a carriage return, nesting, options inside the
alias) can reach push. The lookup is one more `git config` call: a `git status`
in a small repository took 0.021 seconds through the shim against 0.016 seconds
before the lookup and 0.002 seconds with plain Git (median of 41).

The shim does not pin the hooks path on commands other than push: that would hide
the caller's other hooks (pre-commit and the rest), and a wrapper for every hook
would change Git's behaviour where a hook's mere presence matters
(`push-to-checkout`, `proc-receive`). Refusing what it cannot classify is the
simpler closed failure.

The shim refuses, before Git runs, a push that would skip the hook or could not
scan:

- `--no-verify` in any spelling Git accepts (`--no-verify`, `--no-verif`,
  `--no-veri`) and the shorter ambiguous prefixes, in any argument position;
- `--shallow-file`, which swaps the shallow file Git walks;
- `GIT_CONFIG` set to anything, empty included. It narrows what `git config`
  reports to one file, while the push itself reads every configuration
  source, so a `core.sshCommand` or `core.hooksPath` the push uses would be
  invisible to the scanner's and the chain's configuration reads. It is the
  only Git 2.53 variable that changes `git config` and nothing else (the
  other `GIT_CONFIG_*` variables apply to every Git command);
- a missing or non-executable hook, a missing scanner or a missing project
  interpreter. Git itself would silently skip a missing hook.

The hooks directory holds `pre-push`, `reference-transaction` (the other hook a
push runs, for the tracking refs) and `chain`. After a clean scan `chain` runs
the caller's own hook of the same name with the same arguments and input: the
last `core.hooksPath` value that is not the pinned directory, else the
repository's `hooks` directory. A caller hook that fails still refuses the push.
Like the scanner's configuration reads, the chain's `core.hooksPath` query
runs with `GIT_CONFIG` unset, so both see the configuration Git pushes with
even when Git is started with the pinned hooks path but without the shim.

**What is scanned.** The hook reads its whole input and validates every line
before allowing anything: four fields, split from the right because the local
ref can be any expression the caller typed; lowercase ids of the repository's
object format; a remote ref under `refs/`; and a deletion exactly when the
local id is all zeros with the `(delete)` local ref. A malformed line, a scanner
error, a missing matcher or the deadline (`LU_OPSEC_PUSH_SCAN_TIMEOUT`, 300
seconds by default) refuses the push. A deletion publishes no text and needs no
matcher. For a public destination these are scanned through `check_texts`:

- every remote ref name the push updates;
- the name inside every annotated tag object on the way from a sent id to its
  target, nested tags included (it can differ from the ref it is pushed to),
  and each such tag's message;
- the message of every commit reachable from the sent ids, and the tag name and
  message of each tag object embedded in its `mergetag` headers, except commits
  already on the public default branch (below).

Objects are read by the id Git supplied, never by resolving a name again.
Messages are read from the raw objects (`git cat-file`), everything after the
first blank line, so a NUL byte cannot hide the rest of a message. Each message
is decoded as UTF-8 and, when its `encoding` header names a codec that reads it
differently, that reading is scanned too. A `mergetag` value is unfolded
(linearly in the header size) and read with the same tag-object parser; its
fields are reported as `commit[<id>].mergetag[<n>].tagname` and `.message`. An
object, including an embedded one, without a blank line after its headers, or
whose headers open with a continuation line, refuses the push naming only the
object. Refusals name the rule, class, field and line, never the matched text.
The single-use, logged `LU_OPSEC_OVERRIDE` applies only to a flagged push and
is claimed for the command's anchor (see the override above), which the shim
sets to the caller of the push unless a publisher above already carries one;
the caller's own hook receives neither. A clean push neither uses up the override nor looks up that process,
so a failed lookup refuses only a flagged push.
File contents are not scanned.

**History already on the public default branch.** Nothing the destination
reports counts as evidence of what it already has. Per push that sends commits,
one typed `default-head` read asks the catalogue's canonical public repository
(the `public-monorepo` row of `scripts/config/fleet_repos.yaml`) for its name
and the name and head of its default branch, through the publisher's read path,
never the push URL or local configuration. The reply counts only when it names
the catalogue repository and the `main` branch, the head is 40 lowercase hex
characters and there are no GraphQL errors; anything else (failure, 10-second
timeout, 404, rate limit, malformed body) excludes nothing. When that head is
present locally and every commit reachable from it hashes to its id, the scan
set is the commits reachable from the sent ids and not from that head. Local or
alternate object stores could hold altered bytes under a genuine id, so a
commit that fails the hash check or is missing leaves the head `unverified
here` and excludes nothing. Replacement objects, grafts and commit-graph files
are off for every enumeration, a grafted repository is refused, and objects are
never fetched lazily. A merge in the public history is excluded with its
embedded tag text. Ref names and tag text are always scanned. When the head is
absent locally every reachable commit is scanned, and a refusal on older
history adds that fetching the public default branch lets the scan skip it.
Every push that sends commits prints one line with the number of commits
scanned and the state of the public head.

**Shallow clones.** git walks a commit in the shallow file as parentless, so
the scan refuses a push only when a listed boundary commit is inside the scan
set, and says to deepen or unshallow the clone. A boundary outside the scan set
hides nothing the push sends, and a forged entry cannot shrink the scan set. An
unreadable, non-regular or malformed shallow file and `GIT_SHALLOW_FILE` refuse
the push.

**What the scan writes.** The scan's own git calls drop `GIT_TRACE*`,
`GIT_CURL_VERBOSE` and `GIT_CONFIG`, set the trace2 targets to `0`, and disable prompts and lazy
fetches. They keep Git's repository variables, so the hook reads the
repository and object stores the push reads; the scanner's own catalogue,
matcher and override log lookups drop them.

**Private destinations.** A destination is exempt only when `is_private` names
it and Git reaches it on the trusted route: `https://` with certificate
verification, or ssh (URL or scp-like form) through the `ssh` program found on
`PATH`, with Git's own exec path and no remote helper. `GIT_SSH_COMMAND`,
`GIT_SSH`, `core.sshCommand`, a `<transport>::` URL, `remote.<name>.vcs`,
another `GIT_EXEC_PATH`, `GIT_SSL_NO_VERIFY` or `http.sslVerify=false` for that
URL could deliver elsewhere, so such a push is scanned as public. Local paths,
file URLs and unparseable destinations are always scanned.

**Cost.** One ordinary clean push of a single commit to a local bare remote took
0.018 seconds with plain Git and 0.196 seconds through the shim (median of five,
synthetic matcher, no GitHub answer), so the hook adds about 0.18 seconds of
interpreter start-up and object reads. A real push adds the one `default-head`
read and the hash check of the public history when the head is present; both
grow with that history, and a clone without the head scans all of it.

**Supported entry points and recorded gaps.** The scan covers `git push`
through the agent git shim, including recursive submodule pushes; the shim
refuses every alias, every command whose name an alias also defines, and every
`git-<name>` program outside Git's exec path (above). These publish without
it, and stay outside this boundary as for every other publisher: an absolute Git
executable or a `PATH` without the shim; commands that run Git themselves
(`git-<name>` programs in the exec path the caller chose, `git submodule foreach`,
`rebase --exec`, `bisect run`), because
Git puts its own executable first on their `PATH`, so they reach the real Git
and not the shim; direct `git send-pack`, which runs no pre-push hook; other
Git implementations and libraries; and publication through the GitHub API or
web interface, which the typed publisher and the squash checks above cover for
agents. The shim checks the hooks before Git runs, so a hook removed in between
would let Git skip it; a deliberately malicious local writer to the repository
is outside the threat model. ssh client configuration and name resolution decide
where an unchanged ssh URL connects, outside Git. Note blobs under
`refs/notes/` and file contents are not scanned. History is excluded only while
GitHub answers; otherwise the scan is full.

**Scope boundary: identities and signatures.** Author, committer and tagger
identity lines and signature headers are not scanned: an identity repeats on
every commit a person makes, so a rule matching it would refuse every push with
no message edit able to clear it. Signature armor that Git appends to a tag
message is scanned as part of the message.

Historical dispatch briefs, session records and autopsies retain their original
commands as evidence. For current execution, replace their raw writes with the
typed verbs above and their GraphQL reads with named read operations.

Payload transport follows the [GitHub CLI merge manual](https://cli.github.com/manual/gh_pr_merge),
[comment manual](https://cli.github.com/manual/gh_issue_comment) and
[release upload manual](https://cli.github.com/manual/gh_release_upload).
