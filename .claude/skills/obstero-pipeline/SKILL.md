---
name: obstero-pipeline
description: This skill should be used when the user asks to "run the full obstero pipeline", "process my Zotero library end to end", "classify, summarize, and sync", or invokes "/obstero-pipeline". Runs all three Obstero stages in sequence via run_pipeline.py instead of running each script by hand.
version: 1.0.0
---

# Obstero: Full Pipeline

Runs all three stages in order — classify → summarize → sync — via
`run_pipeline.py`, which imports and calls each stage's function directly
(no manual "run script 1, then 2, then 3").

## How to run it

Default is **dry-run** across all three stages. Only add `--live` after the
user reviews the combined preview and confirms.

```
conda run --no-capture-output -n obstero python run_pipeline.py                                   # dry-run, all 3 stages
conda run --no-capture-output -n obstero python run_pipeline.py --max-items 5 --max-papers 5        # dry-run, small sample of each stage
conda run --no-capture-output -n obstero python run_pipeline.py --live                              # actually run everything live
conda run --no-capture-output -n obstero python run_pipeline.py --live --skip-sync                  # classify + summarize live, skip vault sync
```

Skip flags: `--skip-classify`, `--skip-summarize`, `--skip-sync`.
Limits: `--max-items` (stage 1), `--max-papers` (stage 2), `--chunk-size` (stage 3).

## What to do

1. If this is the first run in this session, consider suggesting the
   `obstero-setup` skill first to confirm `.env` and `config/*.json` exist.
2. Run the dry-run command, and summarize what happened at each stage.
3. Only add `--live` once the user has reviewed the preview and explicitly
   asks to apply it — this stage writes to both the user's real Zotero
   library and their real Obsidian vault.
4. If the user only wants one stage, prefer the more specific
   `obstero-classify` / `obstero-summarize` / `obstero-sync` skill instead.
