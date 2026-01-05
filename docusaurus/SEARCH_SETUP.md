# Search Setup Guide

This project supports two search solutions: **Local Search** (active) and **Algolia DocSearch** (configured but inactive).

## 1. Local Search (Active)

We have implemented `@easyops-cn/docusaurus-search-local` as the default search engine.

*   **Pros:** Works out-of-the-box, no API keys required, works offline, zero cost.
*   **Cons:** Increases build size slightly, search happens in-browser (lunr.js).
*   **Configuration:** See `themes` section in `docusaurus.config.ts`.

## 2. Algolia DocSearch (Optional)

If you prefer Algolia (better for very large sites), follow these steps to switch:

### Step 1: Get API Keys
1.  Sign up at [Algolia](https://www.algolia.com/).
2.  Create a new Application.
3.  Go to **Settings > API Keys**.
4.  Copy your **Application ID** and **Search-Only API Key**.

### Step 2: Update Configuration
1.  Open `docusaurus.config.ts`.
2.  **Remove** the `themes` block containing `@easyops-cn/docusaurus-search-local`.
3.  **Uncomment** the `algolia` block in `themeConfig`.
4.  Replace `YOUR_APP_ID` and `YOUR_SEARCH_API_KEY` with your actual keys.

### Step 3: Run the Crawler
You need to populate the Algolia index. You can do this via GitHub Actions or Docker.

**Using Docker:**
1.  Get your **Admin API Key** from Algolia Dashboard.
2.  Run the crawler using the config file provided in this repo:

```bash
docker run -it --env-file=.env -e "APPLICATION_ID=YOUR_APP_ID" -e "API_KEY=YOUR_ADMIN_API_KEY" -e "CONFIG=$(cat algolia-crawler-config.json | jq -r tostring)" algolia/docsearch-scraper
```

(Note: You'll need `jq` installed or pass the JSON content directly).

### Step 4: Verify
Build and serve the site locally to test the search bar:
```bash
npm run build
npm run serve
```
