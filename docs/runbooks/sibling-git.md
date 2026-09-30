# Registered sibling Git maintenance

Use `scripts.fleet.sibling_git` from the repository root owning the deployed
primary-checkout hook. From a dispatch root, use the shared project's absolute
interpreter. Set `PYTHONDONTWRITEBYTECODE=1` in the session environment before
invoking the helper: Python imports packages before module code can prevent
cache writes. Invoke each command separately, with no environment prefix,
redirect, shell composition or interpreter options.

The examples below use the project interpreter; replace its spelling with the
absolute project interpreter path when sending a command through the hook.

```bash
.venv/bin/python -m scripts.fleet.sibling_git status --repo infra-private
.venv/bin/python -m scripts.fleet.sibling_git sync-main --repo infra-private
.venv/bin/python -m scripts.fleet.sibling_git worktree-remove --repo infra-private '/absolute/sibling/.worktrees/dispatch/codex/finished task'
```

`status` emits JSON with branch, head, cleanliness and registered worktrees
(relative locations, head, branch and lock state; no absolute checkout paths).
`sync-main` requires a clean checkout on `main`, fetches the registered remote's
`main`, captures that commit, and fast-forwards to it. Dirty, divergent, locally
ahead or other-branch checkouts are refused. `worktree-remove` removes exactly
one clean, unlocked, registered dispatch worktree with no active task claim. It
uses the existing removal lock and claim policy, never force, unlock, branch
pruning or recovery writes. The dispatch lock must already exist; unmanaged
checkouts go through the existing cleanup workflow. No public repository
files, index, refs or worktree metadata are written by these verbs.

Repository identities come only from `scripts/config/fleet_repos.yaml`.
The public/default repository and unknown names are refused. The supported
transport is GitHub SSH, with the registry's exact owner and repository;
`git@github.com:owner/repository.git` and
`ssh://git@github.com/owner/repository.git` are accepted origin spellings.
Authentication uses installed SSH and its normal trusted host configuration.
There are no user-supplied Git flags, remotes, refs, configuration or executables.

The helper validates real checkout, Git directory, common directory and index
identity, plus the removal target. Symlinked/shared metadata, shared object
stores, repository redirection, URL rewriting, upload-pack overrides, remote
helpers, executable filters and attribute-declared filters are refused. This
also preserves required transformations rather than silently disabling them.
Submodule and symlink checkouts and hardlinked checkout files are unsupported.
Unused configured filters do not block maintenance; applicable filters do.
Git runs through a fixed
executable with a controlled environment, empty hooks, disabled fsmonitor,
submodule recursion and automatic maintenance. Raw sibling Git receives no
new guard exemption.

Exit code `0` means the verb succeeded; `2` means invalid usage, a dependency
failure or a refusal. Refusals preserve local work and include examples. Never
fall back to force, a shell-parsing exemption or an emergency override.

The hook validates literal command identity and module location; the helper
validates effect boundaries. Installed host tooling and the repository's own
code are trusted. This interface is not a sandbox for a compromised host or
concurrent malicious replacement of trusted code or repository metadata.
