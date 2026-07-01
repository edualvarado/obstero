import argparse
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from src.zotero_api import get_all_top_items, get_unclassified_items, get_all_tags, update_item_classification
from src.llm_api import classify_paper

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

def run_pipeline(dry_run=True, target_unclassified=True, max_items=0, rate_limit_delay=2):
    mode_text = "🕵️ (DRY RUN MODE - NO CHANGES WILL BE SAVED)" if dry_run else "🔥 (LIVE MODE - UPDATING ZOTERO)"
    target_text = "📁 TARGETING: '00 - Unclassified' Folder" if target_unclassified else "📚 TARGETING: Entire Zotero Library"

    print(f"--- 🚀 STARTING ZOTERO CLASSIFIER ---\n{mode_text}\n{target_text}\n")

    # 1. Fetch Items
    try:
        if target_unclassified:
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
    if max_items > 0:
         items_to_process = items_to_process[:max_items]
         print(f"⏳ max_items is set. Limiting this run to {max_items} items.")

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

        if dry_run:
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
            time.sleep(rate_limit_delay)

    if dry_run:
        print("\n🏁 Dry run complete! If the preview looks good, re-run with --live.")
    else:
        print("\n🎉 Classification complete!")

def parse_args():
    parser = argparse.ArgumentParser(description="Classify Zotero items into folders/tags via Claude.")
    parser.add_argument("--live", action="store_true", help="Actually write changes to Zotero (default: dry-run preview).")
    parser.add_argument("--all-items", action="store_true", help="Scan the entire library instead of just '00 - Unclassified'.")
    parser.add_argument("--max-items", type=int, default=0, help="Cap the number of items processed (0 = no limit).")
    parser.add_argument("--rate-limit-delay", type=float, default=2, help="Seconds to wait between LLM calls.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        dry_run=not args.live,
        target_unclassified=not args.all_items,
        max_items=args.max_items,
        rate_limit_delay=args.rate_limit_delay,
    )
