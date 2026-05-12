"""Recycle-cadence audit gate for cumulative learner vocabulary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from scripts.audit.checks.learner_state import _strip_non_body_prose, _vesum_helpers
    from scripts.build.learner_immersion import build_lemma_frequency_map
    from scripts.config import get_recycle_cadence_policy
except ModuleNotFoundError:  # pragma: no cover - CLI path compatibility
    from audit.checks.learner_state import _strip_non_body_prose, _vesum_helpers
    from build.learner_immersion import build_lemma_frequency_map
    from config import get_recycle_cadence_policy


def _extract_all_ukrainian_surfaces(content: str) -> list[str]:
    iter_surfaces, normalize_for_vesum = _vesum_helpers()
    normalized = normalize_for_vesum(_strip_non_body_prose(content))
    return [word.lower() for word in iter_surfaces(normalized)]


def _stale_lemmas(
    frequencies: dict[str, list[tuple[int, int]]],
    module_num: int,
    recycle_window: int,
) -> list[str]:
    stale: list[str] = []
    half_window = max(1, recycle_window // 2)
    for lemma, rows in frequencies.items():
        if not rows:
            continue
        introduced = min(module for module, _count in rows)
        seen_modules = [module for module, count in rows if count > 0]
        last_seen = max(seen_modules) if seen_modules else introduced
        if module_num - introduced >= recycle_window and module_num - last_seen >= half_window:
            stale.append(lemma)
    return stale


def check_recycle_cadence(
    content: str,
    level: str,
    module_num: int,
    module_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Warn when a module fails to recycle enough stale earlier lemmas."""
    del module_dir
    track = level.lower()
    policy = get_recycle_cadence_policy(track)
    recycle_window = int(policy["recycle_window"])
    recycle_floor = int(policy["recycle_floor"])

    frequencies = build_lemma_frequency_map(track, module_num)
    stale = _stale_lemmas(frequencies, module_num, recycle_window)
    if not stale:
        return []

    surfaces = _extract_all_ukrainian_surfaces(content)
    stale_set = set(stale)
    observed = sum(1 for surface in surfaces if surface in stale_set)
    if observed >= recycle_floor:
        return []

    return [
        {
            "type": "recycle_cadence",
            "severity": "WARN",
            "blocking": False,
            "issue": (
                f"Only {observed} stale-vocabulary occurrence(s) found; "
                f"expected at least {recycle_floor} from earlier modules."
            ),
            "fix": "Add deliberate recycling of earlier lemmas in prose, examples, or dialogues.",
            "observed": observed,
            "required": recycle_floor,
            "stale_lemmas": stale[:12],
        }
    ]
