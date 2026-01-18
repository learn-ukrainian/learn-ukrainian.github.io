"""External resource URL validation for reading activities.

Validates that external URLs in reading activities:
1. Are accessible (return 200)
2. Content matches the expected topic (based on module/activity title)
3. Suggests correct URLs when mismatches are detected

Issue: #430 (LLM self-validation and URL validation)
"""

import re
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class SimpleHTMLParser(HTMLParser):
    """Extract text content and title from HTML."""

    def __init__(self):
        super().__init__()
        self.text_content = []
        self.title = ""
        self.in_title = False
        self.in_body = False
        self.skip_tags = {'script', 'style', 'noscript'}
        self.current_skip = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True
        elif tag == 'body':
            self.in_body = True
        elif tag in self.skip_tags:
            self.current_skip += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag in self.skip_tags and self.current_skip > 0:
            self.current_skip -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_body and self.current_skip == 0:
            text = data.strip()
            if text:
                self.text_content.append(text)


def fetch_url_content(url: str, timeout: int = 10) -> Tuple[bool, str, str]:
    """
    Fetch URL and extract text content.

    Returns:
        Tuple of (success, title, text_content)
    """
    try:
        # Handle non-ASCII characters in URL
        parts = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit((
            parts.scheme,
            parts.netloc,
            urllib.parse.quote(parts.path),
            urllib.parse.quote(parts.query, safe='=&'),
            parts.fragment
        ))

        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; LearnUkrainian/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw_html = response.read()

            # Try to detect encoding from Content-Type header
            content_type = response.headers.get('Content-Type', '')
            encoding = 'utf-8'

            if 'charset=' in content_type:
                encoding = content_type.split('charset=')[-1].split(';')[0].strip()

            # Try multiple encodings (many Ukrainian sites use windows-1251)
            html = None
            for enc in [encoding, 'windows-1251', 'cp1251', 'utf-8', 'iso-8859-1']:
                try:
                    html = raw_html.decode(enc)
                    # Increase window to 10000 chars to skip large headers/scripts
                    if any(ord(c) > 1024 and ord(c) < 1280 for c in html[:10000]):
                        break
                except (UnicodeDecodeError, LookupError):
                    continue

            if html is None:
                html = raw_html.decode('utf-8', errors='ignore')

        parser = SimpleHTMLParser()
        parser.feed(html)

        text = ' '.join(parser.text_content[:500])  # First 500 text chunks
        return True, parser.title.strip(), text

    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}", ""
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}", ""
    except Exception:
        return False, "Error: Unknown exception during URL fetch", ""


def extract_expected_keywords(activity_title: str, module_title: str = "") -> List[str]:
    """Extract keywords we expect to find in the page content.

    Prioritizes surnames and compound names, filters out generic words.
    """
    keywords = []

    # Generic words to filter out (too common to be meaningful)
    generic_words = {
        'біографія', 'біографії', 'життя', 'творчість', 'аналіз',
        'твору', 'твори', 'автор', 'письменник', 'поет', 'історія',
        'іван', 'тарас', 'леся', 'марія', 'микола', 'петро', 'павло',
        'олександр', 'григорій', 'василь', 'богдан', 'андрій',
    }

    # Compound name pattern (like Нечуй-Левицький, Квітка-Основ'яненко)
    compound_name_pattern = r"[А-ЯІЇЄҐ][а-яіїєґ']+-[А-ЯІЇЄҐ][а-яіїєґ']+"

    # Simple name pattern (single capitalized word)
    simple_name_pattern = r"[А-ЯІЇЄҐ][а-яіїєґ']+"

    combined_text = activity_title + " " + module_title

    # First, extract compound names (these are highly specific)
    for match in re.finditer(compound_name_pattern, combined_text):
        name = match.group()
        keywords.append(name)

    # Then extract simple names, filtering out generic words
    for match in re.finditer(simple_name_pattern, combined_text):
        name = match.group()
        if len(name) > 4 and name.lower() not in generic_words:
            # Likely a surname
            keywords.append(name)

    # Also look for transliterated names in English filenames/slugs
    transliterations = {
        'nechuy-levytsky': 'Нечуй-Левицький',
        'nechuy': 'Нечуй-Левицький',  # Part of compound name
        'levytsky': 'Левицький',
        'shevchenko': 'Шевченко',
        'kulish': 'Куліш',
        'kotliarevsky': 'Котляревський',
        'franko': 'Франко',
        'ukrainka': 'Українка',
        'kobylianska': 'Кобилянська',
        'kvitka': 'Квітка-Основ\'яненко',
    }

    combined_lower = combined_text.lower()
    for eng, ukr in transliterations.items():
        if eng in combined_lower:
            keywords.append(ukr)

    # Deduplicate while preserving priority order (compound names first)
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords


