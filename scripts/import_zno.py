#!/usr/bin/env python3
"""
Import and classify ZNO Ukrainian language exam questions.

Downloads the osyvokon/zno dataset (MIT license, 3,814 questions),
filters to Ukrainian language & literature (2,328), classifies by
skill type, and maps to CEFR levels.

Usage:
  .venv/bin/python scripts/import_zno.py                # Download + classify
  .venv/bin/python scripts/import_zno.py --stats         # Show statistics
  .venv/bin/python scripts/import_zno.py --export-yaml   # Export as activity YAML by topic
  .venv/bin/python scripts/import_zno.py --validate      # Validate exported YAML against schema
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "zno"

# Skill classification patterns (Ukrainian keywords → skill category)
SKILL_PATTERNS: list[tuple[str, list[str]]] = [
    ("наголос", [
        r"наголос",
        r"наголошен",
        r"акцентн",
    ]),
    ("фонетика", [
        r"звук[иів]",
        r"голосн[іий]",
        r"приголосн[іий]",
        r"фонетичн",
        r"чергуванн",
        r"асиміляц",
        r"однаковий звук",
        r"позначають.{0,20}звук",
        r"букв[аи] позначає",
    ]),
    ("орфографія", [
        r"правопис",
        r"апостроф",
        r"м['ʼ]який знак",
        r"подвоєнн",
        r"спрощенн",
        r"велик[аої] літер",
        r"написанн",
        r"правильн\w+ написан",
        r"разом.{0,10}окрем",
        r"через дефіс",
        r"орфографічн",
        r"писати літеру",
        r"пишемо",
        r"пишеться",
        r"літер[аиу] [ґґіїєе]",
        r"з малої літер",
        r"з великої літер",
        r"разом треба писати",
        r"разом пишуться",
        r"на місці пропуску треба писати",
        r"подвоєні літер",
        r"букв[аиу] .{1,5} треба писати",
        r"заповненн\w+ пропуск",
    ]),
    ("морфологія", [
        r"іменник",
        r"прикметник",
        r"дієслов[оа]",
        r"займенник",
        r"прислівник",
        r"числівник",
        r"частк[аиі]",
        r"прийменник",
        r"сполучник",
        r"відмін[оюкі]",
        r"відмінюванн",
        r"дієвідмін",
        r"морфологічн",
        r"частин[аиі] мов",
        r"рід\b",
        r"число\b",
        r"суфікс",
        r"префікс",
        r"закінченн",
        r"корен[ьі]",
        r"основ[аиі] слов",
        r"належать до",
        r"частиною мови",
        r"утворено форму",
        r"дієслівн\w+ форм",
        r"форм[аиу] слов",
        r"імен[а] по батьков",
        r"неправильно утворено",
    ]),
    ("синтаксис", [
        r"речення",
        r"підмет",
        r"присудок",
        r"додат[ок]",
        r"означенн",
        r"обставин",
        r"розділов[іий] знак",
        r"пунктуац",
        r"синтаксичн",
        r"однорідн",
        r"відокремлен",
        r"складн\w+ речен",
        r"підрядн",
        r"сурядн",
        r"безсполучников",
        r"вставн",
        r"звертанн",
        r"пряма мова",
        r"словосполученн",
        r"потребує редагуванн",
        r"граматичн\w+ помилк",
    ]),
    ("лексика", [
        r"синонім",
        r"антонім",
        r"омонім",
        r"пароні",
        r"фразеологі",
        r"значенн\w+ слов",
        r"лексичн",
        r"переносн\w+ значен",
        r"багатозначн",
        r"архаїзм",
        r"неологізм",
        r"діалект",
        r"жаргон",
        r"запозиченн",
        r"пряме значенн",
        r"вжите? в\b.{0,20}значенн",
        r"іншомовн",
        r"помилково вжито слово",
        r"помилку? в уживанн",
    ]),
    ("стилістика", [
        r"стиль мовленн",
        r"стилістичн",
        r"художній засіб",
        r"метафор",
        r"епітет",
        r"порівнянн",
        r"персоніфікац",
        r"алегорі",
        r"гіпербол",
        r"тропи?\b",
        r"риторичн",
        r"анафор",
    ]),
    ("читання", [
        r"прочитайте текст",
        r"виконайте завданн",
    ]),
    ("літературознавство", [
        r"жанр",
        r"напрям",
        r"літературн\w+ напрям",
        r"модернізм",
        r"реалізм",
        r"романтизм",
        r"бароко",
        r"ренесанс",
        r"давня літератур",
        r"поезі",
        r"проз[аи]",
        r"драм[аи]",
        r"автор",
        r"твір",
        r"персонаж",
        r"герой",
        r"сюжет",
        r"композиці",
        # Famous Ukrainian writers
        r"Шевченк",
        r"Франк",
        r"Леся Українка|Леся\b",
        r"Коцюбинськ",
        r"Стефаник",
        r"Хвильов",
        r"Стус",
        r"Костенко",
        r"Забужко",
        r"Андрухович",
    ]),
]

# CEFR level mapping by skill category
CEFR_MAPPING = {
    "наголос":             {"min": "A1", "max": "A2"},
    "фонетика":            {"min": "A1", "max": "B1"},
    "орфографія":          {"min": "A1", "max": "B1"},
    "морфологія":          {"min": "A2", "max": "B2"},
    "синтаксис":           {"min": "B1", "max": "B2"},
    "лексика":             {"min": "A2", "max": "C1"},
    "стилістика":          {"min": "B2", "max": "C2"},
    "читання":             {"min": "B1", "max": "C2"},
    "літературознавство":  {"min": "B2", "max": "C2"},
}


def classify_question(question_text: str, answers_text: str) -> str:
    """Classify a ZNO question by skill category using keyword heuristics."""
    combined = f"{question_text} {answers_text}".lower()
    scores: dict[str, int] = {}

    for category, patterns in SKILL_PATTERNS:
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            score += len(matches)
        if score > 0:
            scores[category] = score

    if not scores:
        return "інше"

    return max(scores, key=scores.get)


def download_dataset() -> list[dict]:
    """Download the ZNO dataset from HuggingFace."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: 'datasets' package not installed. Run: .venv/bin/pip install datasets", file=sys.stderr)
        sys.exit(1)

    print("Downloading osyvokon/zno dataset from HuggingFace...")
    ds = load_dataset("osyvokon/zno", split="train+test")

    records = []
    for row in ds:
        records.append({
            "question": row["question"],
            "answers": row["answers"],
            "correct_answers": row["correct_answers"],
            "subject": row.get("subject", ""),
            "year": row.get("year"),
            "question_number": row.get("question_number"),
        })

    print(f"Downloaded {len(records)} total questions")
    return records


