#!/usr/bin/env python3
"""
Crawl Ukrainian Lessons blog articles and create a structured database.

Sources article URLs from the sitemap (post-sitemap.xml), categorizes them
by topic and suggested CEFR level, and writes a JSON database for pipeline
blog discovery.

Usage:
    .venv/bin/python scripts/crawl_ulp_blog.py [--output PATH]
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Article catalog — sourced from ukrainianlessons.com/post-sitemap.xml
# Each entry: (slug_suffix, title, category, topics, level, content_type)
# ---------------------------------------------------------------------------

ARTICLES: list[tuple[str, str, str, list[str], str, str]] = [
    # === ALPHABET & WRITING ===
    ("ukrainian-alphabet", "Ukrainian Alphabet: Full Guide with Examples and Pronunciation",
     "alphabet", ["alphabet", "cyrillic", "pronunciation", "letters"], "A1", "interactive_guide"),
    ("ukrainian-cyrillic-alphabet", "Ukrainian Cyrillic Alphabet — Letters and Sounds",
     "alphabet", ["alphabet", "cyrillic", "letters", "sounds"], "A1", "guide"),
    ("transliteration", "Transliteration of Ukrainian — How to Write Ukrainian in Latin Letters",
     "alphabet", ["transliteration", "writing", "alphabet"], "A1", "reference"),
    ("punctuation-marks", "Punctuation Marks in Ukrainian",
     "grammar", ["punctuation", "writing"], "A2", "reference"),
    ("ukrainian-punctuation", "Ukrainian Punctuation Rules",
     "grammar", ["punctuation", "writing", "grammar"], "B1", "guide"),
    ("tonguetwisters", "Ukrainian Tongue Twisters for Better Pronunciation",
     "pronunciation", ["tongue twisters", "pronunciation", "phonetics"], "A2", "practice"),

    # === GRAMMAR — NOUNS & CASES ===
    ("ukrainian-cases-chart", "Ukrainian Cases Chart",
     "grammar", ["cases", "grammar", "declension"], "A2", "reference"),
    ("accusativecase", "Accusative Case in Ukrainian",
     "grammar", ["accusative", "cases", "grammar"], "A1", "guide"),
    ("genitive-case", "Genitive Case in Ukrainian",
     "grammar", ["genitive", "cases", "grammar"], "A1", "guide"),
    ("prepositions-cases", "Prepositions and Cases in Ukrainian",
     "grammar", ["prepositions", "cases", "grammar"], "A2", "reference"),
    ("noun-genders-in-ukrainian", "Noun Genders in Ukrainian",
     "grammar", ["gender", "nouns", "grammar"], "A1", "guide"),
    ("plural-of-ukrainian-nouns-special-forms", "Plural of Ukrainian Nouns — Special Forms",
     "grammar", ["plural", "nouns", "grammar", "exceptions"], "A2", "guide"),
    ("nouns-after-numbers", "Nouns After Numbers in Ukrainian",
     "grammar", ["numbers", "nouns", "cases", "grammar"], "A2", "guide"),

    # === GRAMMAR — VERBS ===
    ("grammar-past-tense", "Past Tense in Ukrainian",
     "grammar", ["past tense", "verbs", "grammar"], "A1", "guide"),
    ("grammar-future", "Future Tense in Ukrainian",
     "grammar", ["future tense", "verbs", "grammar"], "A1", "guide"),
    ("ukrainian-tenses", "Ukrainian Verb Tenses — Complete Overview",
     "grammar", ["tenses", "verbs", "grammar"], "A2", "reference"),
    ("ukrainian-verb-prefixes", "Ukrainian Verb Prefixes",
     "grammar", ["prefixes", "verbs", "aspect"], "B1", "reference"),
    ("verb-aspect-in-ukrainian-differences", "Verb Aspect in Ukrainian",
     "grammar", ["aspect", "verbs", "grammar"], "A2", "guide"),
    ("perfective-verbs", "Perfective Verbs in Ukrainian",
     "grammar", ["perfective", "verbs", "aspect", "grammar"], "B1", "guide"),
    ("reflexive-verbs", "Reflexive Verbs in Ukrainian",
     "grammar", ["reflexive verbs", "verbs", "grammar"], "B1", "guide"),

    # === GRAMMAR — ADJECTIVES & ADVERBS ===
    ("adjectives-adverbs-chart", "Ukrainian Adjectives and Adverbs Chart",
     "grammar", ["adjectives", "adverbs", "grammar", "declension"], "A2", "reference"),
    ("adverbs-frequency", "Adverbs of Frequency in Ukrainian",
     "grammar", ["adverbs", "frequency", "grammar"], "A2", "guide"),
    ("adverbs-location", "Adverbs of Location in Ukrainian",
     "grammar", ["adverbs", "location", "grammar"], "A2", "guide"),
    ("adjectival-participle", "Adjectival Participle in Ukrainian",
     "grammar", ["participle", "adjectives", "grammar"], "B2", "guide"),

    # === GRAMMAR — PRONOUNS ===
    ("ukrainian-personal-pronouns", "Ukrainian Personal Pronouns",
     "grammar", ["pronouns", "grammar", "declension"], "A1", "guide"),
    ("pronouns-this-that", "This and That in Ukrainian — Demonstrative Pronouns",
     "grammar", ["demonstratives", "pronouns", "grammar"], "A1", "guide"),
    ("possessive-pronouns-declension", "Possessive Pronouns Declension in Ukrainian",
     "grammar", ["possessive", "pronouns", "declension", "grammar"], "A2", "guide"),
    ("pronouns-ves-vsiakyi-kozhen", "Pronouns: весь, всякий, кожен in Ukrainian",
     "grammar", ["pronouns", "grammar", "quantifiers"], "B1", "guide"),

    # === GRAMMAR — PREPOSITIONS & CONJUNCTIONS ===
    ("prepositions-u-na", "Prepositions У and НА in Ukrainian",
     "grammar", ["prepositions", "grammar"], "A1", "guide"),
    ("prepositions-of-time-in-ukrainian", "Prepositions of Time in Ukrainian",
     "grammar", ["prepositions", "time", "grammar"], "A2", "guide"),
    ("location-destination-prepositions", "Location and Destination Prepositions in Ukrainian",
     "grammar", ["prepositions", "location", "destination", "grammar"], "A2", "guide"),
    ("ukrainian-conjunctions", "Ukrainian Conjunctions — Basic Overview",
     "grammar", ["conjunctions", "grammar", "syntax"], "A2", "guide"),
    ("ukrainian-conjunctions-guide", "Ukrainian Conjunctions Guide — Advanced",
     "grammar", ["conjunctions", "grammar", "syntax"], "B1", "reference"),
    ("dates-in-ukrainian", "Dates in Ukrainian",
     "grammar", ["dates", "numbers", "grammar", "time"], "A2", "guide"),

    # === VOCABULARY ===
    ("vocabulary-family", "Family Vocabulary in Ukrainian",
     "vocabulary", ["family", "vocabulary"], "A1", "vocabulary_list"),
    ("vocabulary-clothes", "Clothes Vocabulary in Ukrainian",
     "vocabulary", ["clothes", "vocabulary"], "A1", "vocabulary_list"),
    ("ukrainian-food", "40+ Ukrainian Dishes",
     "vocabulary", ["food", "culture", "vocabulary"], "A1", "vocabulary_list"),
    ("vocabulary-fruits-and-vegetables", "Fruits and Vegetables in Ukrainian",
     "vocabulary", ["food", "vocabulary"], "A1", "vocabulary_list"),
    ("animals-in-ukrainian-with-audio", "Animals in Ukrainian (with Audio)",
     "vocabulary", ["animals", "vocabulary"], "A1", "vocabulary_list"),
    ("emotions-in-ukrainian", "Emotions and Feelings in Ukrainian",
     "vocabulary", ["emotions", "feelings", "vocabulary"], "A2", "vocabulary_list"),
    ("vocabulary-praise-words", "Praise Words and Compliments in Ukrainian",
     "vocabulary", ["praise", "compliments", "vocabulary"], "A2", "vocabulary_list"),
    ("hiking-vocabulary", "Hiking Vocabulary in Ukrainian",
     "vocabulary", ["hiking", "nature", "vocabulary", "travel"], "B1", "vocabulary_list"),
    ("business-ukrainian", "Business Ukrainian — Office Vocabulary and Phrases",
     "vocabulary", ["business", "work", "vocabulary"], "B2", "vocabulary_list"),
    ("powerful-ukrainian-words", "Powerful Ukrainian Words",
     "vocabulary", ["vocabulary", "advanced", "culture"], "B2", "vocabulary_list"),
    ("12-ukrainian-words-without-translation", "12 Ukrainian Words Without Translation",
     "vocabulary", ["untranslatable", "vocabulary", "culture"], "B1", "vocabulary_list"),
    ("confusing-ukrainian-words", "Confusing Ukrainian Words",
     "vocabulary", ["vocabulary", "common mistakes"], "B1", "troubleshooting"),
    ("false-friends", "False Friends in Ukrainian",
     "vocabulary", ["vocabulary", "common mistakes", "cognates"], "B1", "troubleshooting"),
    ("ukrainian-homonyms", "Ukrainian Homonyms",
     "vocabulary", ["homonyms", "vocabulary", "advanced"], "B2", "vocabulary_list"),
    ("something-hurts", "Something Hurts — Health Vocabulary in Ukrainian",
     "vocabulary", ["health", "body", "vocabulary"], "A2", "vocabulary_list"),
    ("love-in-ukrainian", "Love in Ukrainian — Words and Expressions",
     "vocabulary", ["love", "relationships", "vocabulary"], "A2", "vocabulary_list"),
    ("exclamations", "Ukrainian Exclamations and Interjections",
     "vocabulary", ["exclamations", "interjections", "vocabulary"], "A2", "vocabulary_list"),
    ("ukrainian-currency", "Ukrainian Currency — Hryvnia",
     "vocabulary", ["money", "currency", "numbers", "vocabulary"], "A1", "vocabulary_list"),
    ("birthday-wishes", "Birthday Wishes in Ukrainian",
     "vocabulary", ["birthday", "wishes", "phrases", "vocabulary"], "A1", "vocabulary_list"),
    ("20-ukrainian-idioms-proverbs-and-expressions", "20 Ukrainian Idioms, Proverbs and Expressions",
     "vocabulary", ["idioms", "proverbs", "expressions", "vocabulary"], "B1", "vocabulary_list"),
    ("too-much", "Too Much in Ukrainian — надто, занадто, забагато",
     "vocabulary", ["quantity", "vocabulary", "grammar"], "A2", "guide"),

    # === PHRASES & COMMUNICATION ===
    ("greetings", "Greetings in Ukrainian",
     "phrases", ["greetings", "phrases"], "A1", "phrasebook"),
    ("thank-you-in-ukrainian", "8+ Ways to Say Thank You in Ukrainian",
     "phrases", ["gratitude", "phrases"], "A1", "phrasebook"),
    ("14-basic-ukrainian-phrases", "14 Basic Ukrainian Phrases",
     "phrases", ["phrases", "basics"], "A1", "phrasebook"),
    ("small-talk-in-ukrainian", "Small Talk in Ukrainian",
     "phrases", ["conversation", "phrases"], "A2", "guide"),
    ("useful-ukrainian-questions", "Useful Ukrainian Questions",
     "phrases", ["questions", "phrases", "communication"], "A1", "phrasebook"),
    ("express-support-to-ukrainians", "How to Express Support to Ukrainians",
     "phrases", ["support", "phrases", "culture"], "A2", "guide"),
    ("episodes-meeting-people", "Meeting People — Phrases and Dialogues",
     "phrases", ["introductions", "meeting", "phrases"], "A1", "guide"),

    # === PHRASEBOOK TOPIC PAGES (ph-*) ===
    ("ph-alphabet", "Ukrainian Phrasebook: Alphabet",
     "phrasebook", ["alphabet", "pronunciation", "basics"], "A1", "phrasebook"),
    ("ph-essential", "Ukrainian Phrasebook: Essential Phrases",
     "phrasebook", ["essential", "phrases", "basics"], "A1", "phrasebook"),
    ("ph-numbers", "Ukrainian Phrasebook: Numbers",
     "phrasebook", ["numbers", "counting"], "A1", "phrasebook"),
    ("ph-food", "Ukrainian Phrasebook: Food and Restaurants",
     "phrasebook", ["food", "restaurant", "ordering"], "A1", "phrasebook"),
    ("ph-health", "Ukrainian Phrasebook: Health",
     "phrasebook", ["health", "doctor", "body"], "A2", "phrasebook"),
    ("ph-places", "Ukrainian Phrasebook: Places",
     "phrasebook", ["places", "directions", "city"], "A1", "phrasebook"),
    ("ph-house", "Ukrainian Phrasebook: House and Home",
     "phrasebook", ["house", "home", "furniture"], "A1", "phrasebook"),
    ("ph-clothing", "Ukrainian Phrasebook: Clothing",
     "phrasebook", ["clothing", "shopping"], "A1", "phrasebook"),
    ("ph-money", "Ukrainian Phrasebook: Money",
     "phrasebook", ["money", "shopping", "prices"], "A1", "phrasebook"),
    ("ph-work", "Ukrainian Phrasebook: Work",
     "phrasebook", ["work", "profession", "office"], "A2", "phrasebook"),
    ("ph-feelings", "Ukrainian Phrasebook: Feelings",
     "phrasebook", ["feelings", "emotions"], "A1", "phrasebook"),
    ("ph-animals", "Ukrainian Phrasebook: Animals",
     "phrasebook", ["animals", "nature"], "A1", "phrasebook"),
    ("ph-education", "Ukrainian Phrasebook: Education",
     "phrasebook", ["education", "school", "study"], "A2", "phrasebook"),
    ("ph-children", "Ukrainian Phrasebook: Children",
     "phrasebook", ["children", "family"], "A1", "phrasebook"),
    ("ph-language", "Ukrainian Phrasebook: Language",
     "phrasebook", ["language", "communication", "learning"], "A1", "phrasebook"),
    ("ph-help", "Ukrainian Phrasebook: Asking for Help",
     "phrasebook", ["help", "emergency", "phrases"], "A1", "phrasebook"),
    ("ph-needs", "Ukrainian Phrasebook: Needs",
     "phrasebook", ["needs", "requests", "phrases"], "A1", "phrasebook"),
    ("ph-support", "Ukrainian Phrasebook: Support",
     "phrasebook", ["support", "encouragement", "phrases"], "A2", "phrasebook"),
    ("ph-legal", "Ukrainian Phrasebook: Legal",
     "phrasebook", ["legal", "documents", "phrases"], "B1", "phrasebook"),
    ("ph-war", "Ukrainian Phrasebook: War-Related Phrases",
     "phrasebook", ["war", "safety", "emergency"], "B1", "phrasebook"),

    # === CULTURE & TRAVEL ===
    ("kyiv-things-to-do", "Things to Do in Kyiv",
     "culture", ["kyiv", "culture", "travel"], "A2", "cultural_guide"),
    ("kyiv-guide", "Kyiv Guide for Ukrainian Learners",
     "culture", ["kyiv", "travel", "culture"], "A2", "cultural_guide"),
    ("lviv-cultural-guide", "Lviv Cultural Guide",
     "culture", ["lviv", "culture", "travel"], "B1", "cultural_guide"),
    ("lviv-food-guide", "Lviv Food Guide",
     "culture", ["lviv", "food", "travel", "culture"], "A2", "cultural_guide"),
    ("ukrainian-customs", "Ukrainian Customs and Traditions",
     "culture", ["customs", "culture", "traditions"], "B1", "cultural_guide"),
    ("ukrainian-superstitions", "Ukrainian Superstitions",
     "culture", ["superstitions", "culture", "beliefs"], "B1", "cultural_guide"),
    ("taras-shevchenko", "Taras Shevchenko — Ukraine's National Poet",
     "culture", ["shevchenko", "literature", "history", "poetry"], "B2", "biography"),
    ("ukrainian-national-symbols", "Ukrainian National Symbols",
     "culture", ["symbols", "culture", "history", "patriotic"], "B1", "cultural_guide"),
    ("christmas-new-year-in-ukraine", "Christmas and New Year in Ukraine",
     "culture", ["christmas", "holidays", "culture", "traditions"], "A2", "cultural_guide"),
    ("carol-of-the-bells", "Carol of the Bells — Shchedryk — Ukrainian Origins",
     "culture", ["music", "christmas", "culture", "history"], "B1", "cultural_guide"),
    ("about-crimea", "About Crimea — History and Culture",
     "culture", ["crimea", "history", "geography", "culture"], "B2", "cultural_guide"),
    ("ukrainian-history", "Ukrainian History — Brief Overview",
     "culture", ["history", "culture", "overview"], "B2", "cultural_guide"),
    ("top-places-to-visit-in-ukraine", "Top Places to Visit in Ukraine",
     "culture", ["travel", "tourism", "culture"], "A2", "cultural_guide"),
    ("things-to-prepare-before-ukraine", "Things to Prepare Before Visiting Ukraine",
     "culture", ["travel", "preparation", "culture"], "A2", "cultural_guide"),
    ("how-to-help-ukraine", "How to Help Ukraine",
     "culture", ["support", "charity", "culture"], "B1", "guide"),
    ("support-ukrainian-military", "Support Ukrainian Military",
     "culture", ["support", "military", "culture"], "B2", "guide"),
    ("ukrainian-quotes", "Famous Ukrainian Quotes",
     "culture", ["quotes", "literature", "culture"], "B2", "cultural_guide"),

    # === LITERATURE & SONGS ===
    ("ukrainian-literature", "Ukrainian Literature — Key Authors and Works",
     "literature", ["literature", "authors", "books", "culture"], "B2", "guide"),
    ("ukrainian-plays", "Ukrainian Plays Worth Knowing",
     "literature", ["plays", "theatre", "literature", "culture"], "C1", "guide"),
    ("ukrainian-fiction-books", "Ukrainian Fiction Books for Learners",
     "literature", ["books", "literature", "resources"], "B1", "resource_guide"),
    ("song-chervona-kalyna", "Song: Ой у лузі червона калина — Analysis and Lyrics",
     "songs", ["music", "songs", "history", "patriotic"], "B1", "song_analysis"),
    ("song-chervona-ruta", "Song: Червона рута — Analysis",
     "songs", ["music", "songs", "culture"], "B1", "song_analysis"),
    ("song-spy-sobi-sama", "Song: Співай собі, сама — Analysis",
     "songs", ["music", "songs", "culture"], "B1", "song_analysis"),

    # === LEARNING RESOURCES ===
    ("learning-ukrainian-vocabulary", "How to Learn Ukrainian Vocabulary",
     "learning_resources", ["study tips", "vocabulary", "methodology"], "A1", "methodology"),
    ("ukrainian-dictionaries", "Best Ukrainian Dictionaries",
     "learning_resources", ["dictionaries", "resources"], "A1", "resource_guide"),
    ("ukrainian-podcasts", "Ukrainian Podcasts for Learners",
     "learning_resources", ["podcasts", "resources"], "A2", "resource_guide"),
    ("begin-learning-ukrainian", "How to Begin Learning Ukrainian",
     "learning_resources", ["beginners", "methodology", "resources"], "A1", "methodology"),
    ("ukrainian-language-resources", "Ukrainian Language Resources — Comprehensive List",
     "learning_resources", ["resources", "tools", "methodology"], "A1", "resource_guide"),
    ("ukrainian-tutor", "How to Find a Ukrainian Tutor",
     "learning_resources", ["tutor", "learning", "resources"], "A1", "resource_guide"),
    ("most-popular", "Most Popular Ukrainian Lessons Articles",
     "learning_resources", ["popular", "resources", "best of"], "A1", "resource_guide"),
    ("episodes-for-ukrainian-language-beginners", "Podcast Episodes for Ukrainian Language Beginners",
     "learning_resources", ["podcast", "beginners", "resources"], "A1", "resource_guide"),
    ("ukrainian-youtube", "Ukrainian YouTube Channels for Learners",
     "learning_resources", ["youtube", "videos", "resources"], "A2", "resource_guide"),
    ("ukrainian-cartoons", "Ukrainian Cartoons for Language Learners",
     "learning_resources", ["cartoons", "videos", "resources", "listening"], "A2", "resource_guide"),
    ("ukrainian-subtitles", "How to Watch Ukrainian with Subtitles",
     "learning_resources", ["subtitles", "listening", "resources", "videos"], "A2", "resource_guide"),
    ("ukrainian-cooking-channels", "Ukrainian Cooking Channels",
     "learning_resources", ["cooking", "youtube", "culture", "resources"], "B1", "resource_guide"),
    ("ukrainian-verbs-podcasts", "Ukrainian Verbs — Podcast Episodes",
     "learning_resources", ["verbs", "podcast", "resources"], "A2", "resource_guide"),
    ("ukrainian-for-kids", "Ukrainian for Kids — Resources and Tips",
     "learning_resources", ["kids", "children", "resources", "methodology"], "A1", "resource_guide"),
]

BASE_URL = "https://www.ukrainianlessons.com"


def build_blog_db() -> dict:
    """Build the blog database from the article catalog."""
    articles = []
    for i, (slug, title, category, topics, level, content_type) in enumerate(ARTICLES):
        articles.append({
            "id": f"ulp-blog-{i:03d}",
            "category": category,
            "url": f"{BASE_URL}/{slug}/",
            "title": title,
            "topics": topics,
            "suggested_level": level,
            "content_type": content_type,
        })

    return {
        "version": "2.0",
        "source": "Ukrainian Lessons (www.ukrainianlessons.com)",
        "generated_at": str(date.today()),
        "sitemap_source": f"{BASE_URL}/post-sitemap.xml",
        "total_articles": len(articles),
        "articles": articles,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Ukrainian Lessons blog database")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent.parent / "docs" / "resources" / "ukrainianlessons" / "blog_db.json")
    args = parser.parse_args()

    db = build_blog_db()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {db['total_articles']} articles to {args.output}")

    # Summary
    by_cat = {}
    by_level = {}
    for a in db["articles"]:
        by_cat[a["category"]] = by_cat.get(a["category"], 0) + 1
        by_level[a["suggested_level"]] = by_level.get(a["suggested_level"], 0) + 1

    print(f"\nBy category:")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat}: {n}")
    print(f"\nBy level:")
    for level in ("A1", "A2", "B1", "B2", "C1"):
        if level in by_level:
            print(f"  {level}: {by_level[level]}")


if __name__ == "__main__":
    main()