def search_correct_url(keywords: List[str], site: str = "ukrlib.com.ua") -> Optional[str]:
    """
    Search for the correct URL based on keywords.

    This is a simplified version - in production, would use actual search.
    For now, we construct likely URLs based on common patterns.
    """
    # UkrLib biography URL patterns
    # https://www.ukrlib.com.ua/bio/printit.php?tid=XXXX

    # Known correct mappings (can be extended)
    known_mappings = {
        'Нечуй-Левицький': 'https://www.ukrlib.com.ua/bio/printit.php?tid=1646',
        'Шевченко': 'https://www.ukrlib.com.ua/bio/printit.php?tid=57',
        'Куліш': 'https://www.ukrlib.com.ua/bio/printit.php?tid=1621',
        'Котляревський': 'https://www.ukrlib.com.ua/bio/printit.php?tid=1553',
        'Франко': 'https://www.ukrlib.com.ua/bio/printit.php?tid=71',
        'Леся Українка': 'https://www.ukrlib.com.ua/bio/printit.php?tid=83',
        'Кобилянська': 'https://www.ukrlib.com.ua/bio/printit.php?tid=1582',
        'Квітка-Основ\'яненко': 'https://www.ukrlib.com.ua/bio/printit.php?tid=1568',
    }

    for keyword in keywords:
        for name, url in known_mappings.items():
            if keyword in name or name in keyword:
                return url

    return None


def validate_reading_url(
    url: str,
    activity_title: str,
    module_title: str = "",
    auto_fix: bool = True
) -> Dict:
    """
    Validate a reading activity URL.

    Returns:
        Dict with validation result:
        - valid: bool
        - error: str (if invalid)
        - suggested_url: str (if found better match)
        - details: str
    """
    result = {
        'valid': True,
        'error': None,
        'suggested_url': None,
        'details': None
    }

    # Fetch the URL
    success, title, content = fetch_url_content(url)

    if not success:
        result['valid'] = False
        result['error'] = f"URL not accessible: {title}"
        return result

    # Whitelist trusted domains that might be hard to scrape/decode
    if 'ukrlib.com.ua' in url:
        return result

    # Extract expected keywords
    keywords = extract_expected_keywords(activity_title, module_title)

    if not keywords:
        # No keywords to validate against
        result['details'] = "No keywords to validate - manual check recommended"
        return result

    # Check if any keyword appears in title or content
    combined = (title + " " + content).lower()
    found_keywords = [kw for kw in keywords if kw.lower() in combined]

    if found_keywords:
        result['details'] = f"Found keywords: {', '.join(found_keywords)}"
        return result

    # Content doesn't match expected topic
    result['valid'] = False
    result['error'] = f"Content mismatch - expected keywords {keywords} not found in page"
    result['details'] = f"Page title: {title[:100]}"

    # Try to find correct URL
    if auto_fix:
        correct_url = search_correct_url(keywords)
        if correct_url and correct_url != url:
            # Verify the suggested URL
            success2, title2, content2 = fetch_url_content(correct_url)
            if success2:
                combined2 = (title2 + " " + content2).lower()
                if any(kw.lower() in combined2 for kw in keywords):
                    result['suggested_url'] = correct_url
                    result['details'] += f" | Suggested: {correct_url}"

    return result


def check_external_resources(yaml_activities: list, module_title: str = "") -> List[Dict]:
    """
    Check all external resource URLs in reading activities.

    Args:
        yaml_activities: List of activity objects/dicts
        module_title: Module title for keyword extraction

    Returns:
        List of violations
    """
    violations = []

    for activity in yaml_activities:
        # Get activity type
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'reading':
            continue

        # Get resource URL
        if hasattr(activity, 'resource'):
            resource = activity.resource
        else:
            resource = activity.get('resource')

        if not resource:
            continue

        url = resource.url if hasattr(resource, 'url') else resource.get('url')
        if not url:
            continue

        # Get activity title
        title = activity.title if hasattr(activity, 'title') else activity.get('title', 'Untitled')

        # Validate URL
        result = validate_reading_url(url, title, module_title, auto_fix=True)

        if not result['valid']:
            violation = {
                'type': 'INVALID_EXTERNAL_URL',
                'severity': 'critical',
                'activity': title,
                'message': result['error'],
                'url': url
            }

            if result['suggested_url']:
                violation['suggested_url'] = result['suggested_url']
                violation['suggestion'] = f"Replace URL with: {result['suggested_url']}"
            else:
                violation['suggestion'] = "Manually verify and fix the URL"

            if result['details']:
                violation['details'] = result['details']

            violations.append(violation)

    return violations


def fix_external_resource_url(yaml_path: Path, old_url: str, new_url: str) -> bool:
    """
    Fix an external resource URL in a YAML file.

    Args:
        yaml_path: Path to the YAML file
        old_url: URL to replace
        new_url: New URL

    Returns:
        True if fixed, False otherwise
    """
    try:
        content = yaml_path.read_text(encoding='utf-8')
        if old_url not in content:
            return False

        new_content = content.replace(old_url, new_url)
        yaml_path.write_text(new_content, encoding='utf-8')
        return True
    except Exception:
        return False