def filter_ukrainian_language(records: list[dict]) -> list[dict]:
    """Filter to Ukrainian language & literature questions only."""
    filtered = [
        r for r in records
        if "ukrainian" in (r.get("subject") or "").lower()
        or "українська" in (r.get("subject") or "").lower()
    ]
    print(f"Filtered to {len(filtered)} Ukrainian language questions")
    return filtered


def classify_all(records: list[dict]) -> list[dict]:
    """Add skill_category and cefr_estimate to each record."""
    for r in records:
        answers_text = " ".join(
            a.get("text", "") if isinstance(a, dict) else str(a)
            for a in (r.get("answers") or [])
        )
        category = classify_question(r["question"], answers_text)
        r["skill_category"] = category
        cefr = CEFR_MAPPING.get(category, {"min": "B1", "max": "C1"})
        r["cefr_min"] = cefr["min"]
        r["cefr_max"] = cefr["max"]
    return records


def save_jsonl(records: list[dict], path: Path):
    """Save records as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} records to {path}")


def load_jsonl(path: Path) -> list[dict]:
    """Load records from JSONL."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def print_stats(records: list[dict]):
    """Print classification statistics."""
    from collections import Counter

    categories = Counter(r["skill_category"] for r in records)

    print(f"\n{'Category':<25} {'Count':>6} {'%':>6}  CEFR range")
    print("─" * 60)
    for cat, count in categories.most_common():
        pct = count / len(records) * 100
        cefr = CEFR_MAPPING.get(cat, {"min": "?", "max": "?"})
        print(f"{cat:<25} {count:>6} {pct:>5.1f}%  {cefr['min']}–{cefr['max']}")
    print("─" * 60)
    print(f"{'Total':<25} {len(records):>6}")

    # Year distribution
    years = Counter(r.get("year") for r in records if r.get("year"))
    if years:
        print(f"\nYears: {min(years)}–{max(years)} ({len(years)} distinct)")

    # Answer count distribution
    answer_counts = Counter(len(r.get("answers", [])) for r in records)
    print(f"Answer options: {dict(answer_counts)}")

    # Multi-correct questions
    multi = sum(1 for r in records if len(r.get("correct_answers", [])) > 1)
    print(f"Multi-correct: {multi} ({multi / len(records) * 100:.1f}%)")


