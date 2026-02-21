import json
import re
import os

RAW_DIR = "docs/resources/podcasts/raw_lists"
OUTPUT_FILE = "docs/resources/podcasts/podcast_db.json"

def parse_line(line):
    # Pattern: Season: X, Title: TITLE, URL: URL
    # or Episode: X, Title: TITLE, URL: URL (for FMU)
    
    # Check for FMU format first
    fmu_match = re.match(r'Episode:\s*(\d+),\s*Title:\s*(.+?),\s*URL:\s*(.+)', line)
    if fmu_match:
        episode_num = int(fmu_match.group(1))
        title = fmu_match.group(2).strip()
        url = fmu_match.group(3).strip()
        
        # Clean ID from title if present (e.g. FMU 1-01 ...)
        id_match = re.match(r'(FMU\s*\d+-\d+)\s*\|?\s*(.+)', title)
        if id_match:
            # We construct a clean ID based on episode number
            title = id_match.group(2).strip()
            
        return {
            "id": f"FMU-{episode_num:03d}",
            "season": 1,
            "episode_number": episode_num,
            "title": title,
            "url": url,
            "summary": "",
            "tags": ["FMU", "Season 1"]
        }

    # Check for ULP format
    ulp_match = re.match(r'Season:\s*(\d+),\s*Title:\s*(.+?),\s*URL:\s*(.+)', line)
    if ulp_match:
        season = int(ulp_match.group(1))
        title = ulp_match.group(2).strip()
        url = ulp_match.group(3).strip()
        
        # Try to extract episode number from ULP X-YY
        ep_match = re.search(r'ULP\s+\d+-(\d+)', title)
        if ep_match:
            episode_num = int(ep_match.group(1))
            # Clean title
            title = re.sub(r'^ULP\s+\d+-\d+\s*[|–-]\s*', '', title).strip()
        else:
            # Fallback if title doesn't have ULP prefix
            # Try to extract from URL
            url_ep_match = re.search(r'/lesson/(\d+)/', url)
            if url_ep_match:
                episode_num = int(url_ep_match.group(1))
            else:
                print(f"⚠ Could not determine episode number for: {line}")
                return None

        return {
            "id": f"ULP-{episode_num:03d}",
            "season": season,
            "episode_number": episode_num,
            "title": title,
            "url": url,
            "summary": "",
            "tags": ["ULP", f"Season {season}"]
        }
        
    return None

def main():
    all_episodes = []
    
    if not os.path.exists(RAW_DIR):
        print(f"❌ Directory not found: {RAW_DIR}")
        return

    for filename in sorted(os.listdir(RAW_DIR)):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(RAW_DIR, filename)
        print(f"Processing {filepath}...")
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                entry = parse_line(line)
                if entry:
                    all_episodes.append(entry)
                else:
                    print(f"⚠ Failed to parse line: {line}")

    # Deduplicate by ID
    unique_episodes = {}
    for ep in all_episodes:
        unique_episodes[ep['id']] = ep
        
    sorted_episodes = sorted(unique_episodes.values(), key=lambda x: x['id'])
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_episodes, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Saved {len(sorted_episodes)} episodes to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
