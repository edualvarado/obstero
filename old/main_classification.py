import time
from src.zotero_api import get_unclassified_items, get_all_tags, update_item_classification
from src.llm_api import classify_paper

# --- CONFIGURATION ---
RATE_LIMIT_DELAY = 2  # Keeps you safely under Anthropic's Tier 1 limits

def run_pipeline():
    print("--- 🚀 STARTING ZOTERO DAILY CLASSIFIER ---")
    
    # 1. Fetch existing tags to guide the LLM
    print("Fetching existing tags for context...")
    existing_tags = get_all_tags()
    
    # Filter out the tracker tag so we don't confuse the LLM
    tag_names = [t for t in existing_tags if t != "_CLASSIFIED"] 
    
    # 2. Fetch items waiting to be processed
    items = get_unclassified_items()
    
    if not items:
        print("✅ '00 - Unclassified' is empty. Everything is up to date!")
        return

    print(f"📚 Found {len(items)} items to process in '00 - Unclassified'.\n")
    
    for index, item in enumerate(items, start=1):
        title = item['data'].get('title', 'No Title')
        abstract = item['data'].get('abstractNote', '').strip()
        
        print(f"[{index}/{len(items)}] Processing: {title[:70]}...")
        
        if not abstract:
            print("   ⏩ Skipping: No abstract found for LLM to read.")
            continue
            
        # 3. Ask the AI to classify it
        classification = classify_paper(title, abstract, tag_names)
        
        if not classification:
            print("   ❌ Failed to get AI classification. Skipping.")
            continue
            
        # --- ENFORCE STRICT TAG RULES ---
        # Force lowercase, replace spaces with hyphens, and add our tracker
        raw_tags = classification.get('tags', [])
        clean_tags = [tag.strip().lower().replace(' ', '-') for tag in raw_tags]
        
        if "_CLASSIFIED" not in clean_tags:
            clean_tags.append("_CLASSIFIED")
            
        # Overwrite the classification dictionary with our perfectly clean tags
        classification['tags'] = clean_tags
        # --------------------------------

        print(f"   🤖 AI Folder: {classification.get('target_folder')}")
        print(f"   🏷️  Tags: {clean_tags}")
        
        # 4. Update Zotero
        success = update_item_classification(item, classification)
        if success:
             print("   ✅ Successfully updated and moved item.")
        else:
             print("   ❌ Failed to update Zotero.")
             
        # 5. Respect Rate Limits
        if index < len(items):
            time.sleep(RATE_LIMIT_DELAY)

    print("\n🎉 Daily classification complete!")

if __name__ == "__main__":
    run_pipeline()