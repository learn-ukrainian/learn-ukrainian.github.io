#!/usr/bin/env bash
# Catalog-backed launcher defaults (#9302). Source this helper; it never launches.
# launcher_role_model <checkout-root> <role> [transport]
# Prints one active wire ID. Missing, ambiguous or inactive defaults fail closed.

launcher_role_model() {
    if [[ $# -lt 2 || $# -gt 3 ]]; then
        echo 'Usage: launcher_role_model <checkout-root> <role> [transport]' >&2
        return 2
    fi
    local root="$1" role="$2" transport="${3:-}" py
    source "${BASH_SOURCE[0]%/*}/project_interpreter.sh" || return 2
    py="$(project_interpreter_resolve "$root")" || return 2
    (
        cd "$root" || exit 2
        "$py" - "$role" "$transport" <<'PY'
import sys

from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, resolve_role

try:
    catalog = load_model_catalog()
    resolution = resolve_role(sys.argv[1], catalog=catalog, purpose="inspect", transport=sys.argv[2] or None)
    eligible = [row for row in resolution.candidates if not row.exclusion_reasons]
    if not eligible or any(catalog["models"][row.model_id]["lifecycle"] != "active" for row in eligible):
        raise ModelCatalogError("launcher default requires an active eligible holder")
    pins = {row.wire_id for row in eligible}
    if len(pins) != 1:
        raise ModelCatalogError("launcher default is ambiguous; select a singleton role and transport")
    print(pins.pop())
except (ModelCatalogError, OSError, ValueError) as exc:
    print(f"Error: {exc}", file=sys.stderr)
    sys.exit(2)
PY
    )
}
