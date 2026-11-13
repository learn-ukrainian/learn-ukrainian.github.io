#!/usr/bin/env bash
# Install bubblewrap and grant user namespaces on disposable CI VMs only.
# Optional package arguments keep shard dependencies in the same apt transaction.
# Use image package lists first; switch to fallback mirrors only if that fails.
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"

# True when /var/lib/dpkg/lock is held by a POSIX write lock. dpkg uses fcntl
# (F_SETLK); flock(1) does not contend with that lock and is not a probe.
# /proc/locks prints the id as major:minor:inode with the same hex width as printf %02x.
dpkg_database_lock_held() {
  local dev inode major minor token
  dev=$(stat -c %d /var/lib/dpkg/lock 2>/dev/null) || return 1
  inode=$(stat -c %i /var/lib/dpkg/lock 2>/dev/null) || return 1
  # glibc major()/minor() for dev_t. High major bits stay 0 on runner disks.
  major=$(( (dev & 0xfff00) >> 8 ))
  minor=$(( (dev & 0xff) | ((dev >> 12) & 0xffffff00) ))
  printf -v token '%02x:%02x:%s' "$major" "$minor" "$inode"
  awk -v token="$token" '
    $2 == "POSIX" && $4 == "WRITE" && $6 == token { found = 1 }
    END { exit !found }
  ' /proc/locks
}

# apt-get does not inherit the `apt` binary's Dpkg::Lock::Timeout (120 on a
# non-tty). timeout(1) then kills the wait and leaves no lock text, which this
# script used to treat as a mirror failure.
apt_failure_is_dpkg_lock() {
  local rc="$1" log="$2"
  if grep -E -q 'Could not get lock|was locked by another process|Waiting for cache lock' "$log"; then
    return 0
  fi
  # 124: timeout sent TERM. 137: the command needed KILL.
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    dpkg_database_lock_held
    return
  fi
  return 1
}

# dpkg itself has no lock timeout. Retry until the existing 10 s cap; the 5 s
# kill grace stays on the timeout(1) wrapper, as in the other apt budgets.
dpkg_configure_a() {
  sudo timeout --kill-after=5 10 bash -c '
    deadline=$((SECONDS + 8))
    while true; do
      err=$(dpkg --configure -a 2>&1) && { printf "%s\n" "$err"; exit 0; }
      rc=$?
      printf "%s\n" "$err" >&2
      case "$err" in
        *"was locked by another process"*) ;;
        *) exit "$rc" ;;
      esac
      [ "$SECONDS" -lt "$deadline" ] || exit "$rc"
      sleep 1
    done
  '
}

sudo rm -f /etc/apt/sources.list.d/*chrome* /etc/apt/sources.list.d/*google* \
  /var/lib/apt/lists/*chrome* /var/lib/apt/lists/*google*
missing=()
for pkg in bubblewrap "$@" apparmor; do
  dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "Installing missing native packages: ${missing[*]}"
  # Lock waits sit inside the process caps. apt reports the lock itself;
  # a longer wait would be cut off by timeout(1) and look like a mirror failure.
  apt_opts=(-o Acquire::Retries=0 -o Acquire::http::Timeout=10 -o Acquire::https::Timeout=10 -o DPkg::Lock::Timeout=30)
  # Hard process-level budgets include the 5 s kill grace. The two paths do not stack.
  #   mirror failure: 40 s + 15 s + 65 s + 55 s = 175 s
  #   dpkg lock:      40 s + 135 s = 175 s (one retry in place of the mirror fallback)
  # Either path leaves 65 s of test_env.sh's 240 s wait for apparmor/bwrap and PostgreSQL startup.
  install_log="${RUNNER_TEMP}/bwrap-apt-install.log"
  set +e
  sudo timeout --kill-after=5 35 apt-get "${apt_opts[@]}" install -y --no-install-recommends "${missing[@]}" 2>&1 | tee "$install_log"
  install_rc=${PIPESTATUS[0]}
  set -e
  if [ "$install_rc" -ne 0 ]; then
    if apt_failure_is_dpkg_lock "$install_rc" "$install_log"; then
      echo 'apt install failed because the dpkg lock was held; not switching mirrors'
      # 130 s + 5 s kill grace = 135 s, the mirror path's 15 s + 65 s + 55 s.
      # Lock::Timeout=110 leaves the rest of the cap for the install once the lock clears.
      sudo timeout --kill-after=5 130 apt-get "${apt_opts[@]}" -o DPkg::Lock::Timeout=110 install -y --no-install-recommends "${missing[@]}"
    else
      # During the 2026-11-11 Canonical *.ubuntu.com DNS outage (status.canonical.com),
      # azure.archive.ubuntu.com, archive.ubuntu.com and security.ubuntu.com all failed to
      # resolve, and refreshing the default mirror list first blew test_env.sh's 240 s budget.
      # Switch immediately to Tier-1 HTTPS Ubuntu mirrors outside *.ubuntu.com (keeping
      # archive.ubuntu.com last); apt still verifies Signed-By ubuntu-archive-keyring.gpg.
      echo 'apt install failed against the image package lists; switching to fallback HTTPS Ubuntu mirrors'
      dpkg_configure_a
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
