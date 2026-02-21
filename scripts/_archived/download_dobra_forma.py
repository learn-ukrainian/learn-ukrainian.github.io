#!/usr/bin/env python3
"""
Download all chapters from Dobra Forma (Good Form) Ukrainian Grammar textbook.

Source: https://opentext.ku.edu/dobraforma/
License: Creative Commons (Open Educational Resource)

This script downloads chapters as markdown for local reference.
"""

import os
import re
import time
import subprocess
from pathlib import Path

# All chapters to download - simple chapter numbers only
# URL format: https://opentext.ku.edu/dobraforma/chapter/{num}/
CHAPTERS = [
    # The Noun (1.1-1.3, 2.1-2.4, 3.1-3.3, 4.1-4.6, 5.1-5.4, 6.1-6.3, 7.1-7.4, 8.1-8.2, 9.1-9.4, 10.1-10.3, 11.1-11.4)
    "1-1", "1-2", "1-3",
    "2-1", "2-2", "2-3", "2-4",
    "3-1", "3-2", "3-3",
    "4-1", "4-2", "4-3", "4-4", "4-5", "4-6",
    "5-1", "5-2", "5-3", "5-4",
    "6-1", "6-2", "6-3",
    "7-1", "7-2", "7-3", "7-4",
    "8-1", "8-2",
    "9-1", "9-2", "9-3", "9-4",
    "10-1", "10-2", "10-3",
    "11-1", "11-2", "11-3", "11-4",

    # The Pronoun (12.1-12.3, 13.1-13.3, 14.1-14.2, 15.1-15.2)
    "12-1", "12-2", "12-3",
    "13-1", "13-2", "13-3",
    "14-1", "14-2",
    "15-1", "15-2",

    # The Adjective and Ordinal Numeral (16.1-16.3, 17.1-17.4, 18.1-18.2, 19.1, 20.1-20.3)
    "16-1", "16-2", "16-3",
    "17-1", "17-2", "17-3", "17-4",
    "18-1", "18-2",
    "19-1",
    "20-1", "20-2", "20-3",

    # The Verb (21.1-21.4, 22.1-22.3, 23.1-23.2, 24.1-24.2, 25.1-25.2, 26.1-26.2, 27.1-27.4, 28.1-28.3, 29.1-29.3)
    "21-1", "21-2", "21-3", "21-4",
    "22-1", "22-2", "22-3",
    "23-1", "23-2",
    "24-1", "24-2",
    "25-1", "25-2",
    "26-1", "26-2",
    "27-1", "27-2", "27-3", "27-4",
    "28-1", "28-2", "28-3",
    "29-1", "29-2", "29-3",

    # The Adverb (30.1-30.2)
    "30-1", "30-2",
]

BASE_URL = "https://opentext.ku.edu/dobraforma/chapter"
OUTPUT_DIR = Path("docs/references/dobra-forma/chapters")


