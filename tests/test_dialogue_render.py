from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_mdx import process_dialogues


def test_process_dialogues_converts_v7_blockquote_dialogue_to_dialogue_box():
    content = """**Діалог 1 — Будній ранок**

> **Ліна:** Коли ти прокидаєшся?
> **Настя:** Я прокидаюся о сьомій.
> **Ліна:** Що ти робиш потім?
> **Настя:** Спочатку вмиваюся.
> **Ліна:** А далі?
> **Настя:** Потім одягаюся і снідаю.
> **Ліна:** Коли ти йдеш на роботу?
> **Настя:** О восьмій. А ти?
> **Ліна:** Я прокидаюся пізно — о дев'ятій.
"""

    mdx = process_dialogues(content)

    assert mdx.count("<DialogueBox") == 1
    assert 'title="Діалог 1 — Будній ранок"' in mdx
    assert mdx.count('"speaker"') == 9
    assert "Коли ти прокидаєшся?" in mdx
    assert "> **Ліна:**" not in mdx

