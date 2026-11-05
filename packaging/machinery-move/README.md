# Machinery move: `lu_machinery` rename tools

Step 6 of the machinery move renames machinery code from the `scripts` package to
`lu_machinery` in a disposable clone. These three tools do the renaming. Product code keeps
the name `scripts`. Run them on a filtered clone, or on a throwaway copy for a dry run. Never
run them on the live product tree.

The tools fail closed. A reference is rewritten only when its whole value is known and names
machinery in the ownership map. Everything else that may hold a `scripts` module name or path
is reported. No reference is ever partly rewritten.

| Tool | Rewrites | Reports |
| --- | --- | --- |
| `rename_python.py` (LibCST), every `*.py` file | `import` and `from … import` statements (qualified, unprefixed and relative; a mixed `from scripts import …` is split by owner); names bound by `import scripts.x`; `import_module`, `run_module` and `__import__` targets; string values that are exactly a machinery module name. | Every other string that may hold a `scripts` name or path, computed or relative loader targets, ambiguous owners, unknown modules, map gaps, unprefixed imports whose target cannot be pinned down, and a machinery file importing a product module from its own directory. |
| `rename_nonpython.py`, every other text file | A `scripts.<module>` name or `scripts/<path>` that is a complete plain token, in shell scripts, hooks, systemd and launchd units, configuration files, JSON and Markdown code. | Every other `scripts` name or path. |
| `rename_structured.py`, the files it knows | The path fields of `scripts/lint/mypy_baseline.json`. | Machinery names in messages, unmapped paths, a file reached through a symlink, and any file that does not match its schema. |

Comments (including INI `;` lines and Jinja `{# #}`), docstrings and Markdown prose are never
changed. Machinery mentions in them are listed in the inventory. Each tool's `--help` lists its rules.

## Python strings

A string expression is rewritten only when it is a plain literal, or literals joined by
implicit concatenation, `+` or an f-string without fields, and its exact value is one
machinery module name. A module name followed by attributes counts, such as
`scripts.engine.control.launch`. A package whose directory holds files of both owners is
reported, not renamed: its name also anchors resources and submodules that stay on the other
side (`importlib.resources.files("scripts.review")`). The same holds for the package object
reached through an import (`files(review)`, `scripts.review.__file__`): the file is held. Joined literals become one literal, unless a comment sits
between them.

A known value is searched for module names and paths. The bare word `scripts` counts as the
root when it is the whole value, and as `root_in_text` inside longer text, such as
`"cd scripts && …"` or a regular expression.

Every other string expression is reported when it may hold `scripts`:

- **Exact values.** An expression built only from literals and simple operations has one exact
  value. These operations are `%`, `*`, slices, `str` and `bytes` methods, containers,
  `sorted()` and `str()`. The tool computes the value and reports any machinery or unknown
  module name or path in it. It never rewrites such an expression.
- **Values known only at run time.** A run-time piece makes the value unknown. Such pieces are
  a variable, an attribute, a call to another function or a field. The expression is then
  reported when its literals contain `scripts` in any case. It is also reported when the start of
  one literal, whole literals and the end of another spell `scripts`, in any order, such as
  `"scr" + x + "ipts.y"`.
- **Not traced.** Values in variables and in other functions are not traced, and neither are
  characters produced at run time, such as `chr(n)` or a run-time replacement inside a literal.

A literal is part of a larger string expression when it is an operand, sits in an f-string,
is the receiver of a method or subscript, or is an argument of a `str` method or a text builtin.
Elsewhere it is a whole value, for example an assignment, an argument of another call, a
comparison or an index.

An attribute chain follows its real binding. `import scripts.x` binds `scripts`, so
`scripts.x.f` is renamed with the import, but only when every binding of `scripts` that the use
sees is such an import: a parameter, a local or loop variable, or an alias named `scripts`
holds the file instead. An alias (`import scripts.x as a`,
`from scripts import x`) keeps its name, so `a.f` needs no change, unless `a.y` reaches a
submodule of the other owner.

A file is left unchanged when its rewrites depend on one another through a binding: a bare
use of the package, a rebound name, a missing binding, an alias that reaches the other owner,
or a non-ASCII identifier that Python reads as `scripts` (identifiers are NFKC-normalised).
Each of its rewrites is then reported as `held_rewrite`.

The exact evaluator bounds every operation's result before it runs it, assuming the worst
growth (ten characters per character for `ascii()`, `repr()` and escaping codecs). An operation
that could exceed one million characters is not evaluated; the expression is then judged by its
literals.

## Plain tokens outside Python

A complete plain token is a whole word, or a whole word inside one pair of quotes:

- **Before it.** The token, or its opening quote, follows a blank, the start of the line or `=`.
- **After it.** The token, or its closing quote, is followed by a blank, the end of the line, or
  one of `;`, `&`, `|` and `)`.
- **Root prefix.** The token may start with one of `./`, `../`, `$NAME/`, `${NAME}/` or
  `@NAME@/`, which is taken as the repository root. `$HOME`, `$TMPDIR`, `$TMP`, `$TEMP` and
  `$XDG_*` are not.
- **JSON and plist.** A JSON string or a plist `<string>` element counts when the name is its
  whole text, with no escapes.

