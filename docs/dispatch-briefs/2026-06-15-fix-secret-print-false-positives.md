# Dispatch — fix #M-5 guard-secret-print false-positives (DEACTIVATED, #1908)

`agents_extensions/shared/hooks/guard-secret-print.py` (merged #3233) was DEPLOYED then
**DEACTIVATED** — live-testing caught false-positives that block legitimate commands.
The hook FILE is on main; it is unregistered from settings.json pending this fix (the
orchestrator re-registers after verification).

## Reproducing false-positives (must ALL become ALLOW)
1. `cat agents_extensions/shared/hooks/guard-secret-print.py` — the hook's OWN filename
   contains "secret" → flagged as a secret file. Any path with secret/key/token in the
   NAME (e.g. `guard-secret-print.py`, `test_api_key.py`, `token_utils.py`) false-matches.
2. `python -m pytest tests/foo.py -q 2>&1 | tail -3` — `tail -3` is a **pipe read** (numeric
   flag, no file arg), but combined in a compound command whose text elsewhere contains
   "secret-print", the hook reported `tail would print known secret file 'secret-print'`.
   (Real repro that blocked the orchestrator.)
3. A `git commit -F - <<EOF ... guard-secret-print ... EOF` heredoc body — the hook
   tokenizes heredoc/commit-message TEXT and treats words there as command file-args.

## Root causes
1. **`_is_known_secret_file` (lines ~231-232):** `if "token" in name or "secret" in name:
   return _path_ext(name) in SECRET_FILE_EXTS`. The bare-name heuristic + ext-set ("" is in
   the set, so a no-extension token like `secret-print` matches) is way too loose — it
   matches legitimate FILENAMES and command words. **Remove this heuristic.** Match ONLY
   exact secret files: `.env`/`.envrc`/`.bash_secrets`/`~/.aws/credentials`/`*.pem`/`id_rsa`
   and the explicit `*.env`/`.env.*` (non-sample) cases already handled above it.
2. **A `cat`/`tail`/`head`/`less`/`bat` command must be flagged ONLY when its actual
   positional FILE ARGUMENT (in the SAME segment) is a secret file.** `tail -3` / `tail -n 5`
   / `head -20` with only numeric/flag args = a pipe read → NO file → never flag. Do not
   associate a secret-looking token from another segment/pipeline with the display command.
3. **Do not treat heredoc bodies / quoted commit-message text as command file-args** — only
   real argv tokens of the display command count.

## #M-4 + steps
1. Confirm worktree. 2. Fix `guard-secret-print.py` per the 3 root causes (tighten file
   matching + same-segment positional-file-arg requirement + numeric-arg = pipe-read).
3. Tests in `tests/test_guard_secret_print.py` — ADD regressions: ALLOW
   `cat agents_extensions/shared/hooks/guard-secret-print.py`, `... | tail -3`,
   `head -20 file.py`, `git commit -m "ref guard-secret-print.py"`; KEEP BLOCKING
   `cat ~/.aws/credentials`, `cat .env`, `tail .envrc`, bare `env`, `echo $GH_TOKEN`.
4. `.venv/bin/python -m pytest tests/test_guard_secret_print.py -q` green; `ruff check` clean.
5. Do NOT edit settings.json (orchestrator re-registers). Commit
   `fix(harness): tighten #M-5 secret-guard file-matching to kill false-positives (#1908)`
   + `X-Agent: codex/fix-secret-print`. Push + `gh pr create`. NO merge.

## Acceptance
All 4 repro cases ALLOW; all real secret-dumps still BLOCK. The "contains secret/token"
name heuristic is gone. Tests green.
