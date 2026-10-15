"""Environment limits inherited by governed test runs and their descendants (#10716)."""

from collections.abc import Mapping

THREAD_CAPS = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "ORT_NUM_THREADS": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "RAYON_NUM_THREADS": "1",
}


def apply(env: Mapping[str, str]) -> dict[str, str]:
    """Return a capped copy, preserving only positive ASCII integer limits within the cap."""
    result = dict(env)
    if env.get("LU_TEST_THREAD_CAP", "").strip().lower() == "off":
        return result
    for name, cap in THREAD_CAPS.items():
        if cap != "false" and name in env:
            try:
                if env[name].isascii() and env[name].isdecimal() and 0 < int(env[name]) <= int(cap):
                    continue
            except ValueError:
                pass
        result[name] = cap
    return result
