import re
from pathlib import Path

def verify_frontend():
    print("=== Gold Team Frontend Integrity Test ===\n")
    html_path = Path("playgrounds/v2-gold/batch-monitor.html")
    if not html_path.exists():
        print("❌ FAIL: Dashboard file not found.")
        return

    content = html_path.read_text()
    
    # 1. Check for required IDs
    required_ids = [
        'track-list', 'stat-progress', 'bar-total', 'stat-active', 
        'stat-usage', 'stat-failures', 'fail-badge', 'heatmap',
        'failure-list', 'cli-module', 'cli-track', 'modal', 'modal-body'
    ]
    
    print("Testing DOM IDs...")
    for id_name in required_ids:
        if f'id="{id_name}"' in content or f"id='{id_name}'" in content:
            print(f"  ✅ {id_name}")
        else:
            print(f"  ❌ MISSING ID: {id_name}")

    # 2. Check JS function consistency
    print("\nTesting JS Targets...")
    # Extract all $() calls
    js_ids = re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", content)
    unique_js_ids = set(js_ids)
    for id_name in unique_js_ids:
        if f'id="{id_name}"' in content or f"id='{id_name}'" in content:
            print(f"  ✅ JS -> #{id_name}")
        else:
            print(f"  ❌ BROKEN LINK: JS targets ID '{id_name}' but it's not in HTML")

    # 3. Check onclick handlers
    print("\nTesting Event Handlers...")
    handlers = re.findall(r"onclick=['\"]([^(\"']+)[\(]", content)
    for handler in set(handlers):
        if f"function {handler}" in content:
            print(f"  ✅ {handler}()")
        else:
            print(f"  ❌ UNDEFINED FUNCTION: {handler}()")

    print("\n=== Frontend Scan Complete ===")

if __name__ == "__main__":
    verify_frontend()
