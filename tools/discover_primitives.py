"""
This script discovers existing wiki-links in the Obsidian vault and identifies the most frequently used ones.
It outputs a list of primitives that can be used for auto-linking new notes to existing concepts.
"""

import os
import re
from collections import Counter
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURATION ---
BASE_LIT_FOLDER = "01 - Literature"
TOP_N_RESULTS = 50  # How many top links to display

load_dotenv()
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

def discover_existing_links():
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
                
                # 4. NEW: Filter out category titles (e.g., "01 - Digital Humans")
                # This regex looks for 1 or more digits at the very start (^), followed by a hyphen
                if re.match(r'^\d+\s*-', target):
                    continue  # Skip this link and move to the next one
                
                # 5. We only want to count actual concepts
                if target and not target.endswith('.md'):
                    total_links_found += 1 # Moved this down so we only count valid links
                    link_counter[target] += 1

    print(f"✅ Scanned {files_scanned} files.")
    print(f"🔗 Found {total_links_found} total links.\n")
    print(f"🏆 TOP {TOP_N_RESULTS} MOST FREQUENT EXISTING LINKS:")
    print("-" * 50)
    
    top_links = link_counter.most_common(TOP_N_RESULTS)
    
    # Format the output perfectly for your auto_linker.py script
    print("PRIMITIVES_TO_LINK = [")
    for link, count in top_links:
        print(f'    "{link}",  # Linked {count} times')
    print("]")

if __name__ == "__main__":
    discover_existing_links()