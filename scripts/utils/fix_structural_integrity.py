import os
import re

# Add current directory to path to import audit tools
import sys

import yaml

sys.path.append(os.getcwd())

import contextlib

from scripts.audit.checks.template_compliance import _extract_sections_with_content
from scripts.audit.template_parser import parse_template, resolve_template


_FOOTER_PATTERNS = ['summary', 'підсумок', 'practice?', 'activities', 'vocabulary', 'resources']
_MAJOR_HEADERS = {'summary', 'підсумок', 'activities', 'vocabulary', 'external resources', 'зовнішні ресурси'}
_PRACTICE_INFILL = (
    "To solidify your knowledge, try writing five sentences using the grammar "
    "patterns from this module. Use the vocabulary items provided in the sidecar "
    "to practice your new words in context!"
)


def _build_slot_mapping(template, sections_data):
    """Map each required template slot to matching section indices."""
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

    return slot_to_indices, handled_indices


def _merge_duplicates_and_orphans(template, sections_data, slot_to_indices, handled_indices):
    """Merge duplicate sections and orphan sub-headers into anchors."""
    for slot_idx in range(len(template.required_sections)):
        indices = slot_to_indices[slot_idx]
        if not indices:
            continue

        anchor_idx = indices[0]

        # 1. Merge duplicates into the anchor body
        if len(indices) > 1:
            for dup_idx in indices[1:]:
                sections_data[anchor_idx]['body'] += "\n\n" + sections_data[dup_idx]['body'].strip()
                handled_indices.add(dup_idx)

        # 2. Infill/Merge orphans if anchor is effectively empty
        # CRITICAL: We only merge orphans into NON-footer sections.
        is_footer_anchor = any(p in sections_data[anchor_idx]['header'].lower() for p in _FOOTER_PATTERNS)

        if not _is_meaningful(sections_data[anchor_idx]['body']) and not is_footer_anchor:
            curr = anchor_idx + 1
            while curr < len(sections_data):
                if curr in handled_indices:
                    is_another_anchor = any(
                        slot_to_indices[other_slot] and slot_to_indices[other_slot][0] == curr
                        for other_slot in range(len(template.required_sections))
                    )
                    if is_another_anchor:
                        break

                sections_data[anchor_idx]['body'] += f"\n\n## {sections_data[curr]['header']}\n\n{sections_data[curr]['body']}"
                handled_indices.add(curr)
                curr += 1


def _infill_practice_sections(sections_data):
    """Auto-infill empty 'Need More Practice?' sections."""
    for s in sections_data:
        if "practice?" in s['header'].lower() and not _is_meaningful(s['body']):
            s['body'] = _PRACTICE_INFILL


def _extract_title_and_frontmatter(content):
    """Extract title line and frontmatter from content."""
    title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(0) if title_match else ""

    frontmatter = ""
    if content.startswith("---"):
        fm_match = re.match(r'^(---\s*\n.*?\n---\s*\n)', content, re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(1)

    return title, frontmatter


def _order_sections(sections_data, slot_to_indices, handled_indices):
    """Order sections: main content -> leftover content -> footers."""
    anchors = set()
    for indices in slot_to_indices.values():
        if indices:
            anchors.add(indices[0])

    main_content_indices = []
    footer_indices = []
    leftover_indices = []

    for i, s in enumerate(sections_data):
        header_lower = s['header'].lower()
        is_footer = any(p in header_lower for p in _FOOTER_PATTERNS)

        if i in anchors:
            (footer_indices if is_footer else main_content_indices).append(i)
        elif i not in handled_indices:
            (footer_indices if is_footer else leftover_indices).append(i)

    return [sections_data[idx] for idx in main_content_indices + leftover_indices + footer_indices]


def _reconstruct_content(final_list, title, frontmatter):
    """Reconstruct content from ordered section list."""
    reconstructed = frontmatter
    if title and title not in reconstructed:
        reconstructed += title + "\n\n"

    for s in final_list:
        if s['header'] in title:
            continue
        h_level = "#" if s['header'].lower() in _MAJOR_HEADERS else "##"
        reconstructed += f"{h_level} {s['header']}\n\n{s['body'].strip()}\n\n"

    return re.sub(r'\n{3,}', '\n\n', reconstructed).strip() + "\n"


def fix_structural_integrity(target_dir="curriculum/l2-uk-en/a2"):
    fixed_count = 0

    # Load template mappings
    with open("docs/l2-uk-en/template_mappings.yaml") as f:
        yaml.safe_load(f)

    files = [f for f in os.listdir(target_dir) if f.endswith(".md")]

    for filename in sorted(files):
        path = os.path.join(target_dir, filename)
        with open(path, encoding='utf-8') as f:
            content = f.read()

        slug = filename.replace(".md", "")
        level_code = "a2"
        module_id_for_mapping = f"{level_code}-{slug}"

        # Load Metadata sidecar
        meta_path = os.path.join(target_dir, "meta", slug + ".yaml")
        meta_data = {}
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as mf, contextlib.suppress(Exception):
                meta_data = yaml.safe_load(mf)

        # Resolve template
        try:
            template_path = resolve_template(module_id_for_mapping, meta_data)
        except ValueError:
            continue

        template = parse_template(template_path)
        if not template or not template.required_sections:
            continue

        orig_content = content
        sections_data = _extract_sections_with_content(content)

        slot_to_indices, handled_indices = _build_slot_mapping(template, sections_data)
        _merge_duplicates_and_orphans(template, sections_data, slot_to_indices, handled_indices)
        _infill_practice_sections(sections_data)

        title, frontmatter = _extract_title_and_frontmatter(content)
        final_list = _order_sections(sections_data, slot_to_indices, handled_indices)
        reconstructed = _reconstruct_content(final_list, title, frontmatter)

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
