<!-- version: 0.1.0 | created: 2026-04-21 | Ukrainian-canonical review -->
# V6 Review Prompt — Ukrainian-Canonical Adversarial Review

Ви перевіряєте український навчальний модуль. Це **не** English-L2 bridge-урок. Оцінюйте його як український еталонний модуль: природність, точність, педагогіка, деколонізованість.

## Module Under Review

**Module:** {MODULE_NUM}: {TOPIC_TITLE} ({LEVEL}, {PHASE})
**Writer:** {WRITER_MODEL}
**Word target:** {WORD_TARGET}

## Shared Module Contract (source of truth)

{CONTRACT_YAML}

## Section-Mapped Wiki Excerpts

{SECTION_WIKI_EXCERPTS}

## Generated Content

<generated_module_content>
{GENERATED_CONTENT}
</generated_module_content>

**PIPELINE NOTE — Word count: {WORD_COUNT} words** (визначено детерміновано пайплайном; не переоцінюйте вручну).

## Review Protocol

### Step 1: Scan for linguistic errors

Перевіряйте український текст суворо. Якщо ви не певні, позначайте як `[NEEDS RAG VERIFICATION]`.

**Чотири ОБОВ'ЯЗКОВІ окремі перевірки:**
1. **Russianisms**
2. **Surzhyk**
3. **Calques**
4. **Paronyms**

Також перевіряйте:
- літери `ы, э, ё, ъ`
- хибні граматичні твердження
- неправильні відмінкові форми, рід, керування
- **кириличність прози**: без латинізації та без англомовних метакоментарів усередині української прози

**Критично:** не штрафуйте модуль за **відсутність англійського scaffolding**. Тут це норма.

Якщо помилок немає, напишіть: `No linguistic errors found.`

### Step 2: Check exercises

У прозі можуть бути лише `<!-- INJECT_ACTIVITY: ... -->` маркери, а самі вправи додаються окремо.

Перевірте:
- чи маркер стоїть після того матеріалу, який має тренувати;
- чи кожен запис `activity_obligations` має відповідний маркер; порядок не має значення;
- чи тип вправи відповідає контракту;
- чи вправи тестують **українську мовну навичку**, а не предметний факт;
- чи немає English-bridging патернів, якщо вони не були явно замовлені планом.

### PROOF OF ABSENCE

Перед тим як заявити, що щось відсутнє, ви мусите це перевірити пошуком або уважним перечитуванням потрібної секції. Не вигадуйте missing items.

### Step 3: Score on 9 dimensions

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Усі beats контракту покриті, секції на місці, обсяг не провалений. |
| 2 | **Linguistic accuracy** | 15% | Нормативна українська, нуль росіянізмів/суржику/кальок/паронімних збоїв. |
| 3 | **Pedagogical quality** | 15% | Пояснення ведуть через зразки, приклади конкретні, українська механіка навчена послідовно. |
| 4 | **Vocabulary coverage** | 10% | Планова лексика введена природно, без зайвого English metalanguage. |
| 5 | **Exercise quality** | 15% | Маркери/вправи відповідають контракту й тренують мовну форму, а не content recall. |
| 6 | **Engagement & tone** | 10% | Жива, точна українська вчительська проза без філера й без англомовного classroom-talk. |
| 7 | **Structural integrity** | 5% | Усі заголовки на місці, структура чиста, word target не провалений. |
| 8 | **Cultural accuracy** | 5% | Українська описана на власних підставах, без колоніальних рамок і хибних культурних формул. |
| 9 | **Dialogue & conversation quality** | 10% | Природні українські діалоги, реальні реакції, доречний регістр. |

**Примітка:** downstream `Словник` може містити українські тлумачення або бути відсутнім. Не штрафуйте writer за відсутність англійських перекладів.

### Step 4: Output raw scores

Видайте тільки сирі 1-10 оцінки в таблиці.

### Step 5: List findings

Якщо ви назвали помилку в evidence, вона мусить з'явитися у findings і в `<fixes>`.

Формат:

```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

### Step 6: Verdict

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero real findings, all dimensions ≥9. |
| **REVISE** | Є конкретні помилки або dimensions <9. |
| **REJECT** | Фундаментальна непридатність, потрібен суттєвий rewrite. |

### Step 7: Fix it yourself (REVISE only)

Для `REVISE` обов'язково дайте `<fixes>` з точними `find` / `replace`.

## Output Format

```text
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | ... |
| ... | ... | ... |

## Findings
[list findings]

## Verdict: PASS / REVISE / REJECT
[justification]

<fixes>
- find: "exact text"
  replace: "correct text"
</fixes>
```
