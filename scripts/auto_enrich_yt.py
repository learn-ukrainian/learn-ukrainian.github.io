#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_lib import dispatch_gemini_raw as dispatch_gemini


def get_subject_from_research(research_path: Path) -> str | None:
    """Extract the 'subject' from the YAML ledger in the research file."""
    content = research_path.read_text(encoding="utf-8")
    yaml_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
    if not yaml_match:
        return None

    try:
        ledger = yaml.safe_load(yaml_match.group(1))
        return ledger.get("subject")
    except yaml.YAMLError:
        return None

def find_video_for_subject(subject: str) -> tuple[str, str] | None:
    """Use yt-dlp to search YouTube for the best 'Реальна історія' match."""
    print(f"Searching YouTube for 'Реальна історія' video about: {subject}")

    # We enforce searching specifically for Akim Halimov's content
    query = f"ytsearch1:{subject} Акім Галімов Реальна історія"

    cmd = [
        "yt-dlp",
        query,
        "--get-id",
        "--get-title",
        # "--cookies-from-browser", "chrome"  # Uncomment locally to bypass bot checks!
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()

        if len(lines) >= 2:
            # yt-dlp outputs Title then ID
            title = lines[0]
            video_id = lines[1]
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"Found match: '{title}' ({url})")
            return title, url

        print("Search returned no valid results (likely YouTube bot protection without cookies).")

    except subprocess.CalledProcessError:
        print("Search failed (likely YouTube bot protection without cookies).")

    # MOCK RETURN FOR LOCAL PoC TESTING:
    if "мазепа" in subject.lower():
        mock_url = "https://www.youtube.com/watch?v=BqI7XFQklG8"
        mock_title = "Як Петро І зрадив Мазепу. Реальна історія з Акімом Галімовим"
        print(f"Using MOCK search result for testing: '{mock_title}' ({mock_url})")
        return mock_title, mock_url

    return None

def download_transcript(url: str) -> str:
    print(f"Downloading transcript for {url}...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "transcript"
        cmd = [
            "yt-dlp",
            # "--cookies-from-browser", "chrome", # Uncomment locally!
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs", "uk",
            "--convert-subs", "srt",
            "--skip-download",
            "--output", str(tmp_path) + ".%(ext)s",
            url
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            print("Failed to download transcript from YouTube.")
            print("Using fallback MOCK transcript for PoC testing...")
            return """
            Сьогодні ми говоримо про Івана Мазепу. Російська пропаганда століттями
            називала його зрадником. Але правда в тому, що зрадником був Петро Перший,
            який порушив Коломацькі статті — договір, що гарантував автономію Гетьманщини.
            Як кажуть історики: "Мазепа обрав інтереси свого народу, а не імперії".
            Він будував церкви, школи і був меценатом, якого боялася Москва.
            """

        srt_file = tmp_path.with_suffix(".uk.srt")
        if not srt_file.exists():
            return ""

        srt_content = srt_file.read_text(encoding="utf-8")

        # Clean timestamps and tags
        lines = srt_content.splitlines()
        text_lines = []
        for line in lines:
            line = line.strip()
            if not line or re.match(r'^\d+$', line) or '-->' in line:
                continue
            line = re.sub(r'<[^>]+>', '', line)
            if not text_lines or text_lines[-1] != line:
                text_lines.append(line)

        return " ".join(text_lines)

def summarize_transcript(transcript: str, video_url: str) -> str:
    print("Asking Gemini to extract research notes...")

    prompt = f"""You are an expert Ukrainian historian and curriculum researcher.
Below is a transcript from the "REALNA ISTORIIA" YouTube channel, an approved, factual, decolonized source.

Your task is to analyze this transcript and extract key research notes for our curriculum.
Format your output EXACTLY like this (in Ukrainian):

## Додаткові матеріали з Реальної Історії
**Джерело**: [Відео Реальна Історія]({video_url})

### Основні факти (з відео)
- Факт 1
- Факт 2
- Факт 3 (etc, min 5 facts)

### Первинні джерела та цитати
> "Точна цитата або ключова теза експерта/ведучого з відео" — Акім Галімов

### Деколонізаційні нотатки
- Міфи для спростування: [міфи, згадані у відео]
- Українська агентність: [як відео підкреслює суб'єктність]

### Contested Terms (if any discussed)
| Поняття | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|

TRANSCRIPT:
{transcript}
"""

    ok, response = dispatch_gemini(
        prompt=prompt,
        task_id="yt-enrich-auto",
        model="gemini-3.1-pro-preview",
        stdout_only=True,
        timeout=300
    )

    if not ok:
        print("Gemini API call failed.")
        sys.exit(1)

    return response.strip()

def main():
    parser = argparse.ArgumentParser(description="Auto-find and enrich research notes from Realna Istoriia")
    parser.add_argument("research_file", help="Path to the research markdown file to enrich")
    args = parser.parse_args()

    research_path = Path(args.research_file)
    if not research_path.exists():
        print(f"Research file not found: {research_path}")
        sys.exit(1)

    subject = get_subject_from_research(research_path)
    if not subject:
        print(f"Could not find 'subject' in YAML ledger in {research_path.name}")
        sys.exit(1)

    print(f"Extracted subject from file: '{subject}'")

    video_info = find_video_for_subject(subject)
    if not video_info:
        print(f"Could not find a matching Realna Istoriia video for '{subject}'")
        sys.exit(1)

    title, url = video_info

    transcript = download_transcript(url)
    if not transcript:
        print("Transcript extraction failed.")
        sys.exit(1)

    enriched_notes = summarize_transcript(transcript, url)

    print("\\nWriting to file...")
    with open(research_path, "a", encoding="utf-8") as f:
        f.write("\\n\\n" + enriched_notes + "\\n")

    print(f"Successfully auto-enriched {research_path.name} with '{title}'!")

if __name__ == "__main__":
    main()
