---
name: obstero-setup
description: This skill should be used when the user asks to "set up obstero", "configure obstero for the first time", "onboard obstero", or invokes "/obstero-setup". Checks .env and config/*.json exist (or guides creating them from the example files) before running any pipeline stage.
version: 1.0.0
---

# Obstero: First-Time Setup

Obstero needs three things before any pipeline stage will work: a `.env` with
credentials, `config/collections.json` (which Zotero collection each folder
path maps to), and `config/primitives.json` (optional, but improves
auto-linking quality). All three are gitignored — only the `*.example.json` /
`.env.example` files are committed.

## What to check, in order

1. **`obstero` conda env** — all commands run via
   `conda run --no-capture-output -n obstero python ...`. If `conda env list`
   doesn't show it, create it: `conda create -y -n obstero python=3.12`, then
   `conda run -n obstero pip install -r requirements.txt`.

2. **`.env`** — if missing, tell the user to `cp .env.example .env` and fill
   in `ZOTERO_LIBRARY_ID`, `ZOTERO_API_KEY`, `CLAUDE_API_KEY`,
   `ZOTERO_BASE_DIR`, `OBSIDIAN_VAULT_PATH`. Don't attempt to fill these in
   for them — they're credentials/paths only the user has.

3. **`config/collections.json`** — if missing, run
   `conda run --no-capture-output -n obstero python tools/id_extractor.py` (no `--write`) first to preview the
   discovered Zotero collection mapping, show it to the user, then re-run
   with `--write` to save it to `config/collections.json`. This requires
   `.env` to already have valid Zotero credentials.

4. **`config/primitives.json`** — if missing, this is optional (sync falls
   back to a generic example automatically), but mention that running
   `conda run --no-capture-output -n obstero python tools/discover_primitives.py --write` will seed it from whatever
   wiki-links already exist in their Obsidian vault. If the vault has no
   existing literature notes yet, it's fine to skip this and just copy
   `config/primitives.example.json` to `config/primitives.json` as a
   starting point, or leave it unset for now.

5. Once all of the above are in place, suggest a dry-run of a single item as a smoke test:
   `conda run --no-capture-output -n obstero python 01_classification.py --max-items 1`.

## What not to do

- Never print the contents of `.env` or paste API keys into chat.
- Never run any stage with `--live` as part of setup — setup only prepares
  config, it doesn't process the library.
