import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from src.zotero_api import zot, get_all_top_items, get_pdf_text_for_item, manage_ai_notes, add_note_to_item
from src.llm_api import summarize_paper

# --- CONFIGURATION ---
MAX_PAPERS_TO_PROCESS = 50  # Set to 1 for testing, or a higher number for bulk processing
RATE_LIMIT_DELAY = 5        # Seconds to wait between LLM calls (Claude 3.7 Sonnet needs time to breathe)

def run_summary_pipeline():
    print(f"--- 🚀 STARTING ZOTERO SUMMARIZER (LIMIT: {MAX_PAPERS_TO_PROCESS}) ---")
    
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
    
    for item, current_tags in items_to_process:
        title = item['data'].get('title', 'Untitled')
        item_key = item['key']
        
        print(f"\n[{processed_count + 1}/{MAX_PAPERS_TO_PROCESS}] Target: {title[:70]}...")
        
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
        markdown_note = summarize_paper(title, pdf_text, ai_tags)
        
        if not markdown_note:
            print("   ❌ Failed to generate summary.")
            continue
            
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
        if processed_count >= MAX_PAPERS_TO_PROCESS:
            print(f"\n🛑 Reached configured limit of {MAX_PAPERS_TO_PROCESS} papers.")
            break
            
        # Respect Rate Limits between papers
        if processed_count < MAX_PAPERS_TO_PROCESS:
            print(f"   ⏳ Cooling down for {RATE_LIMIT_DELAY} seconds...")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n✅ Summarization pipeline complete! Processed {processed_count} papers.")

if __name__ == "__main__":
    run_summary_pipeline()