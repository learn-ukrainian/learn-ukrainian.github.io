# Machinery move: `lu_machinery` rename tools

Step 6 of the machinery move renames machinery code from the `scripts` package to
`lu_machinery` in a disposable clone. These two tools do the renaming. Product code keeps the
name `scripts`. Run them on a filtered clone, or on a throwaway copy for a dry run. Never run
them on the live product tree.

| Tool | Rewrites | Reports |
| --- | --- | --- |
| `rename_python.py` (LibCST) | `import` and `from … import` statements (qualified, unprefixed and relative); names bound by `import scripts.x`; `import_module`, `run_module` and `__import__` targets, including aliased loaders; strings that are exactly a machinery module or start with one plus a dot. A mixed `from scripts import …` is split by owner. | Computed or relative loader targets, ambiguous owners, unknown modules, map gaps, and unprefixed imports that change sides when their target cannot be pinned down. |
| `rename_nonpython.py` | `-m scripts.<module>`, other `scripts.<module>` tokens and `scripts/<path>` paths in shell scripts, hooks, systemd and launchd units, config files and Markdown code spans. | Python path strings, split path components, computed `-m` argument lists, references to the shared `scripts/` root or to mixed-owner directories, unknown paths, and file types that have no rewrite rule. Direct script invocations and machinery mentions in Markdown prose are listed in an inventory. |

Comments, docstrings and Markdown prose are never changed. A reference is renamed only when
the map says the file Python binds for it (or the path names) is machinery. Each tool's
`--help` lists the full set of rules.

Nothing is guessed:

- **Strings built in Python.** Both tools share one evaluator (in `rename_python.py`). It
  works out a string built with `+`, `%`, `*`, f-strings, literal lists and dicts, and the
  `str` and `bytes` methods that only reshape text (`format`, `join`, `replace`, `lower` and
  similar), as Python would. A piece known only at run time stays unknown. A module name or path
  that the value may contain is reported, never rewritten. Values passed through variables are
  not traced. When an operation on known values fails, the tool reports `unevaluable_string`.
- **Shell words.** A name or path is rewritten only when it ends where its word ends. If a
  variable, placeholder or more text continues the word, even across quotes
  (`scripts/x.py"${S}"`, `'scripts/x.py'.bak`), the tool reports `computed_path`.
- **Directory changes.** A `cd`, `pushd`, `-C`, `--directory=` or `WorkingDirectory=` target
  under `scripts/` is reported as `cwd_into_scripts` and left as written, because relative
  paths used after it depend on the old layout.
- **Tool errors.** If anything goes wrong while one file is processed, that file is reported
  as `tool_error` and left unchanged. The run still exits `1`.

Every Python file goes through LibCST; there is no fast pre-check. On a 16-core machine, a
whole-repository `rename_python.py --check --jobs 16` takes about eight minutes.

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
```

Read both reports, then rerun with `--apply` in place of `--check`, Python first. Exit codes:
`0` means nothing is unresolved, `1` means at least one reference is unresolved (`--apply`
still writes every resolved rewrite), and `2` means a usage or map error. A second `--apply`
changes nothing.

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

`tests/packaging/test_machinery_rename_codemod.py` covers the contract's rename held-out
cases, idempotence, a computed loader target, a mixed import split, and one case for each
class of built string, run-time path and directory change found in review. The project
environment skips it because LibCST is absent. Run it with the tool environment:

```bash
"$TOOL_PYTHON" -m pytest -p no:cacheprovider tests/packaging/test_machinery_rename_codemod.py
```
