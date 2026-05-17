# OCR setup — how to give the orchestrator a credential safely

> **Threat we're defending against:** MEMORY.md #M-5 records two API-key leaks
> in six weeks via shell-env enumeration patterns. The fix is to keep keys out
> of shell env entirely. Store them in `~/.secret/<provider>.key` (mode 0600,
> owner-only) and let scripts read them on demand.

## Project convention

All third-party API keys live under `~/.secret/`:

```
~/.secret/
├── mistral.key      mode 0600, owned by you
├── deepseek.key     mode 0600, owned by you
└── ...
```

Each file holds **one line**: just the secret, no `KEY=value`, no JSON, no
quotes. Trailing newline is fine.

> **Naming note:** as of 2026-05-17 the deepseek file in this repo's owner's
> setup is `~/.secret/deekseep.key` (typo). Either rename to `deepseek.key`
> or pass the typo'd path via `--credentials` when invoking scripts.

## Creating a credential file

```bash
mkdir -p ~/.secret
install -m 0600 /dev/stdin ~/.secret/mistral.key <<< 'YOUR_MISTRAL_API_KEY_HERE'
# or, if you prefer interactive editing:
touch ~/.secret/mistral.key && chmod 600 ~/.secret/mistral.key && $EDITOR ~/.secret/mistral.key
```

Verify it loaded correctly (no contents printed):

```bash
.venv/bin/python -c "from scripts.ocr._credentials import load_credential; \
    load_credential('~/.secret/mistral.key'); print('OK')"
```

If the credential is missing, world-readable, or owned by a different uid,
the loader refuses with an explicit error message — see
`scripts/ocr/_credentials.py` for the full rules and
`tests/ocr/test_credentials.py` for the security invariants under test.

## Why a file, not an env var

| Concern | Env var (`MISTRAL_API_KEY=...`) | File (`~/.secret/mistral.key`) |
|---|---|---|
| Visible via `env` / `printenv` / shell history | YES — every subprocess sees it | NO — only processes that open the file |
| Visible via `ps aux` if leaked into argv | depends | NO if you use `--credentials PATH` (path is visible, value isn't) |
| Permissions auditable | NO (env vars have no mode) | YES (`ls -la ~/.secret/`) |
| Accidental `echo`/`grep` exposure | HIGH risk (#M-5 happened twice this way) | LOW (the file's content never enters scope unless we deliberately read it) |
| Multi-tenant host hygiene | NO (env may inherit across shells) | YES (mode 0600 enforces) |

## What scripts must promise

Per `scripts/ocr/_credentials.py` docstring, any caller of `load_credential`
must:

1. Pass the returned string DIRECTLY into an HTTP header or SDK constructor.
2. Never put it in argv (`subprocess.run(["curl", "-H", f"Auth: Bearer {key}"])`
   is wrong — `key` is visible in `ps`).
3. Never log it. Never include it in stack traces. Never echo it in dry-run output.
4. Never write it to disk anywhere outside the original `~/.secret/` file.

The `mistral_ocr.py` client follows these rules — read its `_post_ocr` for
the canonical pattern. If you add a new OCR/API client under
`scripts/`, follow the same pattern and add tests under `tests/ocr/` or
`tests/<your-module>/`.

## Adding more providers

Same shape. For Gemini:

```bash
install -m 0600 /dev/stdin ~/.secret/gemini.key <<< 'YOUR_GEMINI_API_KEY'
```

Then in client code:

```python
from scripts.ocr._credentials import load_credential
api_key = load_credential("~/.secret/gemini.key")
# pass api_key directly into the SDK, never log it
```

The same loader works for every API key file under the same permission
contract. No provider-specific code needed in the loader itself.
