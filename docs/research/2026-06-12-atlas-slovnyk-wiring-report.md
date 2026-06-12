# Word Atlas Slovnyk Wiring Report — 2026-06-12

## Rendered Section Counts

Command:

```bash
printf 'synonym_pages=%s\n' "$(rg -l 'id=\"atlas-synonyms-title\"' starlight/dist/lexicon -g 'index.html' | wc -l | tr -d ' ')"; printf 'idiom_pages=%s\n' "$(rg -l 'id=\"atlas-idioms-title\"' starlight/dist/lexicon -g 'index.html' | wc -l | tr -d ' ')"; printf 'red_warning_pages=%s\n' "$(rg -l 'atlas-heritage-pill--russism' starlight/dist/lexicon -g 'index.html' | wc -l | tr -d ' ')"
```

CWD:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-slovnyk-wiring
```

Raw output:

```text
synonym_pages=71
idiom_pages=46
red_warning_pages=4
```

## Rendered Samples

Command:

```bash
.venv/bin/python - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

class TextDump(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,data):
        text=' '.join(data.split())
        if text:
            self.parts.append(text)

def page_text(path):
    parser=TextDump()
    parser.feed(path.read_text(encoding='utf-8'))
    return ' | '.join(parser.parts)

samples={
 'протиріччя':'starlight/dist/lexicon/протиріччя/index.html',
 'книга':'starlight/dist/lexicon/книга/index.html',
 'міроприємство':'starlight/dist/lexicon/міроприємство/index.html',
}
for lemma, rel in samples.items():
    text=page_text(Path(rel))
    print(f'=== {lemma} ===')
    for marker in ['Русизм','Синоніми','Фразеологізми','Українська норма','Стаття-заготовка']:
        idx=text.find(marker)
        if idx >= 0:
            print(text[idx:idx+520])
    print()
PY
```

CWD:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-slovnyk-wiring
```

Raw output:

```text
=== протиріччя ===
Русизм | Деколонізація | Походження та статус | Русизм | Ця форма має ознаки русизму. Для нормативної української використовуйте відповідник нижче. | Українська норма: | суперечність | сперечання | супротивність | противенство | ⚠ Калька. | У курсі | Модулі, де зустрічається слово | Це слово ще не введено у жодному курсовому модулі. | Слововживання | Синоніми | slovnyk.me: Словник синонімів української мови | суперечність | суперечливість | розбіжність | контроверза | противенство | незгідність | незлагодженість |
Синоніми | slovnyk.me: Словник синонімів української мови | суперечність | суперечливість | розбіжність | контроверза | противенство | незгідність | незлагодженість | неузгодженість | антагонізм | протистояння | непримиренна суперечність | Походження даних | slovnyk.me: Словник синонімів української мови | Версія маніфесту: 0.1 · остання генерація: 2026-06-11T22:59:05+00:00 | ← Повернутися до А-Я покажчика | Learn Ukrainian | Self-study is welcome here, but the best learning happens with trained native Ukrainian te
Українська норма: | суперечність | сперечання | супротивність | противенство | ⚠ Калька. | У курсі | Модулі, де зустрічається слово | Це слово ще не введено у жодному курсовому модулі. | Слововживання | Синоніми | slovnyk.me: Словник синонімів української мови | суперечність | суперечливість | розбіжність | контроверза | противенство | незгідність | незлагодженість | неузгодженість | антагонізм | протистояння | непримиренна суперечність | Походження даних | slovnyk.me: Словник синонімів української мови | Версія ма

=== книга ===
Синоніми: | книжка | Слововживання | Синоніми | slovnyk.me: Словник синонімів української мови + Словник синонімів Караванського | книжка | книжина | фоліянт | біблія | стародрук | альбом | том | Сталі вирази | Фразеологізми | за сімома печатками (печатями) | Недоступний для розуміння; незрозумілий, прихований. Виробничий процес “свого” цеху, а відтак і цілої фабрики .. не був для неї якоюсь новиною, ні загадкою за сімома печатками (В. Козаченко); — Ці хлопці,— зауважила вона в бік юнаків, — для мене за сімома печа
Фразеологізми | за сімома печатками (печатями) | Недоступний для розуміння; незрозумілий, прихований. Виробничий процес “свого” цеху, а відтак і цілої фабрики .. не був для неї якоюсь новиною, ні загадкою за сімома печатками (В. Козаченко); — Ці хлопці,— зауважила вона в бік юнаків, — для мене за сімома печатями , емоції приглушені, загнані вглиб (О. Гончар). (мов) книга за сімома печатями. — Підходила Артемова черга, а він поки що не вирішив, який (напій) вибрати. Всі вони були для нього мов книга за сімома печатя

=== міроприємство ===
Русизм | Деколонізація | Походження та статус | Русизм | Ця форма має ознаки русизму. Для нормативної української використовуйте відповідник нижче. | Українська норма: | захід | заходи | ⚠ Калька. | У курсі | Модулі, де зустрічається слово | Це слово ще не введено у жодному курсовому модулі. | ← Повернутися до А-Я покажчика | Learn Ukrainian | Self-study is welcome here, but the best learning happens with trained native Ukrainian teachers. These materials support practice; they do not replace devoted teachers. | Pe
Українська норма: | захід | заходи | ⚠ Калька. | У курсі | Модулі, де зустрічається слово | Це слово ще не введено у жодному курсовому модулі. | ← Повернутися до А-Я покажчика | Learn Ukrainian | Self-study is welcome here, but the best learning happens with trained native Ukrainian teachers. These materials support practice; they do not replace devoted teachers. | Pedagogical inspiration comes in part from Ukrainian Lessons and the public teaching work of Anna Ohoiko, with gratitude for inspiration and help. Cours
```

## Validation

Command:

```bash
cd starlight && npm ci && npm run build
```

Result: passed; final build reported `296 page(s) built`.

Command:

```bash
env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/python -m pytest tests/ -k 'lexicon or manifest or atlas' -q
```

Result: passed; `122 passed, 8304 deselected, 1 xfailed, 3 warnings`.

Note: the unmodified command failed only in this Codex shell because the ambient
`AGENT_NO_TELEMETRY_FOOTER=1` disables the opt-in telemetry asserted by
`tests/test_monitor_api_telemetry.py`.
