# Agent GitHub identity

Dispatches use a repository-scoped GitHub App installation token before any
other GitHub credential. This lets ordinary `git push` and `gh pr create` work
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
export LU_AGENT_GITHUB_APP_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\n…'
export LU_AGENT_GITHUB_APP_INSTALLATION_ID='…'
```

The runtime signs a short-lived JWT and asks GitHub for an installation token
scoped to this repository. It does not request additional permissions.

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
