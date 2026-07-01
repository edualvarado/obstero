import argparse
import importlib
import sys
sys.stdout.reconfigure(encoding='utf-8')

classify = importlib.import_module("01_classification")
summarize = importlib.import_module("02_summary")
sync = importlib.import_module("03_sync_to_obsidian")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the full Obstero pipeline: classify -> summarize -> sync to Obsidian."
    )
    parser.add_argument("--live", action="store_true", help="Actually write changes at every stage (default: dry-run preview).")
    parser.add_argument("--skip-classify", action="store_true", help="Skip Stage 1 (classification).")
    parser.add_argument("--skip-summarize", action="store_true", help="Skip Stage 2 (summarization).")
    parser.add_argument("--skip-sync", action="store_true", help="Skip Stage 3 (Obsidian sync).")
    parser.add_argument("--max-items", type=int, default=0, help="Stage 1: cap items classified (0 = no limit).")
    parser.add_argument("--max-papers", type=int, default=50, help="Stage 2: cap papers summarized.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Stage 3: cap files written to the vault.")
    return parser.parse_args()


def main():
    args = parse_args()
    dry_run = not args.live

    if not args.skip_classify:
        print("\n========== STAGE 1: CLASSIFY ==========")
        classify.run_pipeline(dry_run=dry_run, max_items=args.max_items)
    else:
        print("\n========== STAGE 1: CLASSIFY (skipped) ==========")

    if not args.skip_summarize:
        print("\n========== STAGE 2: SUMMARIZE ==========")
        summarize.run_summary_pipeline(dry_run=dry_run, max_papers=args.max_papers)
    else:
        print("\n========== STAGE 2: SUMMARIZE (skipped) ==========")

    if not args.skip_sync:
        print("\n========== STAGE 3: SYNC TO OBSIDIAN ==========")
        sync.run_sync(dry_run=dry_run, chunk_size=args.chunk_size)
    else:
        print("\n========== STAGE 3: SYNC TO OBSIDIAN (skipped) ==========")

    print("\n🎉 Pipeline run complete.")


if __name__ == "__main__":
    main()
