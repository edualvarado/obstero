import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ZOTERO_LIBRARY_ID = os.getenv("ZOTERO_LIBRARY_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
ZOTERO_BASE_DIR = os.getenv("ZOTERO_BASE_DIR")

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_json(filename):
    with open(CONFIG_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


# Zotero uses unique keys for collections, not names. This maps your
# human-readable folder paths to those keys.
# Real values live in config/collections.json (gitignored, personal to your
# library). Run `python tools/id_extractor.py --write` to generate it, or
# copy config/collections.example.json by hand.
_collections_path = CONFIG_DIR / "collections.json"
if not _collections_path.exists():
    raise FileNotFoundError(
        f"Missing {_collections_path}. Copy config/collections.example.json to "
        "config/collections.json and fill in your own Zotero collection keys "
        "(or run `python tools/id_extractor.py --write`)."
    )
COLLECTION_IDS = _load_json("collections.json")

# 1. Get all paths except Unclassified
_all_paths = [p for p in COLLECTION_IDS.keys() if p != "00 - Unclassified"]

# 2. Filter out any path that acts as a parent to another path
VALID_FOLDERS = [
    path for path in _all_paths
    if not any(other_path.startswith(path + "/") for other_path in _all_paths)
]

# Concepts to auto-link as Obsidian wiki-links during Stage 3 sync.
# Real taxonomy lives in config/primitives.json (gitignored, personal research
# taxonomy). Falls back to the small generic example if missing -- auto-linking
# just degrades gracefully rather than blocking the sync.
_primitives_path = CONFIG_DIR / "primitives.json"
if not _primitives_path.exists():
    print(
        f"⚠️  {_primitives_path} not found. Falling back to "
        "config/primitives.example.json. Run `python tools/discover_primitives.py "
        "--write` or copy the example to config/primitives.json to customize."
    )
    PRIMITIVES_TO_LINK = _load_json("primitives.example.json")
else:
    PRIMITIVES_TO_LINK = _load_json("primitives.json")
