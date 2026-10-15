# Guard hooks: understood forms (#9484)

## Scope

The branch, PR merge and admin merge guard hooks account for visible Git and
GitHub CLI operations. They allow normal literal messages, search, inspection
and safe worktree commands. They are fail closed: a form whose effect cannot be
established is refused, never allowed by default.

Every guard judges the same candidate gate and uses the same pinned AST reader
for shell structure. Hook policy is separate from that reader.

## Closed allowlist (#10521 ruling, 2026-10-15)

This section supersedes every later description of reachability pruning,
function summaries, loop modelling and `cd ... || exit` modelling. The reader
no longer models control flow.

**Threat model (frozen).** A well-meaning or confused agent emits one Bash
command line; the hook payload supplies that line and its cwd. The hooks are a
discipline gate, not a sandbox. Out of scope, recorded as residuals: encoded
payloads, scripts on disk, harness and profile state, concurrent processes and
API merges (`gh api`).

**Order.** `shell_bash.read_commands` works in a fixed order, and every refusal
carries a typed reason class:

1. Parse, repairing only known grammar-0.25 misparses. Any parse error, and any
   node kind outside `GRAMMAR_NODES`, refuses.
2. Refuse shell-binding changes unconditionally, operation visible or not:
   `alias`, `unalias`, `BASH_ALIASES`/`BASH_CMDS` writes, `hash`, `enable`,
   `shopt`, `set -k`, `set -o posix`, `bash --posix`, `POSIXLY_CORRECT`, and
   assignments with a computed variable name.
3. Account for every simple command in the unpruned tree: function and loop
   bodies, substitutions, literal shell payloads, here-strings and heredocs fed
   to shells, `eval` and `trap` payloads.
4. Detect every guarded operation in that same tree.
5. Admit only the written grammar (below).
6. Only then establish context: the payload cwd, or one leading
   `cd <literal> &&`. No filesystem probe or network lookup happens earlier.

**Admitted grammar.** Every top-level item up to and including the last guarded
operation may contain only the node kinds in `shell_bash.ADMITTED_NODES`:
simple commands, pipelines and redirections of literal or plain-parameter
words. A guarded operation inside any compound construct (subshell, group,
`if`, loops, `case`, `!`, substitution, shell payload), or any function
definition in the command, refuses. A function definition next to text shaped
like a guarded operation also refuses, because a definition can rebind the word
that consumes that text.

Before the last guarded operation only these may run: Git subcommands that
write no config or remotes; read-only `gh`; `echo`, `printf` (no `-v`), `true`,
`:`, `test`, `[` and `pwd`; and one leading `cd <literal> &&`, with no `;` or
`||` after it and CDPATH unset. No assignments or `export` there. A merge with
anything before it must name the PR, `--repo` and `--match-head-commit`.
Commands after the last guarded operation cannot change it and are not judged
for context.

**Triggers.** Blockable operations only: non-path `checkout` and `switch`,
forced branch forms, `symbolic-ref HEAD <ref>`, `bisect` steps, `rebase`,
`pr merge` including `--admin`, and the publisher's `pr-merge`. Read-only forms,
`worktree add`/`remove` and quoted data mentions are not triggers.

**Kept from main.** Nothing that `origin/main` blocks becomes allowed (AC-02).
The branch guard keeps main's deliberate case/parameter over-block, and the
merge guard keeps main's line-reader block for merge text it cannot read. #10541
owns unblocking the benign forms.

**Harness shell state (item 6).** The "run it in separate Bash tool calls"
repair is offered only where isolation is proven. Claude Code was probed on
2026-10-15: a function, alias and export from one call were absent in the next;
`git` and `gh` resolved to files; `cd`, `pushd`, `popd`, `command` and `builtin`
resolved to builtins. No other harness has been probed, so elsewhere the repair
names `git -C <worktree>` instead.

