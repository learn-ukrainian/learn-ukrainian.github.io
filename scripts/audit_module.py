import re
import sys
import os

def clean_for_stats(text):
    """
    Removes ONLY metadata that should NOT count towards richness.
    We KEEP Scaffolding (Context, Explanations) because they are part of the 'Instructional Core' for A1.
    """
    # 1. Remove Tables (lines starting with vertical bar) - Vocab lists don't count for core usually
    # But wait, Richness Guidelines say "Instructional Core" includes narrative.
    # Exclude metadata tables.
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)
    
    # 2. Remove ONLY specific metadata callouts, KEEPING content callouts
    # Remove > [!answer], > [!options]
    text = re.sub(r'^\s*>\s*\[!(answer|options|error|id)\].*$', '', text, flags=re.MULTILINE)

    # 3. Remove Images / Links with no text
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # 4. Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # 5. Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)
    
    # 6. Remove frontmatter dividers
    text = re.sub(r'^---', '', text, flags=re.MULTILINE)

    return text

def clean_for_immersion(text):
    """
    Aggressively strips ALL English scaffolding to check the 'Target Language' purity.
    """
    # Remove ALL Blockquotes (Headers + Content)
    # This ensures English translations, Tips, and Notes are excluded from Immersion Calculation
    text = re.sub(r'^\s*>.*$', '', text, flags=re.MULTILINE)
    
    # Remove Tables
    text = re.sub(r'^\s*\|.*$', '', text, flags=re.MULTILINE)
    
    # Remove Headers
    text = re.sub(r'^#+.*$', '', text, flags=re.MULTILINE)
    
    return text

