## Adversarial QA Review — volodymyr-velykii

Reading all provided files in full before flagging anything.

---

### Issues Found

**ISSUE 1 — Register violation (anachronism): "у проектах"**
Location: Intro section, first paragraph
> «коли Москви ще не існувало навіть у проектах»

"У проектах" is modern corporate/bureaucratic slang (anachronistic; borrowed from Russian usage "даже в проектах"). The green team flagged this fix — it was **NOT applied**. At C1 literary register this reads as jarring bathos in an otherwise elevated passage.
Fix: → «у задумах»

---

**ISSUE 2 — Russism: "рихлий"**
Location: Спадщина section
> «він залишив по собі вже не рихлий союз племен»

"Рихлий" is a Russism from "рыхлый" (crumbly/loose soil). It does not exist in standard Ukrainian with this meaning (disorganized/fragmented polity). The green team flagged this — **NOT applied**.
Fix: → «розрізнений»

---

**ISSUE 3 — Typo: "можутьню"**
Location: Same sentence as Issue 2
> «а можутьню, централізовану державу»

Keyboard error — should be «могутню». Green team flagged — **NOT applied**.
Fix: → «могутню»

---

**ISSUE 4 — Plan deviation: section header "Змагання" vs required "Тендер"**
Location: Section 5 H2 header
> `## Геополітичний вибір: Змагання світових релігій`

The plan specifies `"Геополітичний вибір: Тендер світових релігій"`. The body text consistently uses the "тендер" metaphor throughout ("державний замовник на тендері", "геополітичний тендер"). The header contradicts the internal logic of the section. Green team flagged — **NOT applied**.
Fix: → `## Геополітичний вибір: Тендер світових релігій`

---

**Additional scan — no further issues found:**
- No Russian characters (ы, э, ё, ъ) found
- No "приймати участь," "получати," "кушати," "слідуючий"
- Dates verified: Sviatoslav's death 972 ✓; first mention of Moscow 1147 (132 years after 1015) ✓ — the content is correct; the meta note "150 years" is wrong but is only in planning notes, not content
- Factual claims: Bardas Phokas revolt 987–989 ✓; Varangian corps of 6,000 ✓; Desiatynna Church 989–996 ✓; Pochaina as Dnipro tributary ✓; bident (двозуб) of Sviatoslav → trident of Volodymyr ✓
- Activities: all cross-references resolve; quiz answers factually correct; rubric adds to 100 ✓; true/false explanations consistent with prose ✓
- Required vocabulary (хрещення, язичництво, хреститель, рівноапостольний, пантеон, ідол, десятина, усобиця, порфірородна, Корсунь): all present in prose ✓
- Plan sections: all 11 present and covered ✓ (after header fix)
- No "Це не просто X, а Y" overuse; prose voice is distinct and purposeful
- No forward references treated as teachable content

---

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/volodymyr-velykii.md
---OLD---
коли Москви ще не існувало навіть у проектах
---NEW---
коли Москви ще не існувало навіть у задумах
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/volodymyr-velykii.md
---OLD---
він залишив по собі вже не рихлий союз племен, а можутьню, централізовану державу
---NEW---
він залишив по собі вже не розрізнений союз племен, а могутню, централізовану державу
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/volodymyr-velykii.md
---OLD---
## Геополітичний вибір: Змагання світових релігій
---NEW---
## Геополітичний вибір: Тендер світових релігій
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===