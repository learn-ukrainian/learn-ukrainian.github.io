# Search Setup Guide

This project uses **Algolia DocSearch** with multi-language support (English + Ukrainian).

## Why Algolia DocSearch?

**Algolia DocSearch** provides:
- ✅ **Multi-language support** - Excellent for Ukrainian + English content (Cyrillic indexing)
- ✅ **Advanced typo tolerance** - Helps learners with Ukrainian spelling
- ✅ **Fast cloud-based search** - Better performance than client-side search
- ✅ **Free for open-source projects** - No cost for public documentation
- ✅ **Professional search experience** - Used by React, Vue, Bootstrap, etc.

## Setup Instructions

This site is configured for Algolia DocSearch. To activate search:

### Step 1: Apply for Algolia DocSearch (Free for Open Source)

**Recommended:** Apply for the free DocSearch program instead of manual setup.

1. Go to: https://docsearch.algolia.com/apply/
2. Fill out the form:
   - **Website URL:** `https://learn-ukrainian.github.io`
   - **Email:** Your maintainer email
   - **Repository:** `https://github.com/learn-ukrainian/learn-ukrainian.github.io`
   - **Description:** "Ukrainian language learning curriculum with 600+ modules in English and Ukrainian (Cyrillic)"
3. Submit and wait for approval (usually 1-2 weeks)
4. Algolia will provide you with:
   - Application ID
   - Search API Key
   - Index Name
   - Crawler setup (they handle it!)

### Step 2: Update Configuration

Once approved, update `docusaurus.config.ts` (lines 167-169):

```typescript
algolia: {
  appId: 'YOUR_APP_ID',        // Replace with your App ID
  apiKey: 'YOUR_SEARCH_API_KEY', // Replace with your Search-Only API Key
  indexName: 'learn-ukrainian',  // Use the index name provided
  // ... rest stays the same
}
```

**Important:** Only update the credentials. Keep the existing `searchParameters` config for Ukrainian language support!

### Step 3: Verify Search Functionality

Build and serve the site locally to test:

```bash
npm run build
npm run serve
```

Test with these queries:
- **English:** "dative case", "aspect", "future tense"
- **Ukrainian:** "дієслово", "відмінок", "дативний", "майбутній час"
- **Typos:** Should still work with Algolia's typo tolerance

### Alternative: Manual Setup (Not Recommended)

If you need to set up Algolia manually (without DocSearch program):

1. Create an Algolia account at https://www.algolia.com/
2. Get your App ID and Admin API Key from dashboard
3. Use the provided `algolia-crawler-config.json` to set up indexing
4. Run crawler manually or via GitHub Actions

**Note:** The free DocSearch program is much easier and includes automatic weekly re-indexing.

## Multi-Language Search Configuration

The site is configured for **English + Ukrainian** search:

**In `docusaurus.config.ts`:**
```typescript
searchParameters: {
  facetFilters: [
    ['language:en', 'language:uk'], // Search both languages
  ],
}
```

**In `algolia-crawler-config.json`:**
```json
"indexLanguages": ["en", "uk"],
"queryLanguages": ["en", "uk"]
```

This ensures Cyrillic characters are properly indexed and searchable.

## Troubleshooting

**Search not working after deployment?**
1. Verify API keys are correct in `docusaurus.config.ts`
2. Check that Algolia crawler has run and indexed your site
3. Ensure `algolia-crawler-config.json` is properly configured
4. Check browser console for API errors

**Ukrainian content not searchable?**
1. Verify `indexLanguages: ["en", "uk"]` in crawler config
2. Re-run the Algolia crawler to re-index with language support
3. Test with simple Ukrainian words first: "і", "на", "в"

## Current Status

- ✅ Algolia DocSearch configured in `docusaurus.config.ts`
- ✅ Ukrainian language support enabled
- ✅ Crawler config ready (`algolia-crawler-config.json`)
- ⏳ **Waiting for Algolia API keys** - Apply at https://docsearch.algolia.com/apply/

Once API keys are obtained, replace `YOUR_APP_ID` and `YOUR_SEARCH_API_KEY` in the config.
