#!/usr/bin/env bash
# Install bubblewrap and grant user namespaces on disposable CI VMs only.
# Optional package arguments keep shard dependencies in the same apt transaction.
# Use image package lists first; refresh only if the initial install fails.
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"

sudo rm -f /etc/apt/sources.list.d/*chrome* /etc/apt/sources.list.d/*google* \
  /var/lib/apt/lists/*chrome* /var/lib/apt/lists/*google*
missing=()
for pkg in bubblewrap "$@" apparmor; do
  dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Installing missing native packages: ${missing[*]}"
  if ! sudo apt-get install -y --no-install-recommends "${missing[@]}"; then
    echo 'apt install failed against the image package lists; refreshing and retrying'
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends "${missing[@]}"
  fi
fi

# Ubuntu-hosted runners require an application-specific userns grant. This
# profile belongs only to the disposable CI VM.
if [ -f /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
  cat > "${RUNNER_TEMP}/v4-ci-bwrap.apparmor" <<'PROFILE'
abi <abi/4.0>,
include <tunables/global>
profile v4_ci_bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,
}
PROFILE
  sudo apparmor_parser -r "${RUNNER_TEMP}/v4-ci-bwrap.apparmor"
fi
bwrap --unshare-user --unshare-pid --ro-bind / / -- /usr/bin/true
