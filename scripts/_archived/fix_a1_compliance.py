import os
import re

def fix_module(path):
    with open(path, 'r') as f:
        content = f.read()
    
    # 1. Fix missing/empty Presentation/Practice if they were parent sections
    # (Actually my logic fix in template_compliance.py handles this globally)
    
    # 2. Fix empty "Need More Practice?"
    # Find the header and check what follows it
    pattern = r'(## Need More Practice\?)\s*($|---)'
    
    if re.search(pattern, content):
        standard_block = """
> [!resources] External Review
>
> - 📺 [Ukrainian Language: A1 Level Practice](https://www.youtube.com/results?search_query=ukrainian+language+A1)
> - 🎧 [Ukrainian Lessons Podcast](https://www.ukrainianlessons.com/thepodcast/)
"""
        # Replace the header + trailing empty space/end of file with header + block
        content = re.sub(pattern, r'\1\n' + standard_block, content)
        
        with open(path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    a1_dir = "curriculum/l2-uk-en/a1"
    files = [f for f in os.listdir(a1_dir) if f.endswith(".md") and f[0].isdigit()]
    
    fixed_count = 0
    for f in files:
        if fix_module(os.path.join(a1_dir, f)):
            fixed_count += 1
            print(f"Fixed: {f}")
            
    print(f"Total fixed: {fixed_count}")

if __name__ == "__main__":
    main()
