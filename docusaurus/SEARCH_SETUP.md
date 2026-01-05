# Search Setup Guide

This project uses **Algolia DocSearch** for multi-language support (English + Ukrainian).

## Current Implementation: Algolia DocSearch

**Configuration in `docusaurus.config.ts`:**
```typescript
themeConfig: {
  algolia: {
    appId: 'MFWOKG2YFD',
    apiKey: '4413bc11f7878cb2605766f6a050bdcc', // Public Search API Key
    indexName: 'https_learn_ukrainian_github_io_pages',
    contextualSearch: true,
    searchParameters: {
      hitsPerPage: 10,
    },
  },
}
```

## Crawler Configuration (Critical)

To ensure Ukrainian content is indexed and large pages (Grammar/History modules) are split correctly, we use a custom **JavaScript-based Crawler Configuration**.

**File:** `docusaurus/algolia-crawler.js`

### Instructions for Algolia Dashboard
1. Go to the [Algolia Crawler Dashboard](https://crawler.algolia.com/).
2. Select your crawler.
3. Go to **Editor**.
4. Copy the content of `docusaurus/algolia-crawler.js`.
5. **IMPORTANT:** Replace `apiKey: 'YOUR_ADMIN_API_KEY'` with your **Algolia Admin API Key** (or a Write-enabled key). Do NOT use the Search API Key from `docusaurus.config.ts`.
6. Click **Save** and **Restart Crawler**.

### Key Features of this Config
- **Splitting:** Uses `helpers.docsearch` to automatically chunk large content (solving "Record too big" errors).
- **Schema:** Generates `lvl0`...`lvl6` hierarchy expected by Docusaurus.
- **Languages:** Sets `indexLanguages: ['en', 'uk']` to properly tokenized Cyrillic content.
- **Metadata:** Automatically extracts `docusaurus_tag` and `lang` for `contextualSearch`.

## Troubleshooting

### Search returns no results?
- **Check `docusaurus_tag`**: The crawler must extract this meta tag. The provided config does this automatically via `helpers.docsearch`.
- **Check Facets**: Ensure `contextualSearch: true` is enabled in `docusaurus.config.ts`.
- **Check Index Name**: Must match exactly between `docusaurus.config.ts` and the Crawler.

### "Record too big" errors?
- The custom `recordExtractor` in `algolia-crawler.js` uses `aggregateContent: true` and `helpers.docsearch` to manage record sizes. If errors persist, check for single paragraphs >10KB.

---

## Legacy: Local Search

*Deprecated. See git history for setup.*