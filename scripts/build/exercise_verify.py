"""Exercise verification — check that exercise items are grounded in module prose.

Extracts Ukrainian words from exercises and verifies they appear in the prose
sections that precede them. Also checks against plan vocabulary_hints.

Words are tagged as "answer" (the tested word — high risk if ungrounded)
or "context" (sentence framing — low risk). Report groups by risk level.

Issue: #1016
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Ukrainian word pattern: at least 2 Cyrillic characters (skip single-letter prepositions)
# Allows combining acute (U+0301) inside words for stress-marked text
_UK_WORD_RE = re.compile(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ\u0301]+")

# Exercise block pattern: :::type ... :::
_EXERCISE_BLOCK_RE = re.compile(
    r"^:::(quiz|fill-in|match-up|group-sort|true-false)\b(.*?)^:::",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class ExerciseItem:
    """A single testable item extracted from an exercise."""

    word: str
    exercise_type: str
    context: str  # short snippet showing where it came from
    role: str = "context"  # "answer" = tested word (high risk), "context" = framing


@dataclass
class UnjumbleIssue:
    """A problem detected in an unjumble activity item."""

    sentence: str  # the correct sentence
    issue_type: str  # "comma_in_tile" | "ambiguous_order"
    detail: str


@dataclass
class VerifyResult:
    """Result of exercise verification for one module."""

    total_items: int = 0
    grounded_items: int = 0
    ungrounded: list[dict] = field(default_factory=list)
    vocab_coverage: dict = field(default_factory=dict)  # plan vocab check
    unjumble_issues: list[UnjumbleIssue] = field(default_factory=list)

    @property
    def all_grounded(self) -> bool:
        return len(self.ungrounded) == 0

    @property
    def ungrounded_answers(self) -> list[dict]:
        """High-risk: answer words not found in prose."""
        return [u for u in self.ungrounded if u.get("role") == "answer"]

    @property
    def ungrounded_context(self) -> list[dict]:
        """Low-risk: context/framing words not found in prose."""
        return [u for u in self.ungrounded if u.get("role") != "answer"]


def extract_exercise_items(content: str) -> list[ExerciseItem]:
    """Extract Ukrainian words being tested in all exercise blocks.

    Parses each exercise type's DSL to find the words the learner must
    produce or recognize.  Only works with the legacy inline DSL (:::quiz).
    For V6 YAML activities, use extract_exercise_items_from_yaml().
    """
    items: list[ExerciseItem] = []

    for m in _EXERCISE_BLOCK_RE.finditer(content):
        ex_type = m.group(1)
        block = m.group(2)

        if ex_type == "quiz":
            items.extend(_parse_quiz(block))
        elif ex_type == "fill-in":
            items.extend(_parse_fill_in(block))
        elif ex_type == "match-up":
            items.extend(_parse_match_up(block))
        elif ex_type == "group-sort":
            items.extend(_parse_group_sort(block))
        elif ex_type == "true-false":
            items.extend(_parse_true_false(block))

    return items


def extract_exercise_items_from_yaml(activities: dict) -> list[ExerciseItem]:
    """Extract Ukrainian words from a V6 activities YAML structure.

    The YAML has top-level keys 'inline' and 'workbook', each containing
    a list of activity dicts with 'type' and type-specific fields.
    """
    items: list[ExerciseItem] = []

    for section_key in ("inline", "workbook"):
        for activity in activities.get(section_key, []) or []:
            if not isinstance(activity, dict):
                continue
            ex_type = activity.get("type", "")
            items.extend(_extract_words_from_activity(activity, ex_type))

    return items


def _words_from_text(text: str, ex_type: str, role: str = "context") -> list[ExerciseItem]:
    """Extract Ukrainian words from a text string into ExerciseItems."""
    return [
        ExerciseItem(word=w.lower(), exercise_type=ex_type, context=text[:60], role=role)
        for w in _UK_WORD_RE.findall(text)
    ]



def _extract_words_from_activity(
    activity: dict, ex_type: str
) -> list[ExerciseItem]:
    """Extract Ukrainian words from a single activity dict.

    Tags words as "answer" (the tested/correct word) or "context" (framing).
    """
    items: list[ExerciseItem] = []

    activity_items = activity.get("items", [])
    if not isinstance(activity_items, list):
        activity_items = []

    if ex_type == "fill-in":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            # Answer = what the learner must produce → high risk
            answer = str(item.get("answer", ""))
            items.extend(_words_from_text(answer, ex_type, role="answer"))
            # Sentence context = framing → low risk
            items.extend(_words_from_text(str(item.get("sentence", "")), ex_type, role="context"))
            # Options = distractors (intentionally wrong) → skip

    elif ex_type == "error-correction":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            # Correction = the correct form → answer (must be grounded)
            correction = str(item.get("answer", "") or item.get("correction", ""))
            items.extend(_words_from_text(correction, ex_type, role="answer"))
            # Sentence context = framing → low risk
            items.extend(_words_from_text(str(item.get("sentence", "")), ex_type, role="context"))
            # Error field = intentionally wrong word → skip (won't be in prose)
            # Options = distractors → skip

    elif ex_type == "quiz":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            # Question text = context
            items.extend(_words_from_text(str(item.get("question", "")), ex_type, role="context"))
            # Options = mix of correct + distractors → skip
            # (We can't distinguish correct from wrong without the answer key)

    elif ex_type == "match-up":
        pairs = activity.get("pairs", [])
        if not isinstance(pairs, list):
            pairs = []
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            # Left side = the term being matched → answer
            items.extend(_words_from_text(str(pair.get("left", "")), ex_type, role="answer"))
            # Right side = definition/description → context
            items.extend(_words_from_text(str(pair.get("right", "")), ex_type, role="context"))

    elif ex_type == "group-sort":
        groups = activity.get("groups", [])
        if not isinstance(groups, list):
            groups = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            # Group label = context (category name)
            items.extend(_words_from_text(str(group.get("label", "")), ex_type, role="context"))
            # Items being sorted = answer (learner must categorize)
            for gi in group.get("items", []) or []:
                items.extend(_words_from_text(str(gi), ex_type, role="answer"))

    elif ex_type == "true-false":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            # Statement = context (learner reads and evaluates, doesn't produce words)
            items.extend(_words_from_text(str(item.get("statement", "")), ex_type, role="context"))

    elif ex_type == "unjumble":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            # Words to reorder = answer (learner must know these)
            for w in item.get("words", []) or []:
                items.extend(_words_from_text(str(w), ex_type, role="answer"))

    elif ex_type == "order":
        for item in activity_items:
            if not isinstance(item, dict):
                continue
            for seg in item.get("segments", []) or []:
                items.extend(_words_from_text(str(seg), ex_type, role="answer"))

    return items


def _parse_quiz(block: str) -> list[ExerciseItem]:
    """Extract Ukrainian words from quiz options and correct answers."""
    items = []
    # Extract options: o: ["word1", "word2", ...]
    for m in re.finditer(r'o:\s*\[([^\]]+)\]', block):
        options_str = m.group(1)
        for opt in re.findall(r'"([^"]*)"', options_str):
            for w in _UK_WORD_RE.findall(opt):
                items.append(ExerciseItem(word=w.lower(), exercise_type="quiz", context=opt[:60], role="answer"))
    # Extract question text for Ukrainian words
    for m in re.finditer(r'q:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="quiz", context=m.group(1)[:60], role="context"))
    return items


def _parse_fill_in(block: str) -> list[ExerciseItem]:
    """Extract Ukrainian words from fill-in answers and sentences."""
    items = []
    # Extract answers
    for m in re.finditer(r'answer:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="fill-in", context=m.group(1)[:60], role="answer"))
    # Extract sentence context words
    for m in re.finditer(r'sentence:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="fill-in", context=m.group(1)[:60], role="context"))
    return items


def _parse_match_up(block: str) -> list[ExerciseItem]:
    """Extract Ukrainian words from match-up left/right pairs."""
    items = []
    # Left = term being matched → answer
    for m in re.finditer(r'left:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="match-up", context=m.group(1)[:60], role="answer"))
    # Right = definition → context
    for m in re.finditer(r'right:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="match-up", context=m.group(1)[:60], role="context"))
    return items


def _parse_group_sort(block: str) -> list[ExerciseItem]:
    """Extract Ukrainian words from group-sort items and group names."""
    items = []
    # Group names → context
    for m in re.finditer(r'name:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="group-sort", context=m.group(1)[:60], role="context"))
    # Items in arrays → answer
    for m in re.finditer(r'items:\s*\[([^\]]+)\]', block):
        for item in re.findall(r'"([^"]*)"', m.group(1)):
            for w in _UK_WORD_RE.findall(item):
                items.append(ExerciseItem(word=w.lower(), exercise_type="group-sort", context=item[:60], role="answer"))
    return items


def _parse_true_false(block: str) -> list[ExerciseItem]:
    """Extract Ukrainian words from true-false statements."""
    items = []
    for m in re.finditer(r'statement:\s*"([^"]*)"', block):
        for w in _UK_WORD_RE.findall(m.group(1)):
            items.append(ExerciseItem(word=w.lower(), exercise_type="true-false", context=m.group(1)[:60], role="context"))
    return items


def extract_prose_words(content: str) -> set[str]:
    """Extract all Ukrainian words from prose sections (before exercises).

    Prose = everything in H2 sections that is NOT inside an exercise block.
    This includes dialogues, examples, bullet points, etc.
    """
    # Remove exercise blocks from content to get prose only
    prose = _EXERCISE_BLOCK_RE.sub("", content)

    # Remove enrichment tabs (словник, зошит, ресурси)
    tab_marker = prose.find("<!-- TAB:Словник -->")
    if tab_marker != -1:
        prose = prose[:tab_marker]

    # Extract all Ukrainian words (lowercased, 2+ chars)
    words = set()
    for w in _UK_WORD_RE.findall(prose):
        words.add(w.lower())
        # Also add the word without stress marks (combining acute)
        clean = w.replace("\u0301", "").lower()
        if clean != w.lower():
            words.add(clean)

    return words


def _check_unjumble_issues(activities: dict) -> list[UnjumbleIssue]:
    """Check unjumble activities for structural problems.

    Detects:
    1. Commas/semicolons inside word tiles — invisible to learner in UI
    2. Short sentences (≤4 words) with flexible word order — multiple valid solutions
    """
    issues: list[UnjumbleIssue] = []

    for section_key in ("inline", "workbook"):
        for activity in activities.get(section_key, []) or []:
            if not isinstance(activity, dict):
                continue
            if activity.get("type") != "unjumble":
                continue

            for item in activity.get("items", []) or []:
                if not isinstance(item, dict):
                    continue

                words = item.get("words", [])
                correct = item.get("correct_order", item.get("answer", ""))

                # Build the sentence for reporting
                if isinstance(correct, list):
                    sentence = " ".join(correct)
                elif isinstance(correct, str):
                    sentence = correct
                else:
                    sentence = " ".join(words) if words else ""

                # Check 1: commas/semicolons inside tiles
                for w in words:
                    w_str = str(w)
                    # Allow final punctuation (.!?) on last word, but flag commas/semicolons
                    if "," in w_str or ";" in w_str:
                        issues.append(UnjumbleIssue(
                            sentence=sentence,
                            issue_type="comma_in_tile",
                            detail=f"tile \"{w_str}\" contains comma/semicolon — invisible in UI",
                        ))

                # Check 2: missing positional anchors
                # Capital letters, punctuation (.!?,) lock tiles to positions.
                # Flag sentences that lack these cues — learner has no way to
                # determine order.
                has_capital = any(str(w)[0].isupper() for w in words if str(w))
                has_final_punct = any(
                    str(w)[-1] in ".!?" for w in words if str(w)
                )
                if not has_capital and not has_final_punct:
                    issues.append(UnjumbleIssue(
                        sentence=sentence,
                        issue_type="no_anchors",
                        detail="no capital letter or final punctuation — learner can't determine first/last word",
                    ))

    return issues


def extract_plan_vocab(plan: dict) -> set[str]:
    """Extract Ukrainian words from plan vocabulary_hints."""
    from pipeline.vocab_helpers import extract_vocab_words

    words = set()
    vocab_hints = plan.get("vocabulary_hints", {})
    for word in extract_vocab_words(vocab_hints):
        for w in _UK_WORD_RE.findall(word):
            words.add(w.lower())
    return words


def verify_exercises(
    content: str,
    plan: dict | None = None,
    activities: dict | None = None,
) -> VerifyResult:
    """Main verification: check exercise items against prose and plan vocab.

    Args:
        content: module markdown content (prose + optional inline DSL exercises)
        plan: plan dict with vocabulary_hints
        activities: V6 activities YAML dict (inline + workbook sections).
            If provided, exercise items are extracted from this instead of
            parsing DSL blocks in the markdown.

    Returns a VerifyResult with grounded/ungrounded counts and details.
    """
    result = VerifyResult()

    exercise_items = (
        extract_exercise_items_from_yaml(activities)
        if activities
        else extract_exercise_items(content)
    )
    prose_words = extract_prose_words(content)
    plan_vocab = extract_plan_vocab(plan) if plan else set()

    # Combine prose + plan vocab as the "taught" set
    taught = prose_words | plan_vocab

    # Deduplicate exercise items by word (keep highest-risk role)
    seen_words: dict[str, ExerciseItem] = {}
    for item in exercise_items:
        if item.word not in seen_words or (
            item.role == "answer" and seen_words[item.word].role != "answer"
        ):
            seen_words[item.word] = item
    unique_items = list(seen_words.values())

    result.total_items = len(unique_items)

    for item in unique_items:
        # Strip stress marks for comparison
        clean_word = item.word.replace("\u0301", "")
        if clean_word in taught or item.word in taught:
            result.grounded_items += 1
        else:
            result.ungrounded.append({
                "word": item.word,
                "exercise_type": item.exercise_type,
                "context": item.context,
                "role": item.role,
            })

    # Check unjumble activities for structural problems
    if activities:
        result.unjumble_issues = _check_unjumble_issues(activities)

    # Check plan vocab coverage separately
    if plan_vocab:
        exercise_words = {item.word.replace("\u0301", "") for item in exercise_items}
        covered = plan_vocab & exercise_words
        result.vocab_coverage = {
            "plan_vocab_total": len(plan_vocab),
            "tested_in_exercises": len(covered),
            "not_tested": sorted(plan_vocab - exercise_words),
        }

    return result


def format_verify_result(result: VerifyResult) -> str:
    """Format verification result for logging.

    Groups ungrounded words by risk:
    - 🔍 answer words (high risk — learner must produce these)
    - 💬 context words (low risk — sentence framing)
    """
    lines = []
    if result.all_grounded:
        lines.append(
            f"  ✅ All {result.total_items} exercise item(s) grounded in prose"
        )
    else:
        answers = result.ungrounded_answers
        context = result.ungrounded_context

        if answers:
            lines.append(
                f"  🔍 {len(answers)} answer word(s) not in prose — check if taught:"
            )
            for item in answers[:15]:
                lines.append(
                    f"    → {item['word']} ({item['exercise_type']}: {item['context']})"
                )
            if len(answers) > 15:
                lines.append(f"    ... and {len(answers) - 15} more")

        if context:
            lines.append(
                f"  💬 {len(context)} context word(s) not in prose (framing, low risk)"
            )
            # Only show first 5 context words — they're low priority
            for item in context[:5]:
                lines.append(
                    f"    — {item['word']} ({item['exercise_type']}: {item['context']})"
                )
            if len(context) > 5:
                lines.append(f"    ... and {len(context) - 5} more")

        lines.append(
            f"  Summary: {result.grounded_items}/{result.total_items} grounded, "
            f"{len(answers)} answer gaps, {len(context)} context gaps"
        )

    # Unjumble structural issues
    if result.unjumble_issues:
        comma_issues = [i for i in result.unjumble_issues if i.issue_type == "comma_in_tile"]
        order_issues = [i for i in result.unjumble_issues if i.issue_type == "ambiguous_order"]

        if comma_issues:
            lines.append(
                f"  ⚠️ {len(comma_issues)} unjumble tile(s) have commas — invisible in UI:"
            )
            for issue in comma_issues[:5]:
                lines.append(f"    → {issue.detail} — \"{issue.sentence}\"")
            if len(comma_issues) > 5:
                lines.append(f"    ... and {len(comma_issues) - 5} more")

        if order_issues:
            lines.append(
                f"  ⚠️ {len(order_issues)} unjumble sentence(s) may have multiple valid orderings:"
            )
            for issue in order_issues[:5]:
                lines.append(f"    → \"{issue.sentence}\" ({issue.detail})")
            if len(order_issues) > 5:
                lines.append(f"    ... and {len(order_issues) - 5} more")

    if result.vocab_coverage:
        vc = result.vocab_coverage
        lines.append(
            f"  Plan vocab: {vc['tested_in_exercises']}/{vc['plan_vocab_total']} "
            f"words tested in exercises"
        )

    return "\n".join(lines)
