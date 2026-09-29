"""Reproduce the unpublished #9160 meaning-containment evaluation shards.

The pinned release and local source snapshots are inputs. Nothing here uploads,
publishes, or changes the release pointer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.audit import generate_practice_deck as deck
from scripts.practice import meaning_containment
from scripts.practice.meaning_containment import (
    REVIEWED_WRONG_LEMMAS,
    candidate_balla_heads,
    english,
    load_balla_definitions,
    load_dmklinger_rows,
    load_sum11_definitions,
    meaning_problem,
)

LEVELS = ("A1", "A2", "B1", "B2", "C1")
PACKAGE_SHA256 = "d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19"
ATLAS_SHA256 = "fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca"
SOURCES_SHA256 = "7868ce16f3cc8280676f08f436b94563ba20e3e7909ad236f06c2bdce19baa7b"
MEANING_MODES = frozenset({"flashcards", "matching", "choice", "synonym"})

# Literal failed displays copied from the four independent evaluations and the
# brief critic. These are regression evidence, not a lemma blacklist: the
# admission rule above must still reject the same failure class on unseen rows.
HISTORICAL_BAD_DISPLAYS = {
    "словник": "associative array", "успішно": "fortunately", "одягатися": "to wear sth",
    "щеплення": "grafting", "рік": "a Julian year", "перший": "numeral first",
    "здається": "to surrender", "білі": "leucorrhoea", "сім'я": "any small seed-like fruit",
    "пора": "pore", "рада": "board", "мороз": "a surname", "вірус": "computer virus",
    "мова": "computer language", "ціль": "point", "дуже": "way too", "Добре": "very much",
    "екскурсія": "hike", "дно": "bed", "ураження": "impression",
    "електронний": "electron", "музичний": "music", "тікати": "to tick",
    "слізний": "tear", "впливати": "to swim in", "якнайкраще": "intensified form of",
    "навколішки": "get up", "інтелектуальний": "or performed by",
    "практикувати": "put into practice", "зіграти": "compositional style",
    "покуття": "Pokuttia", "лікарняний": "Relating to a hospital",
    "наді": "used before awkward consonant clusters and chiefly before мно́ю",
    "начальниця": "female equivalent of нача́льник",
    "малесенький": "endearing form of мале́нький",
    "незнайомка": "female equivalent of незнайо́мець",
    "однокласниця": "female equivalent of однокла́сник", "ківі": "kiwi 2",
}

# Correct heads and source-gap cases named in rounds 1-4. Their exact
# containment expectation is conditional: an independently bound source row
# permits retention; otherwise the meaning and dependent modes are withheld.
HISTORICAL_COVERAGE_LEMMAS = frozenset("""
прем'єра як-от конфлікт буквально ніж баланс проведено скажімо якому якій рахунок уникнути
приборкати спростувати сила безсоння виконуватися під'їзд ясна катастрофа брехня
доопрацювати помаранчевий переїжджати водночас стрічка лиман пародія почин нота
вимушено альтруїзм шпарко навмисно підходити вгорі зосереджуватися замітка складений
придуманий двигун суб'єктивність співучий спрей тендітний отримувач материна
мотиваційний бирка бризнути потемнілий респіраторний ендорфін мотиватор допливати
шиплячий суфіксально-префіксальний однократність перенавантажити пратися увесь
задовольнятися група про хлопець перебіг район теперішній аудиторія виснаження
зважити максимальний напруження погоджено продається робите тату
ветеринарний аромат боягуз дощовитий красота тяжкий щодуху відбивати штат слава
варт виїхати возити дотла кульмінація реквізит статура словотворення незмінність
складова прочитавши клітка ґрунт прокачувати вірмо особистість переїду
задньоязиковий перевстановити самодіагностика старшокурсниця найвигідніший
допустовість кровити кунжут очікувати снідати збільшити довкілля звати сірий
світ кредит цукерка виведення передано цілісність ремонт перехрестя вирішити
активно використовувати пам'ятка хвора складати скласти службовий будується дрова
бійка досягти краєвид перед змішати деякий спекотний збіг акція веселити горе
оригінально відступати влаштувати проігнорувати зазначати згоріти відбиватися
нестримний підробити вилітати відрекомендуватися квітучий завантажено
кардіограма задумати освітлити протестувальник пекарка біліти проплисти
підписник авітаміноз хіазм літота мікрофлора батьки баскетбол аптекар вже
вечеря вагітний вибачати брама будь-хто вдало випробування запустити музичний
нагадати ухвалення люд скасовувати швидше забронювати добродію показання
садка забудовник враховано вегетаріанський важкий давнина звикнути небезпека
спекотно мелодія усмішка жага карабін сімейство управа славно надягати
будь-куди дослідник кобзар мисткиня перейду перспективний зимний курдський
кобіта ріелтор пробігати каліграфія переформулювання консервований пекельно
повішати неначеб проведення звіт будівництво хід залом приємно місцевий товариш
будинок телефон прізвище дорослий
журнал контроль внесок змінюється тривалий помалу затверджений сором'язливий
торба студентство мати замок горіх живий круто
""".split()) | {"споріднені слова", "складати/скласти іспит"}  # noqa: SIM905


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"source snapshot mismatch: {path.name}: {actual}")


def evaluate(package: Path, atlas_db: Path, sources_db: Path, output: Path) -> dict:
    require_hash(package, PACKAGE_SHA256)
    require_hash(atlas_db, ATLAS_SHA256)
    require_hash(sources_db, SOURCES_SHA256)
    archive = json.loads(gzip.decompress(package.read_bytes()))
    if archive.get("deckVersion") != "atlas-practice-v1-f1e1cf95470ce319":
        raise ValueError("wrong frozen deck version")
    files = {item["path"]: item["content"].encode("utf-8") for item in archive["files"]}
    if len(files) != 55:
        raise ValueError("frozen release must contain 55 unique shards")
    entries = deck.read_atlas_db(atlas_db)
    by_id = {}
    for entry in entries:
        by_id.setdefault(deck._stable_lemma_id(entry), entry)
    published_ids = {
        row["lemmaId"] for level in LEVELS
        for row in json.loads(files[f"practice-lexemes.{level}.json"])["lexemes"]
    }
    balla = load_balla_definitions(
        candidate_balla_heads([by_id[lemma_id] for lemma_id in published_ids if lemma_id in by_id]),
        sources_db,
    )
    dmklinger_rows = load_dmklinger_rows(
        {str(by_id[lemma_id]["lemma"]) for lemma_id in published_ids if lemma_id in by_id}, sources_db
    )

    output.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}
    changed: dict[str, bytes] = {}
    code_hashes = {"generator": sha256(Path(deck.__file__)),
                   "containment": sha256(Path(meaning_containment.__file__)),
                   "reproducer": sha256(Path(__file__))}
    verifier = deck.JsonVesumVerifier({})
    admissions: list[dict] = []
    partitions: Counter[str] = Counter()
    partition_levels: dict[str, Counter[str]] = defaultdict(Counter)
    published_lemmas: set[str] = set()
    for level in LEVELS:
        lex_name = f"practice-lexemes.{level}.json"
        idx_name = f"practice-index.{level}.json"
        lex_payload = json.loads(files[lex_name])
        idx_payload = json.loads(files[idx_name])
        rows = lex_payload["lexemes"]
        published_lemmas.update(str(row["lemma"]) for row in rows)
        if len(rows) != len(idx_payload["items"]):
            raise ValueError(f"index/lexeme count mismatch: {level}")
        missing = [row["lemmaId"] for row in rows if row["lemmaId"] not in by_id]
        if missing:
            raise ValueError(f"{level}: {len(missing)} published rows lack Atlas entries")
        # Ukrainian source text is never cleaned into a new display. The same
        # word СУМ-11 snapshot is a rejection filter for any retained field.
        definitions = load_sum11_definitions({row["lemma"] for row in rows}, sources_db)
        reason_counts: Counter[str] = Counter()
        mode_before: Counter[str] = Counter()
        mode_after: Counter[str] = Counter()
        mode_reasons: dict[str, Counter[str]] = defaultdict(Counter)
        retained_en = retained_uk = changed_display = 0
        withheld_lemmas: dict[str, list[str]] = defaultdict(list)
        for row, item in zip(rows, idx_payload["items"], strict=True):
            if row["lemmaId"] != item["lemmaId"]:
                raise ValueError(f"index order mismatch: {level}: {row['lemmaId']}")
            before = set(item["modes"])
            nonmeaning_before = before - MEANING_MODES
            mode_before.update(before & MEANING_MODES)
            entry = by_id[row["lemmaId"]]
            result = deck._build_lexeme(entry, verifier, definitions, balla, dmklinger_rows)
            if result is None:
                raise ValueError(f"builder lost published row: {level}: {row['lemmaId']}")
            old_gloss = row["gloss"]
            for field in ("gloss", "glossClean", "meaningSource", "meaningWithheldReason", "meaningMcEligible"):
                row[field] = result[field]
            if row["gloss"] != old_gloss:
                changed_display += 1
            if row["gloss"]:
                if row["gloss"] != row["glossClean"]:
                    raise ValueError(f"display fields differ: {level}: {row['lemmaId']}")
                if not english(row["gloss"]) or meaning_problem(row["gloss"], row["lemma"], definitions.get(row["lemma"])):
                    raise ValueError(f"unsafe retained display: {level}: {row['lemmaId']}")
                if level != "A1" and not english(old_gloss):
                    raise ValueError(f"A2+ release display was not English: {level}: {row['lemmaId']}")
                source = row.get("meaningSource")
                if not isinstance(source, dict) or not all(source.get(key) for key in (
                    "mechanism", "supportRule", "sourceTable", "sourceRowId", "sourceCandidate"
                )):
                    raise ValueError(f"missing meaning-specific provenance: {level}: {row['lemmaId']}")
                path = f"{source['mechanism']}|{source['source']}|{source['supportRule']}"
                partitions[path] += 1
                partition_levels[path][level] += 1
                admissions.append({"level": level, "lemmaId": row["lemmaId"], "lemma": row["lemma"],
                                   "gloss": row["gloss"], "path": path, "provenance": source})
                if english(row["gloss"]):
                    retained_en += 1
                else:
                    retained_uk += 1
                if not row["meaningMcEligible"]:
                    for mode in before & {"matching", "choice"}:
                        mode_reasons[mode]["meaning_mc_ineligible"] += 1
                    item["modes"] = [mode for mode in item["modes"] if mode not in {"matching", "choice"}]
            else:
                reason = row["meaningWithheldReason"] or "unknown"
                reason_counts[reason] += 1
                withheld_lemmas[reason].append(row["lemma"])
                item["modes"] = [mode for mode in item["modes"] if mode not in MEANING_MODES]
                for mode in before & MEANING_MODES:
                    mode_reasons[mode][reason] += 1
            mode_after.update(set(item["modes"]) & MEANING_MODES)
            if set(item["modes"]) - MEANING_MODES != nonmeaning_before:
                raise ValueError(f"independent mode changed: {level}: {row['lemmaId']}")
            if not row["gloss"] and (set(item["modes"]) & MEANING_MODES or row["meaningMcEligible"]):
                raise ValueError(f"withheld row retained meaning mode: {level}: {row['lemmaId']}")
        for payload, name in ((lex_payload, lex_name), (idx_payload, idx_name)):
            budget = payload["sizeBudget"]
            payload["sizeBudget"] = deck._size_budget(payload, budget["rawLimitBytes"], budget["gzipLimitBytes"])
            if not payload["sizeBudget"]["ok"]:
                raise ValueError(f"size budget exceeded: {name}")
            changed[name] = deck._json_bytes(payload)
        summary[level] = {
            "rows": len(rows), "retained_en": retained_en, "retained_uk": retained_uk,
            "withheld": sum(reason_counts.values()), "changed_display_from_release": changed_display,
            "reasons": dict(sorted(reason_counts.items())),
            "modes": {mode: {"before": mode_before[mode], "after": mode_after[mode],
                              "withheld_reasons": dict(sorted(mode_reasons[mode].items()))}
                      for mode in sorted(MEANING_MODES)},
            "withheld_lemmas": {reason: sorted(lemmas, key=str.casefold) for reason, lemmas in sorted(withheld_lemmas.items())},
        }
    if sum(summary[level]["rows"] for level in LEVELS) != 6217:
        raise ValueError("frozen denominator is not 6,217")
    if sum(partitions.values()) != len(admissions):
        raise ValueError("admission partition does not cover retained rows")
    by_lemma = {row["lemma"]: row for row in admissions}
    fixture = json.loads((Path(__file__).parents[2] / "tests/fixtures/meaning_9160_eval_cases.json")
                         .read_text(encoding="utf-8"))
    cases: dict[tuple[str, str], dict] = {}
    for lemma in REVIEWED_WRONG_LEMMAS:
        cases[(lemma, "reviewed_wrong_sense")] = {"lemma": lemma, "condition": "reviewed_wrong_sense",
                                                   "expected": "withheld"}
    for lemma, bad in HISTORICAL_BAD_DISPLAYS.items():
        cases[(lemma, "wrong_display")] = {"lemma": lemma, "condition": "wrong_display",
                                            "forbiddenDisplay": bad, "expected": "forbidden_display_absent"}
    for lemma in HISTORICAL_COVERAGE_LEMMAS | {item["lemma"] for item in fixture}:
        cases[(lemma, "source_binding")] = {"lemma": lemma, "condition": "source_binding",
                                             "expected": "row_bound_or_withheld"}
    history = []
    for case in sorted(cases.values(), key=lambda item: (item["lemma"].casefold(), item["condition"])):
        observed = by_lemma.get(case["lemma"])
        case = {**case, "inFrozenRows": case["lemma"] in published_lemmas,
                "retainedDisplay": observed["gloss"] if observed else None}
        if case["condition"] == "reviewed_wrong_sense" and observed:
            raise ValueError(f"reviewed wrong sense retained: {case['lemma']}")
        if case["condition"] == "wrong_display" and observed and (
            observed["gloss"].casefold() == case["forbiddenDisplay"].casefold()
        ):
            raise ValueError(f"historical wrong display retained: {case['lemma']}")
        history.append(case)
    (output / "meaning-9160-history.json").write_text(
        json.dumps({"schema": "meaning-9160-history-v1", "count": len(history), "cases": history},
                   ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {"schema": "meaning-9160-admissions-v1", "inputHashes": {
        "package": PACKAGE_SHA256, "atlasDb": ATLAS_SHA256, "sourcesDb": SOURCES_SHA256},
        "codeHashes": code_hashes,
        "totalRows": 6217, "retainedRows": len(admissions), "partitions": dict(sorted(partitions.items())),
        "partitionLevels": {path: dict(sorted(counts.items())) for path, counts in sorted(partition_levels.items())},
        "rows": admissions}
    (output / "meaning-9160-admissions.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for name, content in files.items():
        (output / name).write_bytes(changed.get(name, content))
    summary["hashes"] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                         for name in sorted(files)}
    summary["input_hashes"] = manifest["inputHashes"]
    summary["code_hashes"] = code_hashes
    summary["admission_partitions"] = manifest["partitions"]
    summary["admission_partition_levels"] = manifest["partitionLevels"]
    summary["admission_manifest_sha256"] = sha256(output / "meaning-9160-admissions.json")
    summary["historical_count"] = len(history)
    summary["historical_manifest_sha256"] = sha256(output / "meaning-9160-history.json")
    (output / "meaning-9160-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--atlas-db", type=Path, required=True)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.package, args.atlas_db, args.sources_db, args.output)
    for level in LEVELS:
        item = result[level]
        print(f"{level}: {item['rows']} rows; {item['retained_en']} EN; {item['retained_uk']} UK; {item['withheld']} withheld")


if __name__ == "__main__":
    main()
