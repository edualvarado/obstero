import time
from src.zotero_api import zot, get_all_top_items, get_pdf_text_for_item, manage_ai_notes, add_note_to_item
from src.llm_api import summarize_paper

# --- CONFIGURATION ---
CHUNK_SIZE = 50         # How many papers to summarize per run (Change this to whatever you want)
RATE_LIMIT_DELAY = 5   # Wait 5 seconds between papers (Sonnet is heavy, give it time to breathe)

def run_bulk_summarizer():
    print(f"--- 🚀 STARTING BULK SUMMARIZER (CHUNK SIZE: {CHUNK_SIZE}) ---")
    
    # 1. Fetch all top-level items
    print("Fetching library database...")
    try:
        items = get_all_top_items()
    except Exception as e:
        print(f"❌ Failed to fetch items: {e}")
        return

    print(f"📚 Found {len(items)} total items in Zotero.")
    
    processed_count = 0
    
    for index, item in enumerate(items, start=1):
        title = item['data'].get('title', 'Untitled')
        item_key = item['key']
        raw_tags = item['data'].get('tags', [])
        current_tags = [t['tag'] for t in raw_tags]
        
        # 2. Skip items we've already summarized
        if "_SUMMARIZED" in current_tags:
            continue
            
        print(f"\n[{processed_count + 1}/{CHUNK_SIZE}] Target: {title[:70]}...")
        
        # 3. Check for attachments
        if item['meta'].get('numChildren', 0) == 0:
            print("   ⏩ Skipping: No attachments found.")
            continue
            
        # 4. Extract PDF text
        print("   📄 Extracting PDF text...")
        pdf_text = get_pdf_text_for_item(item_key)
        
        if not pdf_text:
            print("   ⏩ Skipping: Could not read PDF.")
            continue
            
        # 5. Generate the summary
        print("   🧠 Analyzing paper with Claude 3.7 Sonnet...")
        # Clean tags to feed to Claude (remove our internal trackers)
        ai_tags = [t for t in current_tags if t not in ['_CLASSIFIED', '_SUMMARIZED']]
        markdown_note = summarize_paper(title, pdf_text, ai_tags)
        
        if not markdown_note:
            print("   ❌ Failed to generate summary.")
            continue
            
        # 6. Save to Zotero and update tags
        manage_ai_notes(item_key) # Delete old AI notes
        
        print("   💾 Saving Note to Zotero...")
        success = add_note_to_item(item_key, markdown_note)
        
        if success:
            # Add the tracking tag so we don't process it again next time
            item['data']['tags'].append({'tag': '_SUMMARIZED'})
            try:
                zot.update_item(item)
                print("   ✅ Success! Tagged as _SUMMARIZED.")
                processed_count += 1
            except Exception as e:
                print(f"   ❌ Failed to update Zotero tags: {e}")
        else:
            print("   ❌ Failed to attach note.")
            
        # 7. Stop if we hit our chunk limit
        if processed_count >= CHUNK_SIZE:
            print(f"\n🛑 Reached chunk limit of {CHUNK_SIZE} papers.")
            break
            
        # Respect Rate Limits between papers
        print(f"   ⏳ Cooling down for {RATE_LIMIT_DELAY} seconds...")
        time.sleep(RATE_LIMIT_DELAY)

    if processed_count == 0:
        print("\n🎉 No unsummarized papers found! Your library is 100% up to date.")
    else:
        print(f"\n✅ Bulk summarization chunk complete! Processed {processed_count} papers.")

if __name__ == "__main__":
    run_bulk_summarizer()