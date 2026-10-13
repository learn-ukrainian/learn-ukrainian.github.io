# Agent GitHub identity

Dispatches use a repository-scoped GitHub App installation token before any
other GitHub credential. This lets ordinary `git push` and `.venv/bin/python -m scripts.publish pr-create` work
without giving an agent shell the operator's GitHub keychain identity.

## One-time App setup

Create and install a GitHub App on the `learn-ukrainian` repository only. Give
the installation these repository permissions:

- **Contents:** Read and write
- **Pull requests:** Read and write

Do not grant workflow, administration, organization-secret, or broader
organization permissions. Store the App ID, installation ID, and private key
only in the operator's local secret store, then export them for the dispatch
service as:

```bash
export LU_AGENT_GITHUB_APP_ID='…'
export LU_AGENT_GITHUB_APP_PRIVATE_KEY='<PKCS#8 PEM-encoded private key>'
export LU_AGENT_GITHUB_APP_INSTALLATION_ID='…'
```

The runtime signs a short-lived JWT and asks GitHub for an installation token
scoped to this repository. It does not request additional permissions.

## Protected App provisioning for rescue

The operator provisions `${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/agent-github-app/`
with mode `0700`, owned by the user running rescue. It contains exactly
`app-id`, `installation-id` and `private-key.pem`, each a regular file owned
by that user with mode `0600`. The two IDs are single-line numeric text;
the key is the App's PEM private key. Do not use symlinks.

Only rescue reads this directory. Explicit environment App inputs take
precedence, followed by this directory, then `LU_AGENT_GITHUB_TOKEN` when the
directory is absent. A partial or unsafe directory refuses without fallback;
rescue never uses the legacy operator token. App tokens request only
repository-scoped `contents:write` and are revoked after success or failure.
Keys and provisioning inputs are never exported to child processes.

Refusals retain `rescue_identity_unavailable` and report a `missing` list of
fixed `item:category` codes in the diagnostic and result. Items are
`app-directory`, `app-id`, `installation-id`, `private-key.pem`, `agent-token`
and `app-token`. Categories are `missing`, `wrong_mode`, `wrong_owner`,
`symlink`, `wrong_type`, `unreadable`, `changed`, `invalid`,
`unexpected_items` and `mint_failed`. The supported alternative is publishing
through the normal pre-push push from the worktree.

## Dedicated-token alternative

Until the App is installed, provision a dedicated bot token with the same
repository-level scope and set:

```bash
export LU_AGENT_GITHUB_TOKEN='…'
```

The runtime passes it to child shells as `GH_TOKEN`, which both GitHub CLI and
the Git askpass helper use. It does not pass `GITHUB_TOKEN` through.

## Confirm the active identity

Inside a dispatched agent shell, check only the non-secret provenance:

```bash
printf '%s\n' "$LU_AGENT_GITHUB_IDENTITY_SOURCE"
```

The App route reports `app`; the dedicated-token route reports `token`. The
temporary legacy path reports `legacy` and emits a one-line warning to stderr.
Legacy fallback uses an operator `GH_TOKEN`, `GITHUB_TOKEN`, or local
`~/.bash_secrets` only when neither App nor dedicated-token configuration is
present. It is a transition mechanism, not a long-term dispatch identity.
