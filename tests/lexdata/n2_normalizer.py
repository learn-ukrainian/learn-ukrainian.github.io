"""Normalizer N2 for the §6.7 B9 proof test: same declared version, different code.

N2 differs from the production normalizer in exactly two ways: U+2019 is no
longer unified to U+0027 in keys, and an ``initial_cap`` span derives
``mixed``. ``NORMALIZER_VERSION`` is deliberately not bumped.
"""

from __future__ import annotations

from dataclasses import replace

from scripts.lexdata import normalize


def normalize_span(raw_span: str) -> normalize.Normalized:
    result = normalize.normalize_span(raw_span.replace("’", ""))
    if result.refusal_code is None:
        restore = {name: getattr(result, name).replace("", "’")
                   for name in ("key_stressed", "key_unstressed", "key_fold")}
        flags = tuple(flag for flag in result.norm_flags if flag != "apostrophe_unified")
        result = replace(result, **restore, norm_flags=flags,
                         case_signal="mixed" if result.case_signal == "initial_cap" else result.case_signal)
    return replace(result, surface=result.surface.replace("", "’"))
