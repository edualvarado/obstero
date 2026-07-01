"""
This script scans all markdown files in the specified Obsidian vault folder for wiki-links and normalizes them to a consistent format.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURATION ---
DRY_RUN = True  # ⚠️ Keep this True for the first test!
BASE_LIT_FOLDER = "01 - Literature"

load_dotenv()
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

LINK_PATTERN = re.compile(r'(?<!\!)\[\[(.*?)\]\]')

def smart_title(text):
    """Capitalizes words but preserves acronyms and CamelCase."""
    def replace_word(m):
        w = m.group(0)
        # If the word is fully uppercase (KTH) or has internal capitals (ImageNet),
        # we preserve its casing but ensure the very first letter is capitalized.
        if w.isupper() or any(c.isupper() for c in w[1:]):
            return w[0].upper() + w[1:]
        # Otherwise, capitalize it normally (dataset -> Dataset)
        return w.capitalize()
        
    # Apply this logic to every sequence of letters in the string
    return re.sub(r'[a-zA-Z]+', replace_word, text)

def normalize_match(match):
    inner_text = match.group(1)
    
    # 1. Handle Aliases (e.g., [[Target|alias]])
    if '|' in inner_text:
        target, alias = inner_text.split('|', 1)
    else:
        target = inner_text
        alias = None
        
    # 2. Handle Headings (e.g., [[Target#Heading]])
    if '#' in target:
        page, heading = target.split('#', 1)
    else:
        page = target
        heading = None
        
    # 3. Apply SMART Title Case to the Page Name
    if page and not re.search(r'\.[a-zA-Z0-9]{2,4}$', page):
        page = smart_title(page.strip())
        
    # 4. Reconstruct the link perfectly
    reconstructed = page if page else ""
    if heading is not None:
        reconstructed += f"#{heading}"
    if alias is not None:
        reconstructed += f"|{alias}"
        
    return f"[[{reconstructed}]]"

def run_normalizer():
    if not OBSIDIAN_VAULT_PATH:
        print("❌ ERROR: OBSIDIAN_VAULT_PATH not found in .env file.")
        return

    target_dir = Path(OBSIDIAN_VAULT_PATH) / BASE_LIT_FOLDER
    print(f"--- 🔍 SCANNING FOR WIKI-LINKS IN: {target_dir} ---")
    
    if DRY_RUN:
        print("🕵️ DRY RUN MODE: No files will be changed.\n")
    else:
        print("🔥 LIVE MODE: Updating markdown files...\n")

    files_modified = 0
    links_updated = 0

    for root, _, files in os.walk(target_dir):
        for file in files:
            if not file.endswith(".md"):
                continue
                
            file_path = Path(root) / file
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            matches = LINK_PATTERN.findall(content)
            if not matches:
                continue

            new_content, num_subs = LINK_PATTERN.subn(normalize_match, content)
            
            if new_content != content:
                files_modified += 1
                links_updated += num_subs
                print(f"📄 {file}:")
                
                if DRY_RUN:
                    old_links = LINK_PATTERN.findall(content)
                    new_links = LINK_PATTERN.findall(new_content)
                    for old, new in zip(old_links, new_links):
                        if old != new:
                            print(f"   - [[{old}]]  ➡️  [[{new}]]")
                
                if not DRY_RUN:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"   ✅ Saved {num_subs} link updates.")

    print("\n-------------------------------------------------")
    print(f"🏁 Done! Scanned library.")
    if DRY_RUN:
        print(f"👀 PREVIEW: Would have updated {links_updated} links across {files_modified} files.")
        print("👉 To apply these changes, set DRY_RUN = False and run again.")
    else:
        print(f"🎉 SUCCESS: Updated {links_updated} links across {files_modified} files.")

if __name__ == "__main__":
    run_normalizer()