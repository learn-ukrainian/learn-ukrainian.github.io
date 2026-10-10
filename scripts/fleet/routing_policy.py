"""Role, pair, and handoff defaults from config, with metric overrides.

Hard safety rules are applied after the config and cannot be overridden.
The choices themselves are data in ``scripts/config/routing_defaults.yaml``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import yaml

_DEFAULTS = _ROOT / "scripts" / "config" / "routing_defaults.yaml"

# Fixed. A metric or config edit cannot admit these lanes for language work.
LANGUAGE_LANES = frozenset({"claude", "codex", "agy"})
CHINESE_LANES = frozenset({"kimi", "glm", "deepseek"})
SUBSCRIPTION_LANES = frozenset({"claude", "codex", "agy", "grok", "cursor"})
API_KEY_LANES = frozenset({"deepseek"})


class HardRuleRefused(ValueError):
    """A safety rule rejected a config or metric choice."""


def projected_unused_pct(remaining: float | None, will_last: bool | None) -> float | None:
    """Percent still unused at reset. None when the snapshot has no remaining figure.

    A lane projected to exhaust reports 0. A lane projected to have headroom
    left reports that remaining percent. No host and no quota account.
    """
    if not isinstance(remaining, (int, float)) or isinstance(remaining, bool):
        return None
    if will_last is False:
        return 0.0
    if will_last is True:
        return float(remaining)
    return None


def load_defaults(path: Path | None = None) -> dict[str, Any]:
    target = path or _DEFAULTS
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("routing defaults must be a mapping")
    return data


def done_check_pass_rate(outcomes: list[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    """Passive rate of done-check passes per lane and model. No new runs."""
    counts: dict[str, dict[str, list[int]]] = {}
    for row in outcomes:
        lane = str(row.get("lane") or "")
        model = str(row.get("model") or "")
        bucket = counts.setdefault(lane, {}).setdefault(model, [0, 0])
        bucket[1] += 1
        if row.get("passed") is True:
            bucket[0] += 1
    return {
        lane: {model: (hits[0] / hits[1] if hits[1] else 0.0) for model, hits in models.items()}
        for lane, models in counts.items()
    }


def _pair(defaults: Mapping[str, Any], pair_id: str | None) -> dict[str, Any] | None:
    if not pair_id:
        return None
    for item in defaults.get("pairs") or []:
        if isinstance(item, dict) and item.get("id") == pair_id:
            return dict(item)
    raise HardRuleRefused(f"unknown pair {pair_id}")


def _filter_handoff(order: list[str], *, language: bool) -> list[str]:
    eligible: list[str] = []
    for lane in order:
        if language and (lane in CHINESE_LANES or lane not in LANGUAGE_LANES):
            continue
        eligible.append(lane)
    # A subscription lane removed by the language rule must not keep suppressing
    # an API-key lane. Only a subscription lane that is still eligible does.
    subscription_left = any(lane in SUBSCRIPTION_LANES for lane in eligible)
    chosen: list[str] = []
    for lane in eligible:
        if lane in API_KEY_LANES and subscription_left:
            continue
        chosen.append(lane)
    if language and not chosen:
        raise HardRuleRefused("language handoff has no GPT, Gemini, or Claude lane")
    return chosen


def resolve_job(
    job_type: str,
    *,
    language: bool = False,
    defaults: Mapping[str, Any] | None = None,
    metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the job choice. A metric may replace the default for this job type.

    ``metrics`` is ``{"job_types": {job_type: {"pair": id, "role": name}}}``.
    Every replacement is recorded. A hard rule still wins.
    """
    loaded = dict(defaults or load_defaults())
    jobs = loaded.get("job_types") or {}
    base = dict(jobs.get(job_type) or {})
    if not base:
        raise HardRuleRefused(f"unknown job type {job_type}")
    overrides: list[dict[str, str]] = []
    metric_jobs = (metrics or {}).get("job_types") or {}
    replacement = metric_jobs.get(job_type)
    if isinstance(replacement, dict):
        for key in ("role", "pair"):
            if key in replacement and replacement[key] != base.get(key):
                overrides.append({
                    "job_type": job_type,
                    "field": key,
                    "default": str(base.get(key)),
                    "metric": str(replacement[key]),
                })
                base[key] = replacement[key]
    role_name = str(base.get("role") or "")
    roles = loaded.get("roles") or {}
    if role_name == "orchestrator" and not loaded.get("apply_orchestrator_defaults"):
        lanes = list((roles.get("worker") or {}).get("lanes") or [])
        overrides.append({
            "job_type": job_type,
            "field": "orchestrator_lanes",
            "default": "held",
            "metric": "harness gates not landed",
        })
    else:
        lanes = list((roles.get(role_name) or {}).get("lanes") or [])
    if language:
        lanes = [lane for lane in lanes if lane in LANGUAGE_LANES and lane not in CHINESE_LANES]
        if not lanes:
            raise HardRuleRefused("language work has no GPT, Gemini, or Claude lane")
    requested_pair = base.get("pair")
    pair = _pair(loaded, requested_pair)
    metric_set_pair = isinstance(replacement, dict) and "pair" in replacement
    if language and pair is not None:
        illegal = [
            f"{seat}={pair.get(seat)}"
            for seat in ("executor", "adviser")
            if str(pair.get(seat) or "") in CHINESE_LANES or str(pair.get(seat) or "") not in LANGUAGE_LANES
        ]
        if illegal:
            if metric_set_pair:
                raise HardRuleRefused(
                    "language pair is not GPT, Gemini, or Claude: " + ",".join(illegal)
                )
            overrides.append({
                "job_type": job_type,
                "field": "pair",
                "default": str(requested_pair),
                "metric": "hard rule dropped",
            })
            pair = None
    handoff_table = loaded.get("handoff") or {}
    handoff_key = "language" if language else "default"
    handoff = _filter_handoff(list(handoff_table.get(handoff_key) or []), language=language)
    return {
        "job_type": job_type,
        "role": role_name,
        "lanes": lanes,
        "pair": pair,
        "handoff": handoff,
        "overrides": overrides,
    }


def log_overrides(choice: Mapping[str, Any]) -> list[str]:
    """One line per override. No host, account, or absolute path."""
    lines = []
    for item in choice.get("overrides") or []:
        lines.append(
            f"routing override job={item['job_type']} field={item['field']} "
            f"default={item['default']} metric={item['metric']}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the cap-handoff successor from routing defaults.")
    parser.add_argument("--handoff", action="store_true")
    parser.add_argument("--language", action="store_true")
    args = parser.parse_args(argv)
    if not args.handoff:
        parser.error("pass --handoff")
    choice = resolve_job("orchestrate", language=args.language)
    successor = choice["handoff"][0] if choice["handoff"] else ""
    if not successor:
        print("routing policy: no handoff successor", file=sys.stderr)
        return 1
    print(f"successor={successor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
