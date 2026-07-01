import argparse
import os
import re
import html
from pathlib import Path
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.config import PRIMITIVES_TO_LINK
from src.zotero_api import zot

# --- CONFIGURATION ---
BASE_LIT_FOLDER = "01 - Literature"
TARGET_TAG = "_SUMMARIZED"

load_dotenv()
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

def strip_all_links(content):
    """Strips all [[brackets]] but safely leaves the display text behind."""
    pattern = re.compile(r'(?<!\!)\[\[(.*?)\]\]')
    
    def replacer(match):
        inner_text = match.group(1)
        if '|' in inner_text:
            return inner_text.split('|', 1)[1]
        return inner_text.split('#')[0]
        
    return pattern.sub(replacer, content)

def auto_link_content(content, concept_entry):
    """Safely injects wiki-links ONLY on the first occurrence in the text."""
    if '|' in concept_entry:
        search_term, target_note = concept_entry.split('|', 1)
    else:
        search_term = concept_entry
        target_note = concept_entry

    parts = re.split(r'(\[\[.*?\]\])', content)
    pattern = rf'\b({re.escape(search_term)})\b'
    
    for i in range(0, len(parts), 2):
        if re.search(pattern, parts[i], flags=re.IGNORECASE):
            parts[i] = re.sub(pattern, rf'[[{target_note}|\1]]', parts[i], count=1, flags=re.IGNORECASE)
            break
            
    return "".join(parts)

def format_obsidian_content(raw_content, keep_ai_links=False):
    """The master formatting switchboard."""
    if keep_ai_links:
        return raw_content  # Do nothing, trust the AI
        
    # Phase 1: The Nuke
    cleaned_content = strip_all_links(raw_content)
    
    # Phase 2: The Pave
    sorted_concepts = sorted(list(set(PRIMITIVES_TO_LINK)), key=len, reverse=True)
    final_content = cleaned_content
    
    for concept in sorted_concepts:
        final_content = auto_link_content(final_content, concept)
        
    return final_content

def clean_filename(title):
    cleaned = title.replace(":", " -").replace("/", "-").replace("\\", "-")
    return re.sub(r'[?*<>|"]', '', cleaned).strip()

def html_to_markdown(html_content):
    text = html_content
    text = re.sub(r'<(?:strong|b)>', '**', text)
    text = re.sub(r'</(?:strong|b)>', '**', text)
    text = re.sub(r'<(?:em|i)>', '*', text)
    text = re.sub(r'</(?:em|i)>', '*', text)
    
    lines = []
    level = -1
    tokens = re.split(r'(<(?:ul|ol|li|/ul|/ol|/li|p|div|br|/p|/div)[^>]*>)', text, flags=re.IGNORECASE)
    
    for token in tokens:
        clean_t = token.lower()
        if '<ul' in clean_t or '<ol' in clean_t:
            level += 1
        elif '</ul' in clean_t or '</ol' in clean_t:
            level -= 1
        elif '<li' in clean_t:
            indent = "    " * level 
            lines.append(f"\n{indent}- ")
        elif '<p' in clean_t or '<div' in clean_t or '<br' in clean_t:
            lines.append("\n")
        elif token.startswith('<'):
            continue 
        else:
            content = html.unescape(token).strip()
            if content:
                lines.append(content)

    text = "".join(lines)
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def get_full_collection_path(item, all_collections):
    if not item['data'].get('collections'):
        return []
    col_key = item['data']['collections'][0]
    col = next((c for c in all_collections if c['key'] == col_key), None)
    if not col: return []
    
    path_parts = [col['data']['name']]
    parent_key = col['data'].get('parentCollection')
    while parent_key:
        parent = next((c for c in all_collections if c['key'] == parent_key), None)
        if parent:
            path_parts.insert(0, parent['data']['name'])
            parent_key = parent['data'].get('parentCollection')
        else:
            parent_key = None
    return path_parts

