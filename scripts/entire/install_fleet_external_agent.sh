#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
common_dir="$(git -C "${repo_root}" rev-parse --path-format=absolute --git-common-dir)"
python_command="$(dirname "${common_dir}")/.venv/bin/python"
module_dir="${repo_root}/scripts/entire/external_agents/entire-agent-kimi"
install_dir="${ENTIRE_FLEET_INSTALL_DIR:-${HOME}/.local/bin}"
go_command="${ENTIRE_FLEET_GO:-}"
entire_command="${ENTIRE_FLEET_CLI:-}"

if [[ -z "${go_command}" ]]; then
  go_command="$(command -v go || true)"
fi
if [[ -z "${go_command}" || ! -x "${go_command}" ]]; then
  echo "Go 1.26+ is required; set ENTIRE_FLEET_GO to the Go executable" >&2
  exit 1
fi
if [[ -z "${entire_command}" ]]; then
  entire_command="$(command -v entire || true)"
fi
if [[ -z "${entire_command}" || ! -x "${entire_command}" ]]; then
  echo "Entire CLI 0.8.42 is required; set ENTIRE_FLEET_CLI to the executable" >&2
  exit 1
fi
if [[ ! -x "${python_command}" ]]; then
  echo "Project Python 3.12.8 is required at ${python_command}" >&2
  exit 1
fi
if [[ "$("${entire_command}" version | head -n 1)" != "Entire CLI 0.8.42" ]]; then
  echo "Entire CLI must remain pinned to 0.8.42" >&2
  exit 1
fi

scratch_dir="$(mktemp -d)"
trap 'rm -rf "${scratch_dir}"' EXIT

(
  cd "${module_dir}"
  "${go_command}" test -race ./...
  "${go_command}" build -trimpath -o "${scratch_dir}/entire-agent-fleet" ./cmd/entire-agent-fleet
)

mkdir -p "${install_dir}"
install -m 0755 "${scratch_dir}/entire-agent-fleet" "${install_dir}/entire-agent-fleet"
"${install_dir}/entire-agent-fleet" install-hooks
"${entire_command}" agent add cursor
"${python_command}" "${repo_root}/scripts/entire/cursor_session_start_shim.py" install
echo "Installed Entire fleet adapter and native Cursor integration"
