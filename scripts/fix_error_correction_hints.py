import os
import re
import glob

def clean_line(line):
    # Remove ** markers
    cleaned_line = line.replace('**', '')
    
    # Remove parenthetical hints at the end of the line
    # Matches " (Hint...)" at the end
    cleaned_line = re.sub(r'\s*\([^)]+\)$', '', cleaned_line)
    
    if line != cleaned_line:
        print(f"  Fixed: {line.strip()} -> {cleaned_line.strip()}")
        return cleaned_line
    return line

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    in_error_correction = False
    modified = False
    
    for i, line in enumerate(lines):
        # Check for activity header
        if line.strip().lower().startswith('## error-correction:'):
            in_error_correction = True
            new_lines.append(line)
            continue
        
        # Check if we are leaving the activity (next header)
        if in_error_correction and line.strip().startswith('## '):
            in_error_correction = False
            new_lines.append(line)
            continue
            
        if in_error_correction:
            # Check if this is a numbered sentence line (e.g., "1. Sentence...")
            # It should not start with > (those are properties)
            if re.match(r'^\d+\.\s+', line):
                cleaned = clean_line(line)
                if cleaned != line:
                    modified = True
                    new_lines.append(cleaned)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    if modified:
        print(f"Updating {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

def main():
    curriculum_dir = 'curriculum/l2-uk-en'
    print(f"Scanning {curriculum_dir} for ErrorCorrection hints in source files...")
    files = glob.glob(os.path.join(curriculum_dir, '**/*.md'), recursive=True)
    
    for file_path in files:
        process_file(file_path)

if __name__ == '__main__':
    main()