# Bash reader for Git and GitHub guards

The branch, PR merge and admin merge guards use `shell_bash.py` after their
raw command text gates. The reader uses `tree-sitter==0.26.0` with
`tree-sitter-bash==0.25.1`. The exact wheel hashes are in
`requirements-hooks.txt`; runtime pins also appear in the existing dependency
manifests. There is no repository `uv.lock`.

Install the parser into the canonical project environment, then deploy the
tracked hook sources:

```bash
uv pip install --python <canonical-checkout>/.venv/bin/python --require-hashes --only-binary=:all: -r requirements-hooks.txt
npm run agents:deploy
```

Shared settings resolve that interpreter through `run-project-python-hook.sh`.
Headless Claude settings pass the resolved interpreter explicitly. Codex's
existing hook runner already passes an explicit canonical interpreter. No
system-Python fallback is used for these guards.
Grok consumes the same headless settings; its bridge accepts the three pinned
interpreter/guard argv pairs without a shell and verifies the interpreter
against the canonical project resolver before execution.

The reader keeps possible working directories through commands, conditional
lists, substitutions, subshells and pipelines. Literal shell/eval/heredoc
payloads are parsed recursively. Dynamic command names and payloads, parser
errors and unsupported reserved-word shapes refuse a guarded command. Directory
or repository uncertainty is carried to each guard, rather than selecting a
repository by guess. Bash logical `cd` normalises parent components before
following symlinks; `cd -P` follows them physically. CDPATH, directory-stack
uncertainty and Git repository overrides remain conservative.

The existing branch policy's conservative refusal around `case` and parameter
parentheses remains. The parser identifies these through AST nodes. The PR guard
retains its refusal of dynamic redirects on an actual merge and its existing
raw-text process-substitution refusal. Queued heredocs on ordinary readers are
repaired using AST-identified openers; queued shell stdin is explicitly refused.

Shell alias and command-hash bindings refuse guarded candidates. Function
definitions are inert. Calls to functions containing visible guarded
operations, dynamic command names, indirect execution, or directory changes
(including through another function) are refused. Trap payloads are refused
because their execution time and directory are not established by registration.
Shell stdin from pipelines or process substitution is refused; literal
here-strings, here-documents and `-c` payloads remain recursively parsed.

`xargs` never acts as a removable prefix. Guarded candidates involving its input
or executable arguments are refused; fixed `echo`/`printf` logging commands remain
inert. Dynamic traps and traps calling guarded functions also refuse. `find`
execution actions, `setsid`, `flock`, `ionice` and other indirect
executors with visible operations are refused. `nice`, `timeout` and ordinary
`sudo` are read through explicit argument semantics, including `sudo -p` values.
`sudo -D`, login/remote modes, and `env -S` refuse guarded candidates rather than
guessing a target. Wrapper options remain scoped to their own utility.

Conditional and loop directory states remain conservative, including later loop
iterations. Shell option changes invalidate directory certainty. Redirected `cd`
retains its possible failure directory except where `&&` requires success before
the following command runs. Missing repository or worktree-probe evidence never
establishes safety. Depth and walk-work limits fail closed on guarded commands.

Any parser or grammar bump requires the complete oracle:

```bash
<project-interpreter> scripts/hooks/bash_oracle.py
<project-interpreter> -m pytest -q -n 2 tests/test_shell_redirects.py tests/test_guard_pr_merge.py tests/test_guard_branch_switch_in_main.py tests/test_guard_admin_merge.py tests/test_guard_benign_corpus.py tests/test_shared_hooks_deploy_depth.py tests/test_codex_hooks_contract.py tests/agent_runtime/test_claude_permissions.py
```

The committed issue corpus runs real Bash with recording fake `git` and `gh`
utilities, checks the guard's actual decision and its judged argv/directory,
and exercises the #9490 prefix-redirect shapes at the reader boundary. That
issue still owns migration of the four other guards. A committed sample of
400 public Git commit subjects is tested in three ordinary traffic shapes.
CI runs the oracle after a hash-verified wheel install.

The oracle also records fake `cat` and `touch` invocations, so every prefix
row must observe an operation before its argv comparison can pass. Fake
utilities never perform publication, branch changes, secret reads or writes.
Asynchronous recorders are awaited. The failing-`cd` rows start in a nested
worktree and return to the primary; primary subdirectories remain protected.
The sourced-script residual uses an oracle-owned PATH entry to avoid sourcing
the host's unrelated `script` utility. Reports expose sanitized executed argv/cwd
and judged targets, as well as executed and observed row counts alongside
decisions, and tests mutate both command extraction and
judged directories to prove that omitted or mis-scoped operations fail.

Acceptance is zero missed in-scope operations, at most four over-blocks, and
zero realistic-traffic blocks. The only accepted out-of-reach classes are
operation-free dynamic eval text, sourced scripts and REST merges. The oracle
also has a mutation check: omitting the reader's commands must produce misses.
No oracle result replaces exact-head independent critical review or CI.

API references: [Python bindings](https://tree-sitter.github.io/py-tree-sitter/)
and [Bash grammar](https://github.com/tree-sitter/tree-sitter-bash).

The oracle's `sudo` recorder models value options and directory changes without
using credentials. Its `env` instrumentation maps separated/long split-string
options to the equivalent attached `-S` spelling; the installed utility performs
the actual split. Every deferred-execution family has benign counterparts and
checks observed guarded execution. Refusal is acceptable; a wrong judged target
is a miss. Admin selectors are checked against gold corpus targets independently
of the hook's selector helper. No new residual class is admitted.

Shell semantics references: [functions](https://www.gnu.org/software/bash/manual/html_node/Shell-Functions.html),
[execution environments](https://www.gnu.org/software/bash/manual/html_node/Command-Execution-Environment.html),
and [env split-string](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html).