def convert_to_activity(record: dict) -> dict:
    """Convert a single ZNO question to our activity YAML format.

    Maps to the closest existing activity type based on question structure:
    - Single correct → quiz item
    - Multiple correct → select item
    """
    answers = record.get("answers", [])
    correct = set(record.get("correct_answers", []))

    options = []
    for a in answers:
        marker = a.get("marker", "") if isinstance(a, dict) else ""
        text = a.get("text", str(a)) if isinstance(a, dict) else str(a)
        options.append({
            "text": text,
            "correct": marker in correct,
        })

    is_multi = len(correct) > 1
    item = {
        "question": record["question"],
        "options": options,
    }

    return {
        "type": "select" if is_multi else "quiz",
        "item": item,
        "skill_category": record.get("skill_category", "інше"),
        "cefr_min": record.get("cefr_min", "A2"),
        "cefr_max": record.get("cefr_max", "C1"),
        "source": {
            "dataset": "osyvokon/zno",
            "license": "MIT",
            "year": record.get("year"),
            "question_number": record.get("question_number"),
        },
    }


def export_by_topic(records: list[dict]):
    """Export classified questions as YAML files grouped by skill category."""
    import yaml

    by_topic_dir = DATA_DIR / "by_topic"
    by_topic_dir.mkdir(parents=True, exist_ok=True)

    from collections import defaultdict
    by_category: dict[str, list[dict]] = defaultdict(list)

    for r in records:
        activity = convert_to_activity(r)
        by_category[r["skill_category"]].append(activity)

    for category, activities in sorted(by_category.items()):
        # Group into quiz (single correct) and select (multi correct)
        quiz_items = [a["item"] for a in activities if a["type"] == "quiz"]
        select_items = [a["item"] for a in activities if a["type"] == "select"]

        output = []
        if quiz_items:
            output.append({
                "type": "quiz",
                "title": f"ЗНО: {category}",
                "instruction": f"Завдання ЗНО з теми «{category}». Оберіть одну правильну відповідь.",
                "source": "osyvokon/zno (MIT)",
                "items": quiz_items,
            })
        if select_items:
            output.append({
                "type": "select",
                "title": f"ЗНО: {category} (кілька відповідей)",
                "instruction": f"Завдання ЗНО з теми «{category}». Оберіть усі правильні відповіді.",
                "source": "osyvokon/zno (MIT)",
                "items": select_items,
            })

        slug = category.replace(" ", "-")
        out_path = by_topic_dir / f"{slug}.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"  {slug}.yaml: {len(quiz_items)} quiz + {len(select_items)} select items")

    print(f"\nExported {len(by_category)} topic files to {by_topic_dir}")


def validate_schema():
    """Validate exported YAML files against activity schema."""
    try:
        import jsonschema
        import yaml
    except ImportError:
        print("Error: jsonschema or pyyaml not installed", file=sys.stderr)
        sys.exit(1)

    schema_path = PROJECT_ROOT / "schemas" / "activities-base.schema.json"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    schema = json.loads(schema_path.read_text())
    by_topic_dir = DATA_DIR / "by_topic"

    if not by_topic_dir.exists():
        print("No exported files found. Run --export-yaml first.", file=sys.stderr)
        sys.exit(1)

    valid = 0
    invalid = 0
    for yaml_file in sorted(by_topic_dir.glob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        errors = []
        for i, activity in enumerate(data or []):
            act_type = activity.get("type")
            if act_type in schema.get("definitions", {}):
                try:
                    jsonschema.validate(activity, schema["definitions"][act_type])
                except jsonschema.ValidationError as e:
                    errors.append(f"  [{i}] {e.message[:100]}")

        if errors:
            print(f"FAIL {yaml_file.name}")
            for e in errors[:5]:
                print(e)
            invalid += 1
        else:
            print(f"OK   {yaml_file.name}")
            valid += 1

    print(f"\n{valid} valid, {invalid} invalid")


def main():
    parser = argparse.ArgumentParser(description="Import ZNO dataset")
    parser.add_argument("--stats", action="store_true", help="Show classification statistics")
    parser.add_argument("--export-yaml", action="store_true", help="Export as activity YAML by topic")
    parser.add_argument("--validate", action="store_true", help="Validate exported YAML")
    parser.add_argument("--force", action="store_true", help="Re-download even if data exists")
    args = parser.parse_args()

    jsonl_path = DATA_DIR / "zno_ukrmova_classified.jsonl"

    # Load or download
    if jsonl_path.exists() and not args.force:
        records = load_jsonl(jsonl_path)
        print(f"Loaded {len(records)} records from {jsonl_path}")
    else:
        raw = download_dataset()
        records = filter_ukrainian_language(raw)
        records = classify_all(records)
        save_jsonl(records, jsonl_path)

        # Also save the full raw dataset
        raw_path = DATA_DIR / "zno_all_raw.jsonl"
        save_jsonl(raw, raw_path)

    if args.stats:
        print_stats(records)
        return

    if args.export_yaml:
        export_by_topic(records)
        return

    if args.validate:
        validate_schema()
        return

    # Default: show stats
    print_stats(records)


if __name__ == "__main__":
    main()
