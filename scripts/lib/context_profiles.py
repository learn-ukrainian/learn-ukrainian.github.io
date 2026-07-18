#!/usr/bin/env python3
"""Load and validate main-session context profiles for interactive routes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "scripts" / "config" / "context_profiles.yaml"
REGISTRY_VERSION = 1


class ContextProfileError(ValueError):
    """The context-profile registry or a requested profile is invalid."""


def _integer(value: Any, field: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{field} must be an integer")
        return None
    return value


def validate_profile(profile: dict[str, Any], *, key: str | None = None) -> list[str]:
    """Return all schema and cross-field errors for one profile."""
    errors: list[str] = []
    required = {
        "profile_id",
        "transport",
        "main_model_id",
        "model_id_patterns",
        "main_context_window_tokens",
        "auto_compact_capacity_tokens",
        "cold_start_profile",
        "cold_start_budget_tokens",
        "rollover_warning_percentages",
    }
    missing = sorted(required - profile.keys())
    errors.extend(f"missing required profile key: {name}" for name in missing)
    if missing:
        return errors

    profile_id = profile["profile_id"]
    if not isinstance(profile_id, str) or not profile_id.strip():
        errors.append("profile_id must be a non-empty string")
    elif key is not None and profile_id != key:
        errors.append(f"profile_id {profile_id!r} does not match registry key {key!r}")

    if profile["transport"] not in {"claudex", "native", "native_codex", "unknown"}:
        errors.append("transport must be claudex, native, native_codex, or unknown")
    if not isinstance(profile["main_model_id"], str) or not profile["main_model_id"].strip():
        errors.append("main_model_id must be a non-empty string")

    patterns = profile["model_id_patterns"]
    if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
        errors.append("model_id_patterns must be a list of strings")
    else:
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"invalid model_id_patterns entry {pattern!r}: {exc}")

    window = _integer(profile["main_context_window_tokens"], "main_context_window_tokens", errors)
    budget = _integer(profile["cold_start_budget_tokens"], "cold_start_budget_tokens", errors)
    auto_compact = profile["auto_compact_capacity_tokens"]
    if auto_compact is not None:
        auto_compact = _integer(auto_compact, "auto_compact_capacity_tokens", errors)

    if window is not None and window < 0:
        errors.append("main_context_window_tokens must be >= 0")
    if budget is not None and budget < 0:
        errors.append("cold_start_budget_tokens must be >= 0")
    if auto_compact is not None and auto_compact <= 0:
        errors.append("auto_compact_capacity_tokens must be positive when present")

    cold_start_profile = profile["cold_start_profile"]
    if cold_start_profile not in {"compact", "full"}:
        errors.append("cold_start_profile must be compact or full")

    warnings = profile["rollover_warning_percentages"]
    parsed_warnings: list[float] = []
    if not isinstance(warnings, list) or len(warnings) != 3:
        errors.append("rollover_warning_percentages must contain exactly three values")
    else:
        for value in warnings:
            if isinstance(value, bool) or not isinstance(value, int | float):
                errors.append(f"invalid rollover warning percentage: {value!r}")
                continue
            parsed_warnings.append(float(value))
        if len(parsed_warnings) == 3 and not (
            0 < parsed_warnings[0] < parsed_warnings[1] < parsed_warnings[2] < 100
        ):
            errors.append("rollover warning percentages must be strictly increasing between 0 and 100")

    if window and budget is not None:
        if budget > window:
            errors.append("cold_start_budget_tokens cannot exceed main_context_window_tokens")
        if cold_start_profile == "compact" and budget > window * 0.10:
            errors.append("compact cold-start budget cannot exceed 10% of the main context window")
    if window and auto_compact is not None:
        if auto_compact >= window:
            errors.append("auto_compact_capacity_tokens must be below the main context window")
        if len(parsed_warnings) == 3:
            compact_percent = auto_compact * 100.0 / window
            if parsed_warnings[-1] >= compact_percent:
                errors.append(
                    "emergency rollover warning must fire before the configured auto-compaction capacity"
                )

    return errors


def load_registry(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the versioned registry and fail loudly on malformed configuration."""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ContextProfileError(f"cannot load context-profile registry {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContextProfileError("context-profile registry must be a mapping")
    if data.get("version") != REGISTRY_VERSION:
        raise ContextProfileError(f"context-profile registry version must be {REGISTRY_VERSION}")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or "fallback" not in profiles:
        raise ContextProfileError("context-profile registry must define a fallback profile")

    errors: list[str] = []
    for key, profile in profiles.items():
        if not isinstance(key, str) or not isinstance(profile, dict):
            errors.append(f"profile {key!r} must be a mapping")
            continue
        errors.extend(f"{key}: {error}" for error in validate_profile(profile, key=key))
    if errors:
        raise ContextProfileError("; ".join(errors))
    return data


def load_profiles(config_path: Path = CONFIG_PATH) -> dict[str, dict[str, Any]]:
    """Return validated profiles keyed by profile id."""
    profiles = load_registry(config_path)["profiles"]
    return {key: dict(value) for key, value in profiles.items()}


def get_profile(profile_id: str, *, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Return one validated profile, falling back only for an unknown id."""
    profiles = load_profiles(config_path)
    return dict(profiles.get(profile_id, profiles["fallback"]))


def profile_matches_model(profile: dict[str, Any], model_id: str | None) -> bool | None:
    """Return whether an observed model matches, or None when it is not observed yet."""
    if not model_id:
        return None
    return any(re.search(pattern, model_id) is not None for pattern in profile["model_id_patterns"])


def resolve_profile(
    profile_id: str | None = None,
    model_id: str | None = None,
    *,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    """Resolve an explicit route contract; absent, unknown, or mismatched routes fail closed."""
    profiles = load_profiles(config_path)
    fallback = dict(profiles["fallback"])
    requested_profile_id = profile_id.strip() if isinstance(profile_id, str) and profile_id.strip() else None
    requested_model_id = model_id.strip() if isinstance(model_id, str) and model_id.strip() else None

    expected = profiles.get(requested_profile_id) if requested_profile_id else None
    if expected is None:
        effective = fallback
        reason = "missing-profile" if requested_profile_id is None else "unknown-profile"
        model_mismatch = False
    else:
        match = profile_matches_model(expected, requested_model_id)
        model_mismatch = match is False
        if model_mismatch:
            effective = fallback
            reason = "model-mismatch"
        else:
            effective = dict(expected)
            reason = "explicit-profile"

    result = dict(effective)
    result.update(
        {
            "requested_profile_id": requested_profile_id,
            "requested_model_id": requested_model_id,
            "resolution_reason": reason,
            "trusted": reason == "explicit-profile",
            "model_mismatch": model_mismatch,
            "expected_profile_id": expected.get("profile_id") if expected else None,
            "expected_main_model_id": expected.get("main_model_id") if expected else None,
            "expected_main_context_window_tokens": (
                expected.get("main_context_window_tokens") if expected else None
            ),
        }
    )
    return result


def _env_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Explicit main-session profile id")
    parser.add_argument("--model", help="Observed or requested main model id")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--format", choices=("json", "env0"), default="json")
    args = parser.parse_args()
    try:
        profile = resolve_profile(args.profile, args.model, config_path=args.config)
    except ContextProfileError as exc:
        parser.error(str(exc))

    if args.format == "json":
        print(json.dumps(profile, sort_keys=True))
        return 0

    fields = {
        "PROFILE_ID": profile["profile_id"],
        "TRANSPORT": profile["transport"],
        "MAIN_MODEL_ID": profile["main_model_id"],
        "MAIN_CONTEXT_WINDOW_TOKENS": profile["main_context_window_tokens"],
        "AUTO_COMPACT_CAPACITY_TOKENS": profile["auto_compact_capacity_tokens"],
        "COLD_START_PROFILE": profile["cold_start_profile"],
        "COLD_START_BUDGET_TOKENS": profile["cold_start_budget_tokens"],
        "ROLLOVER_WARNING_PERCENTAGES": profile["rollover_warning_percentages"],
        "REQUESTED_PROFILE_ID": profile["requested_profile_id"],
        "REQUESTED_MODEL_ID": profile["requested_model_id"],
        "RESOLUTION_REASON": profile["resolution_reason"],
        "TRUSTED": profile["trusted"],
        "MODEL_MISMATCH": profile["model_mismatch"],
        "EXPECTED_PROFILE_ID": profile["expected_profile_id"],
        "EXPECTED_MAIN_MODEL_ID": profile["expected_main_model_id"],
        "EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS": profile["expected_main_context_window_tokens"],
    }
    for key, value in fields.items():
        sys.stdout.buffer.write(key.encode("utf-8") + b"\0")
        sys.stdout.buffer.write(_env_value(value).encode("utf-8") + b"\0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
