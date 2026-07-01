---
name: obstero-sync
description: This skill should be used when the user asks to "sync to Obsidian", "export Zotero notes to my vault", "run obstero sync", or invokes "/obstero-sync". Runs Stage 3 of the Obstero pipeline (03_sync_to_obsidian.py), converting summarized Zotero items into Markdown notes with auto-injected wiki-links in the Obsidian vault.
version: 1.0.0
---

# Obstero: Sync to Obsidian

Runs Stage 3 of the Obstero pipeline: for every Zotero item tagged
`_SUMMARIZED`, writes (or skips, if the file already exists) a Markdown note
into `OBSIDIAN_VAULT_PATH/01 - Literature/<collection path>/`, converting the
AI note to Markdown and auto-linking concepts from `config/primitives.json`.

## How to run it

Default is **dry-run** — lists what would be written without touching the
vault. Only add `--live` after the user confirms.

```
python 03_sync_to_obsidian.py                          # dry-run preview
python 03_sync_to_obsidian.py --chunk-size 20           # dry-run, cap to 20 files
python 03_sync_to_obsidian.py --live                     # actually write Markdown files
python 03_sync_to_obsidian.py --live --keep-ai-links     # write files, trust Claude's own [[links]] instead of re-injecting from config/primitives.json
```

## What to do

1. Run the dry-run command and report how many notes would be created and
   where.
2. Only re-run with `--live` after explicit confirmation — this writes real
   files into the user's Obsidian vault (though it never overwrites existing
   notes; it always skips files that already exist at the destination path).
3. If `config/primitives.json` is missing, sync still works — it falls back
   to the small generic example and warns about it. Suggest running
   `python tools/discover_primitives.py --write` to build a real taxonomy
   from the vault's existing links.
