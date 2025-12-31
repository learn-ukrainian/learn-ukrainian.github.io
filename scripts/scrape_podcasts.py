#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
import re
import argparse

# Configuration
BASE_URL = "https://www.ukrainianlessons.com/episode{}/"
OUTPUT_DIR = "docs/resources/podcasts"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
JSON_OUTPUT = os.path.join(OUTPUT_DIR, "podcast_scraped.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,uk;q=0.8",
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

def setup_dirs():
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

def fetch_episode(episode_num):
    url = BASE_URL.format(episode_num)
    print(f"Fetching Episode {episode_num}: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text, url
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching episode {episode_num}: {e}")
        return None, url

def save_raw_html(episode_num, html_content):
    filename = os.path.join(RAW_DIR, f"episode_{episode_num:03d}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    # print(f"Saved raw HTML to {filename}")

def parse_episode(episode_num, html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Title extraction
    title_elem = soup.select_one('h1.elementor-heading-title')
    if not title_elem:
        # Fallback for some pages
        title_elem = soup.select_one('h1')
    
    title = title_elem.get_text(strip=True) if title_elem else f"Episode {episode_num}"
    
    # 2. Season/Episode parsing from Title (e.g., "ULP 2-80 | ...")
    season = 1
    ep_in_season = episode_num
    
    # Regex to find "ULP X-YY"
    match = re.search(r'ULP\s+(\d+)-(\d+)', title)
    if match:
        season = int(match.group(1))
        ep_in_season = int(match.group(2))
        # clean title
        title = re.sub(r'^ULP\s+\d+-\d+\s+\|\s+', '', title).strip()
    else:
        # Season 1 often just has "ULP 1-01" or starts without ULP
        match_s1 = re.search(r'ULP\s+1-(\d+)', title)
        if match_s1:
             season = 1
             ep_in_season = int(match_s1.group(1))
             title = re.sub(r'^ULP\s+1-\d+\s+\|\s+', '', title).strip()

    # 3. Summary extraction
    # The summary is usually in the first text block of the elementor content
    summary = ""
    content_div = soup.select_one('div.elementor-widget-theme-post-content')
    if content_div:
        # Get first paragraph that isn't empty
        paragraphs = content_div.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 30: # arbitrary filter for "real" content
                summary = text
                break
    
    if not summary:
        meta_desc = soup.find('meta', property='og:description')
        if meta_desc:
            summary = meta_desc.get('content')

    # 4. Audio URL extraction
    audio_url = ""
    audio_elem = soup.find('audio')
    if audio_elem:
        src = audio_elem.get('src')
        if src:
            audio_url = src
    
    if not audio_url:
        # Try finding links to mp3s
        mp3_link = soup.find('a', href=re.compile(r'\.mp3$'))
        if mp3_link:
            audio_url = mp3_link.get('href')

    # 5. Tags (Placeholder - hard to extract reliably without NLP or specific markup)
    tags = ["Podcast", "Season " + str(season)]
    
    # Construct Entry
    entry = {
        "id": f"ULP-{episode_num:03d}",
        "season": season,
        "episode_number": ep_in_season,
        "title": title,
        "url": url,
        "summary": summary,
        "tags": tags,
        "audio_url": audio_url,
        "transcript_available": "transcript" in soup.get_text().lower() or "notes" in soup.get_text().lower()
    }
    
    return entry

def main():
    parser = argparse.ArgumentParser(description="Scrape Ukrainian Lessons Podcast episodes")
    parser.add_argument("--start", type=int, default=1, help="Start episode number")
    parser.add_argument("--end", type=int, default=5, help="End episode number")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay between requests in seconds")
    args = parser.parse_args()

    setup_dirs()
    
    results = []
    
    print(f"🚀 Starting scrape for episodes {args.start} to {args.end}...")
    
    for i in range(args.start, args.end + 1):
        html, url = fetch_episode(i)
        if html:
            save_raw_html(i, html)
            entry = parse_episode(i, html, url)
            results.append(entry)
            print(f"✅ Parsed: {entry['id']} - {entry['title'][:50]}...")
        
        # Be polite
        time.sleep(args.delay + random.uniform(0.1, 0.5))

    # Save Results
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Scrape complete! Saved {len(results)} episodes to {JSON_OUTPUT}")

if __name__ == "__main__":
    main()
