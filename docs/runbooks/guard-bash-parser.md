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

The reader keeps possible working directories through commands, conditional
lists, substitutions, subshells and pipelines. Literal shell, eval and heredoc
payloads are parsed recursively. Dynamic command names and payloads, parser
errors and unsupported reserved-word shapes refuse a guarded command. Directory
or repository uncertainty is carried to each guard, rather than selecting a
repository by guess. Bash logical `cd` normalises parent components before
following symlinks; `cd -P` follows them physically. CDPATH, directory-stack
uncertainty and Git repository overrides are handled conservatively.

The branch policy's conservative refusal around `case` and parameter
parentheses is retained. The parser identifies these through AST nodes. The PR
guard refuses dynamic redirects on an actual merge and refuses process
substitution. Queued heredocs on ordinary readers are repaired using AST-identified
openers; queued shell stdin is refused.

Shell alias and command-hash bindings refuse guarded candidates. Function
definitions are inert. Calls to functions containing visible guarded operations,
dynamic command names, indirect execution, or directory changes (including
through another function) are refused. Trap payloads are refused. Shell stdin
from pipelines or process substitution is refused. Literal here-strings,
here-documents and `-c` payloads are parsed recursively.

The merge guard supplies an opt-in candidate-consumer check to the AST reader. It
classifies visible merge text at each command, including redirected stdin and
pipeline input. Known data readers remain usable. Unknown consumers, executor
options, sourced input, arithmetic references and command-local shell startup or
repository environment changes refuse. This check applies recursively to literal
shell and eval payloads. The sibling guards keep their existing reader behaviour.

Dynamic command names with literal `pr merge` arguments and dynamic GH operation
words engage the merge guard even without a literal `gh pr merge`. Inherited
`-R` and `--repo` options before or between GH subcommands are retained when
selecting the merge target. The merge option parser honours `--` and empty
`--option=` values, so data cannot suppress the merge judgment.

`xargs` never acts as a removable prefix. Guarded candidates involving its input
or executable arguments are refused. Fixed `echo` and `printf` logging commands
stay inert. Dynamic traps and traps calling guarded functions also refuse.
Execution actions of `find`, and indirect executors such as process-scheduling
and session wrappers, refuse when they carry visible operations. `nice`, `timeout`
and ordinary `sudo` are read through explicit argument semantics, including
`sudo -p` values. `sudo -D`, login and remote modes, and `env -S` refuse guarded
candidates rather than guessing a target. Wrapper options stay scoped to their
own utility.

Conditional and loop directory states remain conservative, including later loop
iterations. Shell option changes invalidate directory certainty. Redirected `cd`
retains its possible failure directory, except where `&&` requires success before
the following command runs. Missing repository or worktree-probe evidence never
establishes safety. Depth and work limits fail closed on guarded commands.

Any parser or grammar bump must pass the committed oracle before it lands:

```bash
<project-interpreter> scripts/hooks/bash_oracle.py
<project-interpreter> -m pytest -q -n 2 tests/test_shell_redirects.py tests/test_guard_pr_merge.py tests/test_guard_branch_switch_in_main.py tests/test_guard_admin_merge.py tests/test_guard_benign_corpus.py tests/test_shared_hooks_deploy_depth.py tests/test_codex_hooks_contract.py tests/agent_runtime/test_claude_permissions.py
```

The committed corpus runs real Bash with recording stand-ins for `git` and `gh`.
It checks each guard's actual decision and the argv and directory it judges. A
committed sample of public Git commit subjects is tested as ordinary traffic. CI
runs the oracle after a hash-verified wheel install.

Stand-in utilities record invocations only. They never perform publication,
branch changes, secret reads or writes. Asynchronous recorders are awaited.
Reports expose sanitised executed argv and cwd, together with the judged targets.

The `sudo` stand-in models value options and directory changes without using
credentials. The `env` stand-in maps separated and long split-string options to
the equivalent attached `-S` spelling; the installed utility performs the actual
split. Refusal is acceptable. A wrong judged target is a failure.

Acceptance: zero missed in-scope operations, and zero blocks on realistic
traffic.

API references: [Python bindings](https://tree-sitter.github.io/py-tree-sitter/)
and [Bash grammar](https://github.com/tree-sitter/tree-sitter-bash).

Shell semantics references: [functions](https://www.gnu.org/software/bash/manual/html_node/Shell-Functions.html),
[execution environments](https://www.gnu.org/software/bash/manual/html_node/Command-Execution-Environment.html),
and [env split-string](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html).
