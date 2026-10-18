#!/bin/sh
# Run an Entire capture command behind the private-route guard (#10846).
# Every Entire hook entry point calls this instead of `entire`; see
# scripts/entire/capture_guard.py --help. Always exits 0: a refused, failed or
# timed-out capture never blocks the host session, a commit or a push.
root="$(cd "$(dirname "$0")/../.." && pwd -P)" || exit 0
python="$root/.venv/bin/python"
if [ ! -x "$python" ]; then
    common="$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" &&
        python="$(dirname "$common")/.venv/bin/python"
fi
if [ ! -x "$python" ]; then
    echo "[entire] capture refused (project_python_missing): no checkpoint written" >&2
    exit 0
fi
"$python" -I "$root/scripts/entire/capture_guard.py" "$@" ||
    echo "[entire] capture guard failed (exit $?): no checkpoint written" >&2
exit 0
