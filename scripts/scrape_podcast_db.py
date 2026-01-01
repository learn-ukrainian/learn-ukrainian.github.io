#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

# Configuration
SEASON_URLS = [
    ("https://www.ukrainianlessons.com/season1/", 1),
    ("https://www.ukrainianlessons.com/season2/", 2),
    ("https://www.ukrainianlessons.com/season3/", 3),
    ("https://www.ukrainianlessons.com/season4/", 4),
    ("https://www.ukrainianlessons.com/season5/", 5),
    ("https://www.ukrainianlessons.com/season6/", 6),
    ("https://www.ukrainianlessons.com/fmu/", "FMU"),
]
OUTPUT_FILE = "docs/resources/podcasts/podcast_db.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def fetch_url(url):
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def parse_season_page(html, season_id):
    soup = BeautifulSoup(html, 'html.parser')
    episodes = []
    
    # WordPress/Elementor archives often list posts in <article> or divs with specific classes
    # We look for links that match the pattern /episodeX/ or /fmuX/
    
    links = soup.find_all('a', href=True)
    seen_urls = set()
    
    for link in links:
        url = link['href']
        title = link.get_text(strip=True)
        
        # Filter for episode URLs
        is_episode = False
        episode_num = 0
        series = "ULP"
        
        # Check patterns
        ulp_match = re.search(r'/episode(\d+)/?$', url)
        fmu_match = re.search(r'/fmu(\d+)/?$', url)
        
        if ulp_match:
            is_episode = True
            episode_num = int(ulp_match.group(1))
            series = "ULP"
        elif fmu_match:
            is_episode = True
            episode_num = int(fmu_match.group(1))
            series = "FMU"
            
        if is_episode and url not in seen_urls and len(title) > 5:
            seen_urls.add(url)
            
            # Clean title
            clean_title = title
            # Remove "ULP X-XX | " prefix
            clean_title = re.sub(r'^(ULP|FMU)\s+\d+-\d+\s*[|–-]\s*', '', clean_title)
            clean_title = re.sub(r'Episode \d+\s*[|–-]\s*', '', clean_title)
            
            # Construct ID
            id_str = f"{series}-{episode_num:03d}"
            
            episodes.append({
                "id": id_str,
                "season": season_id if season_id != "FMU" else 1,
                "episode_number": episode_num,
                "title": clean_title,
                "url": url,
                "summary": "", # Summary hard to get from simple link list
                "tags": [series, f"Season {season_id}" if season_id != "FMU" else "FMU"]
            })
            
    return episodes

def main():
    all_episodes = []
    
    print("🚀 Starting Catalog Scrape...")
    
    for url, season_id in SEASON_URLS:
        html = fetch_url(url)
        if html:
            episodes = parse_season_page(html, season_id)
            print(f"✅ Found {len(episodes)} episodes in Season {season_id}")
            all_episodes.extend(episodes)
        time.sleep(2) # Be polite
        
    # Sort by ID
    all_episodes.sort(key=lambda x: x['id'])
    
    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_episodes, f, indent=2, ensure_ascii=False)
        
    print(f"\n🎉 Saved {len(all_episodes)} episodes to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