**Evidence.** `tests/test_guard_entry_point_matrix.py` holds one reproducer per
class per hook, plus the `bash_oracle` replay.
`tests/test_guard_closed_grammar_heldout.py` holds a 350-row synthetic corpus
with frozen `origin/main` decisions: every main block stays blocked, and every
branch-only refusal is enumerated with its ruling item. The frozen oracle's
`closed-allowlist-ruling` rows and `bash_oracle.RULED_OVERBLOCKS` enumerate
the over-refusals. The 1,200-row traffic replay stays at zero blocks.

**Known over-refusals against main.** All are listed, not relabelled:

- Merges and switches after `;`, newline or `||` `cd` chains.
- Merges and switches inside subshells, payloads, loops and conditions.
- Commands that are not admitted before an operation (for example
  `gh pr comment && gh pr merge`).
- A merge after an admitted command without an explicit target.
- Benign binding changes (`shopt -s lastpipe`, `alias`, `hash -p`,
  `BASH_CMDS`).
- `bash --posix`.
- Definitions next to operation text.
- `a && b 2>&1 | c`, where grammar 0.25 nests the list inside the pipeline.

**Residuals.**

| Residual | Owner |
| --- | --- |
| Primary-checkout branch switch from anything outside Bash | `reference-transaction` hook, a new architecture needing designated approval |
| Admin merge | Server-side "no bypass" on the protected branch (operator) |
| Encoded payloads, scripts on disk, harness and profile state, concurrent processes, `gh api` merges | Out of scope by the frozen threat model |
| Persistent-shell behaviour of Codex, Grok, AGY and Cursor | Untested |
| Shell snapshot contents | Untested |
| Cost of the computed-name rule | Unmeasured |
| Replay of the 699 real guarded commands | Scripts no longer on disk; infra lane |

## Candidate gate and source accounting

All three hooks use one gate. Bash-aware backslash-newline joining keeps a
byte-range map back to the submitted command. Joining happens only where Bash
removes the escape pair: not inside comments, single quotes or quoted heredoc
bodies. Unquoted heredocs follow Bash expansion rules, and their executable
expansions are inspected. ANSI-C quotes, escaped spellings and literal word
concatenation are decoded. Decode errors refuse. Backslashes are never removed
globally and quoted data is never normalised.

