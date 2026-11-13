# Agent GitHub identity

Agent pushes and pull requests use a repository-scoped identity provisioned
by the operator. Keep provisioning separate from task execution. An agent
must not borrow an operator's personal credentials to make a push succeed.

## One-time App setup

The operator installs a GitHub App only on the intended repository and grants
the permissions required by the approved workflow. Routine publication needs
repository contents and pull-request access; broader organization or
administration access requires separate authorization.

Keep the App identifiers and private key in the approved private secret
store. Never put them in the checkout, a task brief, logs or public evidence.
The runtime mints a short-lived installation token for the repository.

## Protected App provisioning for rescue

Rescue uses operator-provisioned inputs with restrictive ownership and file
permissions. Missing, incomplete, unreadable, symlinked or unsafe provisioning
must refuse the operation. Do not repair it from an agent task or fall back to
a personal identity. Report only the value-free refusal code privately.

Temporary tokens must remain scoped to the authorized operation and be revoked
when it finishes, including after failure. Provisioning inputs must not leak
into child processes.

## Dedicated-token alternative

A dedicated automation token is an operator-provisioned alternative. Scope it
to the intended repository and approved actions. Do not use a personal token,
copy another account's login state or publish the token's discovery location.

## Confirm the active identity

Inside a dispatched shell, inspect only non-secret provenance:

```bash
printf '%s\n' "$LU_AGENT_GITHUB_IDENTITY_SOURCE"
```

Compare that provenance with the authorized task's identity route using the
private procedure. A missing or unexpected result blocks publication. Do not
print the token, environment dump, account profile or secret-store contents.

After the identity is verified, use ordinary project publication commands
from the dispatch worktree:

```bash
git push -u origin HEAD
.venv/bin/python -m scripts.publish pr-create --title '<title>' \
  --body-file '<project-relative-body-file>' --base main --head '<branch>'
```

Operational details are in the private infra repository's `runbooks/agent-github-identity.md`.
