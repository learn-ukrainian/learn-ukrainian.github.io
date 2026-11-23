# shellcheck shell=bash
# Sourced by launch.sh, doctor.sh, drive-playwright.sh and run-checks.sh; not run directly.
#
# The checked-in Node contract: the exact release in .nvmrc, equal to package.json
# engines.node, run with its bundled npm at engines.npm. That npm enforces the
# install-script policy in .npmrc and site/.npmrc, so this file holds no versions.

# The locked site install, the same commands CONTRIBUTING.md and CI run.
LU_VERIFY_SITE_INSTALL='npm ci --ignore-scripts && npm rebuild --ignore-scripts=false'
_LU_VERIFY_EXACT='^[0-9]+\.[0-9]+\.[0-9]+$'

# lu_verify_toolchain ROOT LABEL
# Return 0 when node and npm on PATH match the checked-in pins, selecting the
# release through nvm first if it is installed and the PATH does not match.
# Otherwise print why on stderr, with the command that repairs it, and return 1.
lu_verify_toolchain() {
  local root="$1" label="$2" nvmrc="" node_pin="" npm_pin="" fix nvm_sh flags="$-"
  if [[ -f "$root/.nvmrc" ]]; then
    nvmrc="$(<"$root/.nvmrc")"
    nvmrc="${nvmrc//[[:space:]]/}"
    nvmrc="${nvmrc#v}"
  fi
  # Pins are checked before nvm sees them: an alias such as lts/* would select a
  # moving release.
  if [[ ! "$nvmrc" =~ $_LU_VERIFY_EXACT ]]; then
    printf '%s FAIL: .nvmrc must hold an exact Node release (found "%s"). Restore the checked-in file: git -C %q checkout -- .nvmrc\n' \
      "$label" "$nvmrc" "$root" >&2
    return 1
  fi
  if _lu_verify_versions "$root" "$nvmrc"; then
    return 0
  fi
  if [[ "$_lu_node_pin" != "$nvmrc" || ! "$_lu_npm_pin" =~ $_LU_VERIFY_EXACT ]]; then
    # The pins are read with node, so without one they stay unknown here.
    if [[ -n "$_lu_node_version" ]]; then
      printf '%s FAIL: package.json engines must pin node %s (the .nvmrc release) and an exact npm (found node "%s", npm "%s"). Restore the checked-in files: git -C %q checkout -- .nvmrc package.json\n' \
        "$label" "$nvmrc" "$_lu_node_pin" "$_lu_npm_pin" "$root" >&2
      return 1
    fi
  fi
  nvm_sh="${NVM_DIR:-${HOME:-}/.nvm}/nvm.sh"
  if [[ -s "$nvm_sh" ]]; then
    # nvm is optional: a script that fails under errexit or nounset must not stop us.
    set +eu
    # shellcheck disable=SC1090
    . "$nvm_sh" >/dev/null 2>&1
    if declare -F nvm >/dev/null; then
      nvm use "$nvmrc" >/dev/null 2>&1
    fi
    [[ "$flags" == *e* ]] && set -e
    [[ "$flags" == *u* ]] && set -u
    if _lu_verify_versions "$root" "$nvmrc"; then
      return 0
    fi
  fi
  node_pin="${_lu_node_pin:-$nvmrc}"
  npm_pin="${_lu_npm_pin:-unknown}"
  if declare -F nvm >/dev/null; then
    printf -v fix 'cd %q && nvm install && nvm use' "$root"
  else
    printf -v fix 'install Node %s from https://nodejs.org/dist/v%s/ and put its bin directory first on PATH' \
      "$node_pin" "$node_pin"
  fi
  echo "$label FAIL: need Node $node_pin (.nvmrc, package.json engines.node) with its bundled npm $npm_pin (engines.npm); found Node ${_lu_node_version:-none} and npm ${_lu_npm_version:-none}. Run: $fix" >&2
  return 1
}

# _lu_verify_versions ROOT NVMRC: read node, npm and the engines pins into
# _lu_* globals; return 0 only when all of them match.
_lu_verify_versions() {
  local root="$1" nvmrc="$2"
  _lu_node_version="" _lu_npm_version="" _lu_node_pin="" _lu_npm_pin=""
  if _lu_node_version="$(node -v 2>/dev/null)"; then
    # shellcheck disable=SC2016  # JavaScript template literal, expanded by node
    # A comma separator keeps an empty first field in place.
    IFS=, read -r _lu_node_pin _lu_npm_pin < <(
      node -p 'const e = require(process.argv[1]).engines || {}; `${e.node || ""},${e.npm || ""}`' \
        "$root/package.json" 2>/dev/null
    ) || true
  else
    _lu_node_version=""
  fi
  _lu_npm_version="$(npm --version 2>/dev/null)" || _lu_npm_version=""
  [[ "$_lu_node_pin" == "$nvmrc" && "$_lu_npm_pin" =~ $_LU_VERIFY_EXACT &&
     "$_lu_node_version" == "v$nvmrc" && "$_lu_npm_version" == "$_lu_npm_pin" ]]
}

# lu_verify_site_install_hint ROOT: how to repair a missing locked site install,
# as a command that works from any directory. A site/node_modules link (even a
# dangling one) belongs to another tree, which npm ci would empty through the link.
lu_verify_site_install_hint() {
  local modules="$1/site/node_modules" site
  if [[ -L "$modules" ]]; then
    printf 'site/node_modules is a link to %s, which this checkout must not reinstall; repair that install, or remove the link (rm -- %q) and rerun launch.sh to install from site/package-lock.json' \
      "$(readlink -- "$modules")" "$modules"
    return 0
  fi
  printf -v site '%q' "$1/site"
  printf 'run: cd %s && %s' "$site" "$LU_VERIFY_SITE_INSTALL"
}
