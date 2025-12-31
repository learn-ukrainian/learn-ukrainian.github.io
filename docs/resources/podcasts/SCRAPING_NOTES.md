# Podcast Scraping Notes

## Methodology (Phase 1)
**Date:** December 2025
**Method:** Manual Verification & Browser Inspection
**Agent:** Gemini (Anti-Gravity)

### Overview
Initial data extraction for Ukrainian Lessons Podcast (Season 1, Episodes 1-5) was performed manually to validate the structure and feasibility of scraping.

### URL Structure
- **Pattern:** `https://www.ukrainianlessons.com/episode{N}/`
- **Verified:** Episodes 1-5 exist.
- **Season 2-6 Confirmation:** Verified via spot checks (e.g., Ep 80=S2, Ep 120=S3, Ep 200=S5). The numbering is continuous: `episode1` to `episode200+`.

### Anti-Crawler Protection
- **System:** Cloudflare
- **Impact:** Automated scrapers (like `requests`) are blocked with **403 Forbidden** errors after 1-3 sequential requests, even with browser headers.
- **Workaround:**
    - High delay (30s+).
    - IP rotation / Proxies.
    - Browser automation (Selenium/Playwright) might fare better but is slower.
- **Status:** Created `scripts/scrape_podcasts.py` as a proof-of-concept tool. It works for single requests but hits rate limits quickly.

### HTML Structure (Elementor)
The website uses the Elementor page builder. Key selectors identified:

- **Title:** `h1.elementor-heading-title` (often contains "ULP X-XX | Title")
- **Audio:** Audio player is embedded. Direct MP3 links are often available in the page source but require parsing.
- **Content/Summary:** `div.elementor-widget-theme-post-content`
- **Breadcrumbs:** `.elementor-breadcrumb`

### Data Transformation
1.  **ID Generation:** `ULP-{season}-{episode}` was simplified to `ULP-{000}` format (global episode number).
2.  **Title Cleaning:** Removed "ULP 1-01 |" prefixes to keep the title clean.
3.  **Tags:** Manually assigned based on content analysis (Grammar, Vocabulary, Topic).

## Future Automation Strategy
To scale to all ~200+ episodes, a Python script using `BeautifulSoup` and `requests` (with headers) or `playwright` is recommended.

**Current Script:** `scripts/scrape_podcasts.py`
- Implements headers, delay, and parsing logic.
- Extracts Title, ID, Season, Episode, Summary (basic).
- Audio URL extraction is hit-or-miss (often hidden).
- Use with caution/delays to avoid IP bans.