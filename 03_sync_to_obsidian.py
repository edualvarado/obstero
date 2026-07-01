import os
import re
import html
from pathlib import Path
from pyzotero import zotero
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
DRY_RUN = False
KEEP_AI_LINKS = False
CHUNK_SIZE = 1000        
BASE_LIT_FOLDER = "01 - Literature"
TARGET_TAG = "_SUMMARIZED"

PRIMITIVES_TO_LINK = [
    # --- MASTER LINKS ---
    "01 - Digital Humans & Appearance",
    "02 - Motion Synthesis & Animation",
    "03 - Biomechanics",
    "04 - Computer Vision",
    "05 - Robotics & Control",

    # --- Graphics, Animation & Motion ---
    "Unreal Engine",
    "UE|Unreal Engine",
    "Motion Synthesis",
    "SMPL",
    "Digital Humans",
    "Inverse Kinematics",
    "IK|Inverse Kinematics",
    "Forward Kinematics",
    "FK|Forward Kinematics",
    "AMASS",
    "Motion Capture",
    "Motion Capture Database",
    "VFX",
    "Epic Games",
    "SDF",
    "LBS",
    "Blend Shapes",                             # NEW: common in facial animation / avatars
    "Blendshapes|Blend Shapes",
    "Rigging",                                  # NEW: character setup pipeline
    "Physics-Based Animation",                  # NEW: broad connector across sim & control papers
    "Cloth Simulation",                         # NEW: links sim, rendering, and ML papers
    "Rigid Body Simulation",                    # NEW
    "Articulated Body",                         # NEW: links robotics and character animation
    "FLAME",                                    # NEW: face parametric model
    "3D Morphable Model",                       # NEW: face / body shape models
    "3DMM|3D Morphable Model",
    "Avatar",                                   # NEW: broad connector
    "Point Cloud",
    "Point-cloud|Point Cloud",                                                            # NEW: 3D representation used across vision & graphics
    "Mesh",                                     # NEW: fundamental 3D primitive
    "Physically Based Rendering",               # NEW: PBR / shading research
    "PBR|Physically Based Rendering",
    "Ray Tracing",
    "RT|Ray Tracing",                              # NEW
    "3D Reconstruction",                        # NEW: connects NeRF, SfM, SLAM papers

    # --- Machine Learning & Generative AI ---
    "Neural Radiance Fields",
    "NeRF|Neural Radiance Fields",              # NEW alias
    "Gaussian Splatting",
    "3D Gaussian Splatting|Gaussian Splatting", # NEW alias
    "Diffusion Models",
    "Diffusion Model|Diffusion Models",
    "Score Matching",                           # NEW: theoretical backbone of diffusion models
    "Flow Matching",                            # NEW: growing alternative to diffusion
    "Normalizing Flows",                        # NEW
    "Transformer Architecture",
    "Transformer|Transformer Architecture",     # NEW alias
    "Vision Transformer",                       # NEW
    "ViT|Vision Transformer",
    "Attention Mechanism",                      # NEW: connects NLP and vision papers
    "Self-Attention|Attention Mechanism",
    "CNN",
    "CNNs|CNN",                                    # NEW alias
    "GAN",
    "GANs|GAN",        # NEW alias
    "LSTM",                                     # NEW
    "Recurrent Neural Network",
    "RNN|Recurrent Neural Network",
    "VAE",
    "Variational Autoencoder|VAE",
    "MLP",
    "DDPM",
    "CLIP",
    "Large Language Model",                     # NEW: now common in motion / avatar papers
    "LLM|Large Language Model",
    "Foundation Model",                         # NEW
    "Contrastive Learning",                     # NEW
    "Self-Supervised Learning",                 # NEW
    "Transfer Learning",                        # NEW
    "Graph Neural Network",                     # NEW: used in skeleton/pose/mesh papers
    "GNN|Graph Neural Network",
    "Implicit Neural Representation",           # NEW: links NeRF, SDF, occupancy work
    "INR|Implicit Neural Representation",
    "Occupancy Networks",                       # NEW
    "U-Net",                                    # NEW: backbone in many generation/segmentation papers
    "ResNet",                                   # NEW
    "PointNet",                                 # NEW: canonical point cloud network
    "Hypernetwork",                             # NEW
    "Score Distillation Sampling",              # NEW: connects text-to-3D papers
    "SDS|Score Distillation Sampling",

    # --- Reinforcement Learning & Control ---
    "Proximal Policy Optimization",
    "PPO|Proximal Policy Optimization",
    "Reinforcement Learning",
    "Deep Reinforcement Learning",
    "RL|Reinforcement Learning",
    "MPC",
    "Model Predictive Control|MPC",             # NEW alias
    "CMA",
    "ODE",
    "Soft Actor-Critic",                        # NEW: common RL algorithm
    "SAC|Soft Actor-Critic",
    "Deep Q-Network",                           # NEW
    "DQN|Deep Q-Network",
    "Policy Gradient",                          # NEW: general class covering PPO, TRPO, etc.
    "Actor-Critic",                             # NEW
    "Imitation Learning",                       # NEW: connects RL and motion capture papers
    "Behavior Cloning",                         # NEW
    "BC|Behavior Cloning",
    "Sim-to-Real",                              # NEW: robotics & character control bridge
    "Trajectory Optimization",                  # NEW
    "Motion Planning",                          # NEW
    "Optimal Control",                          # NEW
    "Contact Dynamics",                         # NEW: connects physics sim and RL papers
    "Physics Simulation",                       # NEW

    # --- Hardware, Sensors & Vision ---
    "IMU",
    "GPU",
    "EMG",
    "Computer Vision",
    "RGB",
    "RGB-D",                                    # NEW: depth-color sensor, very common
    "SLAM",
    "DOF",
    "CUDA",
    "RTX",
    "LiDAR",                                    # NEW
    "Depth Camera",                             # NEW
    "Optical Flow",                             # NEW: links video understanding papers
    "Object Detection",                         # NEW
    "Semantic Segmentation",                    # NEW
    "Instance Segmentation|Semantic Segmentation",
    "Keypoint Detection",                       # NEW: fundamental in pose estimation
    "Pose Estimation",                          # NEW
    "Human Pose Estimation|Pose Estimation",
    "Structure from Motion",                    # NEW: connects SLAM, 3D recon, NeRF
    "SfM|Structure from Motion",
    "Feature Matching",                         # NEW
    "Stereo Vision",                            # NEW
    "MediaPipe",                                # NEW: common baseline in vision papers
    "OpenPose",                                 # NEW: common baseline in pose papers
    "COLMAP",                                   # NEW: standard SfM pipeline

    # --- Math & Optimization ---
    "PCA",
    "Principal Component Analysis|PCA",
    "Adam Optimizer",
    "ADAM|Adam Optimizer",
    "FEM",
    "QP",
    "Singular Value Decomposition",             # NEW: matrix factorization, used across papers
    "SVD|Singular Value Decomposition",
    "Stochastic Gradient Descent",              # NEW
    "SGD|Stochastic Gradient Descent",
    "Gaussian Process",                         # NEW
    "Bayesian Optimization",                    # NEW
    "Markov Chain Monte Carlo",                 # NEW
    "MCMC|Markov Chain Monte Carlo",
    "KL Divergence", 
    "KLD|KL Divergence",                                                      # NEW: core in VAE, diffusion theory
    "Chamfer Distance",                         # NEW: standard 3D loss metric
    "Wasserstein Distance",                     # NEW: used in GANs, optimal transport
    "Iterative Closest Point",                  # NEW: registration algorithm
    "ICP|Iterative Closest Point",
    "Jacobian",                                 # NEW: connects IK, optimization, physics
    "Lagrangian",                               # NEW: constrained optimization / physics
    "Convex Optimization",                      # NEW
    "Perceptual Loss",                          # NEW: image/video generation loss
    "Sparse Coding",                            # NEW
]

