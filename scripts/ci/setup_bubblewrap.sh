#!/usr/bin/env bash
# Install bubblewrap and grant user namespaces on disposable CI VMs only.
# Optional package arguments keep shard dependencies in the same apt transaction.
# Use image package lists first; switch to fallback mirrors only if that fails.
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
  apt_opts=(-o Acquire::Retries=0 -o Acquire::http::Timeout=10 -o Acquire::https::Timeout=10)
  # Hard process-level budgets (40 s + 15 s + 65 s + 55 s = 175 s including 5 s kill grace)
  # leave 65 s inside test_env.sh's 240 s wait budget for apparmor/bwrap and PostgreSQL startup.
  if ! sudo timeout --kill-after=5 35 apt-get "${apt_opts[@]}" install -y --no-install-recommends "${missing[@]}"; then
    # During the 2026-11-11 Canonical *.ubuntu.com DNS outage (status.canonical.com),
    # azure.archive.ubuntu.com, archive.ubuntu.com and security.ubuntu.com all failed to
    # resolve, and refreshing the default mirror list first blew test_env.sh's 240 s budget.
    # Switch immediately to Tier-1 HTTPS Ubuntu mirrors outside *.ubuntu.com (keeping
    # archive.ubuntu.com last); apt still verifies Signed-By ubuntu-archive-keyring.gpg.
    echo 'apt install failed against the image package lists; switching to fallback HTTPS Ubuntu mirrors'
    sudo timeout --kill-after=5 10 dpkg --configure -a
    printf '%s\tpriority:%d\n' \
      'https://mirrors.edge.kernel.org/ubuntu/' 1 \
      'https://ftp.osuosl.org/pub/ubuntu/' 2 \
      'https://archive.ubuntu.com/ubuntu/' 3 | sudo tee /etc/apt/apt-mirrors.txt >/dev/null
    sudo chmod 0644 /etc/apt/apt-mirrors.txt
    if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
      sudo sed -i -E \
        's@^(URIs:[[:space:]]+).*(https?://([a-z0-9.-]+\.)?ubuntu\.com/ubuntu/?|mirror\+file:/etc/apt/apt-mirrors\.txt)([[:space:]]|$).*@\1mirror+file:/etc/apt/apt-mirrors.txt@' \
        /etc/apt/sources.list.d/ubuntu.sources
    fi
    if [ -f /etc/apt/sources.list ]; then
      sudo sed -i -E \
        '/^[[:space:]]*#/! s@https?://([a-z0-9.-]+\.)?ubuntu\.com/ubuntu/?([[:space:]]|$)@mirror+file:/etc/apt/apt-mirrors.txt\2@g' \
        /etc/apt/sources.list
    fi
    sudo timeout --kill-after=5 60 apt-get "${apt_opts[@]}" update -qq
    sudo timeout --kill-after=5 50 apt-get "${apt_opts[@]}" install -y --no-install-recommends "${missing[@]}"
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