A shell lexer follows quotes, `$(…)`, backticks, `${…}`, comments and heredoc bodies across
lines. It runs in shell, unit and configuration files and in shell-tagged Markdown fences and
code spans.

These are reported and never rewritten:

- names in heredoc bodies, inside longer quoted text, inside `${…}`, `$((…))` or backticks;
- names with anything glued on, such as `scripts/x.py:3`, `scripts/x.py"$S"` or `<name>`, or glued
  to the text before them (`\nscripts/x.py`, `-Bmscripts.x`, `%2Fscripts`, a colour code such as
  `\033[1m`);
- globs, Markdown fences in other languages and indented code blocks, files that record
  digests, and unsupported file types;
- `cd`, `pushd`, `-C`, `-w`, `--prefix`, `WorkingDirectory=`, `WORKDIR`, `working-directory:`,
  `working_dir:`, `changedir =` and `cwd:` targets under `scripts/`;
- a module named by a Python `from … import` in text (`from scripts.x import y`): `y` may have
  the other owner;
- the `scripts/` root itself, and unknown or mixed-owner names;
- names that only show once a reader joins the word: escapes (`\u0073`, the shell's shorter `\u73`
  and `\U73`, `&#115;`, `%73`), line
  continuations (`scr\` then `ipts` on the next line, in shell, YAML or TOML), quoted pieces glued to
  the word (`scr""ipts`), a backslash before a letter, and run-time pieces taken as empty (`$X`,
  `${X}`, `$(…)`, `$((…))`, backticks, `{{ … }}`). Pieces are found by a balanced scan, so nested
  ones count (`scr${A:-${B}}ipts`), and every substitution body is read at each depth with the pieces
  nested in it taken as empty (`"$(cat scr$(true)ipts/x.py)"`, `scr"$(echo a b)"ipts`). A `$'…'` quote
  with an escape is read, and is also taken as empty like a run-time piece;
- the root in another case (`Scripts/`);
- binary or non-UTF-8 files that may name `scripts` (also as UTF-16), compressed archives (gzip, bzip2,
  xz, zip) whose contents name it, and symlinks whose target names it.

A module name must be exact. A package whose `__main__` has the other owner is reported, because
`-m` runs that file.

## Inputs

- **Ownership map**: a JSON object that maps each repository-relative file path to
  `"machinery"` or `"product"`. Module names come from these paths: drop `.py` and a final
  `__init__`. When a package and a module share a name, the package wins, as it does in
  Python. Keys use the original `scripts/` layout. If filter-repo has already moved a file to
  `lu_machinery/`, the tools look it up under its `scripts/` key.
- **External names** (only for `rename_python.py`): the top-level modules importable in the
  project environment. The tool needs this list to rewrite an unprefixed import such as
  `from lib.x import y`. Without it, those imports are reported instead. Generate it with the
  project interpreter:

  ```bash
  "$PROJECT_PYTHON" -I -c 'import pkgutil, sys; print("\n".join(sorted({m.name for m in pkgutil.iter_modules()} | set(sys.builtin_module_names))))' > external-names.txt
  ```

## Run

```bash
"$TOOL_PYTHON" packaging/machinery-move/rename_python.py --map ownership.json --root "$CLONE" \
  --external-names external-names.txt --jobs "$(nproc)" --check --report py.json
"$TOOL_PYTHON" packaging/machinery-move/rename_nonpython.py --map ownership.json --root "$CLONE" \
  --check --report np.json
"$TOOL_PYTHON" packaging/machinery-move/rename_structured.py --map ownership.json --root "$CLONE" \
  --check --report st.json
```

Read the reports, then rerun with `--apply` in place of `--check`, in the same order. Exit
codes: `0` means nothing is unresolved, `1` means at least one reference is unresolved
(`--apply` still writes every resolved rewrite), and `2` means a usage or map error. A second
`--apply` changes nothing. Each unresolved entry has a `target`: what the map says it names
(`machinery`, `product`, `ambiguous` or `unknown`). Entries with the `machinery` target are the
part of the residue that needs renaming.

If anything goes wrong while one file is processed, that file is reported as `tool_error` and
left unchanged.

## Isolated LibCST environment

LibCST is not a project dependency. Install it into its own virtual environment from a
hash-locked requirements file, so the project lock files stay unchanged:

```bash
printf 'libcst==1.8.6\npytest==9.1.1\n' > libcst-in.txt
uv pip compile libcst-in.txt --python-version 3.12 --generate-hashes -o libcst-lock.txt
uv venv --python 3.12 "$TOOL_ENV"
uv pip install --python "$TOOL_ENV/bin/python" --require-hashes --no-deps -r libcst-lock.txt
TOOL_PYTHON="$TOOL_ENV/bin/python"
```

Keep the lock file next to the environment and record its SHA-256 with the run.

## Tests

`tests/packaging/test_machinery_rename_codemod.py` covers these cases:

- the contract's rename held-out cases;
- idempotence, a computed loader target and a mixed import split;
- the fail-closed rules and the structured baseline transform;
- every reviewer probe from PR 12756, rounds 1 to 5. Each probe is rewritten exactly or left
  unchanged and reported.

The project environment skips the file because LibCST is absent. Run it with the tool
environment:

```bash
"$TOOL_PYTHON" -m pytest -p no:cacheprovider tests/packaging/test_machinery_rename_codemod.py
```