load_dotenv()
ZOTERO_USER_ID = os.getenv('ZOTERO_LIBRARY_ID')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')

zot = zotero.Zotero(ZOTERO_USER_ID, 'user', ZOTERO_API_KEY)

def strip_all_links(content):
    """Strips all [[brackets]] but safely leaves the display text behind."""
    pattern = re.compile(r'(?<!\!)\[\[(.*?)\]\]')
    
    def replacer(match):
        inner_text = match.group(1)
        if '|' in inner_text:
            return inner_text.split('|', 1)[1]
        return inner_text.split('#')[0]
        
    return pattern.sub(replacer, content)

def auto_link_content(content, concept_entry):
    """Safely injects wiki-links ONLY on the first occurrence in the text."""
    if '|' in concept_entry:
        search_term, target_note = concept_entry.split('|', 1)
    else:
        search_term = concept_entry
        target_note = concept_entry

    parts = re.split(r'(\[\[.*?\]\])', content)
    pattern = rf'\b({re.escape(search_term)})\b'
    
    for i in range(0, len(parts), 2):
        if re.search(pattern, parts[i], flags=re.IGNORECASE):
            parts[i] = re.sub(pattern, rf'[[{target_note}|\1]]', parts[i], count=1, flags=re.IGNORECASE)
            break
            
    return "".join(parts)

def format_obsidian_content(raw_content):
    """The master formatting switchboard."""
    if KEEP_AI_LINKS:
        return raw_content  # Do nothing, trust the AI
        
    # Phase 1: The Nuke
    cleaned_content = strip_all_links(raw_content)
    
    # Phase 2: The Pave
    sorted_concepts = sorted(list(set(PRIMITIVES_TO_LINK)), key=len, reverse=True)
    final_content = cleaned_content
    
    for concept in sorted_concepts:
        final_content = auto_link_content(final_content, concept)
        
    return final_content

def clean_filename(title):
    cleaned = title.replace(":", " -").replace("/", "-").replace("\\", "-")
    return re.sub(r'[?*<>|"]', '', cleaned).strip()

