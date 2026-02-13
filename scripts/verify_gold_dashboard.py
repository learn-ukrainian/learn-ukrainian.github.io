import requests
import json
import os
from pathlib import Path

def test_endpoint(name, url):
    print(f"Testing {name}: {url}...", end=" ")
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ OK ({len(data)} items)")
            return data
        else:
            print(f"❌ FAIL (Status {r.status_code})")
            return None
    except Exception as e:
        print(f"❌ ERROR ({e})")
        return None

def verify():
    port = 8888
    base = f"http://localhost:{port}"
    
    print("=== Gold Team System Verification ===\n")
    
    # 1. Config
    config = test_endpoint("Shared Config", f"{base}/api/config")
    
    # 2. Gold Ground Truth
    truth = test_endpoint("Gold Ground Truth", f"{base}/api/gold/ground-truth")
    if truth:
        passed = [k for k, v in truth.items() if v.get('status') == 'pass']
        print(f"   -> Found {len(passed)} passed modules.")
        if len(passed) > 0:
            print(f"   -> Sample: {passed[0]} (Level: {truth[passed[0]].get('level')})")
        else:
            print("   -> ⚠️ WARNING: No passed modules found in current structure.")

    # 3. Gold Active Orchestration
    active = test_endpoint("Gold Active Orch", f"{base}/api/gold/active-orchestration")
    
    # 4. Shared Batch State
    test_endpoint("Shared Dispatcher", f"{base}/api/batch/dispatcher")
    
    # 5. Dashboard HTML Check
    dashboard_path = Path("playgrounds/v2-gold/batch-monitor.html")
    if dashboard_path.exists():
        print(f"\n✅ Dashboard file exists: {dashboard_path}")
        content = dashboard_path.read_text()
        if "/api/gold/ground-truth" in content:
            print("✅ Dashboard points to /api/gold/ground-truth")
        if "/api/gold/active-orchestration" in content:
            print("✅ Dashboard points to /api/gold/active-orchestration")
    else:
        print(f"\n❌ Dashboard file MISSING at {dashboard_path}")

if __name__ == "__main__":
    verify()
