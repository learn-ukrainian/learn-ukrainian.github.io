"""``validation_session`` memoizes a repeated validation as ``None``; that is
faithful only for validators that return ``None``. The decorator must refuse
anything else at decoration time, and every packaged validator must comply."""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil

import learn_ukrainian_v4_runtime
import pytest
from learn_ukrainian_v4_runtime.provenance import validation_session


def test_validation_session_accepts_a_none_returning_validator() -> None:
    @validation_session
    def validate(receipt: dict, root: str = "r") -> None:
        return None

    assert validate({"a": 1}) is None


def test_validation_session_refuses_a_value_returning_validator() -> None:
    def validate(receipt: dict, root: str = "r") -> dict:
        return receipt

    with pytest.raises(TypeError, match="must be annotated '-> None'"):
        validation_session(validate)


def test_validation_session_refuses_an_unannotated_validator() -> None:
    def validate(receipt, root="r"):
        return receipt

    with pytest.raises(TypeError, match="must be annotated '-> None'"):
        validation_session(validate)


def test_every_decorated_packaged_validator_is_annotated_none() -> None:
    """Independent of the decorator: parse each packaged module's source and
    check the declared return annotation of every ``@validation_session``."""
    decorated = []
    for module_info in pkgutil.iter_modules(learn_ukrainian_v4_runtime.__path__):
        module = importlib.import_module(f"{learn_ukrainian_v4_runtime.__name__}.{module_info.name}")
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and any(isinstance(d, ast.Name) and d.id == "validation_session" for d in node.decorator_list):
                decorated.append((module.__name__, node.name, ast.unparse(node.returns) if node.returns else None))
    assert len(decorated) >= 14, decorated
    assert all(annotation == "None" for *_, annotation in decorated), decorated
