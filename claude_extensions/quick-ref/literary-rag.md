# Literary RAG Quick Reference

## Search Tool

```
mcp__rag__search_text(query="your query in Ukrainian", subject="literary")
```

Or with filters:
```python
# Python (pipeline scripts)
from rag.query import search_literary
results = search_literary("Мазепа", limit=5, genre="chronicle")
```

## Available Filters

- `genre`: chronicle, poetry, fable, interlude, religious, grammar, lexicon, legal, manual, letter, scholarly, anthology, polemic, philosophy, hagiography, rhetoric, travelogue, diary, memoir, biography, encyclopedia, reference, ethnography
- `language_period`: old_east_slavic, middle_ukrainian, modern
- `work`: exact work title (e.g., "Літопис Величка")
- `author`: author name
- `year`: publication/composition year

## What's Indexed (~78,100 chunks, 134 files)

### Primary Sources (OES/RUTH tracks)
- **Chronicles**: PVL (3 editions, 1,824 ch.), Kyiv chronicle (1,083), GVL (1,270), Самовидець (111), Грабянка (214), Величко (1,676), Іст. Русів (798), Чернігівський (64), Синопсис (557), Литовські літописи (1,359), Софонович (647)
- **Literature**: Слово о полку (11 + 325 translations), Поезія XVI-XVII (286), Інтермедії (172), Байки (257), Величковський (164), Зіновіїв (403), Сковорода (1,352), Прокопович (1,602), Довгалевський (316), Драматургія XIX (208)
- **Anthologies**: Укр. літ. XI-XIII / XIV-XVI / XVII / XVIII ст. (1,133), Білецький хрестоматія (359), Гуманісти Відродження (498)
- **Religious**: Патерик Києво-Печерський (361), Борис та Гліб (64)
- **Grammars/Lexicons**: Смотрицький (116), Зизаній (20), Беринда (44), Федорович (12), Ужевич (106), Вербицький (8), old glossaries (77), Правопис 2015 (297)
- **Legal/Admin**: Грамоти XIV-XVI ст. (337), Руська Правда (364), Статут ВКЛ 1566 (270), Лікарські порадники (70)
- **Travelogues/Diaries**: Боплан (170), Шевальє (165), Крман (75), Ханенко (810), Де ля Фліз (57)
- **Polemic**: Суспільно-політична думка XVI-XVII (821)

### Scholarly Reference (C1-HIST/LIT tracks)
- **Грушевський — Історія України-Руси** (10 vol, 9,763 ch.) — covers Kyivan Rus through Hetmanate
- **Грушевський — Іст. укр. літератури** (6 vol, 1,341 ch.) — literary history
- **Чижевський** (4 works, 2,284 ch.) — Іст. літ., Бароко, Філософія, Сковорода
- **Грабович — До історії укр. літ.** (750 ch.)
- **Оглоблін — Гетьман Мазепа** (810 ch.)
- **Войтович — Князівські династії** (1,242 ch.)
- **Німчук — Мовознавство XIV-XVII ст.** (368 ch.)
- **Укр. мова Енциклопедія** (239 ch.)
- **Енциклопедія українознавства** (3,242 ch.)
- **Укр. літературна енциклопедія** (5,555 ch.)

### History & Culture (waves 6-7, ~27,400 ch.)
- Дворнік, Крип'якевич, Голобуцький, Литвинов, Когут, Попович, Іст. укр. культури (2 vol), Наливайко, Антонович, Дзюба, Драгоманов, Костомаров, and 15+ more

### Linguistics (wave 9, ~1,990 ch.)
- Шевельов — Іст. фонологія, Огієнко — Іст. літ. мови, Русанівський, Півторак, Східнослов. граматики

### Shevchenko (wave 10, ~7,600 ch.)
- Повне зібрання творів т.1, Літопис життя, Словник, Спогади, Епістолярій, Документи, Біографія, Кониський хроніка

## Full Documentation
See `docs/RAG-LITERARY-CONTENTS.md` for complete inventory with track mapping.
