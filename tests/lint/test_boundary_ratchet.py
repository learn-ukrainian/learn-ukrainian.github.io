"""Gate defects for the scripts/ package-boundary ratchet (#12660, #12677, #12720)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.lint.boundary_ratchet import (
    collect_import_counts,
    evaluate,
    load_config,
    population_report,
    write_baseline,
)

_REPO = Path(__file__).resolve().parents[2]
_GROWTH = "baseline may only shrink; freeze/growth differs from origin/main"

_SCHEMA = "package-boundary.v1"


def _tree(tmp_path: Path, sources: dict[str, str], packages: dict[str, str]) -> tuple[Path, Path, Path]:
    root = tmp_path / "tree"
    scripts = root / "scripts"
    for rel, text in sources.items():
        path = scripts / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    config_path = root / "boundary.yaml"
    payload = {
        "schema": _SCHEMA,
        "packages": {
            name: {"role": role, **({"reason": "test shared"} if role == "shared" else {})}
            for name, role in packages.items()
        },
        "modules": {},
    }
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    baseline = root / "baseline.json"
    write_baseline(baseline, {})
    return root, config_path, baseline


def test_new_machinery_to_product_import_does_not_pass(tmp_path: Path) -> None:
    """A new machinery-to-product import passes CI unnoticed."""
    root, config, baseline = _tree(
        tmp_path,
        {
            "mach/a.py": "from scripts.prod.widget import name\n",
            "prod/__init__.py": "",
            "prod/widget.py": "name = 1\n",
        },
        {"mach": "machinery", "prod": "product"},
    )
    violations = evaluate(root, config, baseline)
    assert violations
    assert any("new machinery-to-product import scripts.prod.widget" in item for item in violations)


def test_unclassified_package_does_not_pass(tmp_path: Path) -> None:
    """An unclassified package passes."""
    root, config, baseline = _tree(
        tmp_path,
        {"extra/x.py": "x = 1\n"},
        {},
    )
    violations = evaluate(root, config, baseline)
    assert any(item == "scripts/extra: unclassified package" for item in violations)
    assert load_config(config).packages == {}


def test_import_inside_a_function_is_not_missed(tmp_path: Path) -> None:
    """An import inside a function is missed."""
    root, config, baseline = _tree(
        tmp_path,
        {
            "mach/a.py": "from scripts.other import ok\n\n\ndef load():\n    from scripts.prod.widget import name\n    return name\n",
            "prod/__init__.py": "",
            "prod/widget.py": "name = 1\n",
            "other/__init__.py": "",
        },
        {"mach": "machinery", "prod": "product", "other": "shared"},
    )
    config_obj = load_config(config)
    counts, fatal = collect_import_counts(root, config_obj)
    assert fatal == []
    assert counts[("scripts/mach/a.py", "scripts.prod.widget")] == 1
    assert ("scripts/mach/a.py", "scripts.other") not in counts
    violations = evaluate(root, config, baseline)
    assert any("scripts.prod.widget x1" in item for item in violations)


def test_population_report_counts_each_edge_kind(tmp_path: Path) -> None:
    """Each population is its own count, and alias-only and ImportError fallback have their own columns."""

    root, config_path, _baseline = _tree(
        tmp_path,
        {
            "mach/a.py": (
                "from scripts.prod import only_alias\n"
                "import scripts.side.leaf\n"
                "import importlib.util\n"
                "\n"
                'importlib.util.spec_from_file_location("loaded", "scripts/prod/loaded.py")\n'
                "\n"
                "def load(module_name):\n"
                "    return importlib.import_module(module_name)\n"
                "\n"
                "try:\n"
                "    import scripts.prod.guarded\n"
                "except ImportError:\n"
                "    guarded = None\n"
                "\n"
                "import scripts.common.helper\n"
            ),
            "prod/__init__.py": "",
            "prod/only_alias.py": "VALUE = 1\n",
            "prod/guarded.py": "GUARDED = 1\n",
            "prod/loaded.py": "LOADED = 1\n",
            "prod/callback.py": "import scripts.mach.a\nimport scripts.common.helper\n",
            "side/__init__.py": "",
            "side/leaf.py": "LEAF = 1\n",
            "common/__init__.py": "",
            "common/helper.py": "HELPER = 1\n",
        },
        {"mach": "machinery", "prod": "product", "side": "product", "common": "shared"},
    )
    (root / "tests").mkdir()
    (root / "tests" / "check_boundary.py").write_text(
        "import scripts.prod.guarded\nimport scripts.mach.a\n",
        encoding="utf-8",
    )
    report = population_report(root, load_config(config_path))
    forward = re.search(
        r"^forward direct=(\d+) parent=(\d+) file-load=(\d+) fallback=(\d+) "
        r"dynamic=(\d+) shared=(\d+) test=(\d+)$",
        report,
        re.MULTILINE,
    )
    reverse = re.search(
        r"^reverse direct=(\d+) parent=(\d+) file-load=(\d+) fallback=(\d+) "
        r"dynamic=(\d+) shared=(\d+) test=(\d+)$",
        report,
        re.MULTILINE,
    )
    assert forward is not None and reverse is not None
    assert forward.groups() == ("4", "1", "1", "1", "1", "1", "1")
    assert reverse.groups() == ("1", "0", "0", "0", "0", "1", "1")
    direct = re.search(
        r"^forward\.direct identities=(\d+) fallback_only=(\d+) alias_only=(\d+)$",
        report,
        re.MULTILINE,
    )
    fallback = re.search(
        r"^forward\.fallback identities=(\d+) fallback_only=(\d+) alias_only=(\d+)$",
        report,
        re.MULTILINE,
    )
    assert direct is not None and fallback is not None
    assert direct.groups() == ("4", "1", "1")
    assert fallback.groups() == ("1", "1", "0")


def test_untracked_scripts_directory_is_not_classified(tmp_path: Path) -> None:
    """A top-level scripts directory with no Git-tracked Python file is not classified."""

    root, config, baseline = _tree(
        tmp_path,
        {
            "kept/a.py": "a = 1\n",
            "loose/b.py": "b = 1\n",
            "ghost/orphan.py": "orphan = 1\n",
        },
        {"kept": "machinery"},
    )
    cache = root / "scripts" / "pycache_only" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.cpython-312.pyc").write_bytes(b"\x00")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=30)
    subprocess.run(
        ["git", "add", "--", "scripts/kept/a.py", "scripts/loose/b.py"],
        cwd=root,
        check=True,
        timeout=30,
    )
    violations = evaluate(root, config, baseline)
    assert "scripts/ghost: unclassified package" not in violations
    assert "scripts/pycache_only: unclassified package" not in violations
    assert "scripts/loose: unclassified package" in violations


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Boundary Fixture",
            "-c",
            "user.email=boundary@example.invalid",
            *args,
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )


def _commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


def _ratchet(root: Path, baseline: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lint.boundary_ratchet",
            "--root",
            str(root),
            "--baseline",
            str(baseline),
            "--config",
            str(config),
        ],
        cwd=_REPO,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_remove_then_restore_matches_origin_main_and_growth_still_fails(tmp_path: Path) -> None:
    """Restoring rows the branch itself removed is reported as growth against HEAD or HEAD^."""

    imported = "from scripts.prod.widget import name\n"
    root, config, _empty = _tree(
        tmp_path,
        {
            "mach/a.py": imported,
            "prod/__init__.py": "",
            "prod/widget.py": "name = 1\n",
            "prod/other.py": "other = 1\n",
        },
        {"mach": "machinery", "prod": "product"},
    )
    baseline = root / "scripts" / "lint" / "boundary_baseline.json"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    counts, fatal = collect_import_counts(root, load_config(config))
    assert fatal == []
    assert counts
    write_baseline(baseline, counts)
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "base")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")

    landed = _ratchet(root, baseline, config)
    assert landed.returncode == 0, landed.stderr
    assert landed.stdout.startswith("OK: package boundary ratchet matches the baseline")

    (root / "scripts" / "mach" / "a.py").write_text("name = 1\n", encoding="utf-8")
    write_baseline(baseline, {})
    _commit(root, "remove the row")
    shrunk = _ratchet(root, baseline, config)
    assert shrunk.returncode == 0, shrunk.stderr

    (root / "scripts" / "mach" / "a.py").write_text(imported, encoding="utf-8")
    write_baseline(baseline, counts)
    dirty = _ratchet(root, baseline, config)
    assert dirty.returncode == 0, dirty.stderr
    assert "differs from" not in dirty.stderr

    _commit(root, "restore the origin/main rows")
    restored = _ratchet(root, baseline, config)
    assert restored.returncode == 0, restored.stderr
    assert restored.stdout.startswith("OK: package boundary ratchet matches the baseline")
    assert "differs from" not in restored.stderr

    source = root / "scripts" / "mach" / "a.py"
    source.write_text(imported + "from scripts.prod.other import other\n", encoding="utf-8")
    grown, grown_fatal = collect_import_counts(root, load_config(config))
    assert grown_fatal == []
    assert set(grown) > set(counts)
    write_baseline(baseline, grown)
    violation = _ratchet(root, baseline, config)
    assert violation.returncode == 1
    assert violation.stderr.splitlines() == [f"scripts/lint/boundary_baseline.json: {_GROWTH}"]
    assert "differs from HEAD" not in violation.stderr
