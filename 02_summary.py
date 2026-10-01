import argparse
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from src.zotero_api import zot, get_all_top_items, get_pdf_text_for_item, manage_ai_notes, add_note_to_item
from src.llm_api import summarize_paper

def run_summary_pipeline(dry_run=True, max_papers=50, rate_limit_delay=5):
    mode_text = "🕵️ (DRY RUN MODE - NO CHANGES WILL BE SAVED)" if dry_run else "🔥 (LIVE MODE - UPDATING ZOTERO)"
    print(f"--- 🚀 STARTING ZOTERO SUMMARIZER (LIMIT: {max_papers}) ---\n{mode_text}\n")

    # 1. Fetch library database
    print("Fetching library database...")
    try:
        items = get_all_top_items()
    except Exception as e:
        print(f"❌ Failed to fetch items: {e}")
        return

    print(f"📚 Found {len(items)} total top-level items in Zotero.")

    # 2. Filter for items that actually need summarizing
    items_to_process = []
    for item in items:
        current_tags = [t['tag'] for t in item['data'].get('tags', [])]
        if "_SUMMARIZED" not in current_tags:
            items_to_process.append((item, current_tags))

    if not items_to_process:
        print("\n🎉 No unsummarized papers found! Your library is 100% up to date.")
        return

    print(f"📄 Found {len(items_to_process)} papers waiting for summaries.")

    # 3. Process the queue
    processed_count = 0
    attempted_count = 0  # Claude calls made — max_papers caps this, so failures still count toward the limit

    for item, current_tags in items_to_process:
        title = item['data'].get('title', 'Untitled')
        item_key = item['key']

        print(f"\n[{attempted_count + 1}/{max_papers}] Target: {title[:70]}...")

        # Check for attachments
        if item['meta'].get('numChildren', 0) == 0:
            print("   ⏩ Skipping: No attachments found.")
            continue

        # Extract PDF text
        print("   📄 Extracting PDF text...")
        pdf_text = get_pdf_text_for_item(item_key)

        if not pdf_text:
            print("   ⏩ Skipping: Could not read PDF.")
            continue

        print(f"   ✅ Extracted {len(pdf_text)} characters from PDF.")

        # Analyze and Summarize
        print("   🧠 Analyzing paper with Claude...")

        # Clean tags to feed to Claude (hide internal trackers)
        ai_tags = [t for t in current_tags if t not in ['_CLASSIFIED', '_SUMMARIZED']]
        attempted_count += 1
        markdown_note = summarize_paper(title, pdf_text, ai_tags)

        if not markdown_note:
            print("   ❌ Failed to generate summary.")
        elif dry_run:
            print("   [PREVIEW] Generated summary (not saved):")
            print(f"   {markdown_note[:300]}...")
            processed_count += 1
        else:
            # Save to Zotero
            manage_ai_notes(item_key) # Delete old AI notes

            print("   💾 Saving Note to Zotero...")
            success = add_note_to_item(item_key, markdown_note)

            if success:
                # Tag the parent item so we don't process it again
                item['data']['tags'].append({'tag': '_SUMMARIZED'})
                try:
                    zot.update_item(item)
                    print("   ✅ Success! Tagged as _SUMMARIZED.")
                    processed_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to update Zotero tags: {e}")
            else:
                print("   ❌ Failed to attach note.")

        # Stop if we hit our configured limit
        if attempted_count >= max_papers:
            print(f"\n🛑 Reached configured limit of {max_papers} papers.")
            break

        # Respect Rate Limits between papers
        if attempted_count < max_papers:
            print(f"   ⏳ Cooling down for {rate_limit_delay} seconds...")
            time.sleep(rate_limit_delay)

    if dry_run:
        print(f"\n🏁 Dry run complete! Previewed {processed_count} summaries. Re-run with --live to save them.")
    else:
        print(f"\n✅ Summarization pipeline complete! Processed {processed_count} papers.")

def parse_args():
    parser = argparse.ArgumentParser(description="Summarize Zotero papers via Claude and attach them as notes.")
    parser.add_argument("--live", action="store_true", help="Actually save notes/tags to Zotero (default: dry-run preview).")
    parser.add_argument("--max-papers", type=int, default=50, help="Cap the number of papers processed per run.")
    parser.add_argument("--rate-limit-delay", type=float, default=5, help="Seconds to wait between LLM calls.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_summary_pipeline(
        dry_run=not args.live,
        max_papers=args.max_papers,
        rate_limit_delay=args.rate_limit_delay,
    )