def fetch_chapter(chapter_num: str) -> str | None:
    """Fetch a chapter using curl and return the content."""
    url = f"{BASE_URL}/{chapter_num}/"

    try:
        result = subprocess.run(
            ["curl", "-s", "-L", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def html_to_markdown(html: str, chapter_num: str) -> str:
    """Convert HTML content to clean markdown."""
    # Extract main content from <section data-type="chapter">
    content_match = re.search(
        r'<section data-type="chapter"[^>]*>(.*?)</section>\s*</main>',
        html,
        re.DOTALL
    )

    if not content_match:
        # Try simpler pattern
        content_match = re.search(
            r'<section data-type="chapter"[^>]*>(.*?)</section>',
            html,
            re.DOTALL
        )

    if not content_match:
        return ""

    content = content_match.group(1)

    # Extract title from entry-title class
    title_match = re.search(r'<h1[^>]*class="entry-title"[^>]*>([^<]+)</h1>', html)
    title = title_match.group(1).strip() if title_match else f"Chapter {chapter_num}"

    # Basic HTML to Markdown conversion
    md = content

    # Headers
    md = re.sub(r'<h1[^>]*>([^<]+)</h1>', r'# \1\n', md)
    md = re.sub(r'<h2[^>]*>([^<]+)</h2>', r'## \1\n', md)
    md = re.sub(r'<h3[^>]*>([^<]+)</h3>', r'### \1\n', md)
    md = re.sub(r'<h4[^>]*>([^<]+)</h4>', r'#### \1\n', md)

    # Paragraphs
    md = re.sub(r'<p[^>]*>', '\n', md)
    md = re.sub(r'</p>', '\n', md)

    # Lists
    md = re.sub(r'<ul[^>]*>', '\n', md)
    md = re.sub(r'</ul>', '\n', md)
    md = re.sub(r'<ol[^>]*>', '\n', md)
    md = re.sub(r'</ol>', '\n', md)
    md = re.sub(r'<li[^>]*>', '- ', md)
    md = re.sub(r'</li>', '\n', md)

    # Bold and italic
    md = re.sub(r'<strong[^>]*>([^<]+)</strong>', r'**\1**', md)
    md = re.sub(r'<b[^>]*>([^<]+)</b>', r'**\1**', md)
    md = re.sub(r'<em[^>]*>([^<]+)</em>', r'*\1*', md)
    md = re.sub(r'<i[^>]*>([^<]+)</i>', r'*\1*', md)

    # Links
    md = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r'[\2](\1)', md)

    # Tables - simplified conversion
    md = re.sub(r'<table[^>]*>', '\n', md)
    md = re.sub(r'</table>', '\n', md)
    md = re.sub(r'<tr[^>]*>', '', md)
    md = re.sub(r'</tr>', ' |\n', md)
    md = re.sub(r'<t[hd][^>]*>', '| ', md)
    md = re.sub(r'</t[hd]>', ' ', md)
    md = re.sub(r'<thead[^>]*>', '', md)
    md = re.sub(r'</thead>', '', md)
    md = re.sub(r'<tbody[^>]*>', '', md)
    md = re.sub(r'</tbody>', '', md)

    # Blockquotes
    md = re.sub(r'<blockquote[^>]*>', '\n> ', md)
    md = re.sub(r'</blockquote>', '\n', md)

    # Line breaks
    md = re.sub(r'<br\s*/?>', '\n', md)

    # Remove remaining HTML tags
    md = re.sub(r'<[^>]+>', '', md)

    # Decode HTML entities
    md = md.replace('&nbsp;', ' ')
    md = md.replace('&amp;', '&')
    md = md.replace('&lt;', '<')
    md = md.replace('&gt;', '>')
    md = md.replace('&quot;', '"')
    md = md.replace('&#8217;', "'")
    md = md.replace('&#8220;', '"')
    md = md.replace('&#8221;', '"')
    md = md.replace('&#8211;', '–')
    md = md.replace('&#8212;', '—')

    # Clean up whitespace
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = re.sub(r' +', ' ', md)
    md = md.strip()

    # Add header with source info
    chapter_url = chapter_num.replace(".", "-") if "." in chapter_num else chapter_num
    header = f"""# {title}

**Source:** https://opentext.ku.edu/dobraforma/chapter/{chapter_url}/
**License:** Creative Commons (CC BY-NC)
**Attribution:** University of Kansas Ukrainian Language Program

---

"""

    return header + md


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    print(f"Downloading {len(CHAPTERS)} chapters from Dobra Forma...")
    print(f"Output directory: {OUTPUT_DIR}\n")

    for chapter_num in CHAPTERS:
        # Convert "1-1" to "1.1" for filename
        filename = f"{chapter_num.replace('-', '.')}.md"
        filepath = OUTPUT_DIR / filename

        # Check if already exists
        if filepath.exists():
            print(f"  [SKIP] {chapter_num}: Already exists")
            skipped += 1
            continue

        print(f"  [GET]  {chapter_num}...")

        html = fetch_chapter(chapter_num)
        if not html:
            print(f"  [FAIL] {chapter_num}: Could not fetch")
            failed += 1
            continue

        md = html_to_markdown(html, chapter_num)
        if not md or len(md) < 100:
            print(f"  [FAIL] {chapter_num}: Empty or too short content")
            failed += 1
            continue

        filepath.write_text(md, encoding='utf-8')
        print(f"  [OK]   {chapter_num}: Saved ({len(md)} chars)")
        downloaded += 1

        # Be polite - don't hammer the server
        time.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print(f"Total:      {len(CHAPTERS)}")


if __name__ == "__main__":
    main()
