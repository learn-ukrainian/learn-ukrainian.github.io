"""
Text cleaning utilities for audit calculations.

Provides functions to clean text for word count and immersion calculations,
removing metadata, tables, and other non-content elements.
"""

import re


def clean_for_stats(text: str) -> str:
    """
    Removes metadata that should NOT count towards word count.
    Keeps scaffolding (context, explanations) as instructional content.
    """
    # 1. Remove Tables (lines starting with vertical bar)
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)

    # 2. Remove ONLY specific metadata callouts (not engagement boxes)
    text = re.sub(r'^\s*>\s*\[!(answer|options|error|id)\].*$', '', text, flags=re.MULTILINE)

    # 3. Remove Images / Links with no text
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 4. Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # 5. Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)

    # 6. Remove frontmatter dividers
    text = re.sub(r'^---', '', text, flags=re.MULTILINE)

    return text


def clean_for_immersion(text: str) -> str:
    """
    Cleans text for immersion calculation. Keeps blockquotes (engagement boxes)
    as they are part of the learning content and contribute to immersion.

    Removes markdown syntax elements that would incorrectly count as non-Ukrainian:
    - URLs in markdown links
    - Callout type markers like [!note], [!tip], etc.
    - Image syntax
    """
    # Remove ONLY metadata callouts (not engagement boxes)
    text = re.sub(r'^\s*>\s*\[!(answer|options|error|id)\].*$', '', text, flags=re.MULTILINE)

    # Remove Tables
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)

    # Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)

    # Remove URLs from markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # Remove callout type markers [!note], [!tip], [!warning], etc.
    text = re.sub(r'\[![a-zA-Z-]+\]', '', text)

    # Remove image syntax ![alt](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)

    return text


def extract_core_content(body: str) -> str:
    """
    Extract content before the Activities section.
    This is the 'instructional core' for word count (not immersion).
    """
    # Match both H1 and H2 (# and ##)
    # Match English: Activities, Exercises
    # Match Ukrainian: Вправи
    activities_pattern = re.compile(r'^#{1,2}\s+(?:Activities|Вправи|Exercises)', re.MULTILINE | re.IGNORECASE)
    activities_match = activities_pattern.search(body)

    if activities_match:
        return body[:activities_match.start()]
    return body


def calculate_immersion(text: str) -> float:
    """
    Calculate percentage of Cyrillic characters in text.

    Only counts alphabetic characters (Cyrillic vs Latin).
    Excludes: numbers, punctuation, markdown syntax - these are universal.
    """
    if not text:
        return 0.0

    # Remove whitespace
    clean_text = re.sub(r'\s+', '', text)
    if not clean_text:
        return 0.0

    # Count only alphabetic characters (Cyrillic + Latin)
    cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', clean_text))
    latin_chars = len(re.findall(r'[a-zA-Z]', clean_text))

    total_alpha = cyrillic_chars + latin_chars
    if total_alpha == 0:
        return 100.0  # No alphabetic text = consider fully immersed

    return (cyrillic_chars / total_alpha) * 100


def count_words(text: str) -> int:
    """Count words in cleaned text."""
    return len(text.split())


def extract_ukrainian_sentences(text: str) -> list[str]:
    """
    Extract Ukrainian sentences from text (lines with Cyrillic content).

    Excludes:
    - Table rows (lines starting with |)
    - Numbered list headers (lines like **1. Title:**)
    - Lines starting with # (markdown headers)
    - Bullet point lists (lines starting with - or *)
    - Blockquote callout markers (lines with [!type])
    - Blockquote bullet points (lines like "> - item")
    - Grammatical pattern demonstrations (lines with X / Y / Z alternatives)
    - Word lists (comma-separated items like "при, від, на, до")
    """
    sentences = []

    # Filter out non-prose lines
    lines = text.split('\n')
    prose_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip table rows (both regular and inside blockquotes)
        if stripped.startswith('|') or stripped.startswith('> |'):
            continue
        # Skip headers
        if stripped.startswith('#'):
            continue
        # Skip numbered lists
        if re.match(r'^\*?\*?\d+\.', stripped):
            continue
        # Skip bullet point lists (common for letter/word lists)
        if re.match(r'^[-*]\s', stripped):
            continue
        # Skip blockquote callout markers (e.g., "> [!tip]", "> [!note]")
        if re.match(r'^>\s*\[!', stripped):
            continue
        # Skip blockquote lines with emoji headers (e.g., "> 💡 **Did You Know**")
        if re.match(r'^>\s*[💡⚡🎬🎭🔗🌍🎁🗣️🏠🔍]', stripped):
            continue
        # Skip blockquote bullet points (e.g., "> - Hard: ...")
        if re.match(r'^>\s*[-*]\s', stripped):
            continue
        # Skip grammatical pattern demonstrations with / alternatives (e.g., "X / Y / Z")
        if stripped.count(' / ') >= 2:
            continue
        # Skip word lists: lines with "Label:" followed by comma-separated items
        # e.g., "Prefixes: при, від, на, до" or "**мов-**: мова, мовлення"
        if re.match(r'^>?\s*\*?\*?[\w\-]+\*?\*?:\s*\w+,', stripped):
            continue
        # Skip transformation/drill patterns (word → word, word :: word)
        # e.g., "читати → прочитати" or "imperfective :: perfective"
        if re.search(r'→|::|↔|⟶', stripped):
            continue
        # Skip lines that are mostly single Cyrillic words (vocab drills)
        # These are short lines with 1-3 Cyrillic words and no sentence structure
        cyrillic_words = re.findall(r'[\u0400-\u04ff]{2,}', stripped)
        if 1 <= len(cyrillic_words) <= 3 and len(stripped) < 50:
            # Check if it looks like a drill item (no verbs/sentence markers)
            if not re.search(r'\b(є|був|була|було|буде|можна|треба|потрібно)\b', stripped, re.IGNORECASE):
                continue
        prose_lines.append(line)

    prose_text = '\n'.join(prose_lines)

    # Split by sentence-ending punctuation, em-dashes, and colons
    # Colon added because Ukrainian instruction text often ends with ":"
    raw_sentences = re.split(r'[.!?—:]', prose_text)
    for sent in raw_sentences:
        cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', sent))
        if cyrillic_chars > 5:
            # Additional check: skip if this looks like a word list
            # Word lists have high comma-to-word ratio (>0.3)
            words = re.findall(r'[\u0400-\u04ff]{2,}', sent)
            commas = sent.count(',')
            if len(words) > 0 and commas / len(words) > 0.3:
                continue
            sentences.append(sent.strip())

    return sentences
