#!/usr/bin/env bash
# Refuse a service start when the configured data volume is not mounted.
set -euo pipefail

EX_CONFIG=78
UUID_FILE=/etc/learn-ukrainian/data-volume.uuid
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

usage() {
    cat <<'EOF'
Usage: data_volume_guard.sh [-- COMMAND [ARG ...] | --status | --help]

Check that repository data/ resolves to the configured volume UUID. Use this
before starting a service or timer; on hosts without the UUID file it is a no-op.

Arguments:
  -- COMMAND [ARG ...]  Check the mount, then replace this process with COMMAND.
  --status              Print the volume UUID, root disk, or unknown identity.
  --help                Show this help.

Examples:
  bash scripts/storage/data_volume_guard.sh
  bash scripts/storage/data_volume_guard.sh -- /usr/bin/env true
  bash scripts/storage/data_volume_guard.sh --status

Outputs: no files or database writes; errors go to stderr.
Exit codes: 0 on success; 78 when the configured mount is unavailable or wrong;
            2 for invalid arguments.
Related: packaging/systemd/dropins/ and docs/runbooks/storage-topology.md (#8804).
EOF
}

mode=check
case "${1:-}" in
    --help|-h) usage; exit 0 ;;
    --status) [[ $# -eq 1 ]] || { usage >&2; exit 2; }; mode=status ;;
    --) shift; [[ $# -gt 0 ]] || { usage >&2; exit 2; }; mode='exec' ;;
    '') ;;
    *) usage >&2; exit 2 ;;
esac

if [[ ! -e "$UUID_FILE" ]]; then
    if [[ -L "$UUID_FILE" ]]; then
        echo "data volume guard: UUID file is a dangling symlink" >&2
        exit "$EX_CONFIG"
    fi
    [[ "$mode" == status ]] && echo 'data: root disk'
    [[ "$mode" == exec ]] && exec "$@"
    exit 0
fi

if [[ ! -f "$UUID_FILE" || ! -r "$UUID_FILE" ]]; then
    echo "data volume guard: cannot read UUID file" >&2
    exit "$EX_CONFIG"
fi
expected="$(tr -d '[:space:]' < "$UUID_FILE")"
if [[ ! "$expected" =~ ^[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}$ ]]; then
    echo "data volume guard: UUID file is invalid" >&2
    exit "$EX_CONFIG"
fi

mount_info="$(findmnt -no UUID,SOURCE -T "$REPO_ROOT/data" 2>/dev/null)" || mount_info=''
actual="${mount_info%%[[:space:]]*}"
if [[ -z "$mount_info" || "${actual,,}" != "${expected,,}" ]]; then
    if [[ "$mode" == status ]]; then
        root_info="$(findmnt -no UUID,SOURCE -T / 2>/dev/null)" || root_info=''
        root_uuid="${root_info%%[[:space:]]*}"
        if [[ -n "$actual" && -n "$root_uuid" && "${actual,,}" != "${root_uuid,,}" ]]; then
            echo "data: volume $actual (expected $expected)"
        elif [[ -n "$root_info" ]]; then
            echo 'data: root disk'
        else
            echo 'data: unknown'
        fi
        exit 0
    fi
    echo "data volume guard: data/ is not mounted from configured UUID $expected" >&2
    exit "$EX_CONFIG"
fi

[[ "$mode" == status ]] && { echo "data: volume $expected"; exit 0; }
[[ "$mode" == exec ]] && exec "$@"
exit 0
