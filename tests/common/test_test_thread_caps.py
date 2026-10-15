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


@pytest.mark.parametrize("value", ["1", "01"])
def test_apply_preserves_positive_integers_within_cap(value: str) -> None:
    from scripts.common.test_thread_caps import apply

    original = {key: value for key in EXPECTED if key != "TOKENIZERS_PARALLELISM"}
    assert apply(original) == {**original, "TOKENIZERS_PARALLELISM": "false"}


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "0.5",
        "",
        " ",
        "\t\n",
        "nan",
        "NaN",
        "inf",
        "-inf",
        "1e400",
        "1.5",
        "0.9",
        "1.0",
        "0_1",
        " 1 ",
        "+1",
        "1\n",
        "٣",
        "00",
        "2",
        "1_000",
        "16abc",
        "1abc",
        "8,4",
        "true",
        "0x10",
        "not-a-number",
        "huge",
        "1" * 500,
        "1" * 5000,
    ],
)
def test_apply_replaces_values_that_are_not_positive_integer_limits(value: str) -> None:
    from scripts.common.test_thread_caps import apply

    original = dict.fromkeys(EXPECTED, value)
    assert apply(original) == EXPECTED
    assert original == dict.fromkeys(EXPECTED, value)


def test_apply_lowers_existing_parallelism() -> None:
    from scripts.common.test_thread_caps import apply

    assert apply(dict.fromkeys(EXPECTED, "8")) == EXPECTED


@pytest.mark.parametrize("setting", ["off", " OFF "])
def test_opt_out_preserves_the_environment(setting: str) -> None:
    from scripts.common.test_thread_caps import apply

    original = {"OMP_NUM_THREADS": "8", "LU_TEST_THREAD_CAP": setting}
    assert apply(original) == original