def audit_module(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 1. Meta Data Extraction ---
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        print("Error: No YAML frontmatter found.")
        sys.exit(1)

    frontmatter_str = match.group(1)
    body = match.group(2)

    # --- Strict Metadata Validation ---
    required_metadata = [
        ('duration', r'duration:'),
        ('transliteration', r'transliteration:'),
        ('tags', r'tags:'),
        ('objectives', r'objectives:'),
        ('grammar', r'grammar:'),
        ('pedagogy', r'pedagogy:')
    ]
    
    missing_meta = []
    for key, pattern in required_metadata:
        if not re.search(pattern, frontmatter_str):
            missing_meta.append(key)
            
    if missing_meta:
        print(f"❌ AUDIT FAILED: Missing Frontmatter Fields: {', '.join(missing_meta)}")
        # We want to fail strict audit if these are missing, as generation differs
        # However, to avoid crashing the whole script for now, we will print big error
        # But actually, we should exit or mark failure.
        # Let's add it to a global failure flag if possible, or just exit.
        print("  -> These fields are REQUIRED for 'npm run generate'")
        sys.exit(1)

    # Parse Phase
    phase_match = re.search(r'phase:\s*([A-Za-z0-9\.]+)', frontmatter_str)
    phase = phase_match.group(1) if phase_match else "A1"
    
    # --- Level Configuration (Strict Enforcement) ---
    LEVEL_CONFIG = {
        'A1': {
            'target_words': 750,
            'min_activities': 8,
            'min_items_per_activity': 12,
            'min_types_unique': 4,
            'min_vocab': 20,
            'min_engagement': 3,
            'transliteration_allowed': True,
            'priority_types': {'fill-in', 'match-up', 'anagram', 'unjumble', 'quiz'}
        },
        'A2': {
            'target_words': 1000,
            'min_activities': 10,
            'min_items_per_activity': 12,
            'min_types_unique': 4,
            'min_vocab': 25,
            'min_engagement': 4,
            'transliteration_allowed': False,
            'priority_types': {'error-correction', 'unjumble', 'fill-in'}
        },
        'B1': {
            'target_words': 1250,
            'min_activities': 12,
            'min_items_per_activity': 14,
            'min_types_unique': 4,
            'min_vocab': 30,
            'min_engagement': 5,
            'transliteration_allowed': False,
            'priority_types': {'fill-in', 'unjumble', 'error-correction'}
        },
        'B2': {
            'target_words': 1500,
            'min_activities': 14,
            'min_items_per_activity': 16,
            'min_types_unique': 4,
            'min_vocab': 25,
            'min_engagement': 6,
            'transliteration_allowed': False,
            'priority_types': {'fill-in', 'unjumble', 'error-correction'}
        },
        'C1': {
            'target_words': 1750,
            'min_activities': 16,
            'min_items_per_activity': 18,
            'min_types_unique': 4,
            'min_vocab': 25,
            'min_engagement': 7,
            'transliteration_allowed': False,
            'priority_types': {'fill-in', 'unjumble', 'error-correction'}
        },
        'C2': {
            'target_words': 2000,
            'min_activities': 16,
            'min_items_per_activity': 18,
            'min_types_unique': 4,
            'min_vocab': 25,
            'min_engagement': 8,
            'transliteration_allowed': False,
            'priority_types': {'fill-in', 'unjumble', 'error-correction'}
        }
    }
    
    # Detect level from file path (more reliable than phase)
    level_from_path = None
    path_match = re.search(r'/([ab][12c][12]?)/', file_path.lower())
    if path_match:
        level_from_path = path_match.group(1).upper()

    # Use path-detected level if available, else fall back to phase
    level_code = level_from_path if level_from_path else phase.split('.')[0]
    if level_code not in LEVEL_CONFIG:
        if level_code.endswith('+'):
             level_code = level_code[:-1]
        # Normalize C1/C2
        if level_code not in LEVEL_CONFIG:
            level_code = 'A1'  # fallback
    
    config = LEVEL_CONFIG.get(level_code, LEVEL_CONFIG['A1'])
    target = config['target_words']
    vocab_target = config.get('min_vocab', 25)
    transliteration_allowed = config.get('transliteration_allowed', True)

    # Extract Pedagogy (Regex fallback since PyYAML is missing)
    pedagogy = "Not Specified"
    pedagogy_match = re.search(r'^pedagogy:\s*(.+)$', frontmatter_str, re.MULTILINE)
    if pedagogy_match:
        pedagogy = pedagogy_match.group(1).strip()
    
    # ------------------------------------------------------------
    # 2. Section Parsing
    # ------------------------------------------------------------
    sections = re.split(r'\n##\s+(.*?)\n', body)
    
    section_map = {}
    if sections[0].strip():
        section_map['Intro/Narrative'] = sections[0]
        
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        text = sections[i+1]
        section_map[title] = text

    # --- 2b. Strict Content & Tone Validation (New Phase) ---
    
    # Tone: Sovereignty Check
    if re.search(r'\bThe\s+Ukraine\b', content, re.IGNORECASE):
        # Allow if it's being corrected (e.g. "not The Ukraine", "The Ukraine is incorrect")
        is_correction = re.search(r'(not|incorrect|offensive|never|avoid)\s+.*?\bThe\s+Ukraine\b', content, re.IGNORECASE) or \
                        re.search(r'\bThe\s+Ukraine\b.*?\s+(is\s+incorrect|is\s+offensive)', content, re.IGNORECASE)
        
        if not is_correction:
            print(f"❌ AUDIT FAILED: Tone Error. Found 'The Ukraine'. Use 'Ukraine' (sovereign nation).")
            sys.exit(1)
        
    if re.search(r'\bKiev\b', content) and not re.search(r'not\s+Kiev', content, re.IGNORECASE) and not re.search(r'Russian', content, re.IGNORECASE):
        # We allow 'Kiev' if it's in a 'not Kiev' or 'Russian' context (e.g. "Russian uses Kiev")
        print(f"❌ AUDIT FAILED: Tone Error. Found 'Kiev'. Use 'Kyiv' (Ukrainian transliteration).")
        sys.exit(1)

    # Summary Check
    has_summary = any(re.search(r'^#+\s*Summary', line, re.IGNORECASE) for line in content.split('\n'))
    if not has_summary:
        print(f"❌ AUDIT FAILED: Missing 'Summary' section.")
        print("  -> Every module must have a Summary section.")
        sys.exit(1)

    # Activity Structure: Fill-in Options & Numbering (Global Rule)
    # Open-ended fill-ins are too ambiguous for digital app. Explicit options are required.
    # ALSO: Parser strictly requires numbered lists (1. ...).
    for title, text in section_map.items():
        if title.lower().startswith('fill-in'):
            if '> [!options]' not in text:
                print(f"❌ AUDIT FAILED: Activity '{title}' missing mandatory > [!options] block.")
                print("  -> ALL fill-in activities require explicit options/choices.")
                sys.exit(1)
            
            # Check for numbered items (Strict Parser Requirement)
            if not re.search(r'^\s*\d+\.', text, re.MULTILINE):
                print(f"❌ AUDIT FAILED: Activity '{title}' missing numbered items (1. ...).")
                print("  -> Parser requires fill-in items to be a numbered list to function.")
                sys.exit(1)
    
    # ------------------------------------------------------------
    # 3. Calculation & Logic
    # ------------------------------------------------------------

    # --- 3. Filtering and Analysis ---
    
    # Keywords
    core_keywords = ["warm-up", "presentation", "introduction", "narrative", "context", "diagnostic", "cultural", "culture", "story", "dialogue", "reading", "deep dive", "riddle", "insight"]
    activity_keywords_list = ["match-up", "gap-fill", "quiz", "true-false", "group-sort", "unjumble", "transform", "fill-in", "error-correction", "anagram"]
    exclude_keywords = ["activities", "activity", "practice", "production", "summary", "vocabulary", "check"]
    
    # Metrics
    total_words = 0
    activity_count = 0
    found_activity_types = []
    valid_density_count = 0
    total_activities = 0
    
    # Regex metrics
    # Engagement: Count inclusive of both Legacy Emojis AND Standard Callouts
    engagement_pattern = re.compile(r'(>\s*[💡⚡🎬🎭🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑])|(>\s*\[!(note|tip|warning|caution|important|cultural)\])')
    engagement_count = len(engagement_pattern.findall(content))
    
    audio_pattern = re.compile(r'\[🔊\]\(.*?\)')
    audio_count = len(audio_pattern.findall(content))
    
    ipa_pattern = re.compile(r'\|.*/.*?/.*\|') 
    ipa_count = len(ipa_pattern.findall(content))
    
    model_answer_pattern = re.compile(r'>\s*\[!answer\]')
    model_answer_count = len(model_answer_pattern.findall(content))

    # Helper: Density
    def count_items(text):
        # 1. Numbered Lists (1. Question)
        numbered = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))
        
        # 2. Table Rows (Match-up)
        # Count lines starting with | that are not separator lines (---)
        table_lines = [line for line in text.split('\n') if line.strip().startswith('|') and '---' not in line]
        # Subtract header if it exists (usually 1 header row) so we count data rows
        # If > 1 rows found, assume 1 is header. items = rows - 1. 
        # Actually my previous logic (len - 2) assumed header + separator. 
        # But I filtered separator above. So len - 1.
        table_count = max(0, len(table_lines) - 1) if len(table_lines) > 0 else 0
        
        # 3. Checkboxes (True/False, Group Sort)
        # Supports [ ], [x], [X]
        checkboxes = len(re.findall(r'^\s*-\s*\[[ xX]?\]', text, re.MULTILINE))
        
        # 4. Bullets (Group Sort source list sometimes)
        # Exclude checkboxes
        bullets = len(re.findall(r'^\s*-\s+[^\[]', text, re.MULTILINE))
        
        # Debug print if low count found
        # print(f"DEBUG: N={numbered} T={table_count} C={checkboxes} B={bullets}")
        
        # Priority Logic to avoid double counting (e.g. Questions + Options)
        # 1. Numbered Lists are usually the distinct "Items" (Questions, Puzzles)
        if numbered > 0:
            return numbered
        # 2. Key-Value Tables (Match-up)
        elif table_count > 0:
            return table_count
        # 3. Checkboxes (True/False - if not numbered)
        elif checkboxes > 0:
            return checkboxes
        # 4. Bullets (Fallback)
        else:
            return bullets

    # Immersion
    def calculate_immersion(text):
        if not text: return 0.0
        clean_text = re.sub(r'\s+', '', text)
        if not clean_text: return 0.0
        total_chars = len(clean_text)
        cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', clean_text))
        return (cyrillic_chars / total_chars) * 100

    core_text_for_immersion = ""
    table_rows = []
    
    print(f"\nAuditing {file_path} (Target: {target})...\n")

    for title, text in section_map.items():
        title_lower = title.lower()
        
        is_core = False
        is_excluded = False
        is_activity = False
        
        # Activity Check
        matched_act_type = None
        for act in activity_keywords_list:
            if act in title_lower:
                is_activity = True
                matched_act_type = act
        if is_activity:
            found_activity_types.append(matched_act_type)
        
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
        
        # For Stats (Richness) - Include Scaffolding
        cleaned_stats = clean_for_stats(text)
        
        # For Immersion (Purity) - Exclude Scaffolding
        cleaned_immersion = clean_for_immersion(text)

        if is_core and not is_excluded:
            core_text_for_immersion += cleaned_immersion + " "

        words = cleaned_stats.split()
        count = len(words)
        
        status_icon = "⚪️"
        note = "Skipped"

        if is_activity:
            activity_count += 1
            total_activities += 1
            
            items = count_items(text)
            density_target = config['min_items_per_activity']
            
            if items >= density_target:
                valid_density_count += 1
                density_icon = "✅"
            else:
                density_icon = "⚠️"
                
            status_icon = "🎮"
            note = f"Activity ({items} items)"
            print(f"  > {title}: {items} items")
            
            # Use ITEM count for Activities, WORD count for Sections
            display_count = items

        elif is_core and not is_excluded:
            total_words += count
            status_icon = "✅"
            note = "Included in Core"
            display_count = count
        elif is_excluded:
            status_icon = "➖"
            note = "Excluded Type"
            display_count = count
        else:
            display_count = count

        table_rows.append(f"| **{title}** | {status_icon} | {display_count} | {note} |")

    # --- 4. Result Gates ---
    results = {}
    has_critical_failure = False


    # Word Count
    if total_words >= target:
        results['words'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{total_words}/{target}"}
    else:
        results['words'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{total_words}/{target}"}
        has_critical_failure = True

    # Activity Count
    act_target = config['min_activities']
    if activity_count >= act_target:
        results['activities'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{activity_count}/{act_target}"}
    else:
        results['activities'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{activity_count}/{act_target}"}
        has_critical_failure = True

    # Density
    failed_density = total_activities - valid_density_count
    dens_threshold = config['min_items_per_activity']
    if failed_density == 0 and total_activities > 0:
        results['density'] = {'status': 'PASS', 'icon': '✅', 'msg': f"All > {dens_threshold}"}
    else:
        results['density'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{failed_density} < {dens_threshold}"}
        has_critical_failure = True

    # Unique Types
    unique_types = set(found_activity_types)
    type_target = config['min_types_unique']
    if len(unique_types) >= type_target:
        results['unique_types'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{len(unique_types)}/{type_target} types"}
    else:
        results['unique_types'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{len(unique_types)}/{type_target} types"}
        has_critical_failure = True
        
    # Priority Check
    priority_intersection = unique_types.intersection(config['priority_types'])
    if priority_intersection:
        results['priority'] = {'status': 'PASS', 'icon': '✅', 'msg': "Priority types used"}
    else:
        results['priority'] = {'status': 'FAIL', 'icon': '❌', 'msg': "No priority types"}
        has_critical_failure = True

    # Engagement (level-dependent target)
    eng_target = config.get('min_engagement', 3)
    if engagement_count >= eng_target:
        results['engagement'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{engagement_count}/{eng_target}"}
    else:
        results['engagement'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{engagement_count}/{eng_target}"}
        has_critical_failure = True

    # Audio
    if audio_count > 0:
        results['audio'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{audio_count} links"}
    else:
        results['audio'] = {'status': 'FAIL', 'icon': '❌', 'msg': "No audio"}
        has_critical_failure = True

    # Immersion (A1 M25+ Gate)
    immersion_score = calculate_immersion(core_text_for_immersion)
    module_num = int(re.search(r'module-(\d+)', os.path.basename(file_path)).group(1))
    
    # Story/Dialogue Immersion Check
    # We check the SPECIFIC sections, not just the whole core text, to avoid false positives from English instructions
    story_immersion_fail = False
    for title, text in section_map.items():
        if "Story Time" in title or "Dialogue" in title:
            # Check ratio of Latin vs Cyrillic in this specific section
            # Filter out translation block in parens (roughly)
            clean_story = re.sub(r'\([^\)]*\)', '', text)
            clean_story = clean_for_immersion(clean_story)
            
            latin_chars = len(re.findall(r'[a-zA-Z]', clean_story))
            cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', clean_story))
            
            # Ratio: Latin shouldn't be more than 30% of Cyrillic (names, formatting overhead)
            # This detects "English story with bold UA words"
            # Unless it's empty
            if cyrillic_chars > 20: 
                ratio = latin_chars / cyrillic_chars
                if ratio > 0.4:
                     print(f"❌ AUDIT FAILED: Low Immersion in '{title}'. Latin/Cyrillic Ratio: {ratio:.2f} (>0.4). Rewrite in UA.")
                     story_immersion_fail = True
    
    if story_immersion_fail:
        results['immersion'] = {'status': 'FAIL', 'icon': '❌', 'msg': "English Story Detected"}
        has_critical_failure = True
    else:
        results['immersion'] = {'status': 'PASS', 'icon': '🇺🇦', 'msg': f"{immersion_score:.1f}%"}

    # Transliteration Policy (A2+ = FORBIDDEN)
    if not transliteration_allowed:
        # Check Frontmatter must say 'none'
        if re.search(r'transliteration:\s*none', frontmatter_str):
             translit_status = "PASS"
        else:
             print(f"❌ AUDIT FAILED: Level {level_code} forbids transliteration. Set 'transliteration: none' in frontmatter.")
             translit_status = "FAIL"
             has_critical_failure = True
        
        # Also check for Latin text in parentheses after Cyrillic (common transliteration pattern)
        translit_pattern = re.search(r'[\u0400-\u04ff]+\s*\([A-Za-z]+\)', content)
        if translit_pattern:
            print(f"❌ AUDIT FAILED: Transliteration detected: '{translit_pattern.group()}'. Remove Latin in parentheses.")
            translit_status = "FAIL"
            has_critical_failure = True
        
        results['translit'] = {'status': translit_status, 'icon': '✅' if translit_status=='PASS' else '❌', 'msg': "None (Policy)"}
    else:
        results['translit'] = {'status': 'INFO', 'icon': 'ℹ️', 'msg': "Allowed (A1)"}

    if immersion_score < 10.0 and module_num > 5:
         # Hard Failure for very low immersion
         has_critical_failure = True

    
    # Structure Check
    has_warmup = re.search(r'## warm-up', content, re.IGNORECASE) is not None
    has_presentation = re.search(r'## presentation', content, re.IGNORECASE) is not None
    if has_warmup and has_presentation:
         results['structure'] = {'status': 'PASS', 'icon': '✅', 'msg': "Valid"}
    else:
         results['structure'] = {'status': 'FAIL', 'icon': '❌', 'msg': "Missing Sections"}
         has_critical_failure = True

    # Define lines_raw early for Linting and Vocab check
    lines_raw = content.split('\n')

    # Vocabulary Count Check
    vocab_count = 0
    in_vocab = False
    for line in lines_raw:
        if re.match(r'^#+\s+(Vocabulary|Словник)', line.strip(), re.IGNORECASE):
            in_vocab = True
            continue
        if in_vocab and re.match(r'^#+', line.strip()):
            in_vocab = False
        
        if in_vocab and line.strip().startswith('|') and '---' not in line:
            # Check if it's a data row (not header)
            cols = line.count('|')
            if cols >= 2:
                # Naive heuristic: If it has pipes, it's a row.
                # We assume 1st row is header checking above or by default.
                pass
    
    # Better Regex approach for Vocab Count to avoid state machine complexity issues
    vocab_section_match = re.search(r'(#+\s+(Vocabulary|Словник).*?)(?=\n#+|$)', content, re.DOTALL | re.IGNORECASE)
    if vocab_section_match:
        vocab_text = vocab_section_match.group(1)
        # Count rows that start with | and don't contain ---
        lines = vocab_text.split('\n')
        v_rows = len([l for l in lines if l.strip().startswith('|') and '---' not in l])
        # Subtract header
        vocab_count = max(0, v_rows - 1)
    else:
        print(f"DEBUG: No 'Vocabulary' section found. Content tail: {content[-200:]}")
    
    if vocab_count >= vocab_target:
        results['vocab'] = {'status': 'PASS', 'icon': '✅', 'msg': f"{vocab_count}/{vocab_target}"}
    else:
        results['vocab'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{vocab_count} < {vocab_target}"}
        has_critical_failure = True

    # --- Markdown Linting (Integrated) ---
    lint_errors = []
    in_activities = False
    current_activity_type = None
    fill_in_needs_answer = False

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()
        
        # Track Activities Section
        if stripped.lower().startswith('# activities'):
            in_activities = True
            
        # Track Activity Type
        if in_activities and stripped.startswith('## '):
            # Check if previous fill-in was dangling
            if fill_in_needs_answer:
                 lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                 fill_in_needs_answer = False

            parts = stripped.split(':')
            if len(parts) > 1:
                # ## match-up: Title -> match-up
                header_type = parts[0].replace('##', '').strip().lower()
                current_activity_type = header_type
            else:
                current_activity_type = None

        # 1. Anagram Check
        if current_activity_type == 'anagram':
             if re.search(r'\w\s+/\s+\w\s+/', stripped):
                  lint_errors.append(f"Line {line_num}: Invalid Anagram format. Use spaces (a b c), not slashes.")

        # 2. Activity YAML Check
        if in_activities:
            if stripped.startswith('type: ') or stripped.startswith('items:'):
                lint_errors.append(f"Line {line_num}: YAML detected in Activities. Use markdown.")

        # 3. Callout Check
        if "**Answer:**" in stripped or "**Option:**" in stripped:
             lint_errors.append(f"Line {line_num}: Old format detected. Use '> [!answer]'.")

        # 4. Audio Link Check (Strict Vocab Table)
        if '|' in stripped and '[🔊]' in stripped:
            parts = stripped.strip().split('|')
            # Expecting format: | uk | ipa | en | audio | (length 6 with empty start/end)
            if len(parts) >= 5:
                audio_cell = parts[-2].strip()  # Last meaningful column
                # Regex: Must be exactly [🔊](link) with optional spaces, nothing else.
                if '[🔊]' in audio_cell:
                     if not re.match(r'^\[🔊\]\(audio_[a-zA-Z0-9_\-]+\)$', audio_cell):
                          lint_errors.append(f"Line {line_num}: Vocab Audio Error. Cell '{audio_cell}' must contain ONLY '[🔊](audio_...)'. No text, no bolding.")

        # 4b. Supported Activity Check
        VALID_ACTIVITY_TYPES = ["match-up", "fill-in", "quiz", "true-false", "group-sort", "unjumble", "error-correction", "anagram", "select"]
        if current_activity_type and current_activity_type not in VALID_ACTIVITY_TYPES:
             lint_errors.append(f"Line {line_num}: Invalid Activity Type '{current_activity_type}'. Supported: {', '.join(VALID_ACTIVITY_TYPES)}.")

        # 5. Strict Fill-In Check
        # Rule: Every numbered item in a fill-in activity MUST contain '___'
        if current_activity_type == 'fill-in':
            if re.match(r'^\d+\.', stripped):
                if fill_in_needs_answer:
                     lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                fill_in_needs_answer = True

                if '___' not in stripped:
                    lint_errors.append(f"Line {line_num}: Fill-in item missing '___' placeholder. Input field will not render.")
            
            if '> [!answer]' in stripped:
                fill_in_needs_answer = False

        # 6. Strict True-False/Explanation Check
        # Rule: Explanations should not contain [!answer] callout artifacts
        if '> [!explanation]' in stripped and '[!answer]' in stripped:
             lint_errors.append(f"Line {line_num}: Malformed Explanation. Contains '[!answer]' inside explanation block.")

        # 7. Checkbox Format Check
        if stripped.startswith('- ['):
            if not re.match(r'- \[[ xX]\]', stripped):
                 lint_errors.append(f"Line {line_num}: Invalid Checkbox format. Use '- [ ]' or '- [x]'.")

        # 8. AI Monologue / Slop Check
        # Keywords that suggest the AI is talking to itself or the user in the content body
        monologue_patterns = [
            r"Let's say",
            r"context suggests",
            r"Usually '.*' here",
            r'\bAI:',
            r'printed your printing'
        ]
        for pat in monologue_patterns:
            if re.search(pat, stripped, re.IGNORECASE):
                lint_errors.append(f"Line {line_num}: Potential AI Monologue detected ('{pat}'). Please remove.")

        # 9. Audio Artifact Check (Strict: Vocab Only)
        # We allow 'audio_' ONLY if we are inside the Vocabulary section.
        # But here we are iterating lines_raw. We need to know if we are in Vocabulary section.
        is_vocab_section = False
        # (Naive check: if we passed "## Vocabulary" header)
        # However, verifying line-by-line state is fragile.
        # Instead, let's just ban 'audio_' in this loop unless it's a Vocab Table row.
        
        # Heuristic: Vocab rows start with | and have multiple columns.
        is_vocab_row = (stripped.startswith('|') and stripped.count('|') >= 3)
        
        if 'audio_' in stripped and not is_vocab_row:
             # Exception: Deep Dive or Grammar Tables might legitimately reference specific audio?
             # User Request: "change the ode that foro links are only in the vocab part please"
             # So we strictly BAN it elsewhere.
             lint_errors.append(f"Line {line_num}: 'audio_' link detected outside Vocabulary Table. User Rule: Audio links only in Vocab.")

        # 10. Empty Header Check (Lonely #)
        if re.match(r'^#+\s*$', stripped):
            lint_errors.append(f"Line {line_num}: Empty Header detected (Lonely '#'). Remove or add title.")

        # 11. Strict True/False Check (No Hints/Explanations)
        if current_activity_type == 'true-false':
            # Ban explicit explanation callouts
            if '> [!explanation]' in stripped:
                lint_errors.append(f"Line {line_num}: T/F Activity contains '[!explanation]'. Remove all hints/solutions.")
            # Ban plain blockquote hints (heuristically)
            # We allow the main instruction which usually asks "Is this...?"
            # Ban plain blockquote hints (heuristically)
            # We allow the main instruction which usually asks "Is this...?"
            elif stripped.startswith('> ') and not any(x in stripped for x in ['Is this', 'True', 'False', 'Correct', 'logic', 'agreement']):
                 lint_errors.append(f"Line {line_num}: T/F Activity contains blockquote hint '{stripped}'. Remove hints.")

        # 12. Transliteration Column Check (M21+)
        if module_num >= 21:
            # Check Vocab Table Header
            if 'Start Header Check' not in locals():
                 Start_Header_Check = True # Just to run this block once per file logically
            
            if '|' in stripped and ('| trans' in stripped.lower() or '| вимо' in stripped.lower()):
                 # This detects explicit headers like "Transliteration" or "Вимова"
                 lint_errors.append(f"Line {line_num}: Transliteration Column detected in M{module_num} (Policy M21+: None). Remove column.")

    # 5. Structural Section Check (Summary & Vocabulary)
    lines = content.split('\n')
    if not any(re.match(r'^#+\s+(Summary|Підсумок)', l, re.IGNORECASE) for l in lines):
        results['structure'] = {'status': 'FAIL', 'icon': '❌', 'msg': "Missing '# Summary'"}
        has_critical_failure = True
    elif not any(re.match(r'^#+\s+(Vocabulary|Словник)', l, re.IGNORECASE) for l in lines):
        results['structure'] = {'status': 'FAIL', 'icon': '❌', 'msg': "Missing '# Vocabulary'"}
        has_critical_failure = True
    # Check for Vocab Table if Vocabulary exists
    elif not any('| Word |' in l or '| Слово |' in l or '| Ukrainian |' in l for l in lines):
        results['structure'] = {'status': 'FAIL', 'icon': '❌', 'msg': "Missing Vocab Table"}
        has_critical_failure = True
    else:
        results['structure'] = {'status': 'PASS', 'icon': '✅', 'msg': "Valid Structure"}

    if lint_errors:
        results['lint'] = {'status': 'FAIL', 'icon': '❌', 'msg': f"{len(lint_errors)} Format Errors"}
        has_critical_failure = True
    else:
        results['lint'] = {'status': 'PASS', 'icon': '✅', 'msg': "Clean Format"}

    # Output
    print(f"\n--- STRICT GATES (Level {level_code}) ---")
    keys_order = ['words', 'activities', 'density', 'unique_types', 'priority', 'engagement', 'audio', 'vocab', 'structure', 'lint']
    for k in keys_order:
        r = results.get(k)
        if r:
            print(f"{k.capitalize():<12} {r['icon']} {r['msg']}")
            
    print(f"Immersion    {results['immersion']['icon']} {results['immersion']['msg']}")

    # Report Generation
    report_lines = []
    report_lines.append(f"# Audit Report: {os.path.basename(file_path)}")
    report_lines.append(f"**Phase:** {phase} | **Level:** {level_code} | **Pedagogy:** {pedagogy} | **Target:** {target}")
    report_lines.append(f"**Overall Status:** {'❌ FAIL' if has_critical_failure else '✅ PASS'}")
    report_lines.append("")
    
    if lint_errors:
        print("\n❌ LINT ERRORS FOUND:")
        for err in lint_errors:
            print(f"  - {err}")
        print("")
        
        report_lines.append("## LINT ERRORS")
        for err in lint_errors:
            report_lines.append(f"- ❌ {err}")
        report_lines.append("")

    report_lines.append("## Gates")
    for k in keys_order:
        r = results.get(k)
        if r:
             report_lines.append(f"- **{k.capitalize()}:** {r['icon']} {r['msg']}")
    
    report_lines.append("")
    report_lines.append("## Section Audit")
    report_lines.append("| Section | Status | Count | Notes |")
    report_lines.append("|---|---|---|---|")
    report_lines.extend(table_rows)

    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    base_name = os.path.splitext(file_name)[0]
    
    if not file_dir.endswith('gemini'):
        target_dir = os.path.join(file_dir, 'gemini')
    else:
        target_dir = file_dir
        
    os.makedirs(target_dir, exist_ok=True)
    report_path = os.path.join(target_dir, f"{base_name}-review.md")

    # PRESERVE MANUAL CONTENT
    manual_content = ""
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                existing_report = f.read()
                if "<!-- MANUAL_NOTES -->" in existing_report:
                    parts = existing_report.split("<!-- MANUAL_NOTES -->")
                    if len(parts) > 1:
                        manual_content = "<!-- MANUAL_NOTES -->" + parts[1]
        except Exception:
            pass # Ignore read errors, overwrite if failed
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        if manual_content:
            f.write("\n\n" + manual_content)

        
    print(f"\nReport: {report_path}")
    
    if has_critical_failure:
        print("\n❌ AUDIT FAILED. Correct errors before proceeding.")
        return False
    else:
        print("\n✅ AUDIT PASSED.")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/audit_module.py <file.md> [file2.md ...]")
        sys.exit(1)
    else:
        any_failure = False
        for file_path in sys.argv[1:]:
             print(f"\n{'='*40}")
             success = audit_module(file_path)
             if not success:
                 any_failure = True
        
        if any_failure:
            sys.exit(1)
        else:
            sys.exit(0) 

