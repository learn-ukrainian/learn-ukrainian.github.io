#!/usr/bin/env bash
# Install bubblewrap and grant user namespaces on disposable CI VMs only.
# Optional package arguments keep shard dependencies in the same apt transaction.
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"

missing=()
for pkg in bubblewrap "$@" apparmor; do
  dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Installing missing native packages: ${missing[*]}"
  # One 170 s transaction plus 5 s kill grace leaves 65 s of test_env.sh's
  # 240 s wait for the AppArmor grant, bwrap check and PostgreSQL startup.
  # Let apt handle transient fetch failures and both dpkg locks. A short
  # install-only timeout can interrupt unpacking and leave dpkg unfinished.
  sudo timeout --kill-after=5 170 bash -euc '
    rm -f /etc/apt/sources.list.d/*chrome* /etc/apt/sources.list.d/*google* \
      /var/lib/apt/lists/*chrome* /var/lib/apt/lists/*google*
    apt_opts=(-o Acquire::Retries=3 -o Acquire::http::Timeout=15 -o Acquire::https::Timeout=15 -o DPkg::Lock::Timeout=110)
    apt-get "${apt_opts[@]}" update -qq
    apt-get "${apt_opts[@]}" install -y --no-install-recommends "$@"
  ' _ "${missing[@]}"
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
