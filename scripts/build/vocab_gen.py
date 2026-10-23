"""Writer-driven vocabulary generation for the словник tab.

The writer produces vocabulary YAML after writing module content.
This module handles deduplication and VESUM enrichment.

Architecture:
  WRITE (prose) → VOCAB GEN (writer outputs YAML) → DEDUPE → VESUM → словник

Issue: #1025
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
except ModuleNotFoundError as exc:
    # Script execution puts the script directory on sys.path, so the
    # top-level package is absent (exc.name == "scripts"). Any other
    # import failure must propagate.
    if exc.name != "scripts":
        raise
    # lib.readonly_sqlite lives in scripts/, which file execution does not put on sys.path.
    _scripts_dir = next(
        parent for parent in Path(__file__).resolve().parents if parent.name == "scripts"
    )
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from lib.readonly_sqlite import open_readonly as _open_readonly  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_shared_data_file(*parts: str) -> Path:
    """Resolve repo-shared data files from a worktree when needed.

    Dispatch worktrees nest under ``.worktrees/``, and a read-write opener can
    leave a 0-byte placeholder in the worktree. Prefer a non-empty file here,
    otherwise the populated database next to that ``.worktrees`` directory.
    """

    def usable(path: Path) -> bool:
        return path.is_file() and path.stat().st_size > 0

    candidate = PROJECT_ROOT.joinpath(*parts)
    if usable(candidate):
        return candidate
    for ancestor in PROJECT_ROOT.parents:
        if ancestor.name == ".worktrees":
            shared = ancestor.parent.joinpath(*parts)
            if usable(shared):
                return shared
            break
    return candidate


VESUM_DB = _resolve_shared_data_file("data", "vesum.db")

# Ukrainian POS labels
_POS_LABELS = {
    "noun": "ім.",
    "verb": "дієсл.",
    "adj": "прикм.",
    "adv": "присл.",
    "numr": "числ.",
    "prep": "прийм.",
    "conj": "спол.",
    "part": "част.",
    "intj": "виг.",
    "pron": "займ.",
}

_GENDER_MAP = {":m:": "ч.", ":f:": "ж.", ":n:": "с."}


def vesum_enrich_entry(entry: dict) -> dict:
    """Add POS, gender, stress, and VESUM verification to a vocabulary entry.

    Skips expressions (multi-word phrases) for VESUM lookup.
    After VESUM lookup, runs stress annotation on the word field.
    Flags words NOT found in VESUM with ``verified: false``.

    Returns the entry with added 'pos', 'gender', 'verified' fields
    and stress-annotated 'word'.
    """
    result = dict(entry)
    result.setdefault("pos", "")
    result.setdefault("gender", "")

    # Skip expressions — VESUM doesn't have multi-word entries
    if entry.get("expression"):
        result["verified"] = True  # expressions skip VESUM check
        return result

    word = entry.get("word", "").strip("?!.,")
    if not word:
        result["verified"] = False
        return result

    found_in_vesum = False

    if VESUM_DB.exists():
        try:
            db = _open_readonly(str(VESUM_DB))
            try:
                row = db.execute(
                    "SELECT pos, tags FROM forms WHERE word_form = ? LIMIT 1",
                    (word.lower(),),
                ).fetchone()
                if not row:
                    # Try lemma lookup
                    row = db.execute(
                        "SELECT pos, tags FROM forms WHERE lemma = ? LIMIT 1",
                        (word.lower(),),
                    ).fetchone()
                if row:
                    found_in_vesum = True
                    result["pos"] = _POS_LABELS.get(row[0], "")
                    if row[0] == "noun":
                        for tag, label in _GENDER_MAP.items():
                            if tag in row[1]:
                                result["gender"] = label
                                break
            finally:
                db.close()
        except Exception:
            pass

    result["verified"] = found_in_vesum
    if not found_in_vesum:
        logger.debug("vocab: word %r not found in VESUM — flagged verified=false", word)

    # Add stress marks to the word
    try:
        from pipeline.stress_annotator import annotate_stress
        stressed_word, count = annotate_stress(word)
        if count > 0:
            result["word"] = stressed_word
    except Exception:
        pass  # Stress annotation is best-effort

    return result


def _stress_word(word: str) -> str:
    """Add stress mark to a word for display in the slovnyk table.

    Best-effort: returns the original word if stress annotation fails.
    """
    try:
        from pipeline.stress_annotator import annotate_stress
        stressed, count = annotate_stress(word)
        if count > 0:
            return stressed
    except Exception:
        pass
    return word


def build_slovnyk_markdown(
    plan_vocab: list[dict],
    additional_vocab: list[dict],
    expressions: list[dict],
    *,
    meaning_label: str = "Переклад",
    flashcards_enabled: bool = True,
    meaning_mode: str = "translation",
) -> str:
    """Build the словник tab: dictionary table + interactive FlashcardDeck below.

    Structure:
    1. Markdown tables (reference dictionary)
    2. FlashcardDeck (interactive practice)
    3. Expressions table
    """
    GENDER_COLORS = {
        "ч.": "#0057B8", "м.": "#0057B8",
        "ж.": "#C2185B", "ф.": "#C2185B",
        "с.": "#E65100", "н.": "#E65100",
    }

    lines = []

    def _entry_meaning(entry: dict) -> str:
        if meaning_mode == "definition":
            return entry.get("definition") or entry.get("translation", "")
        return entry.get("translation") or entry.get("definition", "")

    # 1. Dictionary tables
    if plan_vocab:
        lines.extend([
            "",
            "### Обов'язкові та рекомендовані слова",
            "",
            f"| Слово | {meaning_label} | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
        ])
        for entry in plan_vocab:
            word = _stress_word(entry.get("word", ""))
            trans = _entry_meaning(entry)
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")
            lines.append(f"| **{word}** | {trans} | {pos} | {gender} |")

    if additional_vocab:
        lines.extend([
            "",
            "### Додаткові слова з уроку",
            "",
            f"| Слово | {meaning_label} | Частина мови | Рід |",
            "|-------|----------|-------------|-----|",
        ])
        for entry in additional_vocab:
            word = _stress_word(entry.get("word", ""))
            trans = _entry_meaning(entry)
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")
            lines.append(f"| **{word}** | {trans} | {pos} | {gender} |")

    if expressions:
        lines.extend([
            "",
            "### Вирази",
            "",
            f"| Вираз | {meaning_label} |",
            "|-------|----------|",
        ])
        for entry in expressions:
            word = entry.get("word", "")
            trans = _entry_meaning(entry)
            lines.append(f"| **{word}** | {trans} |")

    # 2. Interactive flashcards below the tables
    all_words = (plan_vocab or []) + (additional_vocab or [])
    if flashcards_enabled and all_words:
        cards = []
        for entry in all_words:
            word = _stress_word(entry.get("word", ""))
            trans = _entry_meaning(entry)
            pos = entry.get("pos", "")
            gender = entry.get("gender", "")

            card_parts = [f'front: "{_esc(word)}", back: "{_esc(trans)}"']
            if pos:
                card_parts.append(f'subtitle: "{_esc(pos)}"')
            if gender:
                card_parts.append(f'tag: "{_esc(gender)}"')
                color = GENDER_COLORS.get(gender, "")
                if color:
                    card_parts.append(f'tagColor: "{color}"')
            cards.append("{ " + ", ".join(card_parts) + " }")

        cards_js = ", ".join(cards)
        lines.extend([
            "",
            "### Картки — Flashcards",
            "",
            f'<FlashcardDeck client:only="react" cards={{[{cards_js}]}} />',
        ])

    lines.append("")
    return "\n".join(lines)


def _esc(s: str) -> str:
    """Escape quotes and apostrophes for JSX string props."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "&#39;")
