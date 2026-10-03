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

`diagnostic=True` exists only for the private `_segments` extraction seams used
by historical tests. It extracts recoverable commands from incomplete syntax
and does not recurse into literal shell payloads in those seams. Enforcement
calls the strict reader directly; diagnostic output is never an admission
receipt. The unchanged benign fixture checks those extraction contracts.

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
the host's unrelated `script` utility. Reports expose executed and observed
row counts alongside decisions, and tests mutate both command extraction and
judged directories to prove that omitted or mis-scoped operations fail.

Acceptance is zero missed in-scope operations, at most four over-blocks, and
zero realistic-traffic blocks. The only accepted out-of-reach classes are
operation-free dynamic eval text, sourced scripts and REST merges. The oracle
also has a mutation check: omitting the reader's commands must produce misses.
No oracle result replaces exact-head independent critical review or CI.

API references: [Python bindings](https://tree-sitter.github.io/py-tree-sitter/)
and [Bash grammar](https://github.com/tree-sitter/tree-sitter-bash).