def html_to_markdown(html_content):
    text = html_content
    text = re.sub(r'<(?:strong|b)>', '**', text)
    text = re.sub(r'</(?:strong|b)>', '**', text)
    text = re.sub(r'<(?:em|i)>', '*', text)
    text = re.sub(r'</(?:em|i)>', '*', text)
    
    lines = []
    level = -1
    tokens = re.split(r'(<(?:ul|ol|li|/ul|/ol|/li|p|div|br|/p|/div)[^>]*>)', text, flags=re.IGNORECASE)
    
    for token in tokens:
        clean_t = token.lower()
        if '<ul' in clean_t or '<ol' in clean_t:
            level += 1
        elif '</ul' in clean_t or '</ol' in clean_t:
            level -= 1
        elif '<li' in clean_t:
            indent = "    " * level 
            lines.append(f"\n{indent}- ")
        elif '<p' in clean_t or '<div' in clean_t or '<br' in clean_t:
            lines.append("\n")
        elif token.startswith('<'):
            continue 
        else:
            content = html.unescape(token).strip()
            if content:
                lines.append(content)

    text = "".join(lines)
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def get_full_collection_path(item, all_collections):
    if not item['data'].get('collections'):
        return []
    col_key = item['data']['collections'][0]
    col = next((c for c in all_collections if c['key'] == col_key), None)
    if not col: return []
    
    path_parts = [col['data']['name']]
    parent_key = col['data'].get('parentCollection')
    while parent_key:
        parent = next((c for c in all_collections if c['key'] == parent_key), None)
        if parent:
            path_parts.insert(0, parent['data']['name'])
            parent_key = parent['data'].get('parentCollection')
        else:
            parent_key = None
    return path_parts

def run_sync():
    print(f"--- 🔄 SYNCING TO: {OBSIDIAN_VAULT_PATH} ---")
    all_collections = zot.all_collections()
    items = zot.everything(zot.top(tag=TARGET_TAG))
    
    processed_count = 0
    for item in items:
        if processed_count >= CHUNK_SIZE: break

        data = item['data']
        title = data.get('title', 'Untitled')
        safe_title = clean_filename(title)
        
        # --- FOLDER & PARENT LOGIC ---
        path_parts = get_full_collection_path(item, all_collections)
        rel_path = "/".join(path_parts) if path_parts else "Unsorted"
        
        # Identify the Parent Note (Text Type)
        # Finds the numbered category (e.g., "03 - Biomechanics")
        parent_name = ""
        for part in path_parts:
            if re.match(r'^\d{2}\s-', part):
                parent_name = part
                break
        
        dest_dir = Path(OBSIDIAN_VAULT_PATH) / BASE_LIT_FOLDER / rel_path
        dest_file = dest_dir / f"{safe_title}.md"

        if dest_file.exists():
            continue

        # Metadata extraction
        extra = data.get('extra', '')
        citekey_match = re.search(r'Citation Key:\s*(\S+)', extra)
        citekey = citekey_match.group(1) if citekey_match else data.get('key')
        authors_list = [c.get('lastName', '') for c in data.get('creators', []) if 'lastName' in c]
        authors_str = ", ".join(authors_list)
        
        raw_date = data.get('date', '')
        year_match = re.search(r'\d{4}', raw_date)
        year = year_match.group(0) if year_match else "n.d."
        
        raw_tags = [t['tag'] for t in data.get('tags', [])]
        cleaned_tags = [t for t in raw_tags if t not in ['_SUMMARIZED', '_CLASSIFIED']]
        for default_tag in ['literature', 'research-intelligence']:
            if default_tag not in cleaned_tags: cleaned_tags.append(default_tag)
        yaml_tags = ", ".join([f'"{t}"' for t in cleaned_tags])

        # Link extraction
        children = zot.children(item['key'])
        pdf_link = ""
        for child in children:
            if child['data'].get('contentType') == 'application/pdf':
                pdf_link = f"| [Open PDF](zotero://open-pdf/library/items/{child['key']})"
                break

        # Process Notes
        notes = [n for n in children if n['data'].get('itemType') == 'note']
        summary_content = "\n".join([html_to_markdown(n['data']['note']) for n in notes])

        # Template with UP Link
        markdown = f"""---
type: literature
up: "[[{parent_name}]]"
citekey: "{citekey}"
authors: ["{authors_str}"]
year: "{year}"
url: "{data.get('url', '')}"
tags: [{yaml_tags}]
---

# 📄 {title}

**Links:** [Open in Zotero](zotero://select/library/items/{item['key']}) {pdf_link}

---

## 🤖 AI-Generated Intelligence

{summary_content}
"""

        if not DRY_RUN:
            dest_dir.mkdir(parents=True, exist_ok=True)

            final_formatted_summary = format_obsidian_content(markdown)

            with open(dest_file, "w", encoding="utf-8") as f:
                f.write(final_formatted_summary)
                
            print(f"✅ [{processed_count + 1}/{CHUNK_SIZE}] Imported: {safe_title}")
        
        processed_count += 1

if __name__ == "__main__":
    run_sync()