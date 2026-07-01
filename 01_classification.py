import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from src.zotero_api import get_all_top_items, get_unclassified_items, get_all_tags, update_item_classification
from src.llm_api import classify_paper

# --- CONFIGURATION ---
DRY_RUN = False                # Set to False to actually modify Zotero
TARGET_UNCLASSIFIED = True    # If True, only scans "00 - Unclassified". If False, scans entire library.
MAX_ITEMS = 0                 # Set to >0 to process only N items (e.g., 1 for testing). Set to 0 to process all.
RATE_LIMIT_DELAY = 2          # Seconds to wait between LLM calls to prevent rate limiting

def pre_flight_check(items):
    """Scans the targeted items for missing abstracts before making API calls."""
    print("\n--- 🔍 PRE-FLIGHT CHECK: MISSING ABSTRACTS ---")
    
    missing_abstracts = []
    for item in items:
        abstract = item['data'].get('abstractNote', '').strip()
        if not abstract:
            title = item['data'].get('title', 'Untitled')
            missing_abstracts.append(title)
            
    if missing_abstracts:
        print(f"⚠️ Found {len(missing_abstracts)} items missing an abstract:")
        # Only print the first 10 to avoid console spam
        for i, title in enumerate(missing_abstracts[:10], 1):
            print(f"   {i}. {title[:75]}...")
        if len(missing_abstracts) > 10:
             print(f"   ...and {len(missing_abstracts) - 10} more.")
        print("These items will be SKIPPED during this run.")
    else:
        print("✅ All items have abstracts! You are good to go.")
        
    print("----------------------------------------------\n")
    time.sleep(2) # Brief pause so the user can see the report

def enforce_tag_rules(raw_tags):
    """Cleans tags, removes AI duplicates, and appends the tracking tag."""
    # 1. Standardize to lowercase and hyphens
    clean_tags = [tag.strip().lower().replace(' ', '-') for tag in raw_tags]
    
    # 2. Remove any duplicate tags the AI might have accidentally generated
    unique_tags = list(set(clean_tags))
    
    # 3. Append our exact tracking tag
    unique_tags.append("_CLASSIFIED")
    
    return unique_tags

def run_pipeline():
    mode_text = "🕵️ (DRY RUN MODE - NO CHANGES WILL BE SAVED)" if DRY_RUN else "🔥 (LIVE MODE - UPDATING ZOTERO)"
    target_text = "📁 TARGETING: '00 - Unclassified' Folder" if TARGET_UNCLASSIFIED else "📚 TARGETING: Entire Zotero Library"
    
    print(f"--- 🚀 STARTING ZOTERO CLASSIFIER ---\n{mode_text}\n{target_text}\n")
    
    # 1. Fetch Items
    try:
        if TARGET_UNCLASSIFIED:
            items = get_unclassified_items()
        else:
            items = get_all_top_items()
    except Exception as e:
         print(f"❌ ERROR fetching items from Zotero: {e}")
         return

    if not items:
        print("✅ No items found to process. Everything is up to date!")
        return

    # 2. Filter out already classified items early
    items_to_process = []
    for item in items:
        tags = [t['tag'] for t in item['data'].get('tags', [])]
        if "_CLASSIFIED" not in tags:
             items_to_process.append(item)
             
    if not items_to_process:
         print(f"✅ Found {len(items)} items, but all are already tagged with '_CLASSIFIED'.")
         return

    print(f"📚 Found {len(items_to_process)} items waiting to be classified.")
    
    # Apply limit if configured
    if MAX_ITEMS > 0:
         items_to_process = items_to_process[:MAX_ITEMS]
         print(f"⏳ MAX_ITEMS is set. Limiting this run to {MAX_ITEMS} items.")

    pre_flight_check(items_to_process)
    
    # 3. Fetch existing tags to guide the LLM
    print("Fetching existing library tags for context...")
    try:
        existing_tags = get_all_tags()
        # Filter out the tracker tag so we don't confuse the LLM
        context_tags = [t for t in existing_tags if t != "_CLASSIFIED"] 
    except Exception as e:
        print(f"⚠️ Could not fetch tags: {e}. Proceeding without tag context.")
        context_tags = []

    # 4. Process Loop
    for index, item in enumerate(items_to_process, start=1):
        title = item['data'].get('title', 'Untitled')
        abstract = item['data'].get('abstractNote', '').strip()
        
        print(f"\n[{index}/{len(items_to_process)}] Processing: {title[:70]}...")
        
        if not abstract:
            print("   ⏩ Skipping: No abstract found.")
            continue
            
        # Call the LLM
        classification = classify_paper(title, abstract, context_tags)
        
        if not classification:
            print("   ❌ Failed to get AI classification. Skipping.")
            continue
            
        # Clean the tags and update the classification dictionary
        raw_tags = classification.get('tags', [])
        clean_tags = enforce_tag_rules(raw_tags)
        classification['tags'] = clean_tags

        target_folder = classification.get('target_folder', 'Unknown')
        
        if DRY_RUN:
            print(f"   [PREVIEW] Suggested Folder: {target_folder}")
            print(f"   [PREVIEW] Generated Tags:   {clean_tags}")
            print("   [PREVIEW] Skipping save to Zotero.")
        else:
            print(f"   🤖 AI Folder: {target_folder}")
            print(f"   🏷️  Tags: {clean_tags}")
            
            success = update_item_classification(item, classification)
            if success:
                 print("   ✅ Successfully updated and moved item.")
            else:
                 print("   ❌ Failed to update Zotero.")
                 
        # Respect Rate Limits (don't sleep on the very last item)
        if index < len(items_to_process):
            time.sleep(RATE_LIMIT_DELAY)

    if DRY_RUN:
        print("\n🏁 Dry run complete! If the preview looks good, change DRY_RUN = False and run again.")
    else:
        print("\n🎉 Classification complete!")

if __name__ == "__main__":
    run_pipeline()