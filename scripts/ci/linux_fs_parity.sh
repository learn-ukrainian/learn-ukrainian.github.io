#!/usr/bin/env bash
# Run macOS-authored filesystem guardrails in Linux before opening a PR.
# Add a test file here only when it verifies OS filesystem semantics; keep this
# list focused so this remains a fast local parity probe rather than a suite.
set -euo pipefail

readonly image="${LINUX_FS_PARITY_IMAGE:-python:3.12-bookworm}"
readonly script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly repo_root="$(cd -- "${script_dir}/../.." && pwd)"

docker run --rm --init \
  --mount "type=bind,src=${repo_root},dst=/workspace,readonly" \
  --workdir /workspace \
  --env PIP_DISABLE_PIP_VERSION_CHECK=1 \
  --env PYTHONDONTWRITEBYTECODE=1 \
  "${image}" \
  bash -lc '
    set -euo pipefail
    command -v git >/dev/null
    python -m pip install --quiet "pytest>=8,<9"
    python -m pytest -q -p no:cacheprovider \
      tests/test_worktree_containment.py \
      tests/test_guard_primary_checkout_write.py \
      tests/test_hooks_executable.py \
      tests/test_deploy_script_idempotency.py::test_agent_manifest_rejects_symlinked_intermediate_component \
      tests/test_deploy_script_idempotency.py::test_agent_manifest_unlinks_symlink_leaf_without_following_target
  '
