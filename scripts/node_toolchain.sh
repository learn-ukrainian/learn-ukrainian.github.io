# shellcheck shell=bash
# Sourced by CONTRIBUTING.md step 3 and the Cursor verify skill's launch.sh,
# doctor.sh, drive-playwright.sh and run-checks.sh; not run directly.
#
# The checked-in Node contract: the exact release in .nvmrc, equal to package.json
# engines.node, run with its bundled npm at engines.npm. That npm enforces the
# install-script policy in .npmrc and site/.npmrc, so this file holds no versions.

# The locked site install, the same commands CONTRIBUTING.md and CI run.
LU_VERIFY_SITE_INSTALL='npm ci --ignore-scripts && npm rebuild --ignore-scripts=false'
_LU_VERIFY_EXACT='^[0-9]+\.[0-9]+\.[0-9]+$'

# lu_verify_toolchain ROOT LABEL
# Return 0 when node and npm on PATH match the checked-in pins, selecting the
# exact release through nvm first when the PATH does not match. Otherwise print
# why on stderr, with the command that repairs it, and return 1.
lu_verify_toolchain() {
  local root="$1" label="$2" nvmrc="" fix nvm_sh nvm_state=absent installed="" use_status="" load note="" tool found flags="$-"
  if [[ -f "$root/.nvmrc" ]]; then
    nvmrc="$(<"$root/.nvmrc")"
    nvmrc="${nvmrc//[[:space:]]/}"
    nvmrc="${nvmrc#v}"
  fi
  # Checked before nvm sees it: an alias such as lts/* selects a moving release.
  if [[ ! "$nvmrc" =~ $_LU_VERIFY_EXACT ]]; then
    printf '%s FAIL: .nvmrc must hold an exact Node release (found "%s"). Restore the checked-in file: git -C %q checkout -- .nvmrc\n' \
      "$label" "$nvmrc" "$root" >&2
    return 1
  fi
  if _lu_verify_versions "$root" "$nvmrc"; then
    return 0
  fi
  _lu_verify_manifest "$root" "$label" "$nvmrc" || return 1
  nvm_sh="${NVM_DIR:-${HOME:-}/.nvm}/nvm.sh"
  if [[ -s "$nvm_sh" ]]; then
    # nvm is optional: a script that fails under errexit or nounset must not stop
    # us. --no-use keeps its default alias off PATH until the exact selection.
    set +eu
    # shellcheck disable=SC1090
    . "$nvm_sh" --no-use >/dev/null 2>&1
    nvm_state=broken
    if declare -F nvm >/dev/null && nvm --version >/dev/null 2>&1; then
      nvm_state=ok
      [[ "$(nvm version "$nvmrc" 2>/dev/null)" == "v$nvmrc" ]] && installed=1
      if [[ -n "$installed" ]]; then
        nvm use "$nvmrc" >/dev/null 2>&1
        use_status=$?
      fi
    fi
    [[ "$flags" == *e* ]] && set -e
    [[ "$flags" == *u* ]] && set -u
    # A failed nvm use may still have changed PATH, so only a successful
    # selection can pass here.
    if _lu_verify_versions "$root" "$nvmrc" && [[ "$use_status" == 0 ]]; then
      return 0
    fi
    # Node may have become available through nvm, so the pins can be read now.
    _lu_verify_manifest "$root" "$label" "$nvmrc" || return 1
  fi
  # Every repair loads nvm first: nvm is a shell function, so the caller's shell
  # does not have it just because this check sourced it. --no-use stops nvm
  # selecting a default or the absent .nvmrc release while it loads. A shell
  # whose dot command drops that argument may fail that selection; loading
  # still counts once the nvm function exists.
  printf -v load 'cd %q && { . %q --no-use || command -v nvm >/dev/null; }' "$root" "$nvm_sh"
  if [[ "$nvm_state:$installed:$use_status" == ok:1:0 ]]; then
    # nvm selected the release. A node or npm earlier on PATH than nvm's own
    # shadows it; only nvm's own npm at the wrong version needs a reinstall.
    for tool in node npm; do
      found="$(command -v "$tool" 2>/dev/null)" || found=""
      if [[ "$found" != "${NVM_BIN:-}/$tool" ]]; then
        note="nvm selected Node $nvmrc, but $tool on PATH is ${found:-missing}, not ${NVM_BIN:-nvm}/$tool; remove that PATH entry, then run: "
        fix="$load && nvm use $nvmrc"
        break
      fi
    done
  fi
  case "$nvm_state:$installed:$use_status" in
    ok:1:0)
      # nvm refuses to uninstall the active release; deactivating none is fine.
      [[ -n "$note" ]] ||
        fix="$load && { nvm deactivate >/dev/null 2>&1 || :; } && nvm uninstall $nvmrc && nvm install $nvmrc && nvm use $nvmrc"
      ;;
    ok:1:*)
      # Installed but not selectable: show nvm's own error rather than reinstalling.
      note="nvm use $nvmrc failed with exit status $use_status; to see why, run: "
      fix="$load && nvm use $nvmrc"
      ;;
    ok::*) fix="$load && nvm install $nvmrc && nvm use $nvmrc" ;;
    *)
      printf -v fix 'nvm (the toolchain manager CONTRIBUTING.md requires) is %s at %q; install it from https://github.com/nvm-sh/nvm#installing-and-updating, then run: %s && nvm install %s && nvm use %s' \
        "$([[ "$nvm_state" == broken ]] && echo 'not working' || echo 'missing')" "$nvm_sh" "$load" "$nvmrc" "$nvmrc"
      ;;
  esac
  echo "$label FAIL: need Node $nvmrc (.nvmrc, package.json engines.node) with its bundled npm ${_lu_npm_pin:-at engines.npm}; found Node ${_lu_node_version:-none} and npm ${_lu_npm_version:-none}. ${note:-Run: }$fix" >&2
  return 1
}

# _lu_verify_manifest ROOT LABEL NVMRC: when node could read package.json, refuse
# engines that do not pin the .nvmrc release and an exact npm. Without node the
# pins stay unknown and the toolchain repair comes first.
_lu_verify_manifest() {
  [[ -z "$_lu_node_version" ]] && return 0
  [[ "$_lu_node_pin" == "$3" && "$_lu_npm_pin" =~ $_LU_VERIFY_EXACT ]] && return 0
  printf '%s FAIL: package.json engines must pin node %s (the .nvmrc release) and an exact npm (found node "%s", npm "%s"). Restore the checked-in files: git -C %q checkout -- .nvmrc package.json\n' \
    "$2" "$3" "$_lu_node_pin" "$_lu_npm_pin" "$1" >&2
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
