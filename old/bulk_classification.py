import time
from src.zotero_api import zot, get_all_top_items
from src.llm_api import classify_paper
from src.config import COLLECTION_IDS

# --- CONFIGURATION ---
RATE_LIMIT_DELAY = 2  
DRY_RUN = False        

def pre_flight_check(items):
    """Scans the library for missing abstracts and prints a warning report."""
    print("\n--- 🔍 PRE-FLIGHT CHECK: MISSING ABSTRACTS ---")
    
    missing_abstracts = []
    for item in items:
        abstract = item['data'].get('abstractNote', '').strip()
        if not abstract:
            title = item['data'].get('title', 'Untitled')
            missing_abstracts.append(title)
            
    if missing_abstracts:
        print(f"⚠️ Found {len(missing_abstracts)} items missing an abstract:")
        for i, title in enumerate(missing_abstracts, 1):
            print(f"   {i}. {title[:80]}...")
        print("These items will be SKIPPED during this run.")
    else:
        print("✅ All items have abstracts! You are good to go.")
        
    print("----------------------------------------------\n")
    time.sleep(2) # Give the user a moment to read the report before starting

def run_bulk_process():
    mode_text = "🕵️ (DRY RUN MODE - NO CHANGES WILL BE SAVED)" if DRY_RUN else "🔥 (LIVE MODE - UPDATING ZOTERO)"
    print(f"--- STARTING BULK RETAG & CLASSIFICATION ---\n{mode_text}\n")
    
    try:
        items = get_all_top_items()
    except AttributeError:
        print("❌ ERROR: 'get_all_top_items' not found in src/zotero_api.py.")
        return

    print(f"📚 Found {len(items)} top-level items to process.")
    
    # Run the check before starting the heavy LLM lifting
    pre_flight_check(items)
    
    unclassified_id = COLLECTION_IDS.get("00 - Unclassified")
    
    for index, item in enumerate(items, start=1):
        title = item['data'].get('title', 'Untitled')
        abstract = item['data'].get('abstractNote', '').strip()
        old_tags = [t['tag'] for t in item['data'].get('tags', [])]
        
        # Skip items that were already flagged with "_CLASSIFIED" so we don't re-process them
        if "_CLASSIFIED" in old_tags:
            print(f"\n[{index}/{len(items)}] ⏭️ Skipping '{title[:50]}...' (Already Classified)")
            continue
            
        print(f"\n[{index}/{len(items)}] Title: {title[:75]}...")
        
        if not abstract:
            print("   ⏩ Skipping: No abstract found.")
            continue
            
        # 1. Ask the AI to classify and tag
        classification = classify_paper(title, abstract, existing_tags=[])
        
        if not classification:
            print("   ❌ Failed to get AI classification. Skipping.")
            continue
            
        raw_tags = classification['tags']
        clean_tags = [tag.strip().lower().replace(' ', '-') for tag in raw_tags]
        clean_tags.append("_CLASSIFIED")

        parent = classification["parent_category"]
        sub = classification["sub_category"]
        target_collection_key = f"{parent}/{sub}"
        target_collection_id = COLLECTION_IDS.get(target_collection_key)

        current_collections = item['data'].get('collections', [])
        is_unclassified = unclassified_id in current_collections
        
        # --- DRY RUN CONSOLE OUTPUT ---
        if DRY_RUN:
            print(f"   [PREVIEW] Old Tags: {old_tags}")
            print(f"   [PREVIEW] New Tags: {clean_tags}")
            if is_unclassified:
                if target_collection_id:
                    print(f"   [PREVIEW] Folder: Will move from '00 - Unclassified' -> '{target_collection_key}'")
                else:
                    print(f"   ⚠️ [WARNING] AI suggested folder '{target_collection_key}', but its ID is missing in config.py!")
            else:
                print(f"   [PREVIEW] Folder: Already classified (No move needed).")
            print("   [PREVIEW] Skipping save to Zotero.")

        # --- LIVE EXECUTION ---
        else:
            item['data']['tags'] = [{'tag': t} for t in clean_tags]
            
            if is_unclassified and target_collection_id:
                current_collections.remove(unclassified_id)
                current_collections.append(target_collection_id)
                item['data']['collections'] = current_collections
                print(f"   📁 Moving -> {target_collection_key}")
            
            try:
                zot.update_item(item)
                print(f"   ✅ Saved: Replaced {len(old_tags)} old tags with {len(clean_tags)} new AI tags.")
            except Exception as e:
                print(f"   ❌ Failed to update Zotero: {e}")
            
        # Respect Rate Limits
        if index < len(items):
            time.sleep(RATE_LIMIT_DELAY)

if __name__ == "__main__":
    run_bulk_process()
    if DRY_RUN:
        print("\n🏁 Dry run complete! If the preview looks good, change DRY_RUN = False and run again.")
    else:
        print("\n🎉 Bulk processing complete!")