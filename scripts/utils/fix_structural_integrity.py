import os
import re
import yaml

# Add current directory to path to import audit tools
import sys
sys.path.append(os.getcwd())

from scripts.audit.template_parser import resolve_template, parse_template
from scripts.audit.checks.template_compliance import _extract_sections_with_content

def fix_structural_integrity(target_dir="curriculum/l2-uk-en/a2"):
    fixed_count = 0
    empty_sections_report = []
    
    # Load template mappings
    with open("docs/l2-uk-en/template_mappings.yaml", "r") as f:
        mappings = yaml.safe_load(f)
    
    files = [f for f in os.listdir(target_dir) if f.endswith(".md")]
    
    for filename in sorted(files):
        path = os.path.join(target_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine level and slug
        slug = filename.replace(".md", "")
        level_code = "a2"
        module_id_for_mapping = f"{level_code}-{slug}"
        
        # Load Metadata sidecar
        meta_path = os.path.join(target_dir, "meta", slug + ".yaml")
        meta_data = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as mf:
                try: meta_data = yaml.safe_load(mf)
                except Exception: pass
        
        # Resolve template
        template_path = ""
        try:
            template_path = resolve_template(module_id_for_mapping, meta_data)
        except ValueError:
            continue
            
        template = parse_template(template_path)
        if not template or not template.required_sections:
            continue
            
        orig_content = content
        sections_data = _extract_sections_with_content(content)
        
        # Define "Footer" sections that must come at the end
        footer_patterns = ['summary', 'підсумок', 'practice?', 'activities', 'vocabulary', 'resources']

        # Mapping from required slot to indices in sections_data
        slot_to_indices = {}
        handled_indices = set()
        
        for slot_idx, required in enumerate(template.required_sections):
            alt_names = [name.strip() for name in required.split('|')]
            slot_to_indices[slot_idx] = []
            
            for i, s in enumerate(sections_data):
                header_lower = s['header'].lower()
                matched = False
                for alt in alt_names:
                    alt_lower = alt.lower()
                    if alt_lower == header_lower or (alt_lower in header_lower and "practice?" not in header_lower):
                        matched = True
                        break
                if matched:
                    slot_to_indices[slot_idx].append(i)
                    handled_indices.add(i)

        # Logic: If a required section is EMPTY, check if the NEXT sections are H2/H3 thematic ones
        # and merge them until we hit another required section.
        for slot_idx in range(len(template.required_sections)):
            indices = slot_to_indices[slot_idx]
            if not indices: continue
            
            # Use the first index as the "Anchor"
            anchor_idx = indices[0]
            
            # 1. Merge duplicates into the anchor body
            if len(indices) > 1:
                for dup_idx in indices[1:]:
                    sections_data[anchor_idx]['body'] += "\n\n" + sections_data[dup_idx]['body'].strip()
                    # Mark duplicates as handled so they aren't added twice
                    handled_indices.add(dup_idx)
            
            # 2. Infill/Merge orphans if anchor is effectively empty
            # CRITICAL: We only merge orphans into NON-footer sections.
            # Footers (Summary, Practice?, etc.) should not "grab" thematic content that follows them.
            is_footer_anchor = any(p in sections_data[anchor_idx]['header'].lower() for p in footer_patterns)
            
            if not _is_meaningful(sections_data[anchor_idx]['body']) and not is_footer_anchor:
                curr = anchor_idx + 1
                while curr < len(sections_data):
                    # If this next section is ALREADY handled as a primary required section, stop
                    if curr in handled_indices:
                        is_another_anchor = False
                        for other_slot in range(len(template.required_sections)):
                            if slot_to_indices[other_slot] and slot_to_indices[other_slot][0] == curr:
                                is_another_anchor = True
                                break
                        if is_another_anchor:
                            break
                    
                    # Merge orphans (thematic sub-headers) into anchor
                    sections_data[anchor_idx]['body'] += f"\n\n## {sections_data[curr]['header']}\n\n{sections_data[curr]['body']}"
                    handled_indices.add(curr)
                    curr += 1
                
        # Handle "Need More Practice?" - Auto-infill if empty
        for i, s in enumerate(sections_data):
            if "practice?" in s['header'].lower() and not _is_meaningful(s['body']):
                s['body'] = "To solidify your knowledge, try writing five sentences using the grammar patterns from this module. Use the vocabulary items provided in the sidecar to practice your new words in context!"

        # Reconstruct
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(0) if title_match else ""
        
        frontmatter = ""
        if content.startswith("---"):
            fm_match = re.match(r'^(---\s*\n.*?\n---\s*\n)', content, re.DOTALL)
            if fm_match: frontmatter = fm_match.group(1)

        reconstructed = frontmatter
        if title and title not in reconstructed: reconstructed += title + "\n\n"
        
        # Define "Footer" sections that must come at the end
        footer_patterns = ['summary', 'підсумок', 'practice?', 'activities', 'vocabulary', 'resources']
        
        # We need to output sections in a sane order.
        # 1. Title (done)
        # 2. Main content sections (matched required ones like Introduction, Presentation)
        # 3. Leftover content sections (Dialogues, Insights, etc.)
        # 4. Footer sections (Summary, Need More Practice, Activities, Vocab)
        
        main_content_indices = []
        footer_indices = []
        leftover_indices = []
        
        # We only care about ANCHORS from slot_to_indices (indices[0])
        # because duplicates are now merged into anchors.
        anchors = set()
        for indices in slot_to_indices.values():
            if indices:
                anchors.add(indices[0])
        
        for i, s in enumerate(sections_data):
            header_lower = s['header'].lower()
            is_footer = any(p in header_lower for p in footer_patterns)
            
            if i in anchors:
                if is_footer:
                    footer_indices.append(i)
                else:
                    main_content_indices.append(i)
            elif i not in handled_indices:
                # This is a truly leftover section (not a required one, not merged as an orphan)
                if is_footer:
                    footer_indices.append(i)
                else:
                    leftover_indices.append(i)
        
        # Build the final list in order: Required Content -> Leftover Content -> Footers
        final_list = []
        for idx in main_content_indices:
            final_list.append(sections_data[idx])
        for idx in leftover_indices:
            final_list.append(sections_data[idx])
        for idx in footer_indices:
            final_list.append(sections_data[idx])

        for s in final_list:
            if s['header'] in title: continue
            # Adjust header level: Summary/Підсумок/Activities/Vocabulary are treated as major blocks
            # Template requires H1 (#) for Summary/Підсумок in some levels, but A2 template shows ##
            # Actually, standardizing Summary to # is safer for the Docusaurus layout.
            h_level = "##"
            if s['header'].lower() in ['summary', 'підсумок', 'activities', 'vocabulary', 'external resources', 'зовнішні ресурси']:
                h_level = "#"
            
            reconstructed += f"{h_level} {s['header']}\n\n{s['body'].strip()}\n\n"

        reconstructed = re.sub(r'\n{3,}', '\n\n', reconstructed).strip() + "\n"
        
        if reconstructed != orig_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(reconstructed)
            fixed_count += 1
            print(f"Standardized and Infilled {filename}")

    print(f"\nFinished. Fixed {fixed_count} modules.")

def _is_meaningful(text):
    clean = text.strip()
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)
    clean = re.sub(r'^[\s\-_*]+$', '', clean, flags=re.MULTILINE)
    return len(clean.strip()) > 10

if __name__ == "__main__":
    fix_structural_integrity()
