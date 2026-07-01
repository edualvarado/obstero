# CLAUDE-context.md — Obstero

## Setup

Copy `.env.example` to `.env` and populate:

| Variable | Purpose |
|----------|---------|
| `ZOTERO_LIBRARY_ID` | Numeric Zotero user ID |
| `ZOTERO_API_KEY` | Zotero API key (read/write) |
| `CLAUDE_API_KEY` | Anthropic API key |
| `ZOTERO_BASE_DIR` | Root path to the ZotFile/OneDrive PDF folder |
| `OBSIDIAN_VAULT_PATH` | Absolute path to the Obsidian vault root |

Also copy the two personal config templates (both gitignored once populated):

```
cp config/collections.example.json config/collections.json   # or: python tools/id_extractor.py --write
cp config/primitives.example.json config/primitives.json     # or: python tools/discover_primitives.py --write
```

`src/config.py` hard-fails if `config/collections.json` is missing (classification
needs real collection keys to write to), but soft-falls-back to
`config/primitives.example.json` with a warning if `config/primitives.json` is
missing (auto-linking is a nice-to-have, not required for sync to work).

## CLI flags (argparse, replaces old hardcoded constants)

Every stage defaults to dry-run; pass `--live` to actually write.

| Flag | Scripts | Purpose |
|------|---------|---------|
| `--live` | 1, 2, 3, run_pipeline | Write to Zotero/Obsidian instead of previewing |
| `--all-items` | 1 | Scan entire library instead of just `00 - Unclassified` |
| `--max-items N` | 1 | Cap items processed per run |
| `--max-papers N` | 2 | Cap papers processed per run |
| `--chunk-size N` | 3 | Max files written per sync run |
| `--keep-ai-links` | 3 | Trust Claude's own `[[links]]` instead of re-injecting from `config/primitives.json` |
| `--rate-limit-delay N` | 1, 2 | Seconds between LLM calls |
| `--skip-classify` / `--skip-summarize` / `--skip-sync` | run_pipeline | Skip a stage in the orchestrated run |

Run `python 0X_*.py --help` or `python run_pipeline.py --help` for the full list.

## Key design details

**Tracking tags** — `_CLASSIFIED` and `_SUMMARIZED` are internal Zotero tags used as
idempotency markers. They are stripped before being shown to the LLM or written to Obsidian.

**Collection routing** — `COLLECTION_IDS`, loaded by `src/config.py` from
`config/collections.json`, maps human-readable folder paths to Zotero collection
keys. `VALID_FOLDERS` auto-derives the leaf-level targets (no parent folders).
Regenerate with `python tools/id_extractor.py --write` when the Zotero library
structure changes.

**PDF resolution** — `get_pdf_text_for_item()` handles two storage modes:
- Zotero-stored (`imported_file`)
- ZotFile/OneDrive linked (`linked_file`) — strips `attachments:` prefix, joins with `ZOTERO_BASE_DIR`

Files under 100 KB are treated as OneDrive stubs and skipped.

**Wiki-link injection** (Stage 3) — `format_obsidian_content()` first strips all
AI-generated links, then re-injects links only for the first occurrence of each term in
`PRIMITIVES_TO_LINK` (loaded from `config/primitives.json`, falling back to
`config/primitives.example.json` if missing). Entries with `|` define an alias
(`search_term|target_note`). Grow the list with `python tools/discover_primitives.py --write`.
