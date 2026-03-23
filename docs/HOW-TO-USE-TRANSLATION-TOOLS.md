# How to Use the Translation Tools

> Available tools for translating between Ukrainian, English, and Russian.
> Built for the learn-ukrainian curriculum but usable by any project (e.g., kube-dojo).

---

## Available Translation Directions

| Direction | Primary Source | Fallback | Best For |
|-----------|---------------|----------|----------|
| 🇺🇦→🇬🇧 Ukrainian→English | Wiktionary API | Горох → e2u reverse | Словник translations |
| 🇬🇧→🇺🇦 English→Ukrainian | e2u.org.ua | Горох | Translating docs/UI |
| 🇷🇺→🇺🇦 Russian→Ukrainian | r2u.org.ua | — | Russicism detection |

---

## Quick Start

```python
import sys
sys.path.insert(0, "scripts")

from rag.source_query import (
    translate_uk_to_en,   # Unified Ukrainian → English
    e2u_translate,        # English → Ukrainian (331K entries)
    r2u_translate,        # Russian → Ukrainian (Russicism detection)
    goroh_translate,      # Ukrainian → English via Горох
    wiktionary_translate, # Ukrainian → English via Wiktionary
    e2u_reverse,          # Ukrainian → English via e2u reverse search
)
```

---

## Ukrainian → English

### Unified function (recommended)
Tries Wiktionary → Горох → e2u in order. Returns first successful translation.

```python
from rag.source_query import translate_uk_to_en

translate_uk_to_en("родина")   # → "family"
translate_uk_to_en("книга")    # → "book"
translate_uk_to_en("кафе")     # → "cafe"
translate_uk_to_en("наголос")  # → "emphasis"
```

### Individual sources

```python
# Wiktionary — cleanest, best for common words
from rag.source_query import wiktionary_translate
wiktionary_translate("родина")  # → "family"

# Горох — broadest Ukrainian coverage, also has stress + frequency
from rag.source_query import goroh_translate
goroh_translate("родина")  # → ["family", "household", "kin", ...]

# e2u reverse — broadest English coverage
from rag.source_query import e2u_reverse
e2u_reverse("кафе")  # → "cafe"
```

---

## English → Ukrainian

### General dictionary (331K entries)
```python
from rag.source_query import e2u_translate

results = e2u_translate("family")
# → [{"headword": "family", "translation": "сім'я, родина, ..."}]
```

### IT dictionary (for technical projects like kube-dojo)
```python
from rag.source_query import _get, _parse_dict_entries

# Use dicts=it for IT-specific translations
r = _get("https://e2u.org.ua/s", params={"w": "deployment", "dicts": "it"})
entries = _parse_dict_entries(r.text)
# → розгортання, розміщення, дислокація
```

### Tested Kubernetes terms (via e2u IT dictionary):
| English | Ukrainian |
|---------|-----------|
| container | контейнер |
| cluster | кластер |
| deployment | розгортання |
| node | вузол |
| namespace | простір імен |

### Available e2u dictionary filters:
- `dicts=all` — all dictionaries (default)
- `dicts=it` — IT terminology
- `dicts=sci` — scientific language
- `dicts=eu` — EU terminology
- `dicts=bus` — business vocabulary

---

## Russian → Ukrainian (Russicism Detection Only)

```python
from rag.source_query import r2u_translate

# Check if a word is a Russicism and find the proper Ukrainian equivalent
results = r2u_translate("кот")
# → [{"headword": "Кот", "translation": "кіт (р. кота́)..."}]

results = r2u_translate("хорошо")
# → [{"headword": "Хорошо́", "translation": "краще, ліпше..."}]
```

---

## Authority Hierarchy for Verification

When verifying Ukrainian text quality, check sources in this order:

1. **VESUM** (vesum.com.ua) — does this word/form exist? POS? Gender? (415K lemmas)
2. **Правопис 2019** (2019.pravopys.net) — is it spelled correctly?
3. **Горох** (goroh.pp.ua) — stress position, frequency, synonyms, translations
4. **Антоненко-Давидович** «Як ми говоримо» (ukrlib.com.ua) — is this natural Ukrainian or a calque?
5. **Грінченко** «Словарь» (hrinchenko.com) — etymology, original historical meaning

### Online fallbacks (if tools are unavailable):
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua: https://slovnyk.ua/ (stress marks, anti-surzhyk, 130K definitions)
- e2u: https://e2u.org.ua/ (English→Ukrainian, 331K entries)
- r2u: https://r2u.org.ua/ (Russian→Ukrainian)

---

## Anti-Russicism Guidelines for Translation

When translating from English (or any language) to Ukrainian:

1. **Never use Russian as intermediary.** English → Ukrainian directly. Not English → Russian → Ukrainian.
2. **Verify the Ukrainian translation is not a Russicism.** Use r2u to check if your Ukrainian word is actually the Russian form.
3. **Four separate checks:**
   - **Russianisms**: кот→кіт, хорошо→добре
   - **Surzhyk**: шо→що, чо→чому
   - **Calques**: приймати душ→брати душ
   - **Paronyms**: тактична≠тактовна
4. **For IT terms:** some Ukrainian IT translations are direct calques from Russian. Check goroh.pp.ua for the established Ukrainian term.
5. **Use VESUM to verify** every Ukrainian word exists in the morphological dictionary.

---

## API Endpoints (no authentication needed)

| Source | Endpoint | Params |
|--------|----------|--------|
| e2u | `GET https://e2u.org.ua/s` | `w={word}&dicts={all,it,sci,eu,bus}` |
| r2u | `GET https://r2u.org.ua/s` | `w={word}` |
| Горох | `GET https://goroh.pp.ua/Переклад/{word}` | URL-encode Ukrainian |
| Wiktionary | `GET https://en.wiktionary.org/w/api.php` | `action=parse&page={word}&format=json&prop=wikitext` |
| VESUM | Local SQLite `data/vesum.db` | `SELECT * FROM forms WHERE word_form = ?` |

---

## Data Files (local)

| Source | File | Entries | Format |
|--------|------|---------|--------|
| VESUM | `data/vesum.db` | 415K lemmas, ~6M forms | SQLite |
| Антоненко-Давидович | `data/antonenko-davydovych/chunks.jsonl` | 279 style entries | JSONL |
| Грінченко | `data/grinchenko/chunks.jsonl` | 67,275 dictionary entries | JSONL |

---

## Integration with learn-ukrainian ENRICH step

The `translate_uk_to_en()` function is used in `scripts/build/enrich.py` to automatically translate vocabulary words in the словник tab. The chain: plan vocabulary (has translations) → `translate_uk_to_en()` for additional prose words → fallback dictionary for common words.
