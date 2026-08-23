"""Regression tests for the changed-test fastlane dependency profile."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ci import fastlane_requirements


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _lock(tmp_path: Path) -> dict[str, str]:
    lock = _write(
        tmp_path / "requirements-lock.txt",
        """\
fastapi==0.139.0
mcp==2.0.0
pymorphy3-dicts-uk==2.4.1.1.1663094765
PyYAML==6.0.3
pytest==9.0.3
pydantic==2.13.4
referencing==0.37.0
requests==2.34.2
""",
    )
    return fastlane_requirements.read_lock(lock)


def test_selected_direct_imports_add_reviewed_exact_lock_pins(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root / "scripts" / "ci" / "__init__.py", "")
    test_path = _write(
        project_root / "tests" / "test_example.py",
        """\
from __future__ import annotations

import yaml
from fastapi import FastAPI
from requests import get
from scripts.ci import changed_tests
""",
    )

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=["pytest==9.0.3", "fastapi==0.139.0"],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["pytest==9.0.3", "fastapi==0.139.0", "PyYAML==6.0.3", "requests==2.34.2"]


def test_unknown_third_party_import_fails_closed(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(project_root / "tests" / "test_example.py", "import unreviewed_vendor\n")

    with pytest.raises(fastlane_requirements.RequirementSelectionError, match="unreviewed_vendor"):
        fastlane_requirements.select_requirements(
            [test_path],
            base_requirements=[],
            lock_requirements=_lock(tmp_path),
            project_root=project_root,
        )


def test_referencing_direct_import_uses_reviewed_exact_lock_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(
        project_root / "tests" / "test_schema.py",
        "from referencing import Registry, Resource\n",
    )

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["referencing==0.37.0"]


def test_mcp_direct_import_uses_reviewed_exact_lock_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(project_root / "tests" / "test_mcp_server.py", "import mcp\n")

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["mcp==2.0.0"]


def test_pydantic_direct_import_uses_reviewed_exact_lock_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(project_root / "tests" / "test_api_model.py", "from pydantic import BaseModel\n")

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["pydantic==2.13.4"]


def test_pymorphy_uk_dictionary_import_uses_reviewed_exact_lock_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(project_root / "tests" / "test_morph.py", "import pymorphy3_dicts_uk\n")

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["pymorphy3-dicts-uk==2.4.1.1.1663094765"]


def test_explicit_non_lock_runtime_import_has_a_reviewed_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(project_root / "tests" / "test_example.py", "import ahocorasick\n")

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["pyahocorasick==2.3.1"]


def test_live_model_imports_do_not_expand_the_default_profile(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    test_path = _write(
        project_root / "tests" / "test_example.py",
        """\
import stanza
import torch
from ukrainian_word_stress import Stressifier
""",
    )

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=["pytest==9.0.3"],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["pytest==9.0.3"]


def test_project_import_graph_adds_transitive_third_party_pin(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root / "scripts" / "__init__.py", "")
    _write(project_root / "scripts" / "helper.py", "import requests\n")
    test_path = _write(project_root / "tests" / "test_example.py", "from scripts.helper import value\n")

    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["requests==2.34.2"]


def test_script_context_fallback_import_resolves_relative_to_importer(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    orchestration = project_root / "scripts" / "orchestration"
    _write(orchestration / "__init__.py", "")
    _write(orchestration / "task_identity.py", "import requests\n")
    _write(orchestration / "thread_handoff_canary.py", "")
    _write(
        orchestration / "thread_handoff.py",
        """\
try:
    from scripts.orchestration import task_identity, thread_handoff_canary
except ImportError:
    import task_identity
    import thread_handoff_canary
""",
    )
    test_path = _write(
        project_root / "tests" / "test_example.py",
        "from scripts.orchestration import thread_handoff\n",
    )

    assert fastlane_requirements._reachable_import_roots([test_path], project_root) == {"requests"}
    selected = fastlane_requirements.select_requirements(
        [test_path],
        base_requirements=[],
        lock_requirements=_lock(tmp_path),
        project_root=project_root,
    )

    assert selected == ["requests==2.34.2"]


def test_unknown_transitive_project_import_fails_closed(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root / "scripts" / "__init__.py", "")
    _write(project_root / "scripts" / "helper.py", "import unreviewed_transitive_vendor\n")
    test_path = _write(project_root / "tests" / "test_example.py", "from scripts.helper import value\n")

    with pytest.raises(
        fastlane_requirements.RequirementSelectionError,
        match="unreviewed_transitive_vendor",
    ):
        fastlane_requirements.select_requirements(
            [test_path],
            base_requirements=[],
            lock_requirements=_lock(tmp_path),
            project_root=project_root,
        )
