---
name: obstero-summarize
description: This skill should be used when the user asks to "summarize my Zotero papers", "generate AI summaries", "run obstero summarization", or invokes "/obstero-summarize". Runs Stage 2 of the Obstero pipeline (02_summary.py), which extracts PDF text and has Claude write a structured research-intelligence note attached to each Zotero item.
version: 1.0.0
---

# Obstero: Summarize

Runs Stage 2 of the Obstero pipeline: finds Zotero items without a
`_SUMMARIZED` tag, extracts their PDF text, asks Claude to generate a
structured Markdown research note, and attaches it as a Zotero child note.

## How to run it

Default is **dry-run** — Claude still generates the summary (so you can
preview it) but nothing is saved to Zotero. Only add `--live` after the user
reviews the preview and confirms.

```
python 02_summary.py                          # dry-run, up to 50 papers, preview only
python 02_summary.py --max-papers 3            # dry-run, cap to 3 papers for a quick check
python 02_summary.py --live                     # actually save notes + _SUMMARIZED tag to Zotero
```

Other flags: `--rate-limit-delay N` (seconds between LLM calls, default 5 —
Sonnet needs a bit more breathing room than the Haiku classifier).

## What to do

1. Run the dry-run command (use `--max-papers` for a small sample if the user
   just wants to sanity-check quality before committing to a big batch —
   each paper costs an LLM call even in dry-run).
2. Show the user a preview of the generated summaries.
3. Only re-run with `--live` after explicit confirmation, since this writes
   permanent notes and tags to their real Zotero library.
4. Papers with no attachment, or a PDF that can't be read (e.g. a OneDrive
   placeholder under 100KB), are skipped automatically — mention this if it
   comes up.
