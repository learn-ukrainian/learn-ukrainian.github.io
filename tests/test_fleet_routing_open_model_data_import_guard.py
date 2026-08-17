"""Mechanical tripwire: fleet routing must not import open_model_data pins.

#6870 item 3 / #6898 exempted project-local open_model_data harness/model pins
from fleet seat alignment because no fleet/launcher/dispatcher consumer reads
them. That exemption was convention-only until #6922 — this AST guard makes it
a gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Fleet routing surfaces only. WHY this list (not broader scripts/): #6870
# item 3 / #6898 — the exemption rests on fleet consumers never reading
# scripts/projects/open_model_data pins (they use model_catalog instead).
_FLEET_ROUTING_SURFACES: tuple[str, ...] = (
    "scripts/delegate.py",
    "scripts/agent_runtime",
    "scripts/ai_agent_bridge",
    # Launcher shell scripts call these Python helpers (scripts/lib/*.py).
    "scripts/lib",
)

_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "scripts.projects.open_model_data",
    # Stripped flavor when only scripts/ is on sys.path.
    "projects.open_model_data",
)


def _iter_surface_python_files() -> list[Path]:
    files: list[Path] = []
    for rel in _FLEET_ROUTING_SURFACES:
        path = _REPO_ROOT / rel
        if path.is_file():
            assert path.suffix == ".py", f"surface file must be Python: {rel}"
            files.append(path)
            continue
        assert path.is_dir(), f"missing fleet routing surface: {rel}"
        files.extend(sorted(path.rglob("*.py")))
    return files


def _imported_module_names(tree: ast.AST) -> list[tuple[int, str]]:
    """Return (lineno, fully-qualified module) for Import / ImportFrom nodes."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            # from pkg import sub → pkg.sub (catches from scripts.projects import open_model_data)
            if any(alias.name == "*" for alias in node.names):
                found.append((node.lineno, node.module))
            else:
                for alias in node.names:
                    found.append((node.lineno, f"{node.module}.{alias.name}"))
    return found


def _is_forbidden(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in _FORBIDDEN_PREFIXES
    )


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


def find_open_model_data_imports(path: Path) -> list[str]:
    """AST-scan one file; return human-readable violation strings."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{_display_path(path)}: syntax error: {exc}"]

    violations: list[str] = []
    for lineno, module_name in _imported_module_names(tree):
        if _is_forbidden(module_name):
            violations.append(f"{_display_path(path)}:{lineno}: imports {module_name!r}")
    return violations


def test_fleet_routing_surfaces_do_not_import_open_model_data() -> None:
    """No fleet routing module may import scripts.projects.open_model_data (#6922)."""
    surfaces = _iter_surface_python_files()
    assert surfaces, "fleet routing surface list resolved to zero Python files"

    violations: list[str] = []
    for path in surfaces:
        violations.extend(find_open_model_data_imports(path))

    assert not violations, (
        "Fleet routing code must not import open_model_data pins "
        "(#6870 item 3 / #6898 / #6922):\n" + "\n".join(violations)
    )


def test_guard_detects_forbidden_import_on_synthetic_module(tmp_path: Path) -> None:
    """Mutation-check helper: a dummy open_model_data import must trip the scanner."""
    synthetic = tmp_path / "synthetic_fleet_module.py"
    synthetic.write_text(
        "from scripts.projects.open_model_data import model_view_exporter\n",
        encoding="utf-8",
    )
    hits = find_open_model_data_imports(synthetic)
    assert hits, "expected AST guard to flag a dummy open_model_data import"
    assert "scripts.projects.open_model_data" in hits[0]
