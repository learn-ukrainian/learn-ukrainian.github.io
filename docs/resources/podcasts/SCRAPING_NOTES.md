# Podcast Scraping Notes

## Methodology (Phase 1)
**Date:** December 2025
**Method:** Manual Verification & Browser Inspection
**Agent:** Gemini (Anti-Gravity)

### Overview
Initial data extraction for Ukrainian Lessons Podcast (Season 1, Episodes 1-5) was performed manually to validate the structure and feasibility of scraping.

### URL Structure
- **Pattern:** `https://www.ukrainianlessons.com/episode{N}/`
- **Verified:** Episodes 1-5 are accessible.
- **Note:** Some URLs redirect (e.g., `episode1/` -> `episode-1/` in some internal links, but the canonical structure seems to be `episode{N}/`).

### Anti-Crawler Protection
- **System:** Cloudflare
- **Impact:** Automated scrapers (like `curl`, `requests`) may be blocked without proper headers or browser emulation (e.g., Selenium, Playwright).
- **Strategy for Phase 2:** Use browser-based extraction or robust headers if automation is required.

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

**Pseudo-code:**
```python
for i in range(1, 250):
    url = f"https://www.ukrainianlessons.com/episode{i}/"
    # fetch content
    # parse title, summary
    # extract tags if available (or use LLM to tag based on summary)
    # save to JSON
```
