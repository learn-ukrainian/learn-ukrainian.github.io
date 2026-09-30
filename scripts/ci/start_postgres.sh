#!/usr/bin/env bash
# Native test dependencies and the PostgreSQL 16 server for a CI pytest shard.
#
# The ubuntu runner image carries PostgreSQL 16, libpq-dev and apparmor; only
# bubblewrap is missing. Install what is absent from the image's package
# lists (no `apt-get update` unless that install fails), grant bwrap user
# namespaces, then start cluster 16/main and prove it is the server behind
# LEARN_UKRAINIAN_CP_PG_DSN. Any failure exits non-zero. Tests that need their
# own clusters (initdb as the runner user) use the same binaries.
set -euo pipefail

: "${LEARN_UKRAINIAN_CP_PG_DSN:?LEARN_UKRAINIAN_CP_PG_DSN must be set}"
: "${RUNNER_TEMP:?RUNNER_TEMP must be set}"

sudo rm -f /etc/apt/sources.list.d/*chrome* /etc/apt/sources.list.d/*google* \
  /var/lib/apt/lists/*chrome* /var/lib/apt/lists/*google*
missing=()
for pkg in bubblewrap postgresql-16 libpq-dev apparmor; do
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

if ! pg_lsclusters --no-header | grep -q '^16 main '; then
  sudo pg_createcluster 16 main
fi
# Start errors are not suppressed; only an already-online cluster is skipped.
if ! pg_lsclusters --no-header | awk '$1 == "16" && $2 == "main" && $4 == "online" {found = 1} END {exit !found}'; then
  sudo pg_ctlcluster 16 main start
fi
ready=""
for _ in $(seq 1 30); do
  if pg_isready -h localhost -p 5432 -q; then ready=1; break; fi
  sleep 2
done
if [ -z "$ready" ]; then
  echo "::error::PostgreSQL 16 was not ready on localhost:5432 within 60 s" >&2
  pg_lsclusters >&2 || true
  sudo tail -n 40 /var/log/postgresql/postgresql-16-main.log >&2 || true
  exit 1
fi
# 16/main must own the DSN port (5432), not some other server listening there.
cluster="$(pg_lsclusters --no-header | awk '$1 == "16" && $2 == "main" {print $3 " " $4}')"
if [ "$cluster" != "5432 online" ]; then
  echo "::error::PostgreSQL cluster 16/main is '${cluster:-missing}', expected '5432 online'" >&2
  pg_lsclusters >&2
  exit 1
fi
sudo -u postgres psql -p 5432 -v ON_ERROR_STOP=1 -q <<'SQL'
ALTER ROLE postgres WITH PASSWORD 'postgres';
SELECT 'CREATE DATABASE lu' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lu')\gexec
SQL
# The exact DSN the tests use must connect, report major version 16, and
# serve the 16/main data directory.
version_num="$(PGPASSWORD=postgres psql "$LEARN_UKRAINIAN_CP_PG_DSN" -v ON_ERROR_STOP=1 -qtAc 'SHOW server_version_num')"
echo "PostgreSQL server_version_num=${version_num}"
if [ "${version_num:0:2}" != "16" ]; then
  echo "::error::DSN server reports version ${version_num}, expected major 16" >&2
  exit 1
fi
expected_dir="$(pg_lsclusters --no-header | awk '$1 == "16" && $2 == "main" {print $6}')"
dsn_dir="$(PGPASSWORD=postgres psql "$LEARN_UKRAINIAN_CP_PG_DSN" -v ON_ERROR_STOP=1 -qtAc 'SHOW data_directory')"
echo "DSN data_directory=${dsn_dir} (16/main: ${expected_dir})"
if [ -z "$expected_dir" ] || [ "$dsn_dir" != "$expected_dir" ]; then
  echo "::error::DSN server data_directory '${dsn_dir}' is not the 16/main data directory '${expected_dir:-missing}'" >&2
  pg_lsclusters >&2
  exit 1
fi
