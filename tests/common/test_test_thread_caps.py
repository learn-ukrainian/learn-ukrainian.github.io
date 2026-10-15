"""Thread-cap policy for governed test processes (#10716)."""

import pytest

EXPECTED = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "ORT_NUM_THREADS": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "RAYON_NUM_THREADS": "1",
}


def test_apply_sets_caps_without_mutating_input() -> None:
    from scripts.common.test_thread_caps import THREAD_CAPS, apply

    original = {"OTHER": "kept"}
    assert apply(original) == {"OTHER": "kept", **EXPECTED}
    assert original == {"OTHER": "kept"}
    assert THREAD_CAPS == EXPECTED


@pytest.mark.parametrize("value", ["0", "-1", "0.5", "1", "not-a-number", ""])
def test_apply_preserves_lower_and_non_numeric_values(value: str) -> None:
    from scripts.common.test_thread_caps import apply

    original = {key: value for key in EXPECTED if key != "TOKENIZERS_PARALLELISM"}
    assert apply(original) == {**original, "TOKENIZERS_PARALLELISM": "false"}


def test_apply_lowers_existing_parallelism() -> None:
    from scripts.common.test_thread_caps import apply

    assert apply(dict.fromkeys(EXPECTED, "8")) == EXPECTED


@pytest.mark.parametrize("setting", ["off", " OFF "])
def test_opt_out_preserves_the_environment(setting: str) -> None:
    from scripts.common.test_thread_caps import apply

    original = {"OMP_NUM_THREADS": "8", "LU_TEST_THREAD_CAP": setting}
    assert apply(original) == original
