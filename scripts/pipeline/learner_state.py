"""Learner State Manifest — cumulative vocabulary + grammar for module N.

Scans all modules before module N in a track to build a picture of
what the learner knows at that point. Injected into content prompts
so Gemini doesn't use unknown words or re-explain known grammar.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CURRICULUM_ROOT = Path(__file__).resolve().parent.parent.parent / "curriculum" / "l2-uk-en"


def _load_curriculum() -> dict:
    """Load curriculum.yaml."""
    path = CURRICULUM_ROOT / "curriculum.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_vocab(track: str, slug: str) -> list[str]:
    """Load vocabulary lemmas for a module."""
    path = CURRICULUM_ROOT / track / "vocabulary" / f"{slug}.yaml"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data:
            return []
        items = data.get("items", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        return [item["lemma"] for item in items if isinstance(item, dict) and "lemma" in item]
    except Exception:
        return []


def _load_grammar(track: str, slug: str) -> list[str]:
    """Load grammar topics from a module's plan."""
    path = CURRICULUM_ROOT / "plans" / track / f"{slug}.yaml"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            plan = yaml.safe_load(f)
        if not plan or not isinstance(plan, dict):
            return []
        return plan.get("grammar", []) or []
    except Exception:
        return []


def _load_plan_title(track: str, slug: str) -> str | None:
    """Load a module's title from its plan."""
    path = CURRICULUM_ROOT / "plans" / track / f"{slug}.yaml"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            plan = yaml.safe_load(f)
        return plan.get("title") if isinstance(plan, dict) else None
    except Exception:
        return None


def _parse_slug(entry) -> str:
    """Extract slug from a manifest entry."""
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def build_learner_state(track: str, module_num: int) -> dict:
    """Build the learner state manifest for module N.

    Returns a dict with:
    - cumulative_vocabulary: list of all lemmas taught before module N
    - known_grammar: list of all grammar topics covered before module N
    - module_count: how many modules precede this one
    - previous_theme: title of the previous module (for narrative continuity)
    - next_topic: grammar topics of the next module (for foreshadowing)
    """
    curriculum = _load_curriculum()
    modules = curriculum.get("levels", {}).get(track, {}).get("modules", [])

    if not modules or module_num <= 1:
        next_grammar = []
        if modules and len(modules) > 1:
            next_slug = _parse_slug(modules[1])
            next_grammar = _load_grammar(track, next_slug)
        return {
            "cumulative_vocabulary": [],
            "known_grammar": [],
            "module_count": 0,
            "previous_theme": None,
            "next_topic": next_grammar,
        }

    # Collect from all modules before this one
    cumulative_vocab: list[str] = []
    known_grammar: list[str] = []
    seen_vocab: set[str] = set()
    previous_theme = None

    for i, entry in enumerate(modules):
        if i >= module_num - 1:  # 1-indexed
            break

        slug = _parse_slug(entry)

        # Vocabulary
        for lemma in _load_vocab(track, slug):
            if lemma not in seen_vocab:
                cumulative_vocab.append(lemma)
                seen_vocab.add(lemma)

        # Grammar
        for topic in _load_grammar(track, slug):
            if topic not in known_grammar:
                known_grammar.append(topic)

        # Track the last module's title
        title = _load_plan_title(track, slug)
        if title:
            previous_theme = title

    # Next module's grammar (for foreshadowing)
    next_topic: list[str] = []
    if module_num <= len(modules):
        next_slug = _parse_slug(modules[module_num - 1])  # current module
        # Look one ahead
        if module_num < len(modules):
            next_next_slug = _parse_slug(modules[module_num])
            next_topic = _load_grammar(track, next_next_slug)

    return {
        "cumulative_vocabulary": cumulative_vocab,
        "known_grammar": known_grammar,
        "module_count": min(module_num - 1, len(modules)),
        "previous_theme": previous_theme,
        "next_topic": next_topic,
    }


def format_learner_state(state: dict) -> str:
    """Format learner state as text for prompt injection."""
    if not state["cumulative_vocabulary"] and not state["known_grammar"]:
        next_topic = state.get("next_topic", [])
        if next_topic:
            return (
                "(This is the first module — no prior learner knowledge.)\n\n"
                f"**Coming next (module after this):** {', '.join(next_topic[:3])}\n"
                "You may use related words as fixed phrases for foreshadowing, "
                "but do NOT explain the grammar rule."
            )
        return "(This is the first module — no prior learner knowledge.)"

    parts = [f"**Modules completed before this one:** {state['module_count']}"]

    if state.get("previous_theme"):
        parts.append(f"**Previous module:** {state['previous_theme']}")

    if state["cumulative_vocabulary"]:
        vocab = state["cumulative_vocabulary"]
        parts.append(f"\n**Cumulative vocabulary ({len(vocab)} words):**")
        for i in range(0, len(vocab), 10):
            chunk = vocab[i:i + 10]
            parts.append(", ".join(chunk))

    if state["known_grammar"]:
        parts.append(f"\n**Grammar already taught ({len(state['known_grammar'])} topics):**")
        for topic in state["known_grammar"]:
            parts.append(f"- {topic}")

    if state.get("next_topic"):
        parts.append(f"\n**Coming next (module after this):** {', '.join(state['next_topic'][:3])}")
        parts.append("You may use related words as fixed phrases for foreshadowing, "
                      "but do NOT explain the grammar rule.")

    parts.append("\n**Rule:** Do not re-explain grammar already taught. "
                 "Do not use vocabulary words the learner hasn't seen unless you "
                 "introduce them explicitly.")

    return "\n".join(parts)