A candidate is any possibly executable `git` or `gh` occurrence, including
decoded, concatenated and escaped spellings, plus typed publisher invocations.
An operation word is not required next to the program name. A dynamic command
name whose literal arguments have a branch-operation or `pr merge` shape is also
a candidate, as described under [Per-hook judgment](#per-hook-judgment).
Literal occurrences in data are still accounted for; the consumer decides
whether they are allowed. A command with no candidate keeps the ordinary
unrelated-command allowance.

Every candidate is assigned exactly once, by source byte interval and consumer.
An AST word may carry several mapped intervals, and concatenation never drops
them. Nested payloads inherit their parent's source map. A quoted mention and a
real invocation with identical text are different occurrences. Redirect words
are inspected as well as command nodes. Missing or duplicate coverage, error
nodes, unparsed trailing bytes, reserved words misread as arguments, decode
failures and exhausted limits refuse the whole candidate.

| Category | Required proof |
| --- | --- |
| Recognized invocation | Complete literal program and subcommand with classified argv. Understood wrapper or context. Every reachable cwd, repository, selector and policy is checked. |
| Proven non-executing data | Literal bytes in an explicitly admitted operand. Every expansion is walked separately, and every later consumer is a known data reader. |
| Proven unreachable code | Structural termination or a constant condition, with no executable expansions and all success and failure edges modelled. |
| Unclassified | The whole command refuses with a typed reason. Unknown or dynamic command identities refuse. |

Definitions and assignments are tracked by use. A variable is data only when
every use in the submitted command is a recognised data operand. Dynamic
invocation arguments can be read-only data, but they never erase a candidate's
source provenance.

## Closed grammar and option classes

Option classes:

- **data**: consumes non-executing literal or text operands.
- **executor**: consumes or supplies code.
- **selector**: chooses the operation, target, ref or policy mode.
- **context**: changes cwd, repository, environment or process state.
- **refuse**: outside the admitted grammar.

Closed option tables cover only the policy-relevant forms: branch switching and
creation, worktree operations, `gh pr merge` (including admin forms), and
executor-capable options and subcommands. They are not an exhaustive allowlist
of Git or GitHub traffic. Other known built-in subcommands are recognised under
the generic executor, configuration, environment and alias rules. Their ordinary
arguments are data unless an executor option applies. Unknown or dynamic
commands, aliases and unsupported executors refuse.

In a closed policy grammar, unlisted options, abbreviations, unknown clusters,
response files, negations, missing values and ambiguous boundaries refuse. A
literal executable path must resolve to a verified supported program; a basename
match alone is insufficient. Options that take values accept separate and
`--long=value` spellings only where the program supports them. Short attachment
and clustering are decoded with that program's own rules.

### Git and GitHub CLI

Git global options:

- `-C` (attached form included, applied left to right), `--git-dir`,
  `--work-tree`, `--namespace` and `--bare` are **context**. They require a
  proven repository binding or refuse.
- `--no-pager` is **context** and disables paging.
- `--paginate` and `-p` are **executor** and refuse in candidates.
- `-c` is **context** only for a literal allowlist of display and pager keys
  with literal values. Every other key or value is **executor/refuse**, including
  aliases, hooks and transports.
- `--config-env` is **executor/refuse**.
- Executable-path and info-path overrides are **context/refuse**. Terminal
  inspection forms (`--version`, `--help`, `-h`) are **data**.
- Pathspec mode flags are **selector**.

| Git subcommand | Admitted options and classifications |
| --- | --- |
| `checkout`, `switch` | Branch creation and reset flags, detach, orphan, tracking, merge, force, ref and start-point options: **selector**. Quiet and progress flags: **data**. `--` ends options and establishes path checkout only when its structural position is proven. Positional refs and paths are **selector**. |
| `branch` | Delete, move, copy, force, list, scope, containment, upstream and display-filter options: **selector**. Verbose, format, sort, colour and quiet options: **data**. Refs are **selector**. `--edit-description` is **executor/refuse**. |
| `worktree` | `list`: display options are **data**. `add`: branch and checkout options are **context/selector**; quiet is **data**. Creation compounds refuse unless the success edge is proven and bound. `remove`: literal directory is **context**; force is **selector**. A successful removal invalidates that directory binding for later commands. Other verbs **refuse**. |

For other Git built-ins, the roles below are examples, not closed allowlists.
Ordinary revision, path, search, format, message and transport arguments are
data. This covers read commands such as `log`, `diff`, `ls-files`, `rev-list`
and `remote -v`, and write commands whose arguments are plain data. Fetch and
push options for upstreams and force-with-lease stay recognised and are judged
by the existing push policy. These hooks add no push-policy restriction. Commit
messages, message files and trailers are data.

Executor semantics still bind. Options that run code supplied in the command
refuse for candidates unless modelled. Examples are rebase exec, bisect run,
submodule foreach, external diff and tool options, transport helper options,
archive exec, filter-branch filters, mail hooks and merge-tool hooks. Pager,
editor, signing, hooks, custom strategies, interactive editing, external diff,
textconv, executable configuration and alias options are never presumed data.
Configuration reads are data. Writes that supply executable configuration
refuse. A normal built-in operation does not refuse merely because its name or an
ordinary option is absent from the tables.

Read commands must account for applicable local configuration, pager, external
diff and textconv, aliases and environment. A candidate is never declared data if
executable customisation could consume it.

GitHub CLI inherited `-R` and `--repo` are **context** with validated literal
values. `--version`, `--help` and `-h` are **data** in terminal help forms.
`--hostname` is not admitted on these PR forms. Host identity comes from the
repository value or verified discovery.

| GH form | Admitted options and classifications |
| --- | --- |
| `pr merge` | Message and body options consume a value and are **data**. `--match-head-commit` is **selector** and consumes a value. Admin, auto, delete-branch and merge-method flags are **selector** Booleans. Help is **data**. `-R` and `--repo` are **context** and consume a value. The sole positional number, URL or branch is **selector**. |
| `pr checkout` | Branch, detach, force and submodule options are **selector**. `-R` and `--repo` are **context**. The PR operand is **selector**. |

Other known GH built-ins use the generic rules. These include `pr ready`, run
view and list, read-only `api` forms, and PR and issue view, list, diff, checks
and create. Literal body, title and message values, JSON, jq and template
arguments, search, limit and other ordinary arguments are data. Editor, web and
alias or custom-command execution require executor accounting when they consume
a candidate. An unknown or dynamic GH command refuses.

The typed project publisher `pr-merge` is a recognised invocation, not a generic
Python exemption. Its closed fields map to the same merge judgment: number and
match-head are **selector**, repository is **context**, subject, body and body
file are **data**, and terminal help is **data**. Other Python payloads refuse.

### Closed data-reader list

For `grep` and `rg`, known non-executing options and their operands are data.
Executor-capable options refuse. For the other readers, the closed forms below
are binding. Literal operands are data only after expansion and consumer checks.

| Program | Admitted options | Executor options and refused forms |
| --- | --- | --- |
| `grep` | Fixed-string, regex, line-number, case, pattern-file, recursive, list, count, context, word and only-matching options, and `--`: **data** | Ambiguous or invalid option boundaries refuse. |
| `rg` | Fixed-string, line-number, case, pattern, glob, file-listing, context, word, only-matching, type and quiet options, and `--`: **data** | Preprocessor options are **executor/refuse**. Ambiguous or invalid boundaries refuse. |
| `echo` | `-n`, `-e`, `-E`: **data**, with Bash echo rules | Output consumed by a shell or an executed redirect target is code. |
| `printf` | Literal format and arguments, and `--`: **data** | Variable-assignment options refuse. Dynamic assignment targets refuse. Format escapes cannot hide emitted code from consumer accounting. |
| `cat` | Display and numbering options, and `--`: **data** | A shell, eval or source consumer makes emitted bytes executable. |
| `jq` | Raw, slurp, null-input, compact, argument and file options, and `--`: **data** for a literal non-loading filter and data arguments | Library-path and module-loading options, and unknown filters or options: **refuse**. |
| `sed` | Quiet and script options, and `--`: **data**, but only for literal print-only scripts with literal addresses | Execute commands and substitution-with-execute: **executor/refuse**. Unknown, read or write scripts, and unverified script files refuse. |
| `awk`, `find` | Not admitted as candidate data readers. | System and pipe forms, and find's execution actions: **executor/refuse**. Other forms refuse in candidate-consuming uses. |

Literal message operands, quoted heredoc messages and literal logging are data.
Nested command substitutions, backticks and process substitutions remain code,
even inside double quotes or an unquoted heredoc. Expansion output passed to a
data operand is data only after its own execution has been checked. Arithmetic
evaluation and indirect references (`${!x}`, namerefs and indirect assignment
targets) that carry a candidate refuse. Arrays and namerefs are never treated
as implicit constant propagation.

### Wrappers, shell programs and execution contexts

| Form | Closed option grammar and effect |
| --- | --- |
| `command` | `--` is transparent. `-p` is **context** and requires verified program resolution. `-v` and `-V` are **data**, lookup only. |
| `builtin` | No options. Only supported builtins are admitted. |
| `exec` | `--` is transparent. `-a NAME` is **data**. `-c` is **context**. A successful invocation terminates the caller. |
| `env` | `--`, `-i`, `-u` and literal assignments: **context**. `-C`: **context**. `-S`: **executor**, decoded and reparsed exactly, or refused. |
| `time` | Reserved-word `-p` is **data**. External time and other options refuse. |
| `nice` | Adjustment option and `--`: **context**, then transparent argv. |
| `nohup` | `--` is transparent, with its stdin and stdout effects understood. Other options refuse. |
| `timeout` | Literal duration, signal, kill-after, preserve-status, foreground and `--`: **context**. Possible termination is retained. |
| `stdbuf` | Input, output and error buffer options: **context**, transparent argv. |
| `sudo` | User, group, chdir, prompt, non-interactive and `--`: **context**. Identity, HOME and cwd effects require proof. Login, shell and unmodelled options refuse. |
| `bash`, `sh` | Literal `-c PAYLOAD [NAME [ARGS...]]`: **executor**, reparsed with the invocation's positional arguments. Plain literal stdin, heredoc and here-string payloads are likewise reparsed. Login, interactive, option-setting and script-file modes refuse unless their effects are proven. Forwarded `$@` and opaque payloads refuse. |
| `eval` | Literal arguments joined by eval's rules and reparsed (**executor**). Opaque forms whose operation is visible refuse. |
| `cd` | `-L`, `-P`, `-e` and `--`: **context**. Requires a literal path, or no argument with proven effective HOME. Success and failure are tracked separately. |
| `pushd`, `popd` | No options. Literal path or bounded numeric stack operand: **context**. Unknown stack refuses. |
| `:`, `true`, `false` | Known status. Expansions still execute. `exit` never ends analysis, because a function can shadow it. `return` with a literal status terminates the function. `break` and `continue` with a bounded literal level affect the modelled loop. Other forms refuse. |
| `trap`, `source`, `.`, alias definitions | **executor/refuse** when they carry a visible candidate. A literal trap may be modelled only if every firing point is checked. |
| `xargs`, `find`, other wrappers and interpreters | **executor/refuse**. The prefix is never stripped. All their options refuse for candidate-consuming forms. Fixed `echo` and `printf` logging stays inert. |

Supported AST contexts are simple commands, lists (`;`, newline, `&&`, `||`, `!`),
if/elif/else, bounded literal case alternatives, constant or bounded loops,
brace groups, subshells, pipelines, command and process substitutions,
background commands and coprocesses. Each nested execution receives a copy of
the state. Background execution contributes possible invocations, not a parent
cwd change. Pipeline elements run in subshells unless the shell option that
changes this is proven, otherwise the dependent operation refuses. A parse error
does not prove unreachability, because Bash can execute a valid prefix before it
reports a later syntax error.

Functions carry bounded summaries of cwd, status and termination. A directory-only
function can be understood. A function that forwards operation arguments through
`$@` refuses. Recursion, alias expansion, dynamic names without a proven finite
safe set, and arbitrary shell-option changes refuse. Depth and work limits are
enforced, and budget exhaustion is never treated as a partial successful scan.

A definition can change what any later word runs, including `cd`, `pushd`,
`popd`, `builtin`, `command`, `enable` and `git` itself. No judgment of a guarded
operation adopts a builtin's semantics from a name that may be shadowed (#10521
ruling, 2026-10-14T21:20Z). Definitions are
found structurally anywhere in the command, regardless of execution order: both
function syntaxes, nested bodies, command substitutions, literal `bash -c`,
`eval` and `trap` operands, `alias`, `enable`, and `BASH_ALIASES` or `BASH_CMDS`
bindings. No list of shadowable names is used. When the command also contains
the hook's own operation, it refuses with `ALIAS_EXECUTION` before any directory
is inferred. This includes an operation inside a definition body, because Bash
runs bodies from traps and `command_not_found_handle`. Alias bindings, and
`trap` or `eval` operands that cannot be read, refuse whenever a hook engages.
Alias text can turn any later word into an operation. The repair is to run
definitions and the guarded operation in separate Bash tool calls, with
`git -C <worktree>` in the guarded call. Separating them with a semicolon inside
one call does not count. Definitions without the hook's operation stay allowed,
and so does definition-like text inside arguments.

