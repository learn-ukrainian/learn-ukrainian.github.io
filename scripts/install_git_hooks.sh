#!/usr/bin/env bash
# Configure this repository's tracked Git hooks for every linked worktree.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$repo_root/.githooks"

required_hooks=(
    pre-commit
    commit-msg
    pre-push
    post-merge
    post-checkout
    post-commit
)
for hook_name in "${required_hooks[@]}"; do
    if [[ ! -x "$hooks_dir/$hook_name" ]]; then
        echo "Expected executable hook at $hooks_dir/$hook_name" >&2
        exit 1
    fi
done

for support_file in _lib.sh check-pytest-stamp.py pytest_stamp.py; do
    if [[ ! -r "$hooks_dir/$support_file" ]]; then
        echo "Expected readable hook support file at $hooks_dir/$support_file" >&2
        exit 1
    fi
done

git -C "$repo_root" config --local core.hooksPath .githooks

# A sparse worktree may omit the top-level hook directory.  Configure the
# shared hooksPath once, then materialize only that directory in every linked
# sparse worktree so Git can execute the tracked hook there as well.
while IFS= read -r worktree; do
    if [[ "$(git -C "$worktree" config --bool core.sparseCheckout 2>/dev/null || true)" == "true" ]]; then
        git -C "$worktree" sparse-checkout add --skip-checks .githooks
    fi
done < <(git -C "$repo_root" worktree list --porcelain | sed -n 's/^worktree //p')

echo "Configured the complete tracked Git hook chain at core.hooksPath=.githooks for $repo_root"
