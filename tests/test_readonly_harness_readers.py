"""Read-only harness boundaries preserve exact paths and refuse mutation (#9662)."""

from __future__ import annotations

import ast
import builtins

import pytest
from lu_machinery.common.repo_root import machinery_path

READERS = (
    "agent_runtime/acpx_discuss.py",
    "scripts/ai_agent_bridge/_opencode.py",
    "scripts/api/fleet_router.py",
    "scripts/api/fleet_workers_collect.py",
    "scripts/api/runtime_router.py",
    "scripts/fleet_comms/authority.py",
    "scripts/fleet_comms/efficiency_metrics.py",
    "scripts/orchestration/task_family/codex_state.py",
)
# Product readers (scripts/review/integration_check.py and scripts/verification/{bench_check_text,
# check_text,verify_antonenko_citations,vesum}.py) import the installed lu_machinery release
# directly (#13030): it is importable in every flavor, so they hold no fallback block to check.


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("missing", ["scripts", "sqlite3"])
def test_helper_fallback_only_handles_missing_scripts(reader, missing):
    """Installed readers propagate missing dependencies instead of selecting a legacy import."""
    source = machinery_path(reader.removeprefix("scripts/")).read_text()
    tree = ast.parse(source)
    imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)
               and node.module == "lu_machinery.lib.readonly_sqlite"]
    assert imports, reader
    attempted = []

    def controlled_import(name, *args, **kwargs):
        attempted.append(name)
        raise ModuleNotFoundError(name=missing)

    namespace = {"__builtins__": {**vars(builtins), "__import__": controlled_import}}
    code = compile(ast.Module(body=imports, type_ignores=[]), reader, "exec")
    with pytest.raises(ModuleNotFoundError) as error:
        exec(code, namespace)
    assert error.value.name == missing
    assert attempted == ["lu_machinery.lib.readonly_sqlite"]
