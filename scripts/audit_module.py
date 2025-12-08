import re
import sys
import os

def clean_text(text):
    """
    removes content that should not be counted:
    - Tables
    - Metadata/Callouts
    - Images
    - HTML comments
    - Headers
    """
    # 1. Remove Tables (lines starting with vertical bar)
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)
    
    # 2. Remove Blockquote Metadata (e.g. > [!answer], > [!options])
    # allow > 💡 (Engagement) 
    # We want to remove lines that start with > [!...
    text = re.sub(r'^\s*>\s*\[!.*$', '', text, flags=re.MULTILINE)

    # 3. Remove Images / Links with no text
    # Remove markdown images ![alt](src)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # 4. Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # 5. Remove YAML frontmatter if somehow passed (though we handle it separately)
    
    # 6. Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)

    # 7. Remove empty blockquote markers (just >) leftover
    # text = re.sub(r'^\s*>\s*$', '', text, flags=re.MULTILINE)

    return text

def audit_module(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 1. Meta Data Extraction ---
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        print("Error: No YAML frontmatter found.")
        return

    frontmatter_str = match.group(1)
    body = match.group(2)

    # Simple parsing of frontmatter for Phase/Pedagogy keys
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else "A1"
    
    # Determine Pedagogy (default to PPP for A1/A2, TTT for B1+, Narrative if explicitly stated)
    pedagogy = "PPP" # Default
    if "Narrative" in content or "Story" in content:
        # Weak check, but usually explicit in frontmatter tags if we parsed them fully. 
        # For now, let's infer from sections.
        pass

    # Targets based on Phase prefix
    level_targets = {
        'A1': 750,
        'A2': 1000,
        'B1': 1250,
        'B2': 1500,
        'C1': 1750,
        'C2': 2000
    }
    
    target_code = phase.split('.')[0] # e.g. A1.1 -> A1
    target = level_targets.get(target_code, 750)

    # --- 2. Section Parsing ---
    # Split by H2
    sections = re.split(r'\n##\s+(.*?)\n', body)
    
    section_map = {}
    if sections[0].strip():
        section_map['Intro/Narrative'] = sections[0]
        
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        text = sections[i+1]
        section_map[title] = text

    # --- 3. Filtering Logic ---
    # Core Keywords (case insensitive partial match)
    core_keywords = [
        "warm-up", "warm up", 
        "presentation", 
        "introduction", 
        "narrative", 
        "context", 
        "diagnostic", 
        "analysis", 
        "deep dive", 
        "cultural", "culture",
        "story",
        "part 1", "part 2", "part 3", 
        "dialogue"
    ]
    
    # Activity Keywords
    activity_keywords = [
        "match-up", "gap-fill", "quiz", "true-false", "group-sort", 
        "unjumble", "select", "transform", "fill-in", "error-correction",
        "anagram"
    ]

    exclude_keywords = [
        "activities", "activity", "practice", "production", "summary", "vocabulary", "check", "drill", "exercise"
    ]
    
    report_lines = []
    report_lines.append(f"# Audit Report: {os.path.basename(file_path)}")
    report_lines.append(f"**Phase:** {phase} | **Target:** {target} words")
    
    total_words = 0
    activity_count = 0
    
    # regex for new metrics
    # Engagement: > 💡, > ⚡, > 🎬, > 🎭, > 🔗
    # Engagement: > 💡, ⚡, 🎬, 🎭, 🔗, 🌍, 🎁, 🗣️, 🏠, 🧭, 🚌, 🚇, 🎟️, 📱, 🕵️, 🌤️, 🌦️, 🎱, 🔮, 🇺🇦, 🕰️, ❓, 🛠️, 💂, 🥪, 🍺, 🛍️, 🏫, 🏥, 💊, 👵, 🔬, 🎨, 🔄, 📅, 🍃, ❄️, 🚂, ⏳, 📚, 🍲, 🥣, 🥗, 🥙, 🥚, 🥛
    engagement_pattern = re.compile(r'>\s*[💡⚡🎬🎭🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛]')
    engagement_count = len(engagement_pattern.findall(content))
    
    # Audio: [🔊](audio_...)
    audio_pattern = re.compile(r'\[🔊\]\(audio_.*?\)')
    audio_count = len(audio_pattern.findall(content))
    
    # IPA: /.../ inside a table row (roughly)
    # strict IPA regex is hard, but looking for slashes in a table line is a good proxy for our format
    ipa_pattern = re.compile(r'\|.*/.*?/.*\|') 
    ipa_count = len(ipa_pattern.findall(content))
    
    # Model Answers: > [!answer]
    model_answer_pattern = re.compile(r'>\s*\[!answer\]')
    model_answer_count = len(model_answer_pattern.findall(content))

    # Create Activity Typology Set
    found_activity_types = set()
    for title in section_map.keys():
        title_lower = title.lower()
        for act_kw in activity_keywords:
            if act_kw in title_lower:
                found_activity_types.add(act_kw)
                
    # New Metrics Logic
    
    # 7. Dialogue Blocks (Speaker names in bold: **Name:**)
    dialogue_pattern = re.compile(r'\*\*(.*?):\*\*')
    dialogue_matches = dialogue_pattern.findall(content)
    # Heuristic: count distinct speakers or lines? Let's count lines.
    dialogue_line_count = len(dialogue_matches)
    
    # 8. Vocabulary Count
    # Find table after # Vocabulary
    vocab_section = re.search(r'# Vocabulary.*?\n((?:\|.*\|\n)+)', content, re.DOTALL)
    vocab_count = 0
    if vocab_section:
        table_content = vocab_section.group(1)
        # Count non-header rows
        vocab_rows = table_content.strip().split('\n')
        # subtract header and separator
        vocab_count = max(0, len(vocab_rows) - 2)
        
    # 9. Structure Check
    has_summary = re.search(r'# Summary', content) is not None
    has_objectives = 'objectives:' in frontmatter_str

    # --- 0. Pedagogy Check (PPP for A1) ---
    # Guidelines: A1/A2 must have Warm-up -> Presentation -> Practice -> Production
    has_warmup = re.search(r'## warm-up', content, re.IGNORECASE) is not None
    has_presentation = re.search(r'## presentation', content, re.IGNORECASE) is not None
    has_practice = re.search(r'## practice', content, re.IGNORECASE) is not None
    has_production = re.search(r'## production', content, re.IGNORECASE) is not None
    
    ppp_missing = []
    if not has_warmup: ppp_missing.append("warm-up")
    if not has_presentation: ppp_missing.append("presentation")
    if not has_practice: ppp_missing.append("practice")
    if not has_production: ppp_missing.append("production")

    # --- Helper: Item Density Counter ---
    def count_items(text):
        # 1. Numbered Lists (1. Question)
        numbered = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
        
        # 2. Table Rows (Match-up)
        table_lines = re.findall(r'^\s*\|.*\|', text, re.MULTILINE)
        # simplistic table count: subtract 2 for header/separator if > 2
        table_count = max(0, len(table_lines) - 2) if len(table_lines) > 2 else 0
        
        # 3. Checkboxes (True/False, Group Sort)
        checkboxes = len(re.findall(r'^\s*-\s*\[', text, re.MULTILINE))
        
        # 4. Bullets (Group Sort source list sometimes)
        bullets = len(re.findall(r'^\s*-\s+[^\[]', text, re.MULTILINE))
        
        return max(numbered, table_count, checkboxes, bullets)

    print(f"\nAuditing {file_path} (Target: {target})...\n")
    # --- 13. Immersion Calculator ---
    def calculate_immersion(text):
        if not text:
            return 0.0
        
        # Remove whitespace to get pure content density
        clean_text = re.sub(r'\s+', '', text)
        if not clean_text:
            return 0.0
            
        total_chars = len(clean_text)
        # Count Cyrillic characters (Unicode range U+0400 to U+04FF)
        cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', clean_text))
        
        return (cyrillic_chars / total_chars) * 100

    # Initialize core_text for immersion calculation
    core_text_for_immersion = ""
    
    table_rows = []
    
    # Store activity densities for gate check
    valid_density_count = 0
    total_activities = 0
    
    # Example Sentence Counter
    example_sentence_count = 0
    # Cyrillic regex
    cyrillic_pattern = re.compile(r'[а-яА-ЯґҐєЄіІїЇ]')

    for title, text in section_map.items():
        title_lower = title.lower()
        
        is_core = False
        is_excluded = False
        is_activity = False
        
        # Check Activity First
        for act in activity_keywords:
            if act in title_lower:
                is_activity = True
                break
        
        if not is_activity:
            for exc in exclude_keywords:
                if exc in title_lower:
                    is_excluded = True
                    break
            
            if not is_excluded:
                for core in core_keywords:
                    if core in title_lower:
                        is_core = True
                        break
                if title == 'Intro/Narrative':
                    is_core = True
        
        # Count Items & Examples
        cleaned = clean_text(text)
        lines = text.split('\n')
        
        if is_core and not is_excluded:
            # Count examples in Core sections
            # Strategy: bullet points or blockquotes containing Cyrillic
            for line in lines:
                line = line.strip()
                if (line.startswith('-') or line.startswith('>') or line.startswith('*')) and cyrillic_pattern.search(line):
                    # Filter out simple words (must be sentence-like, say > 3 words)
                    if len(line.split()) > 3:
                        example_sentence_count += 1
            
            # Accumulate text for immersion calc
            core_text_for_immersion += cleaned + " "

        words = cleaned.split()
        count = len(words)
        
        status_icon = "⚪️"
        note = "Skipped"

        if is_activity:
            activity_count += 1
            total_activities += 1
            
            # Density Check
            items = count_items(text)
            density_target = 12
            
            if items >= density_target:
                valid_density_count += 1
                density_icon = "✅"
            else:
                density_icon = "⚠️"
                
            status_icon = "🎮"
            note = f"Activity ({items} items)"
        elif is_core and not is_excluded:
            total_words += count
            status_icon = "✅"
            note = "Included in Core"
        elif is_excluded:
            status_icon = "➖"
            note = "Excluded Type"
        else:
            status_icon = "❓"
            note = "Not matched"

        table_rows.append(f"| **{title}** | {status_icon} | {count} | {note} |")
        print(f"{status_icon} {title}: {count} words ({note})")

    # --- 4. Result Gates ---
    
    results = {}
    
    # 1. Word Count Gate
    diff = total_words - target
    if diff >= 0:
        results['words'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{total_words}/{target}"}
    else:
        results['words'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{total_words}/{target} ({diff})"}

    # 2. Activity Count Gate (Target 8 for A1)
    activity_target = 8
    if activity_count >= activity_target:
        results['activities'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{activity_count}/{activity_target}"}
    else:
        results['activities'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{activity_count}/{activity_target}"}

    # 3. Density Gate
    # All activities must meet density? Or percentage? Guidelines say "Activity Density: 12+ items".
    # Let's count how many failed.
    failed_density = total_activities - valid_density_count
    if failed_density == 0 and total_activities > 0:
        results['density'] = {'status': 'PASS', 'icon': '✅', 'msg': "All activities > 12 items"}
    else:
        results['density'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{failed_density} activities too short"}

    # 4. Engagement Gate (Target 3 for A1)
    eng_target = 3
    if engagement_count >= eng_target:
        results['engagement'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{engagement_count}/{eng_target}"}
    else:
        results['engagement'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{engagement_count}/{eng_target}"}
        
    # 5. Audio Gate
    if audio_count > 0:
        results['audio'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{audio_count} links"}
    else:
        results['audio'] = {'status': 'FAIL', 'icon': '❌', 'msg': "No audio links found"}

    # 6. IPA Gate
    if ipa_count > 0:
        results['ipa'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{ipa_count} valid rows"}
    else:
        results['ipa'] = {'status': 'FAIL', 'icon': '❌', 'msg': "No IPA found"}
        
    # 7. Dialogue Gate
    if dialogue_line_count >= 2:
        results['dialogue'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{dialogue_line_count} lines"}
    else:
        results['dialogue'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{dialogue_line_count} lines (Target: 2+)"}
        
    # 8. Vocabulary Gate
    if vocab_count >= 15:
        results['vocab'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{vocab_count} words"}
    else:
        results['vocab'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{vocab_count} words (Target: 15+)"}
        
    # 9. Activity Types Gate
    mandatory_types = {'fill-in', 'match-up', 'anagram', 'unjumble', 'quiz'}
    missing_types = mandatory_types - found_activity_types
    if not missing_types:
        results['types'] = {'status': 'PASS', 'icon': '✅', 'msg': "All mandatory types present"}
    else:
        results['types'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"Missing: {', '.join(missing_types)}"}
        
    # 10. Structure Gate
    if has_summary and has_objectives:
        results['structure'] = {'status': 'PASS', 'icon': '✅', 'msg': "Complete"}
    else:
        missing = []
        if not has_summary: missing.append("Summary")
        if not has_objectives: missing.append("Objectives")
        results['structure'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"Missing: {', '.join(missing)}"}

    # 11. Pedagogy Gate (PPP)
    if not ppp_missing:
        results['pedagogy'] = {'status': 'PASS', 'icon': '✅', 'msg': "PPP Structure Valid"}
    else:
        results['pedagogy'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"Missing sections: {', '.join(ppp_missing)}"}

    # 12. Example Sentence Gate (Target 12+)
    if example_sentence_count >= 12:
        results['examples'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{example_sentence_count} sentences"}
    else:
        results['examples'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{example_sentence_count} sentences (Target: 12+)"}

    # 13. Immersion Score
    immersion_score = calculate_immersion(core_text_for_immersion)
    results['immersion'] = {'status': 'INFO', 'icon': '🇺🇦', 'msg': f"{immersion_score:.1f}% Cyrillic"}

    # Console Output
    print(f"\n--- GATES ---")
    print(f"Words:      {results['words']['icon']} {results['words']['msg']}")
    print(f"Activities: {results['activities']['icon']} {results['activities']['msg']}")
    print(f"Density:    {results['density']['icon']} {results['density']['msg']}")
    print(f"Pedagogy:   {results['pedagogy']['icon']} {results['pedagogy']['msg']}")
    print(f"Examples:   {results['examples']['icon']} {results['examples']['msg']}")
    print(f"Engagement: {results['engagement']['icon']} {results['engagement']['msg']}")
    print(f"Audio:      {results['audio']['icon']} {results['audio']['msg']}")
    print(f"IPA:        {results['ipa']['icon']} {results['ipa']['msg']}")
    print(f"Dialogue:   {results['dialogue']['icon']} {results['dialogue']['msg']}")
    print(f"Vocab:      {results['vocab']['icon']} {results['vocab']['msg']}")
    print(f"Types:      {results['types']['icon']} {results['types']['msg']}")
    print(f"Structure:  {results['structure']['icon']} {results['structure']['msg']}")
    print(f"Immersion:  {results['immersion']['icon']} {results['immersion']['msg']}")
    
    # Overall Status
    failures = [k for k, v in results.items() if v['status'] == 'FAIL']
    if len(failures) == 0:
        overall_status = "✅ PASS"
    else:
        overall_status = f"❌ FAIL ({len(failures)} gates)"
    
    # Update Status Line
    report_lines.append(f"**Overall Status:** {overall_status}")
    report_lines.append("")
    report_lines.append("## Gates")
    report_lines.append(f"- **Word Count:** {results['words']['icon']} {results['words']['msg']}")
    report_lines.append(f"- **Activities:** {results['activities']['icon']} {results['activities']['msg']}")
    report_lines.append(f"- **Density:** {results['density']['icon']} {results['density']['msg']}")
    report_lines.append(f"- **Pedagogy (PPP):** {results['pedagogy']['icon']} {results['pedagogy']['msg']}")
    report_lines.append(f"- **Examples:** {results['examples']['icon']} {results['examples']['msg']}")
    report_lines.append(f"- **Engagement:** {results['engagement']['icon']} {results['engagement']['msg']}")
    report_lines.append(f"- **Audio:** {results['audio']['icon']} {results['audio']['msg']}")
    report_lines.append(f"- **IPA:** {results['ipa']['icon']} {results['ipa']['msg']}")
    report_lines.append(f"- **Dialogue:** {results['dialogue']['icon']} {results['dialogue']['msg']}")
    report_lines.append(f"- **Vocabulary:** {results['vocab']['icon']} {results['vocab']['msg']}")
    report_lines.append(f"- **Mandatory Types:** {results['types']['icon']} {results['types']['msg']}")
    report_lines.append(f"- **Structure:** {results['structure']['icon']} {results['structure']['msg']}")
    report_lines.append(f"- **Immersion:** {results['immersion']['icon']} {results['immersion']['msg']}")

    report_lines.append(f"- **Model Answers:** {model_answer_count} (Info)")
    
    report_lines.append("")
    report_lines.append("## Section Breakdown\n")
    report_lines.append("| Section | Status | Words | Notes |")
    report_lines.append("|---|---|---|---|")
    report_lines.extend(table_rows)

    
    # Write report
    # Write report
    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    
    # Target directory: .../{level}/gemini/
    # If already in gemini, stay there. If not, go into gemini.
    if not file_dir.endswith('gemini'):
        target_dir = os.path.join(file_dir, 'gemini')
    else:
        target_dir = file_dir
        
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {target_dir}: {e}")
            return

    report_path = os.path.join(target_dir, f"{base_name}.audit.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"\nReport written to: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/audit_module.py <file.md>")
    else:
        audit_module(sys.argv[1])
