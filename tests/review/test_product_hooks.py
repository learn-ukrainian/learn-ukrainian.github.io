"""Version validation for the configured product review hooks."""

import json

import pytest

from scripts.review.product_hooks import HOOKS_REL, SCHEMA, ProductHooksError, _module_name


def test_schema_version_rejects_boolean_and_float_lookalikes(tmp_path):
    """Equality with 1 must not admit JSON booleans or floating-point versions."""
    path = tmp_path / "review_hooks.v1.json"
    document = json.dumps(
        {
            "schema": SCHEMA,
            "schema_version": 1,
            "origin": HOOKS_REL,
            "attempt_hooks": "scripts.curriculum.review_attempt_hooks",
        }
    )
    path.write_text(document)
    assert _module_name(path) == "scripts.curriculum.review_attempt_hooks"
    for version in ("true", "1.0", "1e0"):
        path.write_text(document.replace('"schema_version": 1', f'"schema_version": {version}'))
        with pytest.raises(ProductHooksError) as caught:
            _module_name(path)
        assert caught.value.code == "hooks_schema_mismatch"


def _hooks_document(**changes):
    return json.dumps({
        "schema": SCHEMA,
        "schema_version": 1,
        "origin": HOOKS_REL,
        "attempt_hooks": "scripts.curriculum.review_attempt_hooks",
        **changes,
    })


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("{", "hooks_not_json"),
        ('{"schema": 1, "schema": 2}', "hooks_not_json"),
        ("[]", "hooks_fields"),
        ("{}", "hooks_fields"),
        (_hooks_document(extra=1), "hooks_fields"),
        (_hooks_document(schema="wrong"), "hooks_schema_mismatch"),
        (_hooks_document(schema_version=2), "hooks_schema_mismatch"),
        (_hooks_document(schema_version="1"), "hooks_schema_mismatch"),
        (_hooks_document(origin="wrong"), "hooks_origin_mismatch"),
    ],
)
def test_hooks_json_refusals_keep_error_codes(tmp_path, raw, code):
    path = tmp_path / "hooks.json"
    path.write_text(raw)
    with pytest.raises(ProductHooksError) as caught:
        _module_name(path)
    assert caught.value.code == code


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "oversized", "invalid_utf8", "unreadable"])
def test_hooks_file_refusals_keep_error_codes(tmp_path, monkeypatch, kind):
    from pathlib import Path

    from scripts.review import product_hooks as hooks

    path = tmp_path / "hooks.json"
    expected = "hooks_not_json"
    if kind == "missing":
        expected = "hooks_missing"
    elif kind == "directory":
        path.mkdir()
        expected = "hooks_not_regular_file"
    elif kind == "symlink":
        target = tmp_path / "target.json"
        target.write_text(_hooks_document())
        path.symlink_to(target)
        expected = "hooks_not_regular_file"
    elif kind == "oversized":
        path.write_bytes(b" " * (hooks.MAX_HOOKS_BYTES + 1))
        expected = "hooks_too_large"
    elif kind == "invalid_utf8":
        path.write_bytes(b"\xff")
    else:
        path.write_text(_hooks_document())

        def unreadable(_path):
            raise OSError("read refused")

        monkeypatch.setattr(Path, "read_bytes", unreadable)
    with pytest.raises(ProductHooksError) as caught:
        _module_name(path)
    assert caught.value.code == expected


@pytest.mark.parametrize(
    "name", [None, 1, [], "", "scripts", "audit.check", ".scripts.audit", "scripts..audit", "scripts.bad-name", "scripts.Audit", "scripts.audit\n", "scripts.українська"]
)
def test_hooks_refuses_malformed_names(tmp_path, name):
    path = tmp_path / "hooks.json"
    path.write_text(_hooks_document(attempt_hooks=name))
    with pytest.raises(ProductHooksError) as caught:
        _module_name(path)
    assert caught.value.code == "hooks_module_invalid"


def test_hooks_refuses_foreign_cached_module_without_repinning(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from scripts.ops.product_entry import ConfiguredModuleError
    from scripts.review import product_hooks as hooks

    pinned = hooks.attempt_hooks()
    name = _module_name(hooks.HOOKS_PATH)
    foreign = ModuleType(name)
    foreign.__file__ = str(tmp_path / "foreign.py")
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        hooks.attempt_hooks.__wrapped__()
    assert hooks.attempt_hooks() is pinned


@pytest.mark.parametrize(
    ("name", "expected"),
    [("scripts.audit.loader_slice_missing", "hooks_module_missing"), ("scripts.loader_slice_missing.child", None)],
)
def test_hooks_missing_target_keeps_leaf_error_and_parent_error(tmp_path, monkeypatch, name, expected):
    from scripts.review import product_hooks as hooks

    path = tmp_path / "hooks.json"
    path.write_text(_hooks_document(attempt_hooks=name))
    monkeypatch.setattr(hooks, "HOOKS_PATH", path)
    if expected:
        with pytest.raises(ProductHooksError) as caught:
            hooks.attempt_hooks.__wrapped__()
        assert caught.value.code == expected
    else:
        with pytest.raises(ModuleNotFoundError) as caught:
            hooks.attempt_hooks.__wrapped__()
        assert caught.value.name == "scripts.loader_slice_missing"


def test_hooks_existing_module_dependency_error_is_not_translated(tmp_path, monkeypatch):
    import sys

    import scripts.audit
    from scripts.review import product_hooks as hooks

    name = "scripts.audit.loader_slice_dependency"
    (tmp_path / "loader_slice_dependency.py").write_text("import loader_slice_missing_dependency\n")
    path = tmp_path / "hooks.json"
    path.write_text(_hooks_document(attempt_hooks=name))
    monkeypatch.setattr(hooks, "HOOKS_PATH", path)
    monkeypatch.setattr(scripts.audit, "__path__", [str(tmp_path)])
    with pytest.raises(ModuleNotFoundError) as caught:
        hooks.attempt_hooks.__wrapped__()
    assert caught.value.name == "loader_slice_missing_dependency"
    assert name not in sys.modules


def test_configured_callers_are_counted_once_and_implementation_separately():
    """The dependency scan must expose both callers without double counting R's old wrapper."""
    from pathlib import Path

    from scripts.ci.components import scan_imports
    from scripts.lint.boundary_ratchet import CONFIG_PATH, _configured_line, _dynamic_count, load_config

    root = Path(__file__).resolve().parents[2]
    paths = ["scripts/research/registry.py", "scripts/review/product_hooks.py", "scripts/ops/product_entry.py"]
    graph = scan_imports({path: (root / path).read_bytes() for path in paths})
    assert [row["path"] for row in graph["configured_loads"]] == paths[:2]
    config = load_config(CONFIG_PATH)
    assert _dynamic_count(graph, config, "machinery") == 2
    assert _configured_line(graph) == "configured-entry-point implementation=1 callers=2"
