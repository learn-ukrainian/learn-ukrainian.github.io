
import os
import re

SUSPICIOUS_PATTERNS = [
    r"\bCorrection:",
    r"\bWait, actually",
    r"\bWait, no\b",
    r"\bOops\b",
    r"\bNote to self\b",
    r"\bAI note\b",
    r"\bignore this\b",
    r"\bdisregard this\b",
    r"\bLet's change\b",
    r"\bRewrite this\b",
    r"\bDraft:\b",
    r"\bCheck this\b",
    r"\bI made a mistake\b",
    r"\bSelf-correction\b",
    r"\bApologies\b",
    r"\bSorry,\b", # classic AI apology
    r"\bAs an AI\b",
    r"\bMy previous\b",
    r"\bIn the previous\b"
]

def scan_file(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line_str = line.strip()
            # Skip empty lines
            if not line_str:
                continue
            
            # Check for patterns
            for pattern in SUSPICIOUS_PATTERNS:
                if re.search(pattern, line_str, re.IGNORECASE):
                    # Filter out likely false positives
                    if "Wait" in pattern and "**" in line_str: # Dialogue "Wait!"
                         continue
                    if "Sorry" in pattern and "**" in line_str: # Dialogue "Sorry!"
                         continue
                    if "error-correction" in line_str: # Legitimate activity type
                         continue
                    
                    issues.append((i + 1, line_str, pattern))
                    break # Found one pattern, move to next line
    return issues

def main():
    target_dirs = [
        os.path.join(os.getcwd(), 'curriculum/l2-uk-en/a1'),
        os.path.join(os.getcwd(), 'curriculum/l2-uk-en/a2')
    ]
    
    found_any = False
    print("Scanning for AI confusion artifacts...")
    
    for target_dir in target_dirs:
        if not os.path.exists(target_dir):
            continue
            
        files = sorted([f for f in os.listdir(target_dir) if f.endswith('.md')])
        
        for filename in files:
            path = os.path.join(target_dir, filename)
            issues = scan_file(path)
            if issues:
                found_any = True
                print(f"\nFILE: {target_dir.split('/')[-1]}/{filename}")
                for line_num, content, pattern in issues:
                    print(f"  Line {line_num} [{pattern}]: {content}")
                print("-" * 40)

    if not found_any:
        print("\nNo AI confusion artifacts found!")

if __name__ == "__main__":
    main()
