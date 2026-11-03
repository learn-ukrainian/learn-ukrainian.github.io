"""Gate defects for the scripts/ package-boundary ratchet (#12660)."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.lint.boundary_ratchet import collect_import_counts, evaluate, load_config, write_baseline

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
