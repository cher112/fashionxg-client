#!/usr/bin/env python3
"""
FashionXG Setup Checker
Validates that all prerequisites are met before running the bridge
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

def check_mark(passed):
    return "✅" if passed else "❌"

def check_comfyui():
    """Check if ComfyUI is running"""
    try:
        urllib.request.urlopen("http://127.0.0.1:8188", timeout=2)
        return True, "ComfyUI is running on port 8188"
    except:
        return False, "ComfyUI is not running. Start it with: cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188"

def check_workflow():
    """Check if workflow file exists"""
    if Path("fashion_tagger_api.json").exists():
        try:
            with open("fashion_tagger_api.json") as f:
                workflow = json.load(f)
            return True, f"Workflow file found with {len(workflow)} nodes"
        except:
            return False, "Workflow file exists but is invalid JSON"
    else:
        return False, "Workflow file not found. Export from ComfyUI as 'fashion_tagger_api.json'"

def check_preferences():
    """Check if preference profile exists"""
    if Path("preference_profile.json").exists():
        try:
            with open("preference_profile.json") as f:
                prefs = json.load(f)
            liked = prefs.get("total_liked", 0)
            disliked = prefs.get("total_disliked", 0)
            return True, f"Preference profile found ({liked} liked, {disliked} disliked)"
        except:
            return False, "Preference file exists but is invalid JSON"
    else:
        return False, "Preference profile not found. Run: python update_preference_lib.py"

def check_server():
    """Check if server is accessible"""
    server_url = os.getenv("FASHIONXG_SERVER", "https://design.chermz112.xyz")
    try:
        import requests
        resp = requests.get(f"{server_url}/api/stats", timeout=10)
        resp.raise_for_status()
        return True, f"Server accessible at {server_url}"
    except Exception as e:
        return False, f"Cannot connect to server at {server_url}. Error: {str(e)[:50]}"

def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import requests
        import websocket
        return True, "All required packages installed"
    except ImportError as e:
        return False, f"Missing package: {e.name}. Run: pip install -r requirements_bridge.txt"

def check_comfyui_installation():
    """Check if ComfyUI is installed"""
    comfyui_path = Path.home() / "ComfyUI"
    if comfyui_path.exists():
        return True, f"ComfyUI found at {comfyui_path}"
    else:
        return False, "ComfyUI not found at ~/ComfyUI. Install it first."

def main():
    print("🍏 FashionXG Setup Checker")
    print("=" * 60)
    print()

    checks = [
        ("ComfyUI Installation", check_comfyui_installation),
        ("ComfyUI Running", check_comfyui),
        ("Workflow File", check_workflow),
        ("Preference Profile", check_preferences),
        ("Server Connection", check_server),
        ("Python Dependencies", check_dependencies),
    ]

    results = []
    for name, check_func in checks:
        passed, message = check_func()
        results.append((name, passed, message))
        print(f"{check_mark(passed)} {name}")
        print(f"   {message}")
        print()

    print("=" * 60)

    all_passed = all(passed for _, passed, _ in results)
    critical_passed = all(passed for name, passed, _ in results
                         if name in ["ComfyUI Running", "Workflow File", "Python Dependencies"])

    if all_passed:
        print("✅ All checks passed! You're ready to run the bridge.")
        print()
        print("Start the bridge with:")
        print("  ./start_bridge.sh")
        print()
        print("Or run directly:")
        print("  python comfy_bridge.py --batch-size 10 --sleep 5")
        return 0
    elif critical_passed:
        print("⚠️  Some optional checks failed, but you can still run the bridge.")
        print()
        print("Recommendations:")
        if not any(passed for name, passed, _ in results if name == "Preference Profile"):
            print("  - Run: python update_preference_lib.py")
        print()
        print("Start the bridge with:")
        print("  ./start_bridge.sh")
        return 0
    else:
        print("❌ Critical checks failed. Please fix the issues above before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
