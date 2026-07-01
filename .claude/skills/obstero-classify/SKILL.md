---
name: obstero-classify
description: This skill should be used when the user asks to "classify my Zotero papers", "run obstero classification", "sort unclassified papers", or invokes "/obstero-classify". Runs Stage 1 of the Obstero pipeline (01_classification.py), which uses Claude to sort unclassified Zotero items into folders and tags.
version: 1.0.0
---

# Obstero: Classify

Runs Stage 1 of the Obstero pipeline: fetches unclassified Zotero items,
asks Claude to pick a target folder (from `config/collections.json`) and 3-5
tags per item, then moves/tags the item in Zotero.

## How to run it

Always start in **dry-run** (the default — no flag needed). Only add `--live`
after the user has reviewed the dry-run preview and explicitly confirms.

```
python 01_classification.py                          # dry-run, only '00 - Unclassified' folder
python 01_classification.py --all-items               # dry-run, entire library
python 01_classification.py --max-items 5             # dry-run, cap to 5 items (good for a quick check)
python 01_classification.py --live                     # actually write to Zotero
```

Other flags: `--rate-limit-delay N` (seconds between LLM calls, default 2).

## What to do

1. Run the dry-run command (add `--max-items` if the user just wants a quick
   sanity check rather than the whole backlog).
2. Summarize the preview: how many items, what folders/tags were suggested.
3. If the user wants to apply it, re-run the same command with `--live` —
   this writes to their real Zotero library, so only do it after explicit
   confirmation.
4. If `config/collections.json` is missing, tell the user to run
   `python tools/id_extractor.py --write` first (see the `obstero-setup` skill).