def run_sync(dry_run=True, chunk_size=1000, keep_ai_links=False):
    mode_text = "🕵️ (DRY RUN MODE - NO FILES WILL BE WRITTEN)" if dry_run else "🔥 (LIVE MODE - WRITING TO VAULT)"
    print(f"--- 🔄 SYNCING TO: {OBSIDIAN_VAULT_PATH} ---\n{mode_text}\n")
    all_collections = zot.all_collections()
    items = zot.everything(zot.top(tag=TARGET_TAG))

    processed_count = 0
    for item in items:
        if processed_count >= chunk_size: break

        data = item['data']
        title = data.get('title', 'Untitled')
        safe_title = clean_filename(title)
        
        # --- FOLDER & PARENT LOGIC ---
        path_parts = get_full_collection_path(item, all_collections)
        rel_path = "/".join(path_parts) if path_parts else "Unsorted"
        
        # Identify the Parent Note (Text Type)
        # Finds the numbered category (e.g., "03 - Biomechanics")
        parent_name = ""
        for part in path_parts:
            if re.match(r'^\d{2}\s-', part):
                parent_name = part
                break
        
        dest_dir = Path(OBSIDIAN_VAULT_PATH) / BASE_LIT_FOLDER / rel_path
        dest_file = dest_dir / f"{safe_title}.md"

        if dest_file.exists():
            continue

        # Metadata extraction
        extra = data.get('extra', '')
        citekey_match = re.search(r'Citation Key:\s*(\S+)', extra)
        citekey = citekey_match.group(1) if citekey_match else data.get('key')
        authors_list = [c.get('lastName', '') for c in data.get('creators', []) if 'lastName' in c]
        authors_str = ", ".join(authors_list)
        
        raw_date = data.get('date', '')
        year_match = re.search(r'\d{4}', raw_date)
        year = year_match.group(0) if year_match else "n.d."
        
        raw_tags = [t['tag'] for t in data.get('tags', [])]
        cleaned_tags = [t for t in raw_tags if t not in ['_SUMMARIZED', '_CLASSIFIED']]
        for default_tag in ['literature', 'research-intelligence']:
            if default_tag not in cleaned_tags: cleaned_tags.append(default_tag)
        yaml_tags = ", ".join([f'"{t}"' for t in cleaned_tags])

        # Link extraction
        children = zot.children(item['key'])
        pdf_link = ""
        for child in children:
            if child['data'].get('contentType') == 'application/pdf':
                pdf_link = f"| [Open PDF](zotero://open-pdf/library/items/{child['key']})"
                break

        # Process Notes
        notes = [n for n in children if n['data'].get('itemType') == 'note']
        summary_content = "\n".join([html_to_markdown(n['data']['note']) for n in notes])

        # Template with UP Link
        markdown = f"""---
type: literature
up: "[[{parent_name}]]"
citekey: "{citekey}"
authors: ["{authors_str}"]
year: "{year}"
url: "{data.get('url', '')}"
tags: [{yaml_tags}]
---

# 📄 {title}

**Links:** [Open in Zotero](zotero://select/library/items/{item['key']}) {pdf_link}

---

## 🤖 AI-Generated Intelligence

{summary_content}
"""

        if dry_run:
            print(f"   [PREVIEW] [{processed_count + 1}/{chunk_size}] Would import: {safe_title} -> {rel_path}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)

            final_formatted_summary = format_obsidian_content(markdown, keep_ai_links=keep_ai_links)

            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(final_formatted_summary)

            print(f"✅ [{processed_count + 1}/{chunk_size}] Imported: {safe_title}")

        processed_count += 1

    if dry_run:
        print(f"\n🏁 Dry run complete! Would have imported {processed_count} notes. Re-run with --live to write them.")
    else:
        print(f"\n✅ Sync complete! Imported {processed_count} notes.")

def parse_args():
    parser = argparse.ArgumentParser(description="Sync summarized Zotero papers into the Obsidian vault as Markdown notes.")
    parser.add_argument("--live", action="store_true", help="Actually write Markdown files to the vault (default: dry-run preview).")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Max number of files to write per run.")
    parser.add_argument("--keep-ai-links", action="store_true", help="Trust Claude's own [[wiki-links]] instead of re-injecting from config/primitives.json.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_sync(
        dry_run=not args.live,
        chunk_size=args.chunk_size,
        keep_ai_links=args.keep_ai_links,
    )