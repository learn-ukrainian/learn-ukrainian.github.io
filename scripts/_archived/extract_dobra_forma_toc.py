#!/usr/bin/env python3
"""
Extract Dobra Forma chapter titles for mapping document.
"""

import re
from pathlib import Path

CHAPTERS_DIR = Path('docs/references/dobra-forma/chapters')
OUTPUT_FILE = Path('docs/l2-uk-en/DOBRA-FORMA-TOC.md')

def extract_title(md_file: Path) -> str:
    """Extract title from markdown file."""
    content = md_file.read_text(encoding='utf-8')
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1) if match else md_file.stem

def main():
    chapters = []
    
    for md_file in sorted(CHAPTERS_DIR.glob('*.md'), key=lambda x: [int(p) if p.isdigit() else p for p in re.split(r'(\d+)', x.stem)]):
        chapter_num = md_file.stem
        title = extract_title(md_file)
        chapters.append((chapter_num, title))
    
    # Write TOC
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('# Dobra Forma - Table of Contents\n\n')
        f.write('**Source:** https://opentext.ku.edu/dobraforma/\n\n')
        f.write(f'**Total Chapters:** {len(chapters)}\n\n')
        f.write('---\n\n')
        
        current_section = None
        for chapter_num, title in chapters:
            # Extract section number (e.g., "1" from "1.1")
            section = chapter_num.split('.')[0]
            
            if section != current_section:
                current_section = section
                f.write(f'\n## Section {section}\n\n')
            
            f.write(f'- **{chapter_num}** {title}\n')
    
    print(f'✅ Created {OUTPUT_FILE} with {len(chapters)} chapters')

if __name__ == '__main__':
    main()
