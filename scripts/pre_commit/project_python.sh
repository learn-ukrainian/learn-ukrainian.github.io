#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "[project-python] ERROR: missing Python command arguments" >&2
  exit 2
fi

# LU_PYTHON is the host binding's machinery interpreter, supplied by the hook delegator or the
# caller's environment. Its release reads and validates the binding, which alone names the
# product's interpreter; the invocation checkout never selects it. Product commands need the
# product's own environment (the mypy ratchet runs mypy), which the machinery runtime lacks.
if [[ "${LU_PYTHON:-}" != /* || ! -f "$LU_PYTHON" || ! -x "$LU_PYTHON" ]]; then
  echo "[project-python] ERROR [missing_interpreter_binding]: LU_PYTHON must name an absolute executable." >&2
  exit 127
fi
product_python="$("$LU_PYTHON" -I -B -c '
import sys
from lu_machinery.host_context import HostContext, HostContextError, load_host_context

try:
    context = load_host_context(role="state")
except HostContextError as exc:
    sys.exit(f"[project-python] ERROR [{exc.code}] {exc}")
if not isinstance(context, HostContext):
    sys.exit("[project-python] ERROR [invalid_role] the product interpreter requires a full host binding")
print(context.products[context.default_product].python)
' </dev/null)" || exit 127
if [[ "$product_python" != /* || ! -f "$product_python" || ! -x "$product_python" ]]; then
  echo "[project-python] ERROR [missing_product_interpreter]: the host binding's product interpreter is not an executable file." >&2
  exit 127
fi
exec "$product_python" "$@"
