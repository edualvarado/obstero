"""
This script discovers existing wiki-links in the Obsidian vault and identifies the most frequently used ones.
By default it just prints a preview; pass --write to merge newly-discovered concepts into config/primitives.json.
"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path
import re

from dotenv import load_dotenv

# --- CONFIGURATION ---
BASE_LIT_FOLDER = "01 - Literature"
TOP_N_RESULTS = 50  # How many top links to display

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "primitives.json"

load_dotenv()
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

def discover_existing_links(write=False):
    if not OBSIDIAN_VAULT_PATH:
        print("❌ ERROR: OBSIDIAN_VAULT_PATH not found.")
        return

    target_dir = Path(OBSIDIAN_VAULT_PATH) / BASE_LIT_FOLDER
    print(f"--- 🔍 SCANNING FOR EXISTING WIKI-LINKS IN: {target_dir} ---")

    link_counter = Counter()

    # Regex to find wiki-links, specifically ignoring image embeds like ![[image.png]]
    link_pattern = re.compile(r'(?<!\!)\[\[(.*?)\]\]')

    files_scanned = 0
    total_links_found = 0

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".md"):
                continue

            file_path = Path(root) / file
            files_scanned += 1

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            matches = link_pattern.findall(content)

            for match in matches:
                # 1. Strip off aliases
                target = match.split('|')[0]

                # 2. Strip off headings
                target = target.split('#')[0]

                # 3. Clean up whitespace
                target = target.strip()

                # 4. Filter out category titles (e.g., "01 - Digital Humans")
                if re.match(r'^\d+\s*-', target):
                    continue  # Skip this link and move to the next one

                # 5. We only want to count actual concepts
                if target and not target.endswith('.md'):
                    total_links_found += 1  # Moved this down so we only count valid links
                    link_counter[target] += 1

    print(f"✅ Scanned {files_scanned} files.")
    print(f"🔗 Found {total_links_found} total links.\n")
    print(f"🏆 TOP {TOP_N_RESULTS} MOST FREQUENT EXISTING LINKS:")
    print("-" * 50)

    top_links = link_counter.most_common(TOP_N_RESULTS)
    discovered = [link for link, _ in top_links]

    for link, count in top_links:
        print(f'    "{link}",  # Linked {count} times')

    if write:
        existing = []
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, encoding="utf-8") as f:
                existing = json.load(f)

        existing_targets = {entry.split('|')[-1] for entry in existing}
        new_entries = [term for term in discovered if term not in existing_targets and term not in existing]

        merged = existing + new_entries
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n💾 Added {len(new_entries)} new concepts to {CONFIG_PATH} ({len(merged)} total).")
    else:
        print(f"\n👉 Preview only. Re-run with --write to merge new concepts into {CONFIG_PATH}")

def parse_args():
    parser = argparse.ArgumentParser(description="Discover frequently-used wiki-links in the Obsidian vault.")
    parser.add_argument("--write", action="store_true", help=f"Merge newly discovered concepts into {CONFIG_PATH}.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    discover_existing_links(write=args.write)
