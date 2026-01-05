# Search Setup Guide

This project uses **Local Search** with multi-language support (English + Ukrainian).

## Current Implementation: Local Search

**Currently using:** `@easyops-cn/docusaurus-search-local`

**Configuration in `docusaurus.config.ts`:**
```typescript
themes: [
  [
    require.resolve("@easyops-cn/docusaurus-search-local"),
    {
      hashed: true,
      language: ["en"],  // Note: Ukrainian not supported by lunr-languages
      highlightSearchTermsOnTargetPage: true,
      explicitSearchResultPath: true,
    },
  ],
],
```

### Pros
- ✅ **No external dependencies** - Works offline, no API keys needed
- ✅ **Fast setup** - Already configured and working
- ✅ **Free** - No costs, no quotas

### Cons
- ❌ **NO Ukrainian language support** - lunr-languages doesn't support Ukrainian
- ⚠️ **English-only indexing** - 70% of content (B1-C2 immersed Ukrainian) not properly searchable
- ⚠️ **Client-side indexing** - Slower initial load for large sites
- ⚠️ **Limited typo tolerance** - Exact matches work better
- ⚠️ **Basic ranking** - Less sophisticated than cloud solutions

**CRITICAL LIMITATION:** Local search does NOT support Ukrainian because the underlying `lunr-languages` library doesn't include Ukrainian. This means immersed Ukrainian content (B1-C2, 70% of the curriculum) is indexed as generic text without proper stemming or language-aware search.

### Test Current Search
Build and serve locally:
```bash
npm run build
npm run serve
```

Test with queries:
- **English:** "dative case", "aspect", "future tense" ✅ Works well
- **Ukrainian:** "дієслово", "відмінок", "дативний" ⚠️ Basic matching only (no language-aware stemming)

---

## Future Enhancement: Algolia DocSearch

**Status:** 📋 Tracked in [Issue #392](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/392)

### Why Upgrade to Algolia?
- ✅ **Advanced typo tolerance** - Helps learners with Ukrainian spelling
- ✅ **Better ranking** - AI-powered relevance
- ✅ **Faster performance** - Cloud-based, no client-side indexing
- ✅ **Automatic re-indexing** - Managed by Algolia weekly
- ✅ **Free for open-source** - No cost for public documentation

### When to Implement
Consider switching to Algolia when:
1. User feedback indicates search quality issues
2. Site grows significantly (1000+ pages)
3. Search performance becomes a bottleneck
4. Time available to apply and wait for approval (1-2 weeks)

### How to Switch

**Step 1: Apply for Algolia DocSearch**
1. Go to: https://docsearch.algolia.com/apply/
2. Fill out form:
   - **Website URL:** `https://learn-ukrainian.github.io`
   - **Email:** Maintainer email
   - **Repository:** `https://github.com/learn-ukrainian/learn-ukrainian.github.io`
   - **Description:** "Ukrainian language learning curriculum with 600+ modules in English and Ukrainian (Cyrillic)"
3. Wait for approval (typically 1-2 weeks)

**Step 2: Update Configuration**
Once approved, update `docusaurus.config.ts`:

```typescript
// Remove local search theme
themes: [],

// Add to themeConfig:
themeConfig: {
  // ... existing config
  algolia: {
    appId: 'YOUR_APP_ID',        // From Algolia
    apiKey: 'YOUR_SEARCH_API_KEY', // From Algolia
    indexName: 'learn-ukrainian',  // From Algolia
    contextualSearch: true,
    searchParameters: {
      facetFilters: [
        ['language:en', 'language:uk'], // Search both languages
      ],
      hitsPerPage: 10,
    },
    searchPagePath: 'search',
  },
}
```

**Step 3: Update Crawler Config**
Algolia will use `algolia-crawler-config.json` (already prepared with Ukrainian support).

**Step 4: Uninstall Local Search**
```bash
npm uninstall @easyops-cn/docusaurus-search-local
```

---

## Comparison

| Feature                | Local Search              | Algolia DocSearch       |
|------------------------|---------------------------|-------------------------|
| **Setup Time**         | ✅ Immediate              | ⏳ 1-2 weeks (approval) |
| **Cost**               | ✅ Free                   | ✅ Free (open-source)   |
| **Ukrainian Support**  | ❌ No (not in lunr-languages) | ✅ Yes (full Cyrillic)  |
| **Typo Tolerance**     | ⚠️ Basic                 | ✅ Advanced             |
| **Performance**        | ⚠️ Client-side indexing   | ✅ Cloud-based          |
| **Maintenance**        | ✅ Zero                   | ✅ Managed by Algolia   |
| **Offline Work**       | ✅ Yes                    | ❌ Requires internet    |

---

## Current Status

- ✅ **Local Search** configured and working
- ❌ **Ukrainian language support** NOT available (lunr-languages limitation)
- ⚠️ **English-only indexing** - B1-C2 content (70% of curriculum) not properly searchable
- 📋 **Algolia migration** tracked in [Issue #392](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/392)

**Recommendation:**
- **Short-term:** Local search works for English content and basic Ukrainian text matching
- **Long-term:** **Strongly recommend migrating to Algolia** to properly index Ukrainian content with Cyrillic support
- **Priority:** Moderate - Local search provides basic functionality, but Ukrainian learners will have limited search capabilities for immersed content (B1-C2)
