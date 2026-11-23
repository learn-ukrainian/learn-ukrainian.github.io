# shellcheck shell=bash
# Sourced by launch.sh, doctor.sh and drive-playwright.sh; not run directly.
#
# The checked-in Node contract: the release in .nvmrc, equal to package.json
# engines.node, run with its bundled npm at engines.npm. That npm enforces the
# install-script policy in .npmrc and site/.npmrc, so this file holds no versions.

# The locked site install, the same commands CONTRIBUTING.md and CI run; the
# sourcing scripts print it in their fix commands.
# shellcheck disable=SC2034
LU_VERIFY_SITE_INSTALL='npm ci --ignore-scripts && npm rebuild --ignore-scripts=false'

# lu_verify_toolchain ROOT LABEL
# Select the pinned Node through nvm when nvm is installed, then return 1 with the
# fix command on stderr unless node and npm on PATH match the checked-in pins.
lu_verify_toolchain() {
  local root="$1" label="$2"
  local nvmrc="" node_pin="" npm_pin="" node_version="" npm_version="" fix
  printf -v fix 'cd %q && nvm install && nvm use' "$root"
  if [[ -f "$root/.nvmrc" ]]; then
    nvmrc="$(<"$root/.nvmrc")"
    nvmrc="${nvmrc//[[:space:]]/}"
    nvmrc="${nvmrc#v}"
  fi
  if [[ -z "$nvmrc" ]]; then
    echo "$label FAIL: no Node release in $root/.nvmrc" >&2
    return 1
  fi
  if [[ -s "${NVM_DIR:-${HOME:-}/.nvm}/nvm.sh" ]]; then
    # shellcheck disable=SC1090,SC1091
    . "${NVM_DIR:-${HOME:-}/.nvm}/nvm.sh"
    # A missing release is reported below together with the command that installs it.
    nvm use "$nvmrc" >/dev/null 2>&1 || true
  fi
  if node_version="$(node -v 2>/dev/null)"; then
    # shellcheck disable=SC2016  # JavaScript template literal, expanded by node
    read -r node_pin npm_pin < <(
      node -p 'const e = require(process.argv[1]).engines || {}; `${e.node} ${e.npm}`' \
        "$root/package.json" 2>/dev/null
    ) || true
  fi
  npm_version="$(npm --version 2>/dev/null)" || npm_version=""
  if [[ -n "$node_pin" && -n "$npm_pin" && "$node_version" == "v$nvmrc" &&
        "$node_version" == "v$node_pin" && "$npm_version" == "$npm_pin" ]]; then
    return 0
  fi
  if [[ "$node_version" == "v$nvmrc" && "$node_version" == "v$node_pin" ]]; then
    # The right Node with another npm: reinstalling the release restores its bundled npm.
    printf -v fix 'cd %q && nvm deactivate && nvm uninstall %q && nvm install && nvm use' "$root" "$nvmrc"
  fi
  echo "$label FAIL: need Node $nvmrc (.nvmrc; package.json engines.node ${node_pin:-unreadable}) with its bundled npm ${npm_pin:-unreadable} (engines.npm); found Node ${node_version:-none} and npm ${npm_version:-none}. Run: $fix" >&2
  return 1
}
