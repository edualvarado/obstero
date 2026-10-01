"""
One-off repair for literature notes written by older versions of 03_sync_to_obsidian.py.
Fixes only these defects and leaves everything else in each note untouched:
  1. Wiki-links injected inside frontmatter tags   ("3d-[[Mesh|mesh]]-generation" -> "3d-mesh-generation")
  2. up: parent link stripped                       (up: "07 - Mathematics" -> up: "[[07 - Mathematics]]")
  3. Raw <h2> HTML headings                         ("...#tag<h2>🎯 1. X</h2>" -> "...#tag\n\n### 🎯 1. X\n\n")
  4. Empty bullets                                  ("- \n**Core Primitives:**" -> "- **Core Primitives:**")
  5. Wiki-links injected inside body #tags          ("#[[RGB|rgb]]-d-perception" -> "#rgb-d-perception")
  6. Raw <hr />                                     ("...pipelines.<hr />" -> "...pipelines.\n\n---\n\n")
  7. Raw <blockquote>                               (standalone -> "> " lines; inside a bullet -> plain bullet text)
  8. Raw <code> (and any wiki-links inside it)      ("<code>[[MLP|MLP]](s)</code>" -> "`MLP(s)`")
  9. Raw <a href>                                   ('<a href="https://x.co">X</a>' -> "[X](https://x.co)")
By default it just prints a preview; pass --write to apply. Originals are copied to a backup folder outside the vault first.
"""

import argparse
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
BASE_LIT_FOLDER = "01 - Literature"

load_dotenv()
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

# [[target|text]] or [[text]] -> text (image embeds ![[...]] are left alone)
LINK = re.compile(r'(?<!\!)\[\[(?:[^\]|]*\|)?([^\]]*)\]\]')
TAGS_LINE = re.compile(r'(?m)^tags: \[.*$')
UP_UNLINKED = re.compile(r'(?m)^up: "(\d{2} - [^"\[\r\n]+)"(?=\r?$)')
RAW_HEADING = re.compile(r'\s*<h([1-6])>(.*?)</h\1>\s*')
EMPTY_BULLET = re.compile(r'(?m)^( *)- \r?\n(?=\S)(?!- )')
LINKED_BODY_TAG = re.compile(r'(?<!\S)#[\w/-]*(?:\[\[[^\]]*\]\][\w/-]*)+')
RAW_HR = re.compile(r'\s*<hr\s*/?>\s*')
BULLET_BLOCKQUOTE = re.compile(r'(?ms)^([ \t]*- )<blockquote>\s*(.*?)\s*</blockquote>')
RAW_BLOCKQUOTE = re.compile(r'(?s)\s*<blockquote>\s*(.*?)\s*</blockquote>\s*')
RAW_CODE = re.compile(r'<code>(.*?)</code>')
RAW_ANCHOR = re.compile(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>')

def repair_note(text, counts):
    """Returns the repaired note text, tallying each fix applied into counts."""
    if not text.startswith('---'):
        return text
    fm_end = text.find('\n---', 3)
    if fm_end == -1:
        return text
    frontmatter, body = text[:fm_end], text[fm_end:]
    nl = '\r\n' if '\r\n' in text else '\n'

    def unlink_tags(m):
        counts['frontmatter tag links'] += len(LINK.findall(m.group(0)))
        return LINK.sub(r'\1', m.group(0))
    frontmatter = TAGS_LINE.sub(unlink_tags, frontmatter)

    frontmatter, n = UP_UNLINKED.subn(r'up: "[[\1]]"', frontmatter)
    counts['up: links restored'] += n

    # Headings go one level down, matching the current sync output ("# 📄 title" is the only H1)
    def heading(m):
        return f"{nl}{nl}{'#' * (int(m.group(1)) + 1)} {m.group(2).strip()}{nl}{nl}"
    body, n = RAW_HEADING.subn(heading, body)
    counts['raw headings'] += n

    body, n = EMPTY_BULLET.subn(r'\1- ', body)
    counts['empty bullets'] += n

    def unlink_body_tag(m):
        counts['body tag links'] += 1
        return LINK.sub(r'\1', m.group(0))
    body = LINKED_BODY_TAG.sub(unlink_body_tag, body)

    # Blank line before "---" so it isn't read as a setext heading underline
    body, n = RAW_HR.subn(f"{nl}{nl}---{nl}{nl}", body)
    counts['raw <hr>'] += n

    body, n = BULLET_BLOCKQUOTE.subn(lambda m: m.group(1) + " ".join(m.group(2).splitlines()), body)
    counts['raw <blockquote>'] += n
    body, n = RAW_BLOCKQUOTE.subn(
        lambda m: nl + nl + nl.join(f"> {l}".rstrip() for l in m.group(1).splitlines()) + nl + nl, body)
    counts['raw <blockquote>'] += n

    body, n = RAW_CODE.subn(lambda m: "`" + LINK.sub(r'\1', m.group(1)) + "`", body)
    counts['raw <code>'] += n

    body, n = RAW_ANCHOR.subn(r'[\2](\1)', body)
    counts['raw <a href>'] += n

    return frontmatter + body

def repair_vault(write=False):
    if not OBSIDIAN_VAULT_PATH:
        print("❌ ERROR: OBSIDIAN_VAULT_PATH not found.")
        return

    vault = Path(OBSIDIAN_VAULT_PATH)
    target_dir = vault / BASE_LIT_FOLDER
    backup_dir = vault.parent / f"{vault.name} - repair backup {datetime.now():%Y-%m-%d %H%M%S}"
    mode_text = f"🔥 (WRITE MODE - backups go to {backup_dir})" if write else "🕵️ (PREVIEW MODE - NO FILES WILL BE CHANGED)"
    print(f"--- 🩹 REPAIRING LITERATURE NOTES IN: {target_dir} ---\n{mode_text}\n")

    counts = Counter()
    files_scanned = 0
    files_changed = 0

    for file_path in sorted(target_dir.rglob("*.md")):
        files_scanned += 1
        # newline='' keeps the file's own line endings untouched
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            original = f.read()

        repaired = repair_note(original, counts)
        if repaired == original:
            continue
        files_changed += 1

        if write:
            backup_path = backup_dir / file_path.relative_to(vault)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(repaired)

    print(f"✅ Scanned {files_scanned} files, {files_changed} need repair.")
    for fix, n in counts.most_common():
        print(f"   - {fix}: {n}")

    if write:
        print(f"\n💾 Repaired {files_changed} notes. Originals backed up to: {backup_dir}")
    else:
        print("\n👉 Preview only. Re-run with --write to apply (originals are backed up outside the vault first).")

def parse_args():
    parser = argparse.ArgumentParser(description="Repair formatting defects in existing Obsidian literature notes.")
    parser.add_argument("--write", action="store_true", help="Apply the repairs (originals are backed up outside the vault first).")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    repair_vault(write=args.write)
