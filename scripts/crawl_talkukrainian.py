#!/usr/bin/env python3
"""
Build Talk Ukrainian lesson database.

Talk Ukrainian (https://talkukrainian.com/) is a Ukrainian grammar and vocabulary
site by a native speaker from Kherson. 36 lessons covering alphabet, grammar cases,
verb tenses, adjectives, adverbs, pronouns, prepositions, and vocabulary topics.

Usage:
    .venv/bin/python scripts/crawl_talkukrainian.py [--output PATH]
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

BASE_URL = "https://talkukrainian.com"

# (slug, title, topics, level, category)
LESSONS: list[tuple[str, str, list[str], str, str]] = [
    # === Alphabet & Basics ===
    ("ukrainian-alphabet", "Ukrainian alphabet with pronunciation",
     ["alphabet", "letters", "pronunciation", "cyrillic"], "A1", "vocabulary"),
    ("greetings", "Greetings in Ukrainian",
     ["greetings", "hello", "привіт", "introductions"], "A1", "vocabulary"),
    ("introducing-yourself", "Introducing yourself in Ukrainian – Мене звати",
     ["introductions", "мене звати", "name", "self-introduction"], "A1", "vocabulary"),

    # === Vocabulary ===
    ("family", "Family – Родина",
     ["family", "родина", "сім'я", "vocabulary"], "A1", "vocabulary"),
    ("occupations", "Occupations",
     ["occupations", "professions", "робота", "vocabulary"], "A1", "vocabulary"),
    ("days-months-seasons", "Days, Months and Seasons in Ukrainian",
     ["days", "months", "seasons", "time", "calendar", "vocabulary"], "A1", "vocabulary"),
    ("count-in-ukrainian", "Learn to count in Ukrainian",
     ["numbers", "counting", "numerals", "vocabulary"], "A1", "vocabulary"),

    # === Nouns & Gender ===
    ("noun-genders", "Noun Genders and Adjective Agreement",
     ["gender", "nouns", "adjectives", "agreement", "grammar"], "A1", "grammar"),
    ("noun-declensions", "Noun declensions",
     ["declension", "nouns", "cases", "grammar"], "A2", "grammar"),
    ("plurals", "Plurals",
     ["plural", "nouns", "grammar"], "A1", "grammar"),

    # === Pronouns ===
    ("personal-pronouns", "Personal Pronouns",
     ["pronouns", "personal", "grammar"], "A1", "grammar"),
    ("possessive-pronouns", "Possessive Pronouns – мій, твій vs свій",
     ["possessive", "pronouns", "свій", "grammar"], "A1", "grammar"),
    ("interrogative-relative-pronouns", "Interrogative and Relative Pronouns",
     ["interrogative", "relative", "pronouns", "який", "grammar"], "A2", "grammar"),
    ("indefinite-negative-pronouns", "Indefinite and Negative Pronouns",
     ["indefinite", "negative", "pronouns", "grammar"], "A2", "grammar"),

    # === Cases ===
    ("grammatical-cases", "Ukrainian Grammatical Cases",
     ["cases", "grammar", "overview", "відмінки"], "A2", "grammar"),
    ("nominative-case", "Nominative case",
     ["nominative", "називний", "cases", "grammar"], "A1", "grammar"),
    ("genitive-case", "Genitive case",
     ["genitive", "родовий", "cases", "grammar"], "A2", "grammar"),
    ("dative-case", "Dative case",
     ["dative", "давальний", "cases", "grammar"], "A2", "grammar"),
    ("accusative-case", "Accusative case",
     ["accusative", "знахідний", "cases", "grammar"], "A2", "grammar"),
    ("instrumental-case", "Instrumental case",
     ["instrumental", "орудний", "cases", "grammar"], "A2", "grammar"),
    ("locative-case", "Locative case",
     ["locative", "місцевий", "cases", "grammar"], "A1", "grammar"),
    ("vocative-case", "Vocative case",
     ["vocative", "кличний", "cases", "grammar"], "A2", "grammar"),

    # === Adjectives & Adverbs ===
    ("adjectives", "Adjectives",
     ["adjectives", "прикметник", "grammar"], "A1", "grammar"),
    ("adjectives-degrees-comparison", "Degrees of comparison of Adjectives",
     ["comparative", "superlative", "adjectives", "grammar"], "A2", "grammar"),
    ("adverbs", "Adverbs",
     ["adverbs", "прислівник", "grammar"], "A2", "grammar"),
    ("adverbs-degrees-comparison", "Degrees of Comparison of Adverbs",
     ["comparative", "superlative", "adverbs", "grammar"], "A2", "grammar"),

    # === Verbs ===
    ("verbs", "Verbs and Common Constructions with Infinitives",
     ["verbs", "infinitive", "grammar"], "A1", "grammar"),
    ("present-tense", "Present Tense",
     ["present tense", "verbs", "conjugation", "grammar"], "A1", "grammar"),
    ("past-tense", "Past Tense",
     ["past tense", "verbs", "grammar"], "A1", "grammar"),
    ("future-tense", "Future Tense",
     ["future tense", "verbs", "grammar"], "A2", "grammar"),
    ("verb-aspect", "Verb Aspect",
     ["aspect", "verbs", "доконаний", "недоконаний", "grammar"], "A2", "grammar"),
    ("verb-transitivity", "Verb Transitivity",
     ["transitivity", "verbs", "grammar"], "B1", "grammar"),
    ("verb-voice-active-passive", "Verb Voice: active / passive",
     ["voice", "active", "passive", "verbs", "grammar"], "B1", "grammar"),
    ("verb-mood", "Verb Mood",
     ["mood", "imperative", "subjunctive", "verbs", "grammar"], "B1", "grammar"),

    # === Prepositions & Conjunctions ===
    ("prepositions", "Ukrainian prepositions",
     ["prepositions", "прийменник", "grammar"], "A2", "grammar"),
    ("conjunctions", "Ukrainian conjunctions",
     ["conjunctions", "сполучник", "grammar"], "A2", "grammar"),
]


def build_db() -> dict:
    articles = []
    for i, (slug, title, topics, level, category) in enumerate(LESSONS):
        articles.append({
            "id": f"tu-{i:03d}",
            "category": category,
            "url": f"{BASE_URL}/{slug}/",
            "title": f"Talk Ukrainian: {title}",
            "topics": topics,
            "suggested_level": level,
            "content_type": "grammar_guide" if category == "grammar" else "vocabulary_guide",
            "source": "talkukrainian",
        })

    return {
        "version": "1.0",
        "source": "Talk Ukrainian (talkukrainian.com) — grammar and vocabulary guides by a native speaker from Kherson",
        "url": "https://talkukrainian.com/",
        "generated_at": str(date.today()),
        "total_articles": len(articles),
        "articles": articles,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Talk Ukrainian lesson database")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent.parent / "docs" / "resources" / "talkukrainian" / "talkukrainian_db.json")
    args = parser.parse_args()

    db = build_db()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {db['total_articles']} lessons to {args.output}")


if __name__ == "__main__":
    main()
