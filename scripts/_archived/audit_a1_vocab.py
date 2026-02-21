import re
import sys
from pathlib import Path

def fix_content_formatting(content):
    """
    Fixes common formatting issues:
    - Double headers in tables
    """
    lines = content.splitlines()
    new_lines = []
    
    i = 0
    fixed = False
    while i < len(lines):
        line = lines[i]
        
        # Check for double headers
        if "Word" in line and "IPA" in line and "|" in line:
            # Check next few lines for a duplicate header
            # Pattern: Header, Separator, [Header, Separator] -> duplicate
            if i + 1 < len(lines) and "---" in lines[i+1]:
                 if i + 2 < len(lines) and "Word" in lines[i+2] and "IPA" in lines[i+2] and "|" in lines[i+2]:
                     if i + 3 < len(lines) and "---" in lines[i+3]:
                         # Found double header, keep first set (i, i+1), skip second set (i+2, i+3)
                         new_lines.append(lines[i])
                         new_lines.append(lines[i+1])
                         i += 4
                         fixed = True
                         continue

        new_lines.append(line)
        i += 1
        
    return "\n".join(new_lines), fixed

def audit_modules():
    modules_dir = Path("/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1")
    modules = sorted(list(modules_dir.glob("*.md")))
    
    issues_found = False
    modules_with_issues = []
    
    print(f"Auditing {len(modules)} modules in {modules_dir}...\n")
    print(f"{'Module':<40} | {'Status':<10} | {'Vocab':<6} | {'Missing Enr.':<12}")
    print("-" * 80)
    
    for mod_file in modules:
        try:
            with open(mod_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"{mod_file.name:<40} | ERROR      | -      | Read Fail: {e}")
            continue

        # 1. Formatting Fix
        fixed_content, was_fixed = fix_content_formatting(content)
        if was_fixed:
            with open(mod_file, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            # Re-read content
            content = fixed_content
            # We don't mark as issue because we fixed it, but we log it
            # print(f"  [FIXED] {mod_file.name}: Removed duplicate headers")

        # 2. Check for Vocab Section
        if "# Vocabulary" not in content and "# Словник" not in content:
            # Maybe M01/M02 don't have it? But they should per new rebuild script?
            # Actually generic instruction says look for it.
            print(f"{mod_file.name:<40} | FAIL       | -      | No Vocab Header")
            issues_found = True
            continue

        # 3. Analyze Table
        # Flexible regex for header
        header_regex = re.compile(r"\|\s*Word\s*\|\s*IPA\s*\|\s*English\s*\|", re.IGNORECASE)
        
        lines = content.splitlines()
        vocab_start = -1
        in_vocab_table = False
        empty_ipa_count = 0
        empty_eng_count = 0
        table_rows = 0
        
        for i, line in enumerate(lines):
            if header_regex.search(line):
                vocab_start = i
                in_vocab_table = True
                continue
            
            if in_vocab_table:
                stripped = line.strip()
                if not stripped: 
                    # End of table
                    in_vocab_table = False
                    continue
                if stripped.startswith("| ---"):
                    continue
                if stripped.startswith("|"):
                    table_rows += 1
                    parts = [p.strip() for p in stripped.strip("|").split("|")]
                    if len(parts) >= 3:
                        ipa = parts[1]
                        eng = parts[2]
                        if not ipa: empty_ipa_count += 1
                        if not eng: empty_eng_count += 1
        
        if vocab_start == -1:
             print(f"{mod_file.name:<40} | FAIL       | -      | No Vocab Table")
             issues_found = True
             continue
        
        missing_count = empty_ipa_count + empty_eng_count
        status = "PASS"
        if missing_count > 0:
            status = "FAIL"
            issues_found = True
            modules_with_issues.append((mod_file.name, empty_ipa_count, empty_eng_count))
        
        print(f"{mod_file.name:<40} | {status:<10} | {table_rows:<6} | {missing_count:<12}")

    print("-" * 80)

    if issues_found:
        print("\n[ATTENTION AI AGENT]")
        print("The following modules contain unenriched vocabulary entries (Missing IPA or English).")
        print("You must fix them using the `replace_file_content` tool.")
        print("The `rebuild_vocab_simple.py` script CANNOT enrich them; only YOU can.")
        print("\nModules to Fix:")
        for mod, ipa, eng in modules_with_issues:
             print(f"- {mod}: Missing IPA={ipa}, Missing English={eng}")
        sys.exit(1)
    else:
        print("\nAll modules passed audit! Formatting verified and vocabulary enriched.")
        sys.exit(0)

if __name__ == "__main__":
    audit_modules()
