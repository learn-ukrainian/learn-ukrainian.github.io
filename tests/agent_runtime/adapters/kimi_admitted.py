"""A git worktree and tool_config a Kimi adapter test uses to pass the coding-only gate."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.agent_runtime.kimi_admission import OWNED_PATHS_KEY

OWNED_FILE = "site/src/components/Widget.tsx"


def admitted_tool_config(worktree: Path, tool_config: dict | None = None) -> dict:
    """Make ``worktree`` a committed repo owning one Cyrillic-free UI file; return ``tool_config`` declaring it."""
    if not (worktree / ".git").exists():
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(
            GIT_AUTHOR_NAME="t",
            GIT_AUTHOR_EMAIL="t@example.com",
            GIT_COMMITTER_NAME="t",
            GIT_COMMITTER_EMAIL="t@example.com",
        )
        target = worktree / OWNED_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("export const Widget = () => null;\n", encoding="utf-8")
        for args in (["init", "-q"], ["add", OWNED_FILE], ["commit", "-q", "-m", "base"]):
            subprocess.run(["git", *args], cwd=worktree, env=env, check=True, capture_output=True, timeout=30)
    return {**(tool_config or {}), OWNED_PATHS_KEY: [OWNED_FILE]}


def install_historical_kimi_catalog(tmp_path: Path, monkeypatch) -> Path:
    """Isolate retained wrapper ABI assertions from the production retirement.

    This synthetic catalog is private to these tests. Production retirement is
    covered separately at dispatch, the runner, the adapter and the real wrapper.
    No checkout catalog or executable route is changed.
    """
    import importlib
    import json
    import sys
    from copy import deepcopy

    import pytest

    from scripts.review.model_catalog import (
        ModelCatalogError,
        load_model_catalog,
        require_execution_model,
        resolve_kimi_model,
    )

    catalog = deepcopy(load_model_catalog())
    for identity, entry in catalog["models"].items():
        if "kimi" in identity:
            with pytest.raises(ModelCatalogError, match="retired in the model catalog"):
                require_execution_model(identity, transport="native_kimi", catalog=catalog)
            entry["lifecycle"] = "active"
            entry["transports"] = ["native_kimi"]
    catalog["review_scheduler"]["endpoints"]["kimicc"]["models"] = [
        identity for identity in catalog["models"]
        if "kimi" in identity and identity not in {"kimi-code/k3-256k", "kimi-k3-max"}
    ]
    for name in ("scripts.agent_runtime.adapters.kimicc", "agent_runtime.adapters.kimicc"):
        module = importlib.import_module(name)
        monkeypatch.setattr(module, "load_model_catalog", lambda: catalog)
        monkeypatch.setattr(module, "resolve_kimi_model", lambda model: resolve_kimi_model(model, catalog))
    monkeypatch.setattr("scripts.review.model_catalog.resolve_kimi_model", lambda model: resolve_kimi_model(model, catalog))
    fixture_path = tmp_path / "historical-kimi-catalog.json"
    fixture_path.write_text(json.dumps(catalog))
    root = Path(__file__).resolve().parents[3]
    shim = tmp_path / "historical-catalog-interpreter"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"sys.path[:0] = {[str(root), str(root / 'scripts')]!r}\n"
        "if len(sys.argv) > 1 and sys.argv[1].endswith('/scripts/review/model_catalog.py'):\n"
        "    from scripts.review import model_catalog\n"
        f"    with open({str(fixture_path)!r}) as stream: catalog = json.load(stream)\n"
        "    model_catalog.load_model_catalog = lambda: catalog\n"
        "    sys.argv = sys.argv[1:]\n"
        "    raise SystemExit(model_catalog._main())\n"
        "os.execv(sys.executable, [sys.executable, *sys.argv[1:]])\n"
    )
    shim.chmod(0o755)
    monkeypatch.setenv("KIMICC_ROUTE_PYTHON", str(shim))
    return shim
