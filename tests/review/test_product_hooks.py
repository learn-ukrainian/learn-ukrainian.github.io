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