## Redirects and dynamic words

Prefix and suffix redirect expansions run in their real shell scope. File
descriptor duplication and redirection do not change a command into data or
change its cwd. Quoted heredoc bodies are literal. Unquoted bodies are scanned
for expansions. A here-string that feeds a shell or source is code.

Text written to a file is data only when the target is a literal path, every
later reader in the submitted command is an admitted data reader, and the path is
not an executed location. Shell startup files, hook directories, Git config, GH
config and their resolved aliases or symlinks refuse. A dynamic or ambiguous
target refuses. Text written to a file that a later source, eval or unknown
consumer reads refuses. Plain output to an ordinary literal file may be allowed.
The guards never assume that future commands are part of the submitted command.

A dynamic word in option position stands for any option. An unquoted dynamic word
can stand for any number of words, because of splitting and globbing. For global
Git options, checkout, switch, branch, worktree and `gh pr merge`, this refuses
unless every possibility is permitted and the context stays proven. `--` can
mark a read-only data boundary, but it cannot rescue a dynamic operation or
subcommand. Recognised read-only subcommands may take dynamic revision and search
arguments when executable customisation is excluded. Unknown or dynamic
subcommands refuse.

A dynamic command name whose first literal operation is `checkout`, `switch`,
`branch`, `worktree`, or `pr merge` refuses, even if the source never spells
`git` or `gh`. The operation-shape check uses AST roles. Identical text inside a
`printf` operand is not a command name.

