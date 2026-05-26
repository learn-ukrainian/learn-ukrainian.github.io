
from scripts.build.linear_pipeline import _register_consistency_gate


def test_register_consistency_exempt_levels():
    """C1, C2, PRO are exempt and should return PASS even if 'шо' is present out of context."""
    text = "Тут є слово шо в звичайному тексті."
    for level in ("c1", "c2", "pro"):
        plan = {"level": level}
        result = _register_consistency_gate(text, plan)
        assert result["passed"] is True
        assert result["verdict"] == "PASS"
        assert result["violation_count"] == 0


def test_register_consistency_dialogue_box_exempt():
    """шо inside <DialogueBox> block -> PASS (no violations)."""
    text = """
Деякий текст перед діалогом.

<DialogueBox
  title="Roommates"
  participants={[{"name": "А", "role": "A"}]}
>
**A**: Шо ти робиш?
</DialogueBox>

Тут немає порушень.
"""
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "PASS"
    assert result["violation_count"] == 0


def test_register_consistency_blockquote_exempt():
    """шо inside a > blockquote -> PASS (no violations)."""
    text = """
Ми читаємо цитату:
> Він сказав: "Шо це таке?"
І продовжуємо далі.
"""
    plan = {"level": "a2"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "PASS"
    assert result["violation_count"] == 0


def test_register_consistency_teacher_voice_warn():
    """шо in teacher-voice paragraph at level A1 -> WARN with violation count 1."""
    text = """
Сьогодні ми вивчимо, шо таке дієслово.
"""
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "WARN"
    assert result["severity"] == "WARN"
    assert result["violation_count"] == 1
    assert result["violations"][0]["form"].lower() == "шо"
    assert result["violations"][0]["line"] == 2


def test_register_consistency_mixed():
    """Multiple шо instances mixed (some in dialogue, some not) -> WARN with only the out-of-context ones counted."""
    text = """
Тут перше порушення: шо це.

<DialogueBox>
А це шо? (це не порушення)
</DialogueBox>

> Шо кажеш? (це не порушення)

Тут друге порушення: тому шо.
"""
    plan = {"level": "b1"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "WARN"
    assert result["violation_count"] == 2
    assert result["violations"][0]["line"] == 2
    assert result["violations"][1]["line"] == 10


def test_register_consistency_only_shcho_pass():
    """Module with only що -> PASS."""
    text = """
Тут ми кажемо що, тому що це літературно.
"""
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "PASS"
    assert result["violation_count"] == 0


def test_register_consistency_code_block_exempt():
    """шо inside fenced code blocks -> PASS (no violations)."""
    text = """
```python
print("Шо тут?")
```
Текст.
"""
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["passed"] is True
    assert result["verdict"] == "PASS"
    assert result["violation_count"] == 0


def test_register_consistency_self_closing_dialogue_box_exempt():
    """Self-closing <DialogueBox uk="..." en="..." /> on one line -> PASS for that line,
    but subsequent teacher-voice prose with шо still flagged.

    Regression for the state-machine edge case where `<DialogueBox ... />`
    set in_dialogue=True without a matching close, suppressing later
    violations until end-of-file (#2307 review).
    """
    text = """
Перший рядок прози: тут немає порушень.

<DialogueBox uk="Шо ти робиш?" en="What are you doing?" />

Тут teacher-voice: шо це таке?
"""
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["verdict"] == "WARN"
    assert result["violation_count"] == 1, (
        f"Self-closing DialogueBox should exempt only line 4, "
        f"not suppress later violations; got {result['violations']!r}"
    )
    assert result["violations"][0]["line"] == 6


def test_register_consistency_inline_tag_on_same_line_as_prose():
    """A line containing BOTH `<DialogueBox ... />` AND teacher-voice шо.

    Pre-masking approach: the DialogueBox region is replaced with spaces;
    the surrounding teacher-voice text remains visible to the scanner so
    шо outside the tag is still flagged.

    The previous line-by-line state machine would set in_dialogue=True at
    the start of the line and skip violation detection for the whole line,
    missing the violation.
    """
    text = "Прозовий контекст з шо. <DialogueBox uk=\"Шо?\" en=\"What?\" />\n"
    plan = {"level": "a1"}
    result = _register_consistency_gate(text, plan)
    assert result["verdict"] == "WARN"
    assert result["violation_count"] == 1
    assert result["violations"][0]["line"] == 1
    # The `шо` inside the DialogueBox prop must NOT be counted.
    assert all(
        v["form"].lower() != "шо" or "DialogueBox" not in v.get("context", "")
        or v["line"] == 1
        for v in result["violations"]
    )
