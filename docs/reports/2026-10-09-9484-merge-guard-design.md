---
title: "Issue 9484: shell completeness in the merge guard"
date: 2026-10-09
issue: 9484
status: proposed
author: codex/recon-9484-merge-guard-sol
evaluated_base: d9df1d0a72207470c05d07f9d94dfd22829c8aad
---

# Issue 9484: shell completeness in the merge guard

Recommend a real Bash syntax tree using `tree-sitter` and `tree-sitter-bash`,
with a bounded semantic reader that refuses unsupported execution constructs.
Reject the raw mention-count design. Do not adopt `bashlex` 0.18 as the default:
its grammar gaps and quoted-heredoc failure conflict with this task's contract.
Tree-sitter is a maintained parser alternative, **not pure Python**; adopting
its native dependencies is part of the proposed decision, not an approved change.

This report delivers investigation and a recommendation. It changes no hook,
dependency, test, fixture, deployed copy, or merge-readiness policy. Implementation,
design approval, independent review, landing and deployment remain with the infra
driver. The issue remained OPEN when read; sibling #9480 was CLOSED.

## Failure modes and decision evidence

The current hook can return ALLOW without judging a merge that Bash runs.
With `_judge` replaced by an unconditional red-fixture refusal, `main()` returned
0 for 45 of 102 executable `gh` matrix rows. These include keyword bodies,
double-quoted command substitutions, shell-fed heredocs and `eval` after `then`.
Plain top-level `eval` is already refused on the evaluated base; the issue's
original description must not be mistaken for current behavior.

Neither counting source text nor merely trusting parser success establishes
completeness. The count candidate missed the following executable command:

```bash
if true; then eval 'gh pr merge 5'; fi
```

Its raw count outside single quotes is zero and the old reader judges zero
merges. A naive Tree-sitter walk also missed `coproc { gh pr merge 5; }; wait`:
the installed grammar produced ordinary command nodes without `ERROR` or
`has_error`. Parser success therefore needs a supported-semantics check.

| Candidate | Executable matrix rows accounted for | New blocks against current full-hook detection on 1,498 corpus commands | Disposition |
| --- | ---: | ---: | --- |
| Current reader | 95 / 170 | Reference | Has unseen merges |
| Current reader plus raw surplus count | 165 / 170 | 19 | Reject: bypasses and benign regressions |
| Naive Tree-sitter reader with shell payload recursion and eval refusal | 165 / 170 | 0 | Insufficient: silently misses coproc |
| Same Tree-sitter reader plus explicit unsupported-coproc refusal | 170 / 170 | 0 | Recommend construction, subject to implementation gates |

These are **discovery/refusal** measurements, not production acceptance results.
The prototypes do not prove PR selection, cwd resolution, green-PR permission,
hook startup under every harness, or the exact-head replacement's benign test
contract. For comparison, `bashlex` parsed 18 of 108 `gh` rows unsuccessfully;
its failure-closed prototype also added two corpus blocks on document heredocs.

## Parser choice: licence, maintenance and import safety

Live package metadata and latest upstream commits were queried on 2026-10-09.
Release recency is a maintenance signal, not a proof of grammar correctness.

| Package | Latest release observed | Latest upstream commit date observed | Import in prescribed project interpreter |
| --- | --- | --- | --- |
| bashlex | 0.18, 2023-01-18 | 2024-04-08 | Absent; scratch-target wheel imported successfully |
| tree-sitter | 0.26.0, 2026-06-30 | 2026-08-16 | Installed 0.26.0; parser constructed successfully |
| tree-sitter-bash | 0.25.1, 2025-12-02 | 2025-12-02 | Installed 0.25.1; language loaded successfully |