## Directory, reachability and repository binding

Each command state carries a set of `(cwd, repository, worktree kind, current
branch, environment, directory stack, status, reachable)` values. Unknown is
never treated as primary or as safe. Logical and physical `cd` semantics, symlink
parents, CDPATH, OLDPWD, effective HOME, `env -C` and repeated `git -C` are each
resolved separately. Global repository overrides and `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_COMMON_DIR` and `GIT_NAMESPACE` must be bound or they refuse the dependent
policy. Visible candidate values of executor environment variables (pager,
editor, browser, and SSH command settings) refuse. Otherwise their relevant effects
are disabled or proven. The hook process's HOME is never used in place of a
command-local assignment. Unknown repository state cannot establish allowance.
A filesystem probe can bind current state, but a missing path is not a guarantee
that a future `cd` fails.

| Compound form | Required success and failure treatment |
| --- | --- |
| `cd X \|\| exit; git ...` | Refused (`UNKNOWN_CONTEXT`) before any directory is inferred: only one leading `cd <literal> &&` sets context (#10521 closed allowlist). |
| `if cd X; then :; fi; git ...` | Refused: a compound construct before a guarded operation is outside the admitted grammar. |
| `f(){ cd X; }; f; git ...` | The definition refuses (`ALIAS_EXECUTION`) before any directory is inferred. |
| Loop that never runs | Refused when the loop holds a guarded operation, whatever its condition: loops are not modelled. |
| `cd /missing && git ...` | Refused when the leading `cd` target is not a directory. |
| `git worktree add ... && cd ... && git ...` | Refused as a creation compound. A separate invocation in the verified worktree is allowed. |

For `gh pr merge`, all option values are consumed before the sole positional
selector is found. `--subject 7 5` and `-t 7 5` target PR 5, not PR 7. Short
attachments, clusters, `=` values, `--`, Boolean false spellings and repeated
options (last value wins) are honoured. With no selector, PR resolution from the
current branch must be proven. Ambiguous selectors and discovery failure refuse.
`--match-head-commit` is never a selector. The effective repository comes from
the last explicit `-R` or `--repo`, then command-local or inherited `GH_REPO`,
then cwd discovery. Host is part of the identity. A PR URL must agree with the
effective repository or the command refuses. Merge and admin judgments both use
the same `(repository, PR, head)`. Admin checks blocking checks on that target.
Unavailable lookups refuse.

### Branch policy

Within the primary checkout, these are allowed: `checkout main`, `checkout -- file`,
`branch -d merged`, `branch --list`, `branch new` and `branch -D x`. Creating or
deleting a branch is not a newly prohibited operation. These are blocked: checkout
or switch with branch-creation flags, switching away from main, detach, orphan,
and the existing guarded force forms.

## Judgments and diagnostics

`allow` means every occurrence is accounted for and every reachable state is
permitted. `block` means a recognised operation violates policy. `refuse` means
proof is insufficient. Across reachable states, the precedence is: block when any
state is a known violation; otherwise refuse when any state is unknown; otherwise
allow. A sampled Bash outcome never proves that a failure edge is unreachable. A
known prohibited edge wins over unknown edges, even if the probed `cd` would not
actually fail.

Block and refuse exit 2. Allow exits 0. Refusals carry a stable reason class and
an actionable repair:

| Reason class | Meaning and repair |
| --- | --- |
| `UNKNOWN_EXECUTOR` | Candidate consumed by an unsupported program. **Run the git command directly in the verified worktree** (or use the typed publisher for merge), then retry. |
| `DYNAMIC_OPERATION` | Dynamic subcommand or option can change policy. Use explicit literal argv. |
| `DYNAMIC_COMMAND` | Dynamic name with guarded operation arguments. Use literal git or gh. |
| `FORWARDED_ARGUMENTS` | `$@` forwards the operation. Invoke the operation directly. |
| `ALIAS_EXECUTION` | Alias, function or builtin-override semantics are unknown. Expand into a direct command, or run the definitions and the guarded operation in separate Bash tool calls with `git -C <worktree>`. |
| `VISIBLE_SOURCE` | Visible code consumed by source, eval or a startup location. Run the literal operation directly. |
| `EXECUTOR_OPTION` | A reader, config or environment option executes text. Remove it and invoke explicitly. |
| `INDIRECT_REFERENCE` | Arithmetic, nameref or indirect assignment carries code. Use direct argv. |
| `EXECUTED_REDIRECT` | Written text can be executed. Use a separate direct operation. |
| `DYNAMIC_REDIRECT` | Destination unknown. Use an ordinary literal data file. |
| `UNKNOWN_CONTEXT` | Cwd, status, HOME, options or stack unresolved. Split the command and verify the worktree. |
| `UNKNOWN_REPOSITORY` | Git or GH repository binding unresolved. Specify and verify it. |
| `UNKNOWN_TARGET` | PR or ref selection unresolved. Specify the target. |
| `CREATION_COMPOUND` | Future worktree binding unproven. Create it, then run a separate verified command. |
| `UNACCOUNTED_OCCURRENCE` | A source interval lacks exactly one classification. Simplify the command. |
| `PARSE_INCOMPLETE`, `DECODE_FAILURE`, `LIMIT_EXCEEDED` | Incomplete syntax, decode failure or exhausted budget. Simplify the command. |
| `RUNTIME_UNAVAILABLE` | Import, construction, walk, resolution or interpreter failure. Run the documented project-interpreter repair and retry. There is no fallback scanner. |

### Judgment line

A guard hook may emit exactly one stderr line: `GUARD_JUDGMENT ` followed by one
JSON object with exactly the keys `disposition` and `reason_class`. For `refuse`,
`reason_class` is one of the classes in the table above. For `allow` and `block`
it is `null`. The line carries no command text, target or private detail. Stdout
is not a judgment. Exit 0 means allow, exit 2 means block or refuse, and any other
exit is an execution failure. A duplicate line, a malformed payload, a duplicate
key, an unknown field or class, or an exit code that disagrees with the
disposition is a failure. A missing line falls back to the exit code and never
satisfies a required refusal or reason class.

The identity a guard uses (repository or host, PR, and working directory) must be
the one the command targets. A wrong or missing identity fails closed, even when
the exit code is 2. A target reported on the judgment line is never evidence on
its own.

## Per-hook judgment

Each hook judges its own operation. The merge hook handles a literal `pr merge`.
The admin hook handles an enabled or indeterminate admin-merge shape. The branch
hook handles branch-operation shapes when a protected primary checkout remains
possible. A proven worktree does not acquire a branch prohibition from the
dynamic-name trigger alone. No hook substitutes for another hook's judgment.

## Acceptance

- Zero unsafe allows.
- Zero wrong-repository, wrong-PR or wrong-cwd judgments.
- Zero blocks on benign traffic: normal literal messages, search, inspection,
  safe worktree commands and everyday Git and GH forms.
- Exact pins for the parser (`tree-sitter==0.26.0`, `tree-sitter-bash==0.25.1`),
  with the deployed project interpreter executing the hooks.
- Bounded fault handling. No parser or scanner fallback that fails open.

Forms outside the grammar above refuse. New admissions require a reviewed change
to this document.

References used for semantics: [Bash escape rules](https://www.gnu.org/software/bash/manual/html_node/Escape-Character.html),
[Bash lists](https://www.gnu.org/software/bash/manual/html_node/Lists.html),
[Git invocation](https://git-scm.com/docs/git),
[gh pr merge](https://cli.github.com/manual/gh_pr_merge).
