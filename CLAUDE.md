# CLAUDE.md — Obstero · Zotero→Obsidian pipeline

## Purpose
Three-stage automation pipeline for academic research management. Pulls papers from
Zotero, classifies and summarizes them via Claude, then syncs structured notes into
the Obsidian vault as `.md` files with injected wiki-links.

## Navigation
| Path | Contents |
|------|----------|
| `01_classification.py` | Stage 1 — classify papers into Zotero folders, add tags |
| `02_summary.py` | Stage 2 — extract PDF text, generate structured note via Claude |
| `03_sync_to_obsidian.py` | Stage 3 — convert Zotero notes to Markdown, inject wiki-links, write vault |
| `run_pipeline.py` | Orchestrator — runs all 3 stages in sequence with shared flags |
| `src/config.py` | `.env` + `config/*.json` loader; `COLLECTION_IDS`, `PRIMITIVES_TO_LINK`, `VALID_FOLDERS` |
| `src/zotero_api.py` | All Zotero I/O |
| `src/llm_api.py` | Claude calls: `classify_paper()` and `summarize_paper()` |
| `config/collections.json` / `config/primitives.json` | Personal, gitignored — real collection map and link taxonomy |
| `config/*.example.json` | Committed generic templates for the above |
| `tools/id_extractor.py` | Fetches Zotero collection key mapping; `--write` saves to `config/collections.json` |
| `tools/discover_primitives.py` | Scans vault for most-used wiki-links; `--write` merges into `config/primitives.json` |
| `.claude/skills/` | Claude Code skills wrapping each stage (`/obstero-classify`, `/obstero-summarize`, `/obstero-sync`, `/obstero-pipeline`, `/obstero-setup`) |
| `old/` | Superseded single-file scripts — ignore |

## Tech Stack
- Python; each stage is an argparse CLI (`python 01_classification.py --help`, etc.), or run all three via `run_pipeline.py`
- Zotero Web API (`pyzotero`) + local PDF access via ZotFile/OneDrive linked files
- Anthropic Claude API — Haiku for classification, Sonnet for summarization

## Conventions
- Every stage is dry-run by default — pass `--live` to actually write to Zotero/the vault
- `_CLASSIFIED` and `_SUMMARIZED` are idempotency tags — do not strip or rename them
- If Zotero library structure changes, regenerate `config/collections.json` with `python tools/id_extractor.py --write`
- Wiki-link injection: strips all AI-generated links first, then re-injects from `config/primitives.json` (`src.config.PRIMITIVES_TO_LINK`)
- Models: `claude-haiku-4-5-20251001` (classify) · `claude-sonnet-4-6` (summarize)

## Current Focus
Maintenance. Run order: Stage 1 → Stage 2 → Stage 3 (or `run_pipeline.py` for all three).

## Extended Context
- `CLAUDE-context.md` (same directory) — `.env`/`config/` setup, CLI flags per script, PDF resolution
  logic, collection routing details, wiki-link injection mechanics
