"""Per-lane Git identity shared by launchers and sanitized worker environments.

These display identities do not attest a model or grant cross-family clearance;
formal review continues to require model trailers and runtime provenance.
"""

from __future__ import annotations

import argparse

from learn_ukrainian_v4_runtime.model_families import Family, canonical_cursor_model, normalize_family

_PROVIDER_FAMILIES = {
    "agy": Family.GOOGLE,
    "gemini": Family.GOOGLE,
    "codex": Family.OPENAI,
    "terra": Family.OPENAI,
    "claude": Family.ANTHROPIC,
    "kimi": Family.MOONSHOT,
    "glm": Family.ZHIPU,
    "opencode": Family.ZHIPU,
    "deepseek": Family.DEEPSEEK,
    "grok": Family.XAI,
}
_GIT_FAMILY_NAMES = {
    Family.GOOGLE: "Gemini",
    Family.OPENAI: "OpenAI",
    Family.ANTHROPIC: "Claude",
    Family.MOONSHOT: "Kimi",
    Family.ZHIPU: "GLM",
    Family.DEEPSEEK: "DeepSeek",
    Family.XAI: "Grok",
}


def git_identity_env(provider: str, model: str | None = None) -> dict[str, str]:
    """Return author and committer identity; unresolved lanes always use Unknown.

    Cursor inherits its effective concrete model's family using the canonical
    runtime normalizer. Auto (even under a family-named parent) stays Unknown.
    """
    provider = provider.strip().lower()
    family = (
        normalize_family(canonical_cursor_model(model))
        if provider == "cursor"
        else _PROVIDER_FAMILIES.get(provider, Family.UNKNOWN)
    )
    name = _GIT_FAMILY_NAMES.get(family, "LU Unknown")
    slug = name.lower() if name != "LU Unknown" else "unknown"
    return {
        f"GIT_{role}_{field}": value
        for role in ("AUTHOR", "COMMITTER")
        for field, value in (("NAME", name), ("EMAIL", f"{slug}@local.invalid"))
    }


def main() -> None:
    """Emit a tab-separated name and email for the Bash launcher (no eval)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider")
    parser.add_argument("model", nargs="?")
    args = parser.parse_args()
    identity = git_identity_env(args.provider, args.model)
    print(f"{identity['GIT_AUTHOR_NAME']}\t{identity['GIT_AUTHOR_EMAIL']}")


if __name__ == "__main__":
    main()
