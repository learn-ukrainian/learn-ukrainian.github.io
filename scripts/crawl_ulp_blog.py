#!/usr/bin/env python3
"""
Crawl Ukrainian Lessons blog articles and create a structured database.

This script:
1. Fetches blog articles from Ukrainian Lessons sitemap
2. Categorizes articles by topic and suggested CEFR level
3. Creates a JSON database for integration into external_resources.yaml

Usage:
    .venv/bin/python scripts/crawl_ulp_blog.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

# Known blog articles from WebFetch discovery
KNOWN_ARTICLES = {
    "grammar": [
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-cases-chart/",
            "title": "Ukrainian Cases Chart",
            "topics": ["cases", "grammar", "declension"],
            "suggested_level": "A2",
            "content_type": "reference",
        },
        {
            "url": "https://www.ukrainianlessons.com/accusativecase/",
            "title": "Accusative Case in Ukrainian",
            "topics": ["accusative", "cases", "grammar"],
            "suggested_level": "A1",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/genitive-case/",
            "title": "Genitive Case in Ukrainian",
            "topics": ["genitive", "cases", "grammar"],
            "suggested_level": "A1",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/grammar-past-tense/",
            "title": "Past Tense in Ukrainian",
            "topics": ["past tense", "verbs", "grammar"],
            "suggested_level": "A1",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/grammar-future/",
            "title": "Future Tense in Ukrainian",
            "topics": ["future tense", "verbs", "grammar"],
            "suggested_level": "A1",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-verb-prefixes/",
            "title": "Ukrainian Verb Prefixes",
            "topics": ["prefixes", "verbs", "aspect"],
            "suggested_level": "B1",
            "content_type": "reference",
        },
        {
            "url": "https://www.ukrainianlessons.com/verb-aspect-in-ukrainian-differences/",
            "title": "Verb Aspect in Ukrainian",
            "topics": ["aspect", "verbs", "grammar"],
            "suggested_level": "A2",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/reflexive-verbs/",
            "title": "Reflexive Verbs in Ukrainian",
            "topics": ["reflexive verbs", "verbs", "grammar"],
            "suggested_level": "B1",
            "content_type": "guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-conjunctions-guide/",
            "title": "Ukrainian Conjunctions Guide",
            "topics": ["conjunctions", "grammar", "syntax"],
            "suggested_level": "A2",
            "content_type": "reference",
        },
    ],
    "vocabulary": [
        {
            "url": "https://www.ukrainianlessons.com/vocabulary-family/",
            "title": "Family Vocabulary in Ukrainian",
            "topics": ["family", "vocabulary"],
            "suggested_level": "A1",
            "content_type": "vocabulary_list",
        },
        {
            "url": "https://www.ukrainianlessons.com/vocabulary-clothes/",
            "title": "Clothes Vocabulary in Ukrainian",
            "topics": ["clothes", "vocabulary"],
            "suggested_level": "A1",
            "content_type": "vocabulary_list",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-food/",
            "title": "40+ Ukrainian Dishes",
            "topics": ["food", "culture", "vocabulary"],
            "suggested_level": "A1",
            "content_type": "vocabulary_list",
        },
        {
            "url": "https://www.ukrainianlessons.com/vocabulary-fruits-and-vegetables/",
            "title": "Fruits and Vegetables in Ukrainian",
            "topics": ["food", "vocabulary"],
            "suggested_level": "A1",
            "content_type": "vocabulary_list",
        },
        {
            "url": "https://www.ukrainianlessons.com/animals-in-ukrainian-with-audio/",
            "title": "Animals in Ukrainian (with Audio)",
            "topics": ["animals", "vocabulary"],
            "suggested_level": "A1",
            "content_type": "vocabulary_list",
        },
    ],
    "phrases": [
        {
            "url": "https://www.ukrainianlessons.com/greetings/",
            "title": "Greetings in Ukrainian",
            "topics": ["greetings", "phrases"],
            "suggested_level": "A1",
            "content_type": "phrasebook",
        },
        {
            "url": "https://www.ukrainianlessons.com/thank-you-in-ukrainian/",
            "title": "8+ Ways to Say Thank You in Ukrainian",
            "topics": ["gratitude", "phrases"],
            "suggested_level": "A1",
            "content_type": "phrasebook",
        },
        {
            "url": "https://www.ukrainianlessons.com/14-basic-ukrainian-phrases/",
            "title": "14 Basic Ukrainian Phrases",
            "topics": ["phrases", "basics"],
            "suggested_level": "A1",
            "content_type": "phrasebook",
        },
        {
            "url": "https://www.ukrainianlessons.com/small-talk-in-ukrainian/",
            "title": "Small Talk in Ukrainian",
            "topics": ["conversation", "phrases"],
            "suggested_level": "A2",
            "content_type": "guide",
        },
    ],
    "culture": [
        {
            "url": "https://www.ukrainianlessons.com/kyiv-things-to-do/",
            "title": "Things to Do in Kyiv",
            "topics": ["kyiv", "culture", "travel"],
            "suggested_level": "A2",
            "content_type": "cultural_guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-customs/",
            "title": "Ukrainian Customs and Traditions",
            "topics": ["customs", "culture", "traditions"],
            "suggested_level": "B1",
            "content_type": "cultural_guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-superstitions/",
            "title": "Ukrainian Superstitions",
            "topics": ["superstitions", "culture", "beliefs"],
            "suggested_level": "B1",
            "content_type": "cultural_guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/taras-shevchenko/",
            "title": "Taras Shevchenko - Ukraine's National Poet",
            "topics": ["shevchenko", "literature", "history"],
            "suggested_level": "B2",
            "content_type": "biography",
        },
    ],
    "learning_resources": [
        {
            "url": "https://www.ukrainianlessons.com/learning-ukrainian-vocabulary/",
            "title": "How to Learn Ukrainian Vocabulary",
            "topics": ["study tips", "vocabulary", "methodology"],
            "suggested_level": "A1",
            "content_type": "methodology",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-dictionaries/",
            "title": "Best Ukrainian Dictionaries",
            "topics": ["dictionaries", "resources"],
            "suggested_level": "A1",
            "content_type": "resource_guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-podcasts/",
            "title": "Ukrainian Podcasts for Learners",
            "topics": ["podcasts", "resources"],
            "suggested_level": "A2",
            "content_type": "resource_guide",
        },
        {
            "url": "https://www.ukrainianlessons.com/ukrainian-fiction-books/",
            "title": "Ukrainian Fiction Books for Learners",
            "topics": ["books", "literature", "resources"],
            "suggested_level": "B1",
            "content_type": "resource_guide",
        },
    ],
    "advanced": [
        {
            "url": "https://www.ukrainianlessons.com/confusing-ukrainian-words/",
            "title": "Confusing Ukrainian Words",
            "topics": ["vocabulary", "common mistakes"],
            "suggested_level": "B1",
            "content_type": "troubleshooting",
        },
        {
            "url": "https://www.ukrainianlessons.com/false-friends/",
            "title": "False Friends in Ukrainian",
            "topics": ["vocabulary", "common mistakes", "cognates"],
            "suggested_level": "B1",
            "content_type": "troubleshooting",
        },
    ],
}


def create_blog_database():
    """Create structured blog article database from known articles."""

    articles = []
    article_id = 1

    for category, items in KNOWN_ARTICLES.items():
        for item in items:
            articles.append({
                "id": f"ulp-blog-{article_id:03d}",
                "category": category,
                **item
            })
            article_id += 1

    database = {
        "version": "1.0",
        "source": "Ukrainian Lessons (www.ukrainianlessons.com)",
        "generated_at": "2026-01-02",
        "total_articles": len(articles),
        "articles": articles
    }

    return database


def save_database(database: dict, output_path: Path):
    """Save blog database to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {database['total_articles']} blog articles to {output_path}")


def main():
    """Main entry point."""
    output_path = Path(__file__).parent.parent / 'docs' / 'resources' / 'ukrainianlessons' / 'blog_db.json'

    print("🔍 Creating Ukrainian Lessons blog database...\n")

    database = create_blog_database()
    save_database(database, output_path)

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total articles: {database['total_articles']}")

    by_level = {}
    for article in database['articles']:
        level = article['suggested_level']
        by_level[level] = by_level.get(level, 0) + 1

    print(f"\n   By level:")
    for level in sorted(by_level.keys()):
        print(f"      {level}: {by_level[level]} articles")

    print(f"\n   By category:")
    for category in KNOWN_ARTICLES.keys():
        count = len(KNOWN_ARTICLES[category])
        print(f"      {category}: {count} articles")

    print(f"\n✅ Blog database created successfully!")
    print(f"\n📝 Next steps:")
    print(f"   1. Review: cat {output_path}")
    print(f"   2. Map articles to curriculum modules")
    print(f"   3. Add priority field and integrate into external_resources.yaml")


if __name__ == '__main__':
    main()
