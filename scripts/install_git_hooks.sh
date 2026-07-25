#!/usr/bin/env bash
# Configure this repository's tracked Git hooks for every linked worktree.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$repo_root/.githooks"

if [[ ! -x "$hooks_dir/pre-push" ]]; then
    echo "Expected executable hook at $hooks_dir/pre-push" >&2
    exit 1
fi

git -C "$repo_root" config --local core.hooksPath .githooks

# A sparse worktree may omit the top-level hook directory.  Configure the
# shared hooksPath once, then materialize only that directory in every linked
# sparse worktree so Git can execute the tracked hook there as well.
while IFS= read -r worktree; do
    if [[ "$(git -C "$worktree" config --bool core.sparseCheckout 2>/dev/null || true)" == "true" ]]; then
        git -C "$worktree" sparse-checkout add --skip-checks .githooks
    fi
done < <(git -C "$repo_root" worktree list --porcelain | sed -n 's/^worktree //p')

echo "Configured core.hooksPath=.githooks for $repo_root"
