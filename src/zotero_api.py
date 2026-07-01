from pyzotero import zotero
from src.config import ZOTERO_LIBRARY_ID, ZOTERO_API_KEY, COLLECTION_IDS, ZOTERO_BASE_DIR
import io
from pypdf import PdfReader
import os
import markdown

# Initialize Zotero Client
zot = zotero.Zotero(ZOTERO_LIBRARY_ID, 'user', ZOTERO_API_KEY)

def get_unclassified_items():
    """Fetches items from the '00 - Unclassified' collection."""
    unclassified_id = COLLECTION_IDS.get("00 - Unclassified")
    if not unclassified_id:
        raise ValueError("Unclassified collection ID not set in config.py")
    
    # Get top-level items (ignores attachments/PDFs which are children)
    return zot.collection_items_top(unclassified_id)

def add_note_to_item(parent_item_key, note_content):
    """Creates a child note attached to a specific Zotero item."""
    template = zot.item_template('note')
    template['note'] = note_content
    template['parentItem'] = parent_item_key
    
    try:
        resp = zot.create_items([template])
        if resp['successful']:
            return True
        else:
            print(f"Error creating note: {resp.get('failed')}")
            return False
    except Exception as e:
        print(f"Zotero API Error: {e}")
        return False

def get_all_top_items():
    """Fetches all top-level items (papers, books) ignoring attachments."""
    print("Downloading all items from Zotero. This may take a minute...")
    # zot.everything() handles the pagination automatically for large libraries
    return zot.everything(zot.top())

def get_all_tags():
    """Fetches all existing tags in your library to ensure consistency."""
    return zot.tags()

def update_item_classification(item, ai_classification):
    """Applies tags and moves the item to the new collection."""
    
    # Now we just grab the exact path string Claude selected
    target_collection_key = ai_classification.get("target_folder")
    target_collection_id = COLLECTION_IDS.get(target_collection_key)
    
    if not target_collection_id:
        print(f"   ⚠️ Skipping: Claude suggested invalid folder '{target_collection_key}'")
        return False

    new_tags = ai_classification.get("tags", [])

    # This completely overwrites any existing tags with our perfect AI tags
    item['data']['tags'] = [{'tag': tag} for tag in new_tags]

    # 3. Update the collection (move it)
    current_collections = item['data'].get('collections', [])
    
    # Remove from unclassified
    unclassified_id = COLLECTION_IDS.get("00 - Unclassified")
    if unclassified_id in current_collections:
        current_collections.remove(unclassified_id)
        
    # Add to new target collection
    current_collections.append(target_collection_id)
    item['data']['collections'] = current_collections

    # 4. Push the update back to Zotero
    try:
        zot.update_item(item)
        print(f"Successfully moved '{item['data']['title']}' to {target_collection_key}")
        return True
    except Exception as e:
        print(f"Failed to update item in Zotero: {e}")
        return False
    
def _sanitize_text(text):
    """Removes lone Unicode surrogate characters that cause UTF-8 encoding errors."""
    return text.encode('utf-8', errors='ignore').decode('utf-8')

def get_pdf_text_for_item(item_key):
    """Finds the PDF attached to a Zotero item and extracts its text."""
    children = zot.children(item_key)
    
    for child in children:
        if child['data'].get('itemType') == 'attachment' and child['data'].get('contentType') == 'application/pdf':
            
            # Scenario A: The PDF is physically stored in Zotero
            if child['data'].get('linkMode') in ['imported_file', 'imported_url']:
                try:
                    file_bytes = zot.file(child['key'])
                    reader = PdfReader(io.BytesIO(file_bytes))
                    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    return _sanitize_text(text)
                except Exception as e:
                    print(f"   ❌ Failed to read Zotero storage PDF: {e}")
                    return None
            # Scenario B: The PDF is linked locally (e.g., ZotFile/OneDrive)
            elif child['data'].get('linkMode') == 'linked_file':
                raw_path = child['data'].get('path')
                
                # Resolve the 'attachments:' prefix to your real OneDrive path
                if raw_path.startswith("attachments:"):
                    if not ZOTERO_BASE_DIR:
                        print("   ❌ Error: ZOTERO_BASE_DIR is missing in your .env file!")
                        return None
                        
                    # Strip 'attachments:' and any leading slashes
                    relative_path = raw_path.replace("attachments:", "").lstrip("\\/")
                    # Join your OneDrive path with the PDF's relative path
                    local_path = os.path.join(ZOTERO_BASE_DIR, relative_path)
                else:
                    local_path = raw_path # Fallback if it's already an absolute path
                
                # Windows paths can be tricky, so we normalize it
                clean_path = os.path.normpath(local_path)
                print(f"   🔍 Locating file at: {clean_path}")
                
                if not os.path.exists(clean_path):
                    print(f"   ❌ File not found on disk at {clean_path}")
                    return None
                
                # --- 1. NEW: CHECK FOR CLOUD STUBS ---
                try:
                    file_size_kb = os.path.getsize(clean_path) / 1024
                    if file_size_kb < 100:
                        print(f"   ⚠️ Skipping: File is a OneDrive placeholder ({file_size_kb:.1f} KB). Please download it.")
                        return None
                except Exception as e:
                    print(f"   ❌ Could not check file size: {e}")
                    return None
                
                # --- 2. NEW: HEAL THE PDF IF CORRUPTED ---
                heal_pdf_header(clean_path)
                
                # --- 3. EXISTING: READ THE PDF ---
                try:
                    reader = PdfReader(clean_path)
                    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    return _sanitize_text(text)
                except Exception as e:
                    print(f"   ❌ Failed to read local PDF at {clean_path}: {e}")
                    return None
                
                # try:
                #     # Windows paths can be tricky, so we normalize it
                #     clean_path = os.path.normpath(local_path)
                #     print(f"   🔍 Locating file at: {clean_path}")
                    
                #     reader = PdfReader(clean_path)
                #     text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                #     return text
                # except Exception as e:
                #     print(f"   ❌ Failed to read local PDF at {clean_path}: {e}")
                #     return None
                    
    return None # No PDF found

def manage_ai_notes(item_key, note_title="🤖 AI-Generated Summary"):
    """Finds and deletes any existing notes with the specified title."""
    children = zot.children(item_key)
    for child in children:
        if child['data'].get('itemType') == 'note':
            note_content = child['data'].get('note', '')
            # Zotero wraps note content in HTML tags sometimes, so we check if our title is inside
            if note_title in note_content:
                print(f"   🗑️ Found existing '{note_title}'. Deleting it...")
                zot.delete_item(child)

def add_note_to_item(parent_item_key, note_content):
    """Creates a child note attached to a specific Zotero item."""
    
    # Translate Claude's raw Markdown into Zotero-friendly HTML
    html_content = markdown.markdown(note_content)
    
    template = zot.item_template('note')
    template['note'] = html_content
    template['parentItem'] = parent_item_key
    
    resp = zot.create_items([template])
    return resp.get('successful', False)

def heal_pdf_header(pdf_path):
    """Scans a file for the true PDF start and strips garbage bytes at the top."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
            
        # Look for the actual start of the PDF
        pdf_start_index = content.find(b'%PDF-')
        
        # If it's found, but not at the very beginning (index 0)
        if pdf_start_index > 0:
            print(f"   🛠️ Healing corrupted PDF header (found garbage bytes)...")
            # Slice the file to start exactly at %PDF- and overwrite it
            with open(pdf_path, 'wb') as f:
                f.write(content[pdf_start_index:])
            return True
    except Exception as e:
        pass
    
    return False