`bashlex` is a non-executing Python port of Bash's parser. Its upstream README
documents missing arithmetic expansion and incomplete parameter-expansion child
nodes. The probe confirmed that `${x:-$(gh pr merge 5)}` parses without exposing
the inner command to a simple command-node visitor. Arithmetic, `time`, `coproc`
and `case` also caused failures in the matrix. A valid quoted document heredoc
raised `ParsingError` with `wanted "'EOF'"`, causing false refusal when its body
contained merge prose. These are measured failures, not a claim that every
possible adapter around bashlex must fail. [Upstream description and limitations](https://github.com/idank/bashlex),
[release metadata](https://pypi.org/project/bashlex/).

Bashlex is GPLv3+; this repository's code licence is MIT. Do not vendor it as
MIT or assume importing it resolves redistribution obligations. The two
Tree-sitter components carry MIT licences; preserve their notices. This is a
licence inventory, not a legal determination. [Bashlex licence](https://github.com/idank/bashlex#license),
[Bash grammar licence](https://github.com/tree-sitter/tree-sitter-bash/blob/master/LICENSE),
[Python binding licence](https://github.com/tree-sitter/py-tree-sitter/blob/master/LICENSE).

Tree-sitter has Python bindings over native extensions. Both installed packages
contained native `.so` modules. Neither package was explicitly named in the
examined project requirements files, so a successful import here is not a
deployment guarantee. Declare and lock both dependencies through the existing
dependency process, verify wheels for supported hook runtimes, and smoke-test
the actual hook interpreter and deployment path. Test the measured pair together;
do not independently float the grammar and binding versions. [Python binding](https://github.com/tree-sitter/py-tree-sitter),
[Bash package metadata](https://pypi.org/project/tree-sitter-bash/).

Preserve the hook's early ordinary-command return before optional parser imports.
For a merge-bearing command, any import, native-loader, language-construction,
ABI, parse, traversal or resource-limit failure must exit 2 as unreadable. Never
return success or silently fall back to the old reader after a parser failure.
Disable bytecode writes before imports, as the existing hook does. Parsing must
never invoke Bash, eval, source a script, import command text, or contact GitHub;
only the unchanged readiness evaluator may perform its existing lookups.

## Why the completeness counter is inadequate

The evaluated counter preserves current refusals, masks single-quoted text and
comments, retains double-quoted text, and compares regex counts for `gh pr merge`
and `scripts.publish pr-merge` with `_judged_segments()` merge counts. Comments
start at shell-word boundaries; a `#` inside a word is retained.

On the simple matrix it catches many keyword and double-quote omissions, but
misses five executable rows: quoted eval after `then`, in all three `gh` forms
and both valid typed forms. Additional probes returned current `main()` rc=0
with raw count=0 and judged count=0 for `g'h' pr merge` and escaped `g\h` after
`then`. Quote concatenation, payload decoding, heredoc consumers and nested
quote contexts require shell semantics to fix this reliably.

The counter also newly blocks `echo gh pr merge 5`, quoted commit-message prose,
document heredocs, escaped backticks, `xargs echo gh pr merge 5`, help and
disable-auto commands, and the pinned double-quoted printf literal:

```bash
echo $(printf "%s" "# gh pr merge 5 --admin")
```

Ignoring every quoted mention misses executable double-quoted substitutions;
counting them all rejects data. Furthermore, equality of counts cannot establish
that the reader judged the right source occurrence, target or repository.
Correcting those distinctions would create another shell reader alongside the
one this issue intends to replace. The counter cannot serve as the acceptance
mechanism, even if retained as a non-authoritative diagnostic.

## Proposed construction

Keep the smallest change within `guard-pr-merge.py` and a private parser adapter
if needed. Replace its runtime shell-event reader, preserving `_merge_args()`,
flag handling, typed publisher recognition and the readiness evaluator. Leave
sibling hooks and their shared readers unchanged in this outcome.

1. Parse the complete original command bytes. Retain source spans and quotation
   context. Reject error recovery, missing nodes and unknown execution semantics
   when the input may merge. A merge-marker probe may over-select work; it must
   cover existing escaped and split-quoted command names and continued lines.
   It must never be treated as proof that a merge exists or is harmless.
2. Visit simple commands in all compound statements, functions, lists, pipelines,
   redirects, assignments and expansions. Visit command substitutions beneath
   strings as well as unquoted words, including backticks and parameter defaults.
   Visit unquoted process substitutions. Double-quoted `<(...)` and `>(...)` are
   literal data: do not manufacture an executable merge from their contents.
3. Build argv only from proven literal word pieces, preserving real argument
   boundaries. Reuse the existing prefix/flag policy; do not shlex the whole
   source or mistake a redirect descriptor for a PR. A dynamic target, option,
   wrapper argument or command string is unreadable where it can affect a merge.
4. Recursively parse literal supported shell `-c` payloads. Decode supported
   shell quoting correctly; do not strip `$` from ANSI-C strings and assume it
   decoded escapes. Associate heredoc bodies with their command/redirect: parse
   bodies consumed by supported `bash`/`sh`; treat document bodies as data while
   visiting executable expansions in unquoted heredocs. Refuse unknown script
   input, dynamic shell payloads and unsupported shell dialects when merge-bearing.
5. Refuse opaque eval at its AST execution position, including after keywords.
   Preserve its potential effect on later cwd resolution. For this grammar,
   reject unquoted `coproc` in command-name position as unsupported when the
   command may merge; the prototype verifies this closes its silent parse gap.
   Do not equate quoted ordinary argv text with a reserved word. Every newly
   encountered unsupported execution shape gets a fail-closed test, not a guess.
6. Track cwd as scoped state, using the hook payload's documented session cwd.
   Subshells, substitutions, shell payloads, pipelines and background execution
   must not leak their cwd changes outward. Braces and executed function bodies
   share the caller's state. Join conditional/loop paths conservatively; if repo
   identity is uncertain, refuse a cwd-dependent merge. An explicit repo option
   removes that dependency only under the existing target-selection policy.
7. Bound bytes, nodes, recursion and work through existing hook conventions.
   Exceeding a bound refuses a merge-bearing command. Unknown nodes cannot be
   skipped simply because the parser produced a tree. Feed only proven target,
   flags, repo and cwd into the unchanged evaluator.

This is a syntax-aware, bounded discipline gate. Aliases, generated scripts,
arbitrary indirect execution and API merges are not made safe by an AST. No
new sandbox claim is proposed. Outside-denominator uncertainty remains an infra
driver residual; the issue's denominator is not reduced to accommodate a parser.

## Evaluation procedure and denominator

All repository commands ran from the assigned dispatch worktree using the
prescribed shared project interpreter, with no worktree virtualenv or `PYTHONPATH`
change. Scratch packages, stubs and probes were placed under the managed
`TMPDIR`, outside report storage. No real merge or typed publication ran.

The matrix has the following 36 templates, with `M` standing for a merge command.

| Context | Templates |
| --- | --- |
| Keywords and loops | `if M; then :; fi`; `if true; then M; fi`; `if false; then :; else M; fi`; `if false; then :; elif M; then :; fi`; `while M; do break; done`; `until M; do break; done`; `for x in a; do M; done`; `for ((i=0;i<1;i++)); do M; done` |
| Compound execution | `{ M; }`; `( M )`; `f() { M; }; f`; `time M`; `coproc { M; }; wait`; `! M` |
| Lists and pipeline | `M \| cat`; `true && M`; `false \|\| M`; `:; M`; `M & wait` |
| Re-evaluated shell input | quoted-delimiter heredoc containing M fed to `bash`, and to `sh`; `eval 'M'`; `bash -c 'M'`; `sh -c 'M'` |
| Substitutions | `echo $(M)`; `echo "$(M)"`; unquoted and double-quoted backticks; `cat <(M)`; `printf x > >(M); wait`; double-quoted literal `<(M)` and `>(M)` arguments |
| Additional witnesses | `case x in x) echo "$(M)";; esac`; `x="$(M)"`; `if true; then eval 'M'; fi`; `unset x; echo ${x:-$(M)}` |

Expand `gh pr merge 5` into plain, `2>/dev/null`, and `--admin` forms: 108
syntactically valid rows, 102 recorded executions and six inert quoted process
forms. Expand the existing typed publisher with `--number 5 --match-head` plus
a fixed 40-hex fixture into plain and redirected forms: 72 rows, 68 recorded
launcher executions and four inert forms. `--admin` is not a valid typed option;
the production test must assert refusal rather than pretend it is a valid merge.

Real Bash was the execution oracle. The recording `gh` stub appended argv to
a managed scratch file and always exited 1. A recording `python` launcher stub
did the same for typed `-m scripts.publish pr-merge` input; this proves shell
invocation/argv, not publisher success. Nested shells inherited the stub PATH.
The harness awaited background and coproc execution and inspected the record
after Bash exit. It separately ran `bash -n` for syntax validity.

The current reader was evaluated both through merge extraction and, for the
102 executable gh rows, through `main()` with stdin payloads and a refusal-only
`_judge`. Parser prototypes walked every descendant simple command; Tree-sitter
also recursed into literal shell payloads and shell-consumed heredocs, refusing
eval and then coproc. No readiness lookup was permitted by the oracle harness.

The full 1,498-command fixture was compared against current runtime extraction,
not executed as shell input. Candidate refusal is additive for that comparison,
so its zero block-to-allow count is constructed, not evidence that replacing the
scanner preserves every historical block. The measured Tree-sitter candidate
added zero full-runtime blocks; the counter added 19 and bashlex added two.
Fixture SHA-256: `c9b89f375f9826ed216f482ced728974386f6aff9404618678b842d9a8616c7b`.

Four actual ablations of the discovery prototype were run against the same
170 executable rows. Control missed zero; removing eval refusal missed 10;
dropping shell-heredoc recursion missed 10; dropping double-quoted descendants
missed 20; removing coproc refusal missed five. These are prototype mutation
results, not mutation coverage of a future production implementation.

## Existing-suite proof and benign-contract limits

The issue's named suite ran on the unchanged base. Here `$PROJECT_PYTHON`
denotes the task-prescribed shared interpreter; the command was executed with
that interpreter's absolute path in the assigned worktree.

```bash
$PROJECT_PYTHON -m pytest -q -n 2 \
  tests/test_guard_pr_merge.py tests/test_guard_benign_corpus.py \
  tests/test_codex_hooks_contract.py tests/agent_runtime/test_claude_permissions.py
```

Raw summary: `643 passed, 1 skipped in 19.99s`. A bounded rerun with `-rs`
of the last two files returned `162 passed, 1 skipped in 18.36s`, identifying
the skip as `opt-in paid Claude CLI matcher check` at
`tests/agent_runtime/test_claude_permissions.py:50`. It was not a product failure
or evidence about the proposed parser. The paid check was not requested.

The benign contract reads `_segments()` and `_merge_args()`, not `main()` or
`_judged_segments()`. The pinned historical subset has 1,492 commands; the full
fixture has 1,498, including head-only literal cases. Comparing a recursive
runtime reader directly with the legacy segment contract produced 14 additional
recognitions of already-judged shell payloads. Do not call those benign regressions
or rewrite the fixture. Preserve the established segment view for its callers
while implementing the runtime reader, and prove both views at the exact head.

The existing suite is independently authored baseline evidence. Neither it nor
the self-authored matrix is an independent review or a held-out acceptance proof
of a replacement that has not been written. Add full-hook corpus tests alongside
the unchanged contract, with red, draft, unknown and green readiness fixtures;
compare pre-change and post-change decisions, not merely parser recognition.

## Implementation acceptance and driver handoff

- Freeze this proposed outcome and full issue denominator before implementation.
  Obtain designated design approval; this worker report does not adopt a new
  architecture or satisfy cross-family review.
- Retain the current benign test and fixture byte-for-byte. Every current refusal
  must stay refused; every pinned benign allowance must stay allowed. Implement
  affected helper tests and run their explicitly named importers' test files.
- For each denominator row, a recording Bash oracle must prove that the hook
  judges the actual argv/repo/PR or refuses it as unreadable. Add conditional cwd,
  quote-concatenation, parameter-default, Unicode byte-offset, dynamic payload,
  bounds, missing-dependency and coproc-without-parse-error witnesses. An
  independent reviewer should select held-out target/repo/cwd cases.
- Fault-inject both native imports and language construction. A merge-bearing
  input must refuse; ordinary non-merge commands must remain usable. Verify the
  actual deployed wrapper uses the interpreter containing the pinned packages.
- Run the named suite, affected new parser/importer tests and Ruff. Then obtain
  independent exact-head cross-family review at the issue's high-risk floor,
  same-head CI, landing and agent-system deployment through the normal driver.
- Stop after two review rounds to state the blocker/residual boundary. Any actual
  denominator bypass, benign-corpus regression, relaxed existing block or wrong
  target/repo judgement remains blocking; it cannot become a tolerated residual.

One open issue remains in this report's scope: #9484. Its implementation,
approval, independent held-out proof and deployment are a single remaining
delivery outcome owned by the infra driver. Hook-runtime portability, unsupported
semantics and correct cwd/control-flow interpretation are the material risks.
This report supplies the proposed construction and evaluation; it does not close
AC-01, AC-02 or AC-03.
