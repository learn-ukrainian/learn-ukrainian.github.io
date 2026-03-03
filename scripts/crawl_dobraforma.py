#!/usr/bin/env python3
"""
Build Dobra Forma chapter database.

Dobra Forma (https://opentext.ku.edu/dobraforma/) is an open-access Ukrainian
grammar textbook from the University of Kansas (CC license). ~90 chapters covering
nouns, pronouns, adjectives, verbs, and adverbs with contextualized exercises.

Usage:
    .venv/bin/python scripts/crawl_dobraforma.py [--output PATH]
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

BASE_URL = "https://opentext.ku.edu/dobraforma/chapter"

# (slug, title, topics, level)
# All chapters are grammar guides suitable for A1-B1 learners
CHAPTERS: list[tuple[str, str, list[str], str]] = [
    # === THE NOUN: Gender ===
    ("1-1", "Gender of Nouns", ["gender", "nouns", "grammar"], "A1"),
    ("1-2", "Gender of Nouns (Masculine and Feminine)", ["gender", "nouns", "grammar"], "A1"),
    ("1-3", "Gender of Nouns (Neuter)", ["gender", "nouns", "grammar"], "A1"),

    # === THE NOUN: Plural ===
    ("2-1", "Regular Plural Nouns", ["plural", "nouns", "grammar"], "A1"),
    ("2-2", "Plural Nouns in -ї and Exceptions", ["plural", "nouns", "grammar", "exceptions"], "A2"),
    ("2-3", "Plural Nouns with Stem Changes", ["plural", "nouns", "grammar", "alternation"], "A2"),
    ("2-4", "Exceptions, Plural-only and Singular-only Nouns", ["plural", "nouns", "grammar", "exceptions"], "A2"),

    # === THE NOUN: Vocative ===
    ("3-1", "Vocative Case (Feminine Nouns)", ["vocative", "cases", "nouns", "grammar"], "A2"),
    ("3-2", "Vocative Case (Masculine Nouns)", ["vocative", "cases", "nouns", "grammar"], "A2"),
    ("3-3", "Vocative Case (Plural Nouns)", ["vocative", "cases", "nouns", "grammar"], "A2"),

    # === THE NOUN: Locative ===
    ("4-1", "Locative Case (Use of в and у)", ["locative", "cases", "prepositions", "grammar"], "A1"),
    ("4-2", "Locative Case (в, у and на)", ["locative", "cases", "prepositions", "grammar"], "A1"),
    ("4-3", "Locative Case (Consonant Mutations)", ["locative", "cases", "grammar", "alternation"], "A2"),
    ("4-4", "Locative Case (Endings in -ї and -у)", ["locative", "cases", "grammar"], "A2"),
    ("4-5", "Locative Case (Foreign Loan Words)", ["locative", "cases", "grammar", "loanwords"], "A2"),
    ("4-6", "Locative Case (Plural)", ["locative", "cases", "grammar", "plural"], "A2"),

    # === THE NOUN: Accusative ===
    ("5-1", "Inanimate Nouns as Direct Objects (Accusative Case)", ["accusative", "cases", "grammar"], "A1"),
    ("5-2", "Inanimate Nouns as Direct Objects (Accusative and Genitive)", ["accusative", "genitive", "cases", "grammar"], "A2"),
    ("5-3", "Genitive Case for Direct Objects after Negation (Neuter and Masculine)", ["genitive", "negation", "cases", "grammar"], "A2"),
    ("5-4", "Genitive Case for Direct Objects after Negation (Masculine)", ["genitive", "negation", "cases", "grammar"], "A2"),

    # === THE NOUN: Genitive ===
    ("6-1", "Genitive Case with Expressions of Quantity (Masculine Plural)", ["genitive", "cases", "quantity", "grammar"], "A2"),
    ("6-2", "Genitive Case with Expressions of Quantity (Feminine and Neuter Plural)", ["genitive", "cases", "quantity", "grammar"], "A2"),
    ("6-3", "Genitive Case with Expressions of Quantity (Exceptions)", ["genitive", "cases", "quantity", "grammar", "exceptions"], "A2"),
    ("7-1", "Genitive Case after Prepositions з, до, and в/у", ["genitive", "cases", "prepositions", "grammar"], "A2"),
    ("7-2", "Genitive Case after Prepositions біля, після, для and без", ["genitive", "cases", "prepositions", "grammar"], "A2"),
    ("7-3", "Genitive Case to Express Possession and Relationship", ["genitive", "cases", "possession", "grammar"], "A2"),
    ("7-4", "Genitive Case to Express Quantity and Attributive Function", ["genitive", "cases", "quantity", "grammar"], "A2"),

    # === THE NOUN: Accusative animate ===
    ("8-1", "Accusative Case of Animate Nouns", ["accusative", "cases", "animate", "grammar"], "A2"),
    ("8-2", "Accusative Case after Prepositions в/у, на and про", ["accusative", "cases", "prepositions", "grammar"], "A2"),

    # === THE NOUN: Instrumental ===
    ("9-1", "Instrumental Case (Intro to Singular Endings)", ["instrumental", "cases", "grammar"], "A2"),
    ("9-2", "Instrumental Case (Other Singular Endings and Stem Changes)", ["instrumental", "cases", "grammar", "alternation"], "A2"),
    ("9-3", "Instrumental Case (Plural Nouns)", ["instrumental", "cases", "grammar", "plural"], "A2"),
    ("9-4", "Instrumental Case (Use of зі and із)", ["instrumental", "cases", "prepositions", "grammar"], "A2"),
    ("10-1", "Instrumental Case after Verbs", ["instrumental", "cases", "verbs", "grammar"], "B1"),
    ("10-2", "Instrumental Case after Verbs (цікавитися, захоплюватися, займатися)", ["instrumental", "cases", "verbs", "grammar"], "B1"),
    ("10-3", "Instrumental Case after Verbs (працювати, бути, стати)", ["instrumental", "cases", "verbs", "grammar"], "B1"),

    # === THE NOUN: Dative ===
    ("11-1", "Dative Case (Feminine Nouns)", ["dative", "cases", "grammar"], "A2"),
    ("11-2", "Dative Case (Masculine and Neuter Nouns)", ["dative", "cases", "grammar"], "A2"),
    ("11-3", "Dative Case (Animate Masculine Nouns)", ["dative", "cases", "animate", "grammar"], "A2"),
    ("11-4", "Dative Case (Plural Nouns)", ["dative", "cases", "grammar", "plural"], "A2"),

    # === THE PRONOUN: Possessive ===
    ("12-1", "Possessive Pronouns (мій, твій, чий in Nominative)", ["possessive", "pronouns", "grammar"], "A1"),
    ("12-2", "Possessive Pronouns (наш and ваш in Nominative)", ["possessive", "pronouns", "grammar"], "A1"),
    ("12-3", "Possessive Pronouns (його, її and їхній in Nominative)", ["possessive", "pronouns", "grammar"], "A1"),

    # === THE PRONOUN: Personal ===
    ("13-1", "Personal Pronouns (Nominative and Accusative Cases)", ["pronouns", "accusative", "grammar"], "A1"),
    ("13-2", "Personal Pronouns (Accusative and Genitive Cases)", ["pronouns", "accusative", "genitive", "grammar"], "A2"),
    ("13-3", "Personal Pronouns (Accusative and Genitive after Prepositions)", ["pronouns", "prepositions", "grammar"], "A2"),
    ("14-1", "Personal Pronouns (Instrumental Case after з)", ["pronouns", "instrumental", "grammar"], "A2"),
    ("14-2", "Personal Pronouns (Instrumental Case after Verbs)", ["pronouns", "instrumental", "verbs", "grammar"], "B1"),
    ("15-1", "Personal Pronouns (Dative Case Forms)", ["pronouns", "dative", "grammar"], "A2"),
    ("15-2", "Personal Pronouns (Dative Case for Indirect Object)", ["pronouns", "dative", "grammar"], "A2"),

    # === THE ADJECTIVE ===
    ("16-1", "Adjectives (Gender and Number in Nominative)", ["adjectives", "gender", "grammar"], "A1"),
    ("16-2", "Soft-Stem Adjectives (Gender and Number in Nominative)", ["adjectives", "soft stem", "grammar"], "A2"),
    ("16-3", "Ordinal Numerals (Gender and Number in Nominative)", ["ordinal", "numerals", "grammar"], "A2"),
    ("17-1", "Accusative Case of Adjectives (With Inanimate Nouns)", ["adjectives", "accusative", "cases", "grammar"], "A2"),
    ("17-2", "Accusative Case of Adjectives (With Animate Nouns)", ["adjectives", "accusative", "animate", "grammar"], "A2"),
    ("17-3", "Genitive Case of Adjectives", ["adjectives", "genitive", "cases", "grammar"], "A2"),
    ("17-4", "Genitive Case of Adjectives and Ordinal Numerals (Time Expressions)", ["adjectives", "genitive", "time", "grammar"], "A2"),
    ("18-1", "Locative Case of Adjectives and Ordinal Numerals", ["adjectives", "locative", "cases", "grammar"], "A2"),
    ("18-2", "Dative Case of Adjectives", ["adjectives", "dative", "cases", "grammar"], "A2"),
    ("19-1", "Instrumental Case of Adjectives", ["adjectives", "instrumental", "cases", "grammar"], "A2"),
    ("20-1", "Comparative Degree of Adjectives", ["comparative", "adjectives", "grammar"], "B1"),
    ("20-2", "Comparative Degree of Adjectives (Exceptions)", ["comparative", "adjectives", "grammar", "exceptions"], "B1"),
    ("20-3", "Superlative Degree of Adjectives", ["superlative", "adjectives", "grammar"], "B1"),

    # === THE VERB: Present Tense ===
    ("21-1", "Present Tense of Verbs (Читати Type)", ["present tense", "verbs", "conjugation", "grammar"], "A1"),
    ("21-2", "Present Tense of Verbs (Працювати Type)", ["present tense", "verbs", "conjugation", "grammar"], "A1"),
    ("21-3", "Present Tense of Verbs (Other First Conjugation Verbs)", ["present tense", "verbs", "conjugation", "grammar"], "A2"),
    ("21-4", "Present Tense of Verbs (Бути)", ["present tense", "verbs", "бути", "grammar"], "A1"),
    ("22-1", "Present Tense of Verbs (Лежати and Сидіти Types)", ["present tense", "verbs", "conjugation", "grammar"], "A2"),
    ("22-2", "Present Tense of Verbs (Говорити and Любити Types)", ["present tense", "verbs", "conjugation", "grammar"], "A2"),
    ("22-3", "Present Tense of Verbs (Other Second-Conjugation Verbs)", ["present tense", "verbs", "conjugation", "grammar"], "A2"),

    # === THE VERB: Reflexive ===
    ("23-1", "Present Tense of -ся Verbs (First Conjugation)", ["reflexive", "verbs", "conjugation", "grammar"], "A2"),
    ("23-2", "Present Tense of -ся Verbs (Second Conjugation)", ["reflexive", "verbs", "conjugation", "grammar"], "A2"),

    # === THE VERB: Past & Future ===
    ("24-1", "Past Tense of Verbs", ["past tense", "verbs", "grammar"], "A1"),
    ("24-2", "Past Tense of -ся Verbs", ["past tense", "reflexive", "verbs", "grammar"], "A2"),
    ("25-1", "Future Tense of Verbs (With бути)", ["future tense", "verbs", "grammar"], "A1"),
    ("25-2", "Future Tense of Verbs (Synthetic: Читатиму)", ["future tense", "verbs", "grammar"], "A2"),

    # === THE VERB: Modal ===
    ("26-1", "Modal Verbs (Want, Must, Can)", ["modal", "verbs", "grammar"], "A1"),
    ("26-2", "Modal Constructions (треба and можна)", ["modal", "verbs", "grammar"], "A2"),

    # === THE VERB: Aspect ===
    ("27-1", "Introduction to Verbal Aspect (Prefixed Perfective Verbs)", ["aspect", "verbs", "grammar"], "A2"),
    ("27-2", "Verbal Aspect (Past Tense)", ["aspect", "verbs", "past tense", "grammar"], "B1"),
    ("27-3", "Verbal Aspect (Other Types of Aspectual Pairs)", ["aspect", "verbs", "grammar"], "B1"),
    ("27-4", "Verbal Aspect (Future Tense)", ["aspect", "verbs", "future tense", "grammar"], "B1"),

    # === THE VERB: Motion ===
    ("28-1", "Verbs of Motion (іти – їхати)", ["motion", "verbs", "grammar"], "A2"),
    ("28-2", "Verbs of Motion (ходити – їздити)", ["motion", "verbs", "grammar"], "A2"),
    ("28-3", "Verbs of Motion (піти – прийти, поїхати – приїхати)", ["motion", "verbs", "grammar"], "B1"),

    # === THE VERB: Imperatives ===
    ("29-1", "Imperatives (Читай Type)", ["imperative", "verbs", "grammar"], "A2"),
    ("29-2", "Imperatives (Пиши Type)", ["imperative", "verbs", "grammar"], "A2"),
    ("29-3", "Imperatives (Other Forms and Exceptions)", ["imperative", "verbs", "grammar", "exceptions"], "A2"),

    # === THE ADVERB ===
    ("30-1", "Adverbs (Formation from Adjectives)", ["adverbs", "grammar", "word formation"], "A2"),
    ("30-2", "Using Adverbs", ["adverbs", "grammar"], "A2"),
]


def build_db() -> dict:
    articles = []
    for i, (slug, title, topics, level) in enumerate(CHAPTERS):
        articles.append({
            "id": f"df-{i:03d}",
            "category": "grammar",
            "url": f"{BASE_URL}/{slug}/",
            "title": f"Dobra Forma: {title}",
            "topics": topics,
            "suggested_level": level,
            "content_type": "grammar_exercises",
            "source": "dobraforma",
        })

    return {
        "version": "1.0",
        "source": "Добра форма / Dobra Forma (University of Kansas, CC license)",
        "url": "https://opentext.ku.edu/dobraforma/",
        "generated_at": str(date.today()),
        "total_articles": len(articles),
        "articles": articles,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Dobra Forma chapter database")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent.parent / "docs" / "resources" / "dobraforma" / "dobraforma_db.json")
    args = parser.parse_args()

    db = build_db()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {db['total_articles']} chapters to {args.output}")


if __name__ == "__main__":
    main()
