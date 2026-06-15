# Dispatch — #1908 hook: #M-5 secret-print guard (script + tests ONLY)

Push "#M-5 NEVER print secrets" down to the enforcement layer (2 recurrences in 6 weeks
despite being canonical). **Pattern to mirror:** `agents_extensions/shared/hooks/guard-admin-merge.py`
+ `guard-branch-switch-in-main.py` (PreToolUse Bash, stdin JSON `tool_input.command`,
`shlex` tokenize, exit 2 = block + stderr reason, exit 0 = allow). **Read both first.**

## CRITICAL scope constraint
**Write ONLY the hook script + its tests. DO NOT edit `agents_extensions/shared/settings.json`**
(orchestrator registers it serially). DO NOT run the deploy script.

## Hook: `agents_extensions/shared/hooks/guard-secret-print.py` — PreToolUse(Bash)
Block (exit 2) a command that would dump secret VALUES to the transcript, with a stderr
message naming the safe alternative + the override. Otherwise exit 0.

**NARROW matching is the whole game — false-positives that block legit commands are worse
than the rule being advisory.** Block ONLY these clear secret-dump shapes (quote/segment
aware; ignore matches inside a quoted arg such as a commit `-m` body):
- bare `env` / `printenv` / `set` with NO downstream filter (`| cut`, `| grep -o`, `| jq keys`,
  `| wc`) — i.e. a full unfiltered dump. `env | cut -d= -f1` etc. must PASS.
- `cat`/`bat`/`less`/`head`/`tail` of a known secret file: `~/.aws/credentials`,
  `~/.bash_secrets`, `*.env`, `.envrc`, `*.pem`, `id_rsa`, `*token*`, `*secret*` paths.
- `grep`/`rg`/`ugrep` of a dotenv/secret file (`.env`, `.envrc`, `.bash_secrets`) WITHOUT a
  key-only transform.
- `echo`/`printf` of a known-secret env var (`$*_TOKEN`, `$*_API_KEY`, `$*_PAT`, `$GH_TOKEN`,
  `$ANTHROPIC_API_KEY`, `$*_SECRET`, `$DAGGER_CLOUD_TOKEN`, etc.).

Do NOT block: `[ -n "${X:-}" ] && echo SET` presence checks, key-only listings
(`cut -d= -f1`, `jq keys`), `grep -v`/`grep -L`, reading non-secret files.

Override: env `LEARN_UK_SECRETS_OK=1` → allow. The stderr message must show the
format-correct safe alternative (per #M-5: JSON→`jq keys`, shell-env→`cut -d= -f1`,
presence→`[ -n "${X:-}" ]`). Conservative: when genuinely uncertain whether a command
leaks, **allow** (favor not-blocking-legit-work) — the explicit dump shapes above are the
high-confidence set.

## #M-4 + steps
- Report `pytest`/`ruff` final lines raw.
1. Confirm worktree. 2. Write `guard-secret-print.py` (chmod +x). 3. Tests in
   `tests/test_guard_secret_print.py` (importlib load, mirror `test_guard_admin_merge.py`):
   block bare `env`, `cat ~/.aws/credentials`, `grep KEY .envrc`, `echo $GH_TOKEN`; ALLOW
   `env | cut -d= -f1`, `[ -n "${X:-}" ] && echo SET`, `cat README.md`, `jq keys`, a quoted
   `--admin`-style body, and `LEARN_UK_SECRETS_OK=1 env`.
4. `pytest tests/test_guard_secret_print.py -q` green. 5. `ruff check` clean.
6. Commit `feat(harness): #M-5 secret-print guard hook (#1908)` + `X-Agent: codex/hook-secret-scan`.
7. `git push -u origin <branch>` + `gh pr create`. NO merge. NO settings.json edit.

## Acceptance
Clear secret-dump commands blocked (with safe-alternative guidance + override); key-only /
presence-check / non-secret-read commands PASS. Tests green, ruff clean.
