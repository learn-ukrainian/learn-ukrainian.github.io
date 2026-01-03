import os

c1_dir = "curriculum/l2-uk-en/c1"
files = [f for f in os.listdir(c1_dir) if f.endswith(".md")]

frontmatter_files = []
resource_files = []

for f in files:
    path = os.path.join(c1_dir, f)
    with open(path, "r") as file:
        lines = file.readlines()
        if not lines:
            continue
        if lines[0].strip() == "---":
            frontmatter_files.append(f)
        
        content = "".join(lines)
        if "[!resources]" in content:
            resource_files.append(f)

print(f"Total MD files checked: {len(files)}")
print(f"Files with Frontmatter: {len(frontmatter_files)}")
if frontmatter_files:
    print(f"Sample: {frontmatter_files[:5]}")

print(f"Files with [!resources]: {len(resource_files)}")
if resource_files:
    print(f"Sample: {resource_files[:5]}")
