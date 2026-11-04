# Claude account labels for ordinary workers (#10619)

Account labels identify the approved runtime identity used by a worker. They
support accounting and attribution; they do not isolate processes running as
the same operating-system user. Provisioning and account selection belong to
the operator's private configuration.

For an already authorized task, inspect the dispatch plan and task record for
non-secret provenance. Confirm that the expected model, provider and identity
verification succeeded before relying on its output. Do not print credentials,
login-directory contents, account names or authentication status containing
personal information.

```bash
.venv/bin/python scripts/dispatch.py status
```

## Allowlisted login-directory names

The runtime validates the configured login directory and the settings that
could change its credential source, endpoint or provider. Keep the allowlist
in the tracked adapter; do not expand it to silence a refusal. A partial,
unreadable or changed configuration must stop the launch rather than silently
select another identity.

An account label is not a permission to copy authentication files, change
organization policy or repair an operator's login. Report a refused launch
with its value-free diagnostic and task identifier through the approved
private channel.

### Why `autoMode` refuses

Settings can affect credential use and permissions even when a launch omits
user settings. A setting outside the runtime's supported contract must be
reviewed before use. Do not edit a login directory or weaken a check to make a
worker start. Preserve the refusal and ask the accountable driver to resolve
it through the authorized provisioning process.

## API-key labels

A separately provisioned API identity requires its own approval and budget.
A subscription label does not authorize switching to a key-backed provider.
Keep keys and the mapping from labels to accounts in private configuration.
Record only sanitized provenance in public evidence.

### Spend cap and prompt cache

A prompt cache does not guarantee zero spend. Before an authorized paid run,
confirm its approved budget and stop condition through private operational
evidence. A missing or uncertain budget is not permission to proceed. Never
publish live spending limits, account balances or routing choices here.

## Fleet-wide default account file

Defaults are local operational configuration. Public documentation does not
choose an account or publish the default file's contents or discovery paths.
Use the approved private procedure for changes, then verify a sanitized
result. Do not reinterpret a refused label as an instruction to try a default.

Operational details are in the private infra repository's `runbooks/claude-account-labels.md`.
