# Guard hooks: frozen understood forms (#9484 part B)

## Outcome, authority and scope

This is a testable freeze, not an implementation or an implementation approval.
The outcome is that the three hooks account for visible Git/GitHub CLI operations
without blocking normal literal messages, search, inspection or safe worktree
commands. The designated change-of-approach decision on
[#9484](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9484)
is normative. The review is defect evidence; Bash recordings are execution
evidence, not policy. The decision digests are:

- Sol: `541a4ed9d82ccc786c41d89943864b2e990cab5a896954fb7072f9f05383c19a`.
- Opus: `daedf1d3a172cba03b4ee6851bca8f8df43a806d50937e7e8e472404e9c8837e`.

The smallest adequate change is a shared conservative gate and occurrence
accounting boundary around the pinned AST reader, replacing the executor
deny-list. Hook policy remains separate. This packet changes no hook or parser.
Non-goals: executing commands during hook admission, general shell interpretation,
network mutations, a new policy for branch operations, and new residual classes.
The author owns this freeze; the infra driver owns implementation and landing;
an independent critical-risk cross-family reviewer owns exact-head review.

## Candidate gate and source-position accounting (amendment 1)

All three hooks use the same gate. First perform Bash-aware backslash-newline
joining with a byte-range map back to the submitted command. Join in unquoted
words and double quotes where Bash removes the escape pair. Do not join inside
comments, single quotes or quoted heredoc bodies. A comment ends at its actual
newline, including when its final character is a backslash. In an unquoted
heredoc, apply its expansion/continuation rules and inspect executable
expansions. Delimiter quote removal controls heredoc expansion. Preserve ANSI-C
quote decoding, escaped spellings and literal-word concatenation; decode errors
are refusals. Never globally remove backslashes or normalize quoted data.

Trigger on possibly executable `git` or `gh` occurrences, including decoded,
concatenated and escaped spellings, and the existing typed publisher interface.
Do not require an operation word alongside a git/gh occurrence. Also trigger
on a dynamic command name whose literal arguments have a branch-operation or
`pr merge` shape (amendment 6). Literal occurrences in data still trigger
accounting; their consumer determines allowance. An untriggered command keeps
the existing unrelated-command allowance, within the residual boundaries below.

Every candidate is assigned exactly once by source byte interval and consumer,
not token counts. An AST word may contain multiple mapped intervals. Word
concatenation cannot drop intervals. Nested payloads inherit their parent source
map. A quoted mention and a real invocation with identical text are distinct.
For silent mis-parses, inspect redirect-node words as well as command nodes;
missing/duplicate coverage, ERROR/missing nodes, trailing unparsed bytes, reserved
words misread as arguments, decode failure and exhausted limits refuse the
whole candidate. The existing coproc, integer-overflow and glued-redirect rows
remain required. Removing one invocation while preserving the number of words
must fail fault-injection coverage.

| Category | Required proof |
| --- | --- |
| Recognized invocation | Complete literal program/subcommand and classified argv; understood wrapper/context; every reachable cwd, repository, selector and policy checked. |
| Proven non-executing data | Literal bytes in an explicitly admitted operand, with all expansions walked separately, and all later consumers known to be data readers. Basename or quotation alone proves nothing. |
| Proven unreachable code | Structural termination/constant condition with no executable expansions; all prior success/failure edges modeled. A sample Bash run or absent path is insufficient. |
| Unclassified | Refuse the entire command with a typed reason. Unknown/dynamic command identities refuse; known built-ins follow the generic rules below. |

Definitions and assignments require use tracking. A variable is data only when
every use in the submitted command is a recognized data operand. Invocation
arguments can be read-only dynamic data under the rules below; they cannot
erase a candidate's source provenance.

## Closed grammar and option classes

Classes: **data** consumes non-executing literal/text operands; **executor**
consumes or supplies code; **selector** chooses the operation, target, ref or
policy mode; **context** changes cwd, repository, environment or process state;
**refuse** is outside the admitted grammar. Closed option tables bind only to
policy-relevant branch switching/creation, worktree operations, `gh pr merge`
(including admin forms), and executor-capable options/subcommands. They are not
an exhaustive allowlist of Git/GH traffic. Every other known built-in Git/GH
subcommand is recognized under the generic executor, configuration, environment
and alias rules; its ordinary arguments are data unless an executor option
applies. Unknown/dynamic commands, aliases and unsupported executors refuse.
In a closed policy grammar, unlisted options, abbreviations, unknown clusters,
response files, negations, missing values and ambiguous boundaries refuse.
A literal executable path must resolve to a verified supported program; an
arbitrary basename match is insufficient. Options taking values accept separate and `--long=value` spellings only where
the program actually supports them; short attachment/clustering is decoded
with that program's rules, never a generic skip-one-token rule.

### Git and GitHub CLI

Git global options: `-C` (including attached form, repeated left to right),
`--git-dir`, `--work-tree`, `--namespace`, `--bare`: **context**, require proven
repository binding or refuse. `--no-pager`: **context**, disables paging.
`--paginate`, `-p`: **executor**, refuse in candidates.
`-c`: **context** only for literal `color.ui=never`, `core.pager=cat`,
`pager.log=false`, `pager.show=false`, `pager.diff=false`; all other keys/values
are **executor/refuse**, including aliases, hooks and transports.
`--config-env`: **executor/refuse**. `--exec-path`, `--html-path`, `--man-path`,
`--info-path`, `--version`, `--help`, `-h`: **data** only in terminal inspection
forms; an executable-path override is **context/refuse**. `--literal-pathspecs`,
`--glob-pathspecs`, `--noglob-pathspecs`, `--icase-pathspecs`: **selector**.

| Git subcommand | Admitted options and classifications |
| --- | --- |
| `checkout`, `switch` | `-b`, `-B`, `-c`, `-C`, `--create`, `--force-create`, `--orphan`, `--detach`, `--track[=direct\|inherit]`, `-t`, `--no-track`, `--guess`, `--no-guess`, `--ours`, `--theirs`, `--conflict`, `--merge`, `-m`, `--force`, `-f`, `--ignore-other-worktrees`, `--recurse-submodules`, `--no-recurse-submodules`, `--overlay`, `--no-overlay`, `--patch`, `-p`, `--ignore-skip-worktree-bits`, `--pathspec-from-file`, `--pathspec-file-nul`, `--start-point`: **selector**; `-q`, `--quiet`, `--progress`, `--no-progress`: **data**. `--` ends options and establishes path checkout only when its structural position is proven. Positional ref/path operands are **selector**. |
| `branch` | `-d`, `--delete`, `-D`, `-m`, `--move`, `-M`, `-c`, `--copy`, `-C`, `-f`, `--force`, `--list`, `-a`, `--all`, `-r`, `--remotes`, `--merged`, `--no-merged`, `--contains`, `--no-contains`, `--points-at`, `--show-current`, `--track`, `-t`, `--no-track`, `--set-upstream-to`, `-u`, `--unset-upstream`, `--edit-description`: **selector** (`--edit-description` also **executor/refuse**); `-v`, `-vv`, `--verbose`, `--format`, `--sort`, `--color`, `--no-color`, `--column`, `--no-column`, `-q`, `--quiet`: **data**. Refs are **selector**. |
| `worktree` | `list`: `--porcelain`, `-v`, `--verbose`, `-z`: **data**. `add`: `-b`, `-B`, `--detach`, `--orphan`, `--track`, `--no-track`, `-f`, `--force`, `--lock`, `--reason`, `--no-checkout`, `--checkout`: **context/selector**; `-q`, `--quiet`: **data**. Creation compounds refuse unless the success-edge model and binding are proven. `remove`: literal directory **context**, `-f`/`--force` **selector**; successful removal invalidates that directory binding for later commands. Other verbs **refuse**. |

For other Git built-ins, the following roles are examples, not closed option
allowlists. Ordinary revision, path, search, format, message and transport/ref
arguments are data. This includes `ls-files`, `merge-base`, `ls-remote`,
`sparse-checkout list`, `remote -v`, `rev-list`, `log -<N>`, `diff --cached`,
`reset --hard`, `pull`, `clean --dry-run -fdx`, `cherry-pick`, `revert`, `archive`
and `read-tree`. Fetch/push options `-u`, `--set-upstream` and
`--force-with-lease[=REF:EXPECT]` remain recognized and are judged by the existing
push policy; these three hooks add no push-policy restriction. Commit
`-m`/`--message`, `-F`/`--file`, trailers and merge messages are data.

Executor semantics still bind: rebase `-x`/`--exec`, `bisect run`,
`submodule foreach`, difftool `-x`/`--extcmd`, fetch/ls-remote/clone/pull `--upload-pack`, archive `--exec`, filter-branch
filters (`--env-filter`, `--tree-filter`, `--index-filter`, `--parent-filter`,
`--msg-filter`, `--commit-filter`, `--setup`), send-email `--*-cmd`, mergetool, and push
`--receive-pack` consume code and refuse unless explicitly modeled. Pager,
editor, signing, hooks, custom strategies, interactive/edit, external diff,
textconv, executable configuration and alias options are never presumed data.
`config` read forms are data; writes supplying executable configuration refuse.
A normal built-in operation does not refuse just because its name or ordinary
option is missing from the tables. The frozen benign baseline remains binding.

Git read commands must account for applicable local configuration, pager,
external diff/textconv, aliases and environment. No candidate is declared data
if executable customization may consume it. Inspection without such a candidate
does not acquire a new global security-policy gate.

GitHub CLI inherited `-R`, `--repo`: **context** (literal validated values);
`--version`, `--help`, `-h`: **data** in terminal help forms. `--hostname` is
not admitted on these PR/issue forms; host identity comes from the repository
value or verified discovery.

| GH form | Admitted options and classifications |
| --- | --- |
| `pr merge` | `--subject`, `-t`, `--body`, `-b`, `--body-file`, `-F`, `--author-email`, `-A`: **data**, consume a value. `--match-head-commit`: **selector**, consumes a value. `--admin`, `--auto`, `--disable-auto`, `--delete-branch`, `-d`, `--merge`, `-m`, `--squash`, `-s`, `--rebase`, `-r`: **selector**, Boolean. `--help`, `-h`: **data**. `-R`, `--repo`: **context**, consume a value. Sole positional number/URL/branch is **selector**. |
| `pr checkout` | `--branch`, `-b`, `--detach`, `--force`, `-f`, `--recurse-submodules`: **selector**; `-R`, `--repo`: **context**; PR operand **selector**. |

Other known GH built-ins use the generic rules, including `pr ready 5`,
`run view/list`, read `api` forms, and PR/issue view/list/diff/checks/create.
Literal body/title/message, JSON/jq/template, search, limit and other ordinary
arguments are data. `--editor`, `--web` and alias/custom-command execution
require executor accounting when consuming candidates. Ordinary `gh api` reads
are recognized; REST merges remain the explicitly accepted residual, not a
supported shell wrapper. An unknown/dynamic GH command still refuses.

The existing typed project publisher `project-python -m scripts.publish
pr-merge` is a recognized invocation, not a generic Python exemption. Its closed
fields `--number` (**selector**), `--repo` (**context**), `--match-head`
(**selector**), `--subject`, `--body`, `--body-file` (**data**), and terminal
`--help` (**data**) map to the same merge judgment. Other Python payloads refuse.

### Closed data-reader list (amendment 2)

For grep/rg, known non-executing options and their operands are data; the examples
below are not closed allowlists. For the other readers the closed forms remain
binding. Literal operands are data only after expansion and consumer checks.

| Program | Admitted options | Executor options / refused forms |
| --- | --- | --- |
| `grep` | `-F`, `--fixed-strings`, `-E`, `--extended-regexp`, `-n`, `--line-number`, `-i`, `--ignore-case`, `-e`, `--regexp`, `-f`, `--file`, `-r`, `-R`, `--recursive`, `-l`, `--files-with-matches`, `-q`, `--quiet`, `-v`, `--invert-match`, `-c`, `--count`, `-A`, `-B`, `-C`, `--after-context`, `--before-context`, `--context`, `-w`, `--word-regexp`, `-o`, `--only-matching`, `--include`, `--`: **data** | Known grep options are data; ambiguous/invalid option boundaries refuse. |
| `rg` | `-F`, `--fixed-strings`, `-n`, `--line-number`, `-i`, `--ignore-case`, `-e`, `--regexp`, `-f`, `--file`, `-g`, `--glob`, `--files`, `-l`, `--files-with-matches`, `-q`, `--quiet`, `--hidden`, `--no-ignore`, `--color=never`, `-A`, `-B`, `-C`, `--after-context`, `--before-context`, `--context`, `-w`, `--word-regexp`, `-o`, `--only-matching`, `-t`, `--type`, `--`: **data** | `--pre`, `--pre-glob`: **executor/refuse**; known non-executing options are data, ambiguous/invalid boundaries refuse. |
| `echo` | `-n`, `-e`, `-E`: **data**, with Bash echo option/escape rules | Output consumed by a shell or executed redirect destination is code. |
| `printf` | Literal format and arguments, `--`: **data** | `-v`: **context/refuse**, dynamic assignment targets and `%n` variable targets refuse. Format escapes cannot hide emitted code from consumer accounting. |
| `cat` | `-n`, `--number`, `-b`, `--number-nonblank`, `-s`, `--squeeze-blank`, `-E`, `--show-ends`, `-T`, `--show-tabs`, `-v`, `--show-nonprinting`, `-A`, `--show-all`, `--`: **data** | A shell/eval/source consumer makes emitted bytes executable. |
| `jq` | `-r`, `--raw-output`, `-R`, `--raw-input`, `-s`, `--slurp`, `-n`, `--null-input`, `-c`, `--compact-output`, `--arg`, `--argjson`, `-f`, `--from-file`, `--`: **data** for a literal non-loading filter and data arguments/files | `-L`, module `import`/`include`, unknown filters/options: **refuse**. |
| `sed` | `-n`, `--quiet`, `--silent`, `-e`, `--expression`, `-f`, `--file`, `--`: **data**, but only literal print-only `p` scripts with numeric/range or literal regex addresses | `e` command or `s///e`: **executor/refuse**. Unknown/read/write scripts and unverified script files refuse. |
| `awk`, `find` | Not admitted as candidate data readers | awk `system`, pipe/getline command forms; find `-exec`, `-execdir`, `-ok`, `-okdir`: **executor/refuse**. Every other option/form refuses in candidate-consuming uses. |

Literal message operands, quoted heredoc messages and literal data-only logging
are allowed; nested `$()`, backticks and process substitutions remain code even
inside double quotes or an unquoted heredoc. Expansion output passed to a proven
data operand is data only after its own execution has been checked.
Arithmetic expansion/evaluation and indirect references (`${!x}`, `declare -n`,
`printf -v` targets) carrying candidates refuse. Arrays and namerefs are not
implicit constant propagation.

### Wrappers, shell programs and execution contexts

| Form | Closed option grammar / effect |
| --- | --- |
| `command` | `--` transparent; `-p` **context** requires verified program resolution; `-v`, `-V` **data**, lookup only. |
| `builtin` | No options; only supported builtins, otherwise refuse. |
| `exec` | `--` transparent, `-a NAME` **data**, `-c` **context** clears environment; successful invocation terminates the caller. |
| `env` | `--`, `-i`/`--ignore-environment`, `-u`/`--unset NAME`, literal assignments: **context**; `-C`/`--chdir DIR`: **context**; `-S`/`--split-string`: **executor**, decode/reparse exact env splitting or refuse. |
| `time` | Reserved-word `-p` **data**; external time and other options refuse. |
| `nice` | `-n`/`--adjustment NUM`, `--`: **context**, then transparent argv. |
| `nohup` | `--`: transparent with understood stdin/stdout redirection effects; other options refuse. |
| `timeout` | literal duration, `-s`/`--signal`, `-k`/`--kill-after`, `--preserve-status`, `--foreground`, `--`: **context**; possible termination is retained. |
| `stdbuf` | `-i`, `-o`, `-e` and long `--input`, `--output`, `--error` values: **context**, transparent argv. |
| `sudo` | `-u`/`--user`, `-g`/`--group`, `-D`/`--chdir`, `-p`/`--prompt`, `-n`/`--non-interactive`, `--`: **context**. Identity/HOME/cwd effects require proof; `-i`, `-s` and unmodeled options refuse. |
| `bash`, `sh` | Literal `-c PAYLOAD [NAME [ARGS...]]`: **executor**, reparsed with invocation positional arguments; plain literal stdin/heredoc and `-s` here-string payload likewise. `--`, `--noprofile`, `--norc`: **context**; `-l`, `--login`, `-i`, `-O`, `-o`, startup/script-file modes refuse unless their full effects are proven. `$@` forwarding and opaque payloads refuse. |
| `eval` | Literal arguments joined according to eval's rules and reparsed (**executor**); opaque operation-visible forms refuse; only operation-invisible dynamic eval is residual. |
| `cd` | `-L`, `-P`, `-e`, `--`: **context**; literal path or no argument with proven effective HOME. Track success/failure separately. |
| `pushd`, `popd` | No options, literal path or bounded numeric stack operand: **context**; unknown stack refuses. |
| `:`, `true`, `false` | No options, known status; expansions still execute. `exit` with literal status terminates; `return` with literal status terminates only the function. `break`/`continue` with literal bounded level affect the modeled loop. Other forms refuse. |
| `trap`, `source`, `.`, alias definitions | **executor/refuse** when carrying visible candidate payloads. Literal traps may instead be fully modeled only if every firing point is checked; no data exemption. |
| `xargs`, `find`, unknown wrappers/interpreters | **executor/refuse**; never just strip the prefix. Includes `strace`, `script`, `numactl`, `nsenter`, `systemd-run`, `tmux`, `uv`, Python, SSH, Docker, `chrt`, `taskset`, `prlimit`, `parallel` and `watch -x` candidate-consuming forms. All their options are **refuse**; examples do not constitute a deny-list. |

Supported AST contexts: simple commands, lists (`;`, newline, `&&`, `||`, `!`),
if/elif/else, bounded literal case alternatives, constant/bounded for/while/until,
brace groups, subshells, pipelines, command/process substitutions, background
commands and plain/named coprocesses. Each nested execution receives a copy of
state. Background execution contributes possible invocations, not parent cwd.
Pipelines run elements in subshells by default; `lastpipe`, job control and
other relevant option differences must be proven or the dependent operation
refuses. Parse errors do not prove unreachability: Bash can execute a valid
prefix before reporting a later syntax error.

Functions require bounded summaries of cwd, status and termination edges.
Directory-only functions can be understood; functions forwarding operation
arguments through `$@` refuse under this decision. Recursion, alias expansion,
dynamic names without a proven finite safe set, and arbitrary shell-option
mutations refuse. Limits remain bounded (existing depth/work bounds are a floor);
budget exhaustion is not a partial successful scan.

## Redirect and dynamic-word rules (amendments 3, 4 and 6)

All prefix/suffix redirect expansions execute in their actual shell scope.
FD duplication and redirection do not turn a command into data or change cwd.
Quoted heredoc bodies are literal; unquoted bodies are scanned for expansions.
Here-strings feeding a shell/source are code.

Written candidate text is data only when its target is a literal path, all
later readers in the submitted command are admitted data readers, and the path
is not an executed location. Shell startup files, `.git/hooks/*`, git config,
gh config and their resolved aliases/symlinks refuse. A dynamic/ambiguous target
refuses. `echo 'git ...' > x.sh; bash x.sh` refuses; a later source/eval or unknown
consumer likewise refuses. Plain output to an ordinary literal notes file may
allow; no future command is presumed part of this submitted command.

A dynamic word in option position represents ANY option; an unquoted dynamic
word can represent ANY NUMBER of words (splitting/globbing). For global Git
options, checkout/switch/branch/worktree and gh pr merge this refuses unless all
possibilities are permitted and context remains proven. `--` can establish a
read-only data boundary but cannot salvage a dynamic operation/subcommand.
Recognized read-only subcommands may take dynamic revisions/search arguments
when executable customization is excluded. Unknown/dynamic subcommands refuse.

A dynamic command name with literal first operation `checkout`, `switch`,
`branch`, `worktree`, or literal `pr merge` refuses even if the source never
spells git/gh: `G=gi; ${G}t checkout -b x`. The operation-shape trigger examines
AST roles; identical text in a printf operand is not a command name.

## Directory, reachability and repository/target binding

Carry a set of `(cwd, repository, worktree-kind, current-branch, environment,
directory-stack, status, reachable)` states. Unknown is not primary or safe.
Resolve logical/physical cd semantics, symlink parents, CDPATH, OLDPWD,
effective HOME, env -C and repeated git -C separately. Global git repository
overrides and `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`
require binding or refuse dependent policy. `GIT_SSH_COMMAND`, `GIT_PAGER`,
`GIT_EDITOR`, `PAGER`, `EDITOR`, `GH_PAGER`, `BROWSER` are executor environment:
visible candidate values refuse, otherwise disable/prove their relevant effects.
Never use the hook process's HOME in place of a command-local assignment.
Unknown repository state cannot establish allowance. Filesystem probes can bind
current state; absence is not a structural guarantee of future cd failure.

| Six reviewed forms | Required success/failure treatment |
| --- | --- |
| `cd X || exit; git ...` | Allow a verified worktree success edge; failure terminates before Git. Check substitutions and exit traps independently. |
| `if cd X; then :; fi; git ...` | Retain original cwd on failure and X on success. Refuse from primary with uncertain cd; allow only if every reachable state permits the operation (e.g. both worktrees). |
| `f(){ cd X; }; f; git ...` | Sound directory-only summary retains failed cd; otherwise refuse. Original primary remains a prohibited possibility. |
| Loop that never runs | Allow only structurally constant-false condition without executable expansions; run-once or expansion counterpart must be checked. |
| `cd /missing && git ...` | Refuse when missing is only a filesystem observation. Allow only structurally proven unreachable RHS. The Opus amendment removes the earlier unconditional benign label. |
| `git worktree add ... && cd ... && git ...` | Allow only with a sound successful-creation model bound to the repository; this freeze chooses the explicitly permitted compound refusal. A separate invocation in the subsequently verified worktree must allow. |

For gh pr merge, consume ALL option values before finding the sole positional
selector. `--subject 7 5` and `-t 7 5` target PR 5, not 7. Honor short attachment,
clusters, `=` values, `--`, Boolean false spellings and repeated options with
last-value semantics. An absent selector requires proven current-branch PR
resolution; ambiguous multiple selectors or discovery failure refuse.
`--match-head-commit` is never a selector. Resolve the effective repository from
explicit `-R`/`--repo` (last occurrence), then command-local/inherited `GH_REPO`,
then cwd discovery. Include host in identity. A PR URL must agree with the
effective repository or refuse; never silently judge a different repository.
Both merge and admin judgments must use the same `(repository, PR, head)`.
Admin must check failing blocking checks on that target, not the subject value.
Unavailable lookups refuse. Frozen probe metadata uses synthetic local
repository identities and red CI; no GitHub mutations occur.

Branch-policy correction: `checkout main`, `checkout -- file`, `branch -d
merged`, and `branch --list` in the primary are **allow** under the existing
hook's policy. `git branch new` and `git branch -D x` also allow under the existing policy.
Checkout/switch with branch-creation flags, switching away from main, detach,
orphan and the existing guarded force forms block. Git branch creation/deletion
alone is not a newly prohibited operation. New corrected rows retain these four commands;
no historical row or label is edited. The old oracle's `guarded()` broadly
counts any checkout/branch invocation as prohibited, which is a scoring defect,
not permission to change the frozen labels. It also counts deliberate refusals
as over-blocks when Bash happens not to execute a guarded operation.

## Typed dispositions and diagnostics

`allow` means every occurrence accounted for and every reachable policy allows;
`block` means a recognized operation violates policy; `refuse` means proof is
insufficient. Precedence across reachable states: block when ANY reachable state
is a known violation; otherwise refuse when ANY state is unknown; otherwise
allow. No sampled Bash outcome proves another failure edge unreachable.
Append-only rows `freeze-b-precedence-correction-000/-001` supersede
`freeze-six-benign-003/-005`, retaining the originals as history with a correction
reason. Append-only `freeze-g-precedence-completion` rows supersede 002/004 as block:
the failed-cd edge retains the known primary cwd. A known prohibited edge wins
over other unknown edges; it does not require that cd actually fail in the probe. Block and refuse exit
2, allow exits 0. Do not conflate them in acceptance scoring. Refusals carry a stable class and actionable repair:

| Reason class | Meaning / repair |
| --- | --- |
| `UNKNOWN_EXECUTOR` | Candidate consumed by unsupported program. **Run the git command directly in the verified worktree** (or use the typed publisher for merge), then retry. |
| `DYNAMIC_OPERATION` | Dynamic subcommand or option can alter policy; use explicit literal argv. |
| `DYNAMIC_COMMAND` | Dynamic name with guarded operation arguments; use literal git/gh. |
| `FORWARDED_ARGUMENTS` | `$@` operation forwarding; invoke the operation directly. |
| `ALIAS_EXECUTION` | Alias/custom command semantics unknown; expand into a direct command. |
| `VISIBLE_SOURCE` | Visible code consumed by source/eval/startup location; run the literal operation directly. |
| `EXECUTOR_OPTION` | Reader/config/environment option executes text; remove it and invoke explicitly. |
| `INDIRECT_REFERENCE` | Arithmetic, nameref or indirect assignment carries code; use direct argv. |
| `EXECUTED_REDIRECT` | Written text can execute; use separate direct operation. |
| `DYNAMIC_REDIRECT` | Destination unknown; use an ordinary literal data file. |
| `UNKNOWN_CONTEXT` | Cwd/status/HOME/options/stack unresolved; split and verify the worktree. |
| `UNKNOWN_REPOSITORY` | Git/GH repository binding unresolved; specify and verify it. |
| `UNKNOWN_TARGET` | PR/ref selection unresolved; specify the target. |
| `CREATION_COMPOUND` | Future worktree binding unproven; create it, then run a separate verified command. |
| `UNACCOUNTED_OCCURRENCE` | Source interval lacks exactly one classification; simplify the command. |
| `PARSE_INCOMPLETE`, `DECODE_FAILURE`, `LIMIT_EXCEEDED` | Incomplete syntax, decode failure or bounded budget exhausted; simplify the command. |
| `RUNTIME_UNAVAILABLE` | Import/construction/walk/resolution or interpreter failure; run the documented project-interpreter repair and retry. No old-scanner fallback. |

## Denominator, ground truth and acceptance

The companion frozen manifest lists hashes and exact family counts. Original
oracle rows and traffic subjects are byte-semantically preserved. New oracle
rows use `expected: {disposition, reason_class, target?}`, `hooks`, and `bash_truth`.
A target is `{repository: "HOST/OWNER/REPO", pr: "NUMBER"}`. The round-2
identity/Boolean/environment and merge/admin misparse rows require target equality
at the lookup seam; only that gold target returns red CI, all others return green.
The merge seam is `_pr_snapshot`, so the hook's own selector/repository parser is
exercised; admin records the actual PR/repository passed to its checks seam.
Wrong PR, repository, host or cwd, or a missing required judgment, fails acceptance
even if a separate guard happens to exit 2. Expected refusals with conflicting URL
and repository must reject before judging an inconsistent identity.
Legacy no-target rows keep their original red stub and raw scoring; they cannot
supply exact-target proof. Target metadata and recordings are independently frozen;
no hook parser computes the gold expectation.
The additional traffic fixture extends the row schema rather than converting
the legacy string list. Ground truth records physical cwd, argv, return code,
whether a guarded operation was seen, and any probe limitation beside each
label. Probe setup is frozen separately; temp paths are normalized to
`<probe>`. Only Git/GH are recording fakes; real Bash and available executor
programs determine execution. A Python launcher selects the prescribed real
interpreter; it does not emulate Python. Git internal executor probes delegate
to a real scratch repository while recording nested git calls; the gh alias
adapter models alias expansion. Repository/PR metadata derives from documented
CLI option roles and recorded argv/environment, not a real GitHub mutation.
Unavailable host facilities never count as a proved non-executing shape.

Ground truth is descriptive. A required refusal is not contradicted by a
single safe/non-executing run: uncertainty is itself the prescribed reason.
Any actual required allow that executes a prohibited operation is a
decision-versus-Bash conflict and blocks implementation pending reconciliation.
The six reviewed forms and failure counterparts are reported separately from
traffic. Historical labels cannot be lowered to obtain passing results.

Round-2 freeze verification in the assigned dispatch worktree:

- `timeout 120 <project-interpreter> -m pytest tests/test_guard_understood_freeze.py
  tests/test_guard_benign_corpus.py tests/test_shell_redirects.py -n 2 -q`:
  **1,531 passed, 1 failed** in **27.64 s**, exit **1**. The sole failure is
  `test_pinned_real_bash_oracle`. No test was skipped, xfailed or weakened.
- That pinned oracle reports **1,431** non-residual rows, **81** raw misses,
  **22** raw over-blocks, **50/50** prefix argv observations, **1,200** legacy
  traffic cases with **0** traffic blocks; **3** accepted residual rows remain
  separate. Raw over-block scoring still includes the legacy defects described above.
- All **829** post-legacy freeze rows: **580** exit/target matches and **249**
  mismatches. On just the **352** round-2 appended rows: **317** matches and
  **35** mismatches. There are **17** wrong-target judgments and **8** missing
  required target judgments. Exit-only matching on the appended rows is
  **326/352**: **16** required blocks and **10** required refusals are allowed;
  **0** required allows are blocked. Typed reason/disposition compliance beyond
  the exit decision remains unverified until implementation.
- Everyday traffic is **66** distinct commands / **198** hook cases, all
  currently allowed. The earlier **60** inspection commands / **180** hook
  cases and all **1,082** prior oracle rows remain intact; the complete oracle
  is **1,434** rows. Only new rows carry corrections and their reasons.
- `ruff check scripts/hooks/bash_oracle.py tests/test_guard_understood_freeze.py`:
  **All checks passed!** Target mutation tests reject the wrong PR, repository,
  host, initial cwd and omitted judgment even when the hook exits 2.

`tests/test_shell_redirects.py::test_pinned_real_bash_oracle` is expected to FAIL
on this branch: the approved implementation remains unchanged, while the freeze
requires refusals/accounting and exact-target checks it does not yet satisfy.
This expected failure is reported, never skipped, xfailed or used as approval.

Historical round-1 measurements (at `c968d99de0`) are superseded by the round-2
measurements, not implementation evidence for this enlarged denominator.
Namespace probes now use `nsenter -U --target $$ --wd=.`; the original invalid
no-namespace probes remain immutable history and are superseded by new rows.
Namespace entry may be unavailable and then remains unverified execution.
`docker --help 'git ...'` is a policy refusal because Docker is outside the
candidate-consumer grammar; help does not execute its argument. Its historical
absence-of-Docker limitation supplies no evidence of payload execution.
Systemd-run facility limitations also remain explicit, owned by claude-infra.

The recording fixture's round-2 fake reports physical cwd via `pwd -P` and uses
physical `cd -P` for Git `-C`. Command-p probes use environment-selected absolute
recording programs, so real `command -p` executes safely without exposing a live
Git/GH target. The dynamic program names retain the amendment-6 refusal; this
is not proof that an arbitrary default-PATH git/gh binary is trusted. The installed
moreutils `parallel -- 'COMMAND'` form executes the recording operation. Bounded
`timeout ... watch -x` probes record execution before termination.

The legacy scoring defects are documented above rather than corrected in this
freeze. Implementation must consume the typed expected fields and preserve
the denominators. A hash/fixture-loading check cannot supply held-out review or
demonstrate implementation acceptance.

Acceptance after implementation:

- Zero unsafe allows and zero wrong-target/repository/cwd judgments outside
  **only** the three residual classes below.
- At most four over-blocks on the frozen oracle. Intentional typed refusals are
  correct, not over-blocks. Required search/inspection forms must all allow.
- Zero blocks in all 1,200 legacy traffic cases and the additional frozen
  search/inspection and everyday Git/GH traffic families; benign baseline
  decisions unchanged.
- Exact pins/hashes (`tree-sitter==0.26.0`, `tree-sitter-bash==0.25.1`), actual
  deployed project-interpreter execution, bounded fault handling, occurrence
  deletion/data misclassification/context mutants caught, and retained
  silent-misparse coverage. No parser/scanner fail-open fallback.
- Independent reviewer-held-out shapes are chosen before implementation review
  and recorded by that reviewer. This author's freeze is not held-out proof.
  No such new independent implementation proof exists in this packet.

Three accepted residual classes, stated exactly:

1. **operation-invisible dynamic `eval`**
2. **sourced scripts whose operation is absent from the submitted command**
3. **REST merges**

Owner: **claude-infra**. Visible sourced payloads are not residual 2. Dynamic
command names with guarded literal arguments are not residual 1. No new class
is accepted. At most two implementation-review rounds; unresolved visible
bypasses, wrong-context judgments or required benign regressions block. New
classes after that return for a designated decision on a narrower typed
execution interface, never a larger residual budget.

References used for semantics: [Bash escape rules](https://www.gnu.org/software/bash/manual/html_node/Escape-Character.html),
[Bash lists](https://www.gnu.org/software/bash/manual/html_node/Lists.html),
[Git invocation](https://git-scm.com/docs/git),
[gh pr merge](https://cli.github.com/manual/gh_pr_merge).
Installed Bash recording is the local execution evidence; documentation
establishes option roles, not hook approval or real target CI status.

## Implementation round 1 freeze amendments

The operator ordered executor-option completion, zero-lookups URL/repository
conflict refusals, the known-primary precedence corrections, a loop returning
to primary, and executable namespace probes. New rows supply these amendments;
all historical rows and labels remain immutable. The namespace command is
`unshare -U sleep 3 & nsenter -U --preserve-credentials --target $! …`;
its ground truth comes from recording fake binaries in temporary repositories.
The three systemd-run probes remain an environment gap owned by claude-infra.
Conflict corrections require `targets == []`, before any CI judgment.

## Designated clarification 2026-10-03: amendment 6 applies per hook

Amendment 6’s operation-shape trigger and `DYNAMIC_COMMAND` refusal apply per hook: merge handles literal `pr merge`; admin handles an enabled or indeterminate admin-merge shape; branch handles branch-operation shapes when a protected-primary context remains possible. A proven worktree does not acquire a branch prohibition from this trigger alone. Other accounting and refusal rules remain binding.

The earlier blanket dynamic-name sentence is superseded by this clarification.
New `per-hook-clarification` rows supersede every affected historical row,
including merge rows 001/004/007/010. `per-hook-table` records all five
commands in the approved table, plus the verified-worktree switch counterpart,
using recording fake binaries in temporary repositories. If guard-pr-merge
is absent or disabled, ordinary merges lose their responsible guard; sibling
hooks do not replace its readiness enforcement.
