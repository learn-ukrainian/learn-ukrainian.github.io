"""audit_assistant_quality.py - Independent verification and 50-record audit report generator.

Performs independent audit with strict adversarial criteria and exports a human-readable
markdown report (SAMPLE_INSPECTION_50.md) containing 50 full inspected records
(eval and SFT) covering:
1. Citation form (nominative noun head, no bare adjectives/prepositions/verbs, no proper nouns).
2. Deictic opener & ungrounded anaphora absence (including participles, external refs, labelled objects).
3. Definitional alignment of defined subject (verifying concept is the defined subject).
4. Absence of space-split broken OCR words, hyphen-loss, and column fusion.
5. Scientific terminology authenticity (>= 2 terms, VESUM attested common nouns, no stopwords/fillers/adjectives).
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RELEASE_DIR = PROJECT_ROOT / "data" / "projects" / "open_model_data" / "release" / "uldr_v06_general_assistant"


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = PROJECT_ROOT / rel_path
    if local_p.exists() and (local_p.is_dir() or local_p.stat().st_size > 0):
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and (main_p.is_dir() or main_p.stat().st_size > 0):
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")

# Independent stopword terms specifically for assistant quality audit
AUDIT_STOPWORD_TERMS = {
    "клас", "класу", "класи", "класів", "класом", "математика", "математики", "математику",
    "підручник", "підручника", "підручнику", "розділ", "розділу", "розділі",
    "тема", "теми", "тему", "темі", "сторінка", "сторінки", "сторінку",
    "учень", "учня", "учні", "учнів", "учням", "учениця", "учениці",
    "вчитель", "вчителя", "вчителька", "вчительки",
    "завдання", "завдань", "вправа", "вправи", "вправу",
    "україна", "україни", "українська", "української", "українською",
    "слово", "слова", "словом", "мова", "мови", "мову", "мовою",
    "предмет", "предмета", "предмету", "робота", "роботи", "роботу", "роботі", "роботою",
    "параграф", "параграфа", "частина", "частини", "частину",
    "питання", "відповідь", "відповіді", "відповіддю",
    "школа", "школи", "школу", "курс", "курсу", "курсі",
    "урок", "уроку", "уроці", "поняття", "приклад", "прикладу", "значення",
    "автор", "автори", "авторів", "підсумок", "підсумки", "правило", "правила",
    "число", "числа", "чисел", "числу", "числом", "член", "члена", "членів",
    "треба", "можна", "слід", "бути", "мати", "стати", "дати", "буде", "було",
    "випадок", "випадку", "випадки", "вигляд", "вигляду", "спосіб", "способу", "способом",
    "відміна", "відміну", "умова", "умови", "умовою", "початок", "початку",
    "кінець", "кінця", "кінцем", "допомога", "допомогою", "основа", "основи", "основою",
    "зв'язок", "зв'язку", "наслідок", "наслідку", "порядок", "порядку",
    "запис", "запису", "записом", "форма", "форми", "формою", "тип", "типу", "типом",
    "вид", "виду", "видом", "група", "групи", "групою", "рівень", "рівня", "рівнем",
    "текст", "тексту", "рядок", "рядка", "знак", "знака", "знаком", "знаки",
    "ознака", "ознаки", "ознакою",
    "справа", "справи", "справу", "справі", "справою",
    "створення", "створенні", "створенням",
    "художник", "художника", "художники", "художників",
    "людина", "людини", "людині", "людиною", "люди", "людей", "людям", "людьми",
    "час", "часу", "часом", "часі",
    "використання", "використанні", "використанням",
    "сукупність", "сукупності", "сукупністю",
    "можливість", "можливості", "можливістю",
    "розгляд", "розгляду", "діяльність",
    "процес", "процесу", "процеси", "процесів",
    "явище", "явища", "явищ", "явищем",
    "складова", "властивість", "властивості", "властивостей",
    "особливість", "факт", "інформація", "дані", "потреба", "мета", "ціль",
    "напрям", "напрямок", "сторона", "точка", "місце", "край", "стан", "роль",
    "сутність", "середина", "межа", "розмір", "кількість", "якість",
    "величина", "величини", "величину", "величиною",
    "безліч", "безлічі", "безліччю", "кількості",
    "метод", "методи", "методів", "метода", "двері", "дверей", "дверима",
    "досягнення", "історія", "людство",
    "життя", "світ", "світу", "рік", "року", "роки", "років",
    "день", "дня", "дні", "днів", "протилежне", "живе", "живий", "живим", "актиній",
    "житель", "жителі", "жителя", "жителів", "прихильник", "прихильники", "прихильника",
    "богиня", "богині", "богинею", "божество", "божества", "божеств", "бог", "бога", "боги", "богів", "міф", "міфи", "міфів", "міфологія",
    "давньоримський", "давньоримська", "давньоримське", "давньоримські",
    "основний", "основна", "основне", "основні", "основного", "основній", "основних", "основним",
    "численний", "численна", "численне", "численні", "численних", "численними", "численним",
    "непростий", "непроста", "непросте", "непрості", "непростих", "непростим",
    "простий", "проста", "просте", "прості", "простих", "простим",
    "складний", "складна", "складне", "складні", "складних", "складним",
    "різний", "різна", "різне", "різні", "різних", "різними", "різним",
    "новий", "нова", "нове", "нові", "нових", "новим",
    "старий", "стара", "старе", "старі", "старих",
    "важливий", "важлива", "важливе", "важливі", "важливих", "важливим",
    "головний", "головна", "головне", "головні", "головних", "головним",
    "великий", "велика", "велике", "великі", "великих", "великим", "великою",
    "малий", "мала", "мале", "малі", "малих", "малим", "малою",
    "середній", "середня", "середнє", "середні", "середніх",
    "високий", "висока", "високе", "високі", "високих",
    "низький", "низька", "низьке", "низькі", "низьких",
    "певний", "певна", "певне", "певні", "певного", "певній", "певних", "певним",
    "деякий", "деяка", "деяке", "деякі", "деяких",
    "окремий", "окрема", "окреме", "окремі", "окремих", "окремим",
    "загальний", "загальна", "загальне", "загальні", "загальних", "загальним",
    "кожен", "кожна", "кожне", "кожні", "кожного", "кожній", "кожним",
    "всякий", "інший", "інша", "інше", "інші", "інших", "іншим",
    "подібний", "подібна", "подібне", "подібні", "подібних",
    "однаковий", "однакова", "однакове", "однакові", "однакових",
    "перший", "другий", "третій", "четвертий", "п'ятий",
    "наступний", "попередній", "подальший",
    "цілий", "повний", "правильний", "вільний", "довгий", "короткий", "прямий",
    "відомий", "відома", "відоме", "відомі", "відомих", "відомим", "невідомий",
    "можливий", "неможливий", "необхідний", "необхідна", "необхідне", "необхідні", "необхідних",
    "єдиний", "сучасний", "давній", "минулий", "майбутній",
    "шкільний", "учнівський", "домашній", "класний", "навчальний",
    "кращий", "гірший", "найкращий", "найбільший", "найменший",
    "фізичний", "фізична", "фізичне", "фізичні", "фізичних", "фізичним",
    "питомий", "питома", "питоме", "питомі", "питомих",
    "майбутнє", "вика", "середа", "раз", "повня", "красий", "точок",
}


def audit_citation_form(concept: str, cur: sqlite3.Cursor) -> bool:
    """Audit citation form: nominative noun head, no bare adjectives, no proper nouns, no superlatives."""
    c = concept.strip()
    if not c or len(c) < 3:
        return False
    if not c[0].isupper():
        return False

    # Reject superlatives, evaluatives, ordinals, conditionals, conjunctions at start
    if re.match(
        r"^(?:най|якнай|щонай)\w+|"
        r"^(?:найкращ\w*|найголовніш\w*|найбільш\w*|найважливіш\w*|найскладніш\w*|потужн\w*|ефективн\w*|унікальн\w*|чудов\w*|прекрасн\w*|висок\w*\s+цінност\w*|велик\w*\s+листк\w*)\b|"
        r"^(?:перш\w*|друг\w*|трет\w*|четверт\w*|п['ʼ’]?ят\w*|шост\w*|сьом\w*|восьм\w*|дев['ʼ’]?ят\w*|десят\w*|наступн\w*|останн\w*)\b|"
        r"^(?:якщо|коли|та|і|й|або|чи)\b",
        c,
        re.IGNORECASE,
    ):
        return False

    if re.search(r"\b(?:очевидн\w*|зрозуміл\w*|незрозуміл\w*|безперечн\w*|помітн\w*)\b", c, re.IGNORECASE):
        return False

    if c.lower() in AUDIT_STOPWORD_TERMS:
        return False

    words = [w.strip(".,;:?!'\"«»„“—–()") for w in c.split() if w.strip(".,;:?!'\"«»„“—–()")]
    if not words or len(words) > 5:
        return False

    preps = {"від", "для", "до", "з", "із", "зі", "на", "по", "про", "за", "під", "над", "при", "без"}
    if len(words) >= 3 and any(w.lower() in preps for w in words[1:-1]):
        cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[-1].lower(),))
        if any(r[0] == "adj" for r in cur.fetchall()):
            return False

    # Check proper nouns: if single-word has a proper noun reading in capitalized form and no common nominative noun reading
    if len(words) == 1:
        w = words[0]
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (w.capitalize(),))
        cap_rows = cur.fetchall()
        has_prop = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in cap_rows)
        if has_prop:
            cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (w.lower(),))
            low_rows = cur.fetchall()
            has_nom_common_noun = any(
                r[1] == "noun"
                and ("v_naz" in r[0] or "naz" in r[0])
                and not any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr"))
                for r in low_rows
            )
            if not has_nom_common_noun:
                return False

    if len(words) == 1:
        cur.execute("SELECT pos FROM forms_all WHERE word_form = ?", (words[0].lower(),))
        poses = {r[0] for r in cur.fetchall()}
        if "adj" in poses and "noun" not in poses:
            return False
        if "adj" in poses and words[0].lower().endswith(("ий", "ій", "е", "є", "і")):
            return False

    # Verify presence of nominative noun head
    has_nom_noun = False
    for w in words:
        cur.execute("SELECT tags, pos, lemma FROM forms_all WHERE word_form IN (?, ?)", (w.lower(), w))
        rows = cur.fetchall()
        for r in rows:
            if (
                r[1] == "noun"
                and ("v_naz" in r[0] or "naz" in r[0] or r[2].lower() == w.lower())
                and not any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr"))
            ):
                has_nom_noun = True
                break
        if has_nom_noun:
            break

    return has_nom_noun


def audit_anaphora_and_starters(snippet: str) -> bool:
    """Audit deictic openers, ungrounded anaphora, and external textbook references."""
    s = snippet.strip()
    if not s or not s[0].isupper():
        return False

    # Reject deictic openers or continuation words
    if re.match(
        r"^(?:Це|Цей|Ця|Ці|Цих|Цього|Цьому|Цим|Таким|Такий|Така|Таке|Такі|"
        r"Він|Вона|Воно|Вони|Його|Її|Їх|Тому|Отже|Також|Крім того|"
        r"Подібно до|Завдяки|Внаслідок|Згідно з|Розглянутий|Зазначений|Вказаний|"
        r"Наведений|Описаний|Так називають|Саме так називається|Для цього|При цьому|У цьому|Втім|Однак|Проте)\b",
        s,
    ):
        return False

    # Mid-sentence anaphora
    if re.search(r"\b(?:так|саме\s+так)\s+(?:називають|називається|називали|назвали)\b", s, re.IGNORECASE):
        return False

    # Demonstrative constructs
    if re.search(r"\bтаке\s+[а-яіїєґ]+", s, re.IGNORECASE):
        return False

    # Textbook structural references (figures, tables, exercises)
    return not bool(
        re.search(
            r"\b(?:мал\.|рис\.|табл\.)\b|"
            r"\b(?:мал\.|малюнк\w*|рис\.|рисунк\w*|табл\.|таблиц\w*|параграф\w*|вправ\w*|рубрик\w*)\s*(?:№\s*)?\d+",
            s,
            re.IGNORECASE,
        )
    )


def audit_ocr_cleanliness(snippet: str, cur: sqlite3.Cursor) -> bool:
    """Audit OCR cleanliness: no space-split words, no missing hyphens, no spliced sentences."""
    s = snippet.strip()

    # Indefinite pronouns and adverbs missing hyphens
    if re.search(
        r"\b(?:будь|хтозна|казна)(?:який|яка|яке|які|якого|якій|якому|яким|яких|якою|хто|що|де|коли|куди|кого|кому|ким|чого|чому|чим|як)\b",
        s,
        re.IGNORECASE,
    ):
        return False

    # Suffixes without hyphen: -небудь, -но, -то
    if re.search(
        r"\b(?:кого|кому|ким|чого|чому|чим|хто|що|де|коли|куди|як)небудь\b",
        s,
        re.IGNORECASE,
    ):
        return False
    if re.search(r"\b(?:тількино|якто)\b", s, re.IGNORECASE):
        return False

    # Spliced sentence / column fusion OCR:
    # Lowercase word followed by capitalized word: [а-яіїєґ]{2,}\s+[А-ЯІЇЄҐ][а-яіїєґ]{2,}
    for m in re.finditer(r"\b([а-яіїєґ]{2,})\s+([А-ЯІЇЄҐ][а-яіїєґ]{2,})\b", s):
        w2 = m.group(2)
        cur.execute("SELECT tags FROM forms_all WHERE word_form = ?", (w2,))
        rows = cur.fetchall()
        is_proper = any(any(p in r[0] for p in (":prop", ":geo", ":fname", ":lname", ":patr")) for r in rows)
        if not is_proper:
            return False

    return True


def audit_definitional_alignment(concept: str, snippet: str, cur: sqlite3.Cursor) -> bool:
    """Audit definitional alignment: defined subject matches concept, no evaluatives or metaphors."""
    s = snippet.strip()
    c = concept.strip()
    if len(s) < 25 or len(s) > 400:
        return False
    if not (s.endswith(".") or s.endswith("!") or s.endswith("?")):
        return False

    # Reject evaluatives and superlatives in definition
    if re.search(
        r"(?:один|одна|одне|одні)\s+(?:з|із)\s+най\w+|"
        r"[—–-]\s*(?:це\s+)?якщо\b|"
        r"[—–-]\s*(?:це\s+)?така\s+сама\s+\w+,\s+як\b|"
        r"[—–-]\s*(?:це\s+)?(?:ефективн\w*|унікальн\w*|чудов\w*|важлив\w*|цікав\w*|зручн\w*|найкращ\w*|найважливіш\w*|головн\w*)\b",
        s,
        re.IGNORECASE,
    ):
        return False

    # Definitional marker check
    has_def_marker = bool(
        re.search(r"[—–-]\s*(?:це\s+)?", s)
        or re.search(r"\b(?:називають|називається|називали|назвали|являє собою|являють собою|визначається як)\b", s, re.IGNORECASE)
        or re.search(r"\bє\s+(?:одним|однією|основним|важливим|системою|процесом|явищем|сукупністю|формою|частиною|результатом|величиною|правилом|числом|добутком|відношенням|наукою)\b", s, re.IGNORECASE)
        or re.search(r"\bє\s+[а-яіїєґ']+(?:ою|им|ем|ом|єю|ією)\b", s, re.IGNORECASE)
    )
    if not has_def_marker:
        return False

    # Concept grounding check
    s_lower = s.lower()
    c_lower = c.lower()
    if c_lower in s_lower:
        return True
    c_words = [w.strip(".,;:?!'\"«»„“—–()") for w in c_lower.split() if w.strip(".,;:?!'\"«»„“—–()")]
    matched = sum(1 for cw in c_words if cw in s_lower or (len(cw) > 4 and cw[:-2] in s_lower))
    return matched >= max(1, len(c_words) // 2)


def audit_scientific_terms(terms: list[str], snippet: str, concept: str, cur: sqlite3.Cursor) -> bool:
    """Audit scientific terminology: >= 2 terms, single-word common nouns, VESUM attested, no adjectives."""
    if len(terms) < 2:
        return False

    s_lower = snippet.lower()
    for t in terms:
        t_clean = t.strip().lower()
        if len(t_clean) < 3 or " " in t_clean:
            return False
        if t_clean in AUDIT_STOPWORD_TERMS or t_clean.endswith(("е", "є")):
            return False

        # Query VESUM
        cur.execute("SELECT tags, pos FROM forms_all WHERE word_form = ?", (t_clean,))
        rows = cur.fetchall()
        if not rows:
            return False

        has_noun = False
        has_adj = False
        is_prop = True
        for r in rows:
            tag, pos = r[0], r[1]
            if pos == "adj" or ":ns" in tag:
                has_adj = True
            if pos == "noun" and not any(pt in tag for pt in (":prop", ":fname", ":lname", ":geo", ":patr")):
                is_prop = False
                if not has_adj and ":ns" not in tag:
                    has_noun = True

        if has_adj or is_prop or not has_noun:
            return False

        # Term or lemma stem must be present in snippet (verbatim, stem, or via VESUM word_form -> lemma)
        in_snip = t_clean in s_lower or (len(t_clean) > 4 and t_clean[:-2] in s_lower)
        if not in_snip:
            snip_words = [w.strip(".,;:?!'\"«»„“—–()") for w in s_lower.split() if w.strip(".,;:?!'\"«»„“—–()")]
            for sw in snip_words:
                cur.execute("SELECT lemma FROM forms_all WHERE word_form = ?", (sw,))
                if any(r[0].lower() == t_clean for r in cur.fetchall()):
                    in_snip = True
                    break
        if not in_snip:
            return False

    return True


def audit_records() -> tuple[list[dict], bool]:
    rng = random.Random(42)

    conn = sqlite3.connect(f"file:{DEFAULT_VESUM_DB}?mode=ro", uri=True)
    cur = conn.cursor()

    eval_shards = sorted(RELEASE_DIR.glob("eval/eval_shard_*.jsonl"))
    sft_shards = sorted(RELEASE_DIR.glob("sft/sft_shard_*.jsonl"))

    sampled_records: list[dict] = []
    seen_eval_concepts: set[str] = set()

    # 1. Sample 25 distinct records across eval shards
    per_shard_eval = max(1, 25 // len(eval_shards)) if eval_shards else 0
    for shard in eval_shards:
        records_in_shard = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    records_in_shard.append(d)
        rng.shuffle(records_in_shard)
        shard_sampled = 0
        for d in records_in_shard:
            conc = (d.get("concept") or "").strip()
            if conc and conc not in seen_eval_concepts:
                seen_eval_concepts.add(conc)
                sampled_records.append(d)
                shard_sampled += 1
                if shard_sampled >= per_shard_eval:
                    break
        if len(sampled_records) >= 25:
            break

    # 2. Sample 25 distinct records across all SFT shards using seeded PRNG
    seen_sft_concepts: set[str] = set()
    sft_indices = list(range(len(sft_shards)))
    rng.shuffle(sft_indices)
    for s_idx in sft_indices:
        if len(sampled_records) >= 50:
            break
        shard = sft_shards[s_idx]
        records_in_shard = []
        with shard.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    d = json.loads(line)
                    d["_origin"] = f"{shard.name}:line_{idx + 1}"
                    records_in_shard.append(d)
        rng.shuffle(records_in_shard)
        for d in records_in_shard:
            conc = (d.get("concept") or d.get("target_concept") or "").strip()
            if conc and conc not in seen_sft_concepts:
                seen_sft_concepts.add(conc)
                sampled_records.append(d)
                break

    all_passed = True
    audit_results: list[dict] = []

    for rec in sampled_records:
        concept = (rec.get("concept") or rec.get("target_concept") or "").strip()
        terms = rec.get("scientific_terminology", [])
        steps = rec.get("reference_reasoning") or rec.get("reasoning_steps") or []
        if len(steps) > 1:
            body = steps[1]
            parts = body.split(":", 2)
            raw_snip = parts[2].strip() if len(parts) >= 3 else parts[-1].strip()
        else:
            sol = rec.get("reference_solution") or rec.get("final_response") or ""
            m = re.search(r"«([^»]{20,})»", sol)
            raw_snip = m.group(1) if m else sol
        raw_snip = raw_snip.strip("«» \t\n")

        # Run independent adversarial checks
        citation_ok = audit_citation_form(concept, cur)
        anaphora_clean = audit_anaphora_and_starters(raw_snip)
        ocr_clean = audit_ocr_cleanliness(raw_snip, cur)
        def_aligned = audit_definitional_alignment(concept, raw_snip, cur)
        terms_ok = audit_scientific_terms(terms, raw_snip, concept, cur)

        rec_ok = citation_ok and anaphora_clean and ocr_clean and def_aligned and terms_ok
        if not rec_ok:
            all_passed = False

        audit_results.append({
            "origin": rec.get("_origin", ""),
            "concept": concept,
            "subject": rec.get("subject", ""),
            "grade": rec.get("grade", ""),
            "terms": terms,
            "snippet": raw_snip,
            "citation_ok": citation_ok,
            "anaphora_clean": anaphora_clean,
            "ocr_clean": ocr_clean,
            "def_aligned": def_aligned,
            "terms_ok": terms_ok,
            "verdict": "PASS" if rec_ok else "FAIL",
        })

    conn.close()
    return audit_results, all_passed


def main() -> None:
    results, ok = audit_records()

    out_md = [
        "# Sample Inspection of 50 Mined Records (Phase 6.1)\n",
        f"**Audit Result:** {'ALL 50 RECORDS PASSED' if ok else 'FAILURES DETECTED'}\n",
        f"**Inspected Records:** {len(results)}\n",
        "| # | Origin | Concept | Subject | Grade | Terms | Citation | Anaphora-Free | OCR-Clean | Def-Aligned | Terms Valid | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for i, r in enumerate(results, 1):
        terms_str = ", ".join(r["terms"][:4])
        out_md.append(
            f"| {i} | `{r['origin']}` | **{r['concept']}** | {r['subject']} | {r['grade']} | {terms_str} | "
            f"{'✅' if r['citation_ok'] else '❌'} | {'✅' if r['anaphora_clean'] else '❌'} | "
            f"{'✅' if r['ocr_clean'] else '❌'} | {'✅' if r['def_aligned'] else '❌'} | "
            f"{'✅' if r['terms_ok'] else '❌'} | **{r['verdict']}** |"
        )

    out_md.append("\n## Detailed Record Inspection (Full Text)\n")
    for i, r in enumerate(results, 1):
        out_md.append(f"### Record {i}: {r['concept']} ({r['origin']})")
        out_md.append(f"- **Subject / Grade:** {r['subject']} (Grade {r['grade']})")
        out_md.append(f"- **Concept:** `{r['concept']}` (Citation form: {'✅' if r['citation_ok'] else '❌'})")
        out_md.append(f"- **Scientific Terminology:** `{r['terms']}` (Terms >= 2 & non-generic: {'✅' if r['terms_ok'] else '❌'})")
        out_md.append(f"- **Textbook Snippet:** «{r['snippet']}» (Anaphora-free: {'✅' if r['anaphora_clean'] else '❌'}, OCR-Clean: {'✅' if r['ocr_clean'] else '❌'}, Def-Aligned: {'✅' if r['def_aligned'] else '❌'})")
        out_md.append(f"- **Overall Record Verdict:** **{r['verdict']}**\n")

    report_path = RELEASE_DIR / "SAMPLE_INSPECTION_50.md"
    report_path.write_text("\n".join(out_md) + "\n", encoding="utf-8")
    print(f"Wrote inspection report to {report_path}")
    print(f"Inspected {len(results)} records. Verdict: {'PASS' if ok else 'FAIL'}")

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
