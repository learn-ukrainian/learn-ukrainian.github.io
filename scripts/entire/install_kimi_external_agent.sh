#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
module_dir="${repo_root}/scripts/entire/external_agents/entire-agent-kimi"
install_dir="${ENTIRE_KIMI_INSTALL_DIR:-${HOME}/.local/bin}"
go_command="${ENTIRE_KIMI_GO:-}"

if [[ -z "${go_command}" ]]; then
  go_command="$(command -v go || true)"
fi
if [[ -z "${go_command}" || ! -x "${go_command}" ]]; then
  echo "Go 1.26+ is required; set ENTIRE_KIMI_GO to the Go executable" >&2
  exit 1
fi

scratch_dir="$(mktemp -d)"
trap 'rm -rf "${scratch_dir}"' EXIT

(
  cd "${module_dir}"
  "${go_command}" test -race ./...
  "${go_command}" build -trimpath -o "${scratch_dir}/entire-agent-kimi" ./cmd/entire-agent-kimi
)

mkdir -p "${install_dir}"
install -m 0755 "${scratch_dir}/entire-agent-kimi" "${install_dir}/entire-agent-kimi"
"${install_dir}/entire-agent-kimi" info >/dev/null
echo "Installed ${install_dir}/entire-agent-kimi"
