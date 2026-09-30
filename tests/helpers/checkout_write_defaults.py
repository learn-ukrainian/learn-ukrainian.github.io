"""Redirect test write defaults without importing production modules eagerly."""

from __future__ import annotations

import sys
import weakref
from collections.abc import Iterator
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_TARGET_FILES = {
    "linear_pipeline.py": PROJECT_ROOT / "scripts/build/linear_pipeline.py",
    "extract_sections.py": PROJECT_ROOT / "scripts/wiki/extract_sections.py",
    "build_sources_db.py": PROJECT_ROOT / "scripts/wiki/build_sources_db.py",
}


def _target_file(module: ModuleType) -> str | None:
    origin = getattr(module, "__file__", None)
    if not isinstance(origin, str):
        return None
    # Avoid resolving every loaded module's path for every test.
    name = origin.rsplit("/", 1)[-1]
    target = _TARGET_FILES.get(name)
    return name if target is not None and Path(origin).resolve() == target else None


class WriteDefaults:
    """Remember collection aliases, including objects replaced in sys.modules."""

    def __init__(self) -> None:
        self.modules: weakref.WeakSet[ModuleType] = weakref.WeakSet()
        self.patches: pytest.MonkeyPatch | None = None
        self.tmp_path: Path | None = None

    def loaded(self, module: ModuleType) -> None:
        name = _target_file(module)
        if name is None:
            return
        self.modules.add(module)
        if self.patches is None or self.tmp_path is None:
            return
        if name == "linear_pipeline.py":
            target = self.tmp_path / ".claude/agents/curriculum-writer.md"
            self.patches.setattr(module, "CLAUDE_WRITER_AGENT_TARGET", target)
            # Mutate the function's bound default so existing from-imports work.
            self.patches.setitem(module.ensure_claude_writer_agent_deployed.__kwdefaults__, "target_path", target)
        else:
            report = self.tmp_path / "corpus_audit/section_extraction_report.md"
            self.patches.setattr(module, "DEFAULT_REPORT_PATH", report)
            if name == "extract_sections.py":
                self.patches.setitem(module.extract_sections.__kwdefaults__, "report_path", report)


def pytest_configure(config: pytest.Config) -> None:
    defaults = WriteDefaults()
    config._checkout_write_defaults = defaults
    original_exec = SourceFileLoader.exec_module

    def exec_module(loader: SourceFileLoader, module: ModuleType) -> None:
        original_exec(loader, module)
        defaults.loaded(module)

    # File-location specs use this loader directly, bypassing sys.meta_path.
    # Install before collection so overwritten aliases remain discoverable.
    patches = pytest.MonkeyPatch()
    patches.setattr(SourceFileLoader, "exec_module", exec_module)
    config.add_cleanup(patches.undo)


@pytest.fixture(autouse=True)
def checkout_write_defaults(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[None]:
    defaults = request.config._checkout_write_defaults
    with pytest.MonkeyPatch.context() as patches:
        defaults.patches = patches
        defaults.tmp_path = tmp_path
        try:
            for module in (*list(sys.modules.values()), *list(defaults.modules)):
                if isinstance(module, ModuleType):
                    defaults.loaded(module)
            yield
        finally:
            defaults.patches = None
            defaults.tmp_path = None
