"""
This script connects to the Zotero API, retrieves all collections, and prints a dictionary mapping collection paths to their unique keys.
Pass --write to save the result directly to config/collections.json.
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pyzotero import zotero
from pyzotero.zotero_errors import HTTPError

# Load environment variables
load_dotenv()

ZOTERO_LIBRARY_ID = os.getenv("ZOTERO_LIBRARY_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "collections.json"

def check_credentials():
    print("--- 🔍 DIAGNOSTIC CHECK ---")

    # Check Library ID
    if not ZOTERO_LIBRARY_ID:
        print("❌ ERROR: ZOTERO_LIBRARY_ID is empty. The .env file might not be loading.")
    else:
        print(f"✅ Library ID found: {ZOTERO_LIBRARY_ID}")

    # Check API Key
    if not ZOTERO_API_KEY:
        print("❌ ERROR: ZOTERO_API_KEY is empty.")
    else:
        # Mask the key for security: shows first 5 and last 3 characters
        masked_key = f"{ZOTERO_API_KEY[:5]}...{ZOTERO_API_KEY[-3:]}"
        print(f"✅ API Key found: {masked_key}")

    print("---------------------------\n")
    return bool(ZOTERO_LIBRARY_ID and ZOTERO_API_KEY)

def fetch_collection_mapping(write=False):
    if not check_credentials():
        return

    print("Connecting to Zotero API...")
    # 'user' indicates a personal library. If it's a group library, this should be 'group'
    zot = zotero.Zotero(ZOTERO_LIBRARY_ID, 'user', ZOTERO_API_KEY)

    try:
        collections = zot.collections()
        print(f"✅ Success! Found {len(collections)} collections.\n")
    except HTTPError as e:
        print(f"❌ API HTTP ERROR: Zotero rejected the request.")
        print(f"Details: {e}")
        print("-> Double-check your API key and ensure it has 'Read' permissions.")
        return
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return

    # If it works, process and print the dictionary
    col_dict = {c['key']: c['data'] for c in collections}

    def build_path(col_key):
        data = col_dict[col_key]
        name = data['name']
        parent_key = data.get('parentCollection')
        if parent_key and parent_key in col_dict:
            return f"{build_path(parent_key)}/{name}"
        return name

    path_to_key = {build_path(key): key for key in col_dict}
    sorted_mapping = {path: path_to_key[path] for path in sorted(path_to_key.keys())}

    if write:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"💾 Wrote {len(sorted_mapping)} collections to {CONFIG_PATH}")
    else:
        print(json.dumps(sorted_mapping, indent=2, ensure_ascii=False))
        print(f"\n👉 Preview only. Re-run with --write to save this to {CONFIG_PATH}")

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch your Zotero collection key mapping.")
    parser.add_argument("--write", action="store_true", help=f"Save the mapping to {CONFIG_PATH} instead of just printing it.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    fetch_collection_mapping(write=args.write)
