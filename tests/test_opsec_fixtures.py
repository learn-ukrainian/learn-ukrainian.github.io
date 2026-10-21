"""Sandbox dependency regressions without importing repository tools to discover them."""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests.opsec_fixtures import copy_publisher_scripts


@pytest.mark.parametrize("dependency", ["from scripts.dependency import leaf", "from ..dependency import leaf"])
def test_publisher_sandbox_follows_transitive_imports(tmp_path, dependency):
    source = tmp_path / "source/scripts"
    files = {
        "__init__.py": "from scripts.root_dependency import VALUE\n",
        "root_dependency.py": "VALUE = 1\n",
        "publish/__init__.py": "",
        "publish/__main__.py": "from . import entry\n",
        "publish/entry.py": f"def publish():\n    {dependency}\n",
        "opsec/__init__.py": "",
        "opsec/blocking.json": "{}",
        "dependency/__init__.py": "from . import initializer_dependency\n",
        "dependency/initializer_dependency.py": "",
        "dependency/leaf.py": "import scripts.transitive.module as module\n",
        # A namespace package and a cycle must not cause omissions or an endless walk.
        "transitive/module.py": "from scripts.dependency import leaf\n",
        "dependency/unrelated.py": "raise RuntimeError('unreachable sibling')\n",
    }
    for name, content in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    destination = tmp_path / "sandbox/scripts"

    copy_publisher_scripts(source, destination)

    assert {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()} == (
        set(files) - {"dependency/unrelated.py"}
    )


def test_publisher_sandbox_imports_merge_guard_in_isolation(gh_shim_sandbox):
    root, _shim, _tooling = gh_shim_sandbox
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scripts.publish.merge_guard import ensure_merge_ready; "
            "from scripts.ci.advisory_checks import load_advisory_checks; "
            "assert load_advisory_checks().reason is None",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert (root / "scripts/ci/advisory_checks.py").is_file()
    assert (root / "scripts/common/github_client.py").is_file()
