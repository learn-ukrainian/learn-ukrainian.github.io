"""``validation_session`` memoizes a repeated validation as ``None``; that is
faithful only for validators that return ``None``. The decorator must refuse
anything else at decoration time, and every packaged validator must comply."""

from __future__ import annotations

import pytest
from learn_ukrainian_v4_runtime.provenance import validation_session


def test_validation_session_refuses_a_value_returning_validator() -> None:
    def validate(receipt: dict, root: str = "r") -> dict:
        return receipt

    with pytest.raises(TypeError, match="must be annotated '-> None'"):
        validation_session(validate)
