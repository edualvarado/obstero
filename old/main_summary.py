from src.zotero_api import zot, get_pdf_text_for_item, manage_ai_notes, add_note_to_item
from src.llm_api import summarize_paper

def test_single_summary():
    print("--- 🧪 TESTING FULL-PDF OBSIDIAN SUMMARY ---")
    
    # Grab recent items and find one with a PDF attachment
    items = zot.top(limit=15)
    target_item = None
    
    for item in items:
        # Check if it has an attachment
        if item['meta'].get('numChildren', 0) > 0:
            target_item = item
            break
            
    if not target_item:
        print("❌ Could not find an item with an attachment to test on.")
        return

    title = target_item['data'].get('title', 'Untitled')
    item_key = target_item['key']
    raw_tags = target_item['data'].get('tags', [])
    clean_tags = [t['tag'] for t in raw_tags if t['tag'] not in ['_CLASSIFIED', '_SUMMARIZED']]

    print(f"\n📚 Target Paper: {title}")
    
    # 1. Read PDF
    print("📄 Extracting text from attached PDF...")
    pdf_text = get_pdf_text_for_item(item_key)
    
    if not pdf_text:
        print("❌ No readable PDF found for this item.")
        return
        
    print(f"✅ Extracted {len(pdf_text)} characters from PDF.")
    
    # 2. Generate Summary
    print("🧠 Asking Claude 3.7 Sonnet to read the paper and write summary...")
    markdown_note = summarize_paper(title, pdf_text, clean_tags)
    
    if not markdown_note:
        return

    # 3. Delete old notes & Save new one
    manage_ai_notes(item_key)
    
    print("💾 Saving as a Note in Zotero...")
    success = add_note_to_item(item_key, markdown_note)
    
    if success:
        # 4. Update the parent item with _SUMMARIZED tag
        if "_SUMMARIZED" not in [t['tag'] for t in target_item['data'].get('tags', [])]:
            target_item['data']['tags'].append({'tag': '_SUMMARIZED'})
            zot.update_item(target_item)
            
        print("✅ Success! Open Zotero to see your new generated note and tag.")
    else:
        print("❌ Failed to attach note to Zotero item.")

if __name__ == "__main__":
    test_single_summary